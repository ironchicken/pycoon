#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import os
import sys
import traceback
import logging
import mimetypes
import cgi
import threading
import time
from lxml import etree

from pycoon.sitemap.treeprocessor import TreeProcessor
from pycoon.source import SourceResolver
from pycoon.environment import HttpRequest, Environment
from pycoon import ResourceNotFoundException
from pycoon.sitemap.manager import ClassLoader

class Pycoon:
    httpStatusCodes = {
        1: "Informational",
        2: "Successful",
        3: "Redirection",
        4: "Client Error",
        5: "Server Error",
        200: "OK",
        301: "Moved Permanently",
        302: "Found",
        304: "Not Modified",
        404: "Not Found",
        500: "Internal Server Error",
    }
    
    def __init__(self, conf):
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(logging.BASIC_FORMAT, None))
        root.addHandler(sh)
        try:
            self.contextPath = conf 
            source = SourceResolver().resolveUri(conf, "")
            self.xconf = etree.fromstring(source.read())
            
            logging.disable(logging.getLevelName(self.xconf.find("logging").get("disable", "NOTSET")))
            for l in self.xconf.findall("logging/loggers/logger"):
                logging.getLogger(l.get("name")).setLevel(logging.getLevelName(l.get("level", "DEBUG")))
                
            loader = ClassLoader()
            for h in self.xconf.findall("logging/handlers/handler"):
                args = [eval(arg.text) for arg in h.findall("args/arg")]
                if h.find("kwargs"):
                    kwargs = dict([(arg.get("name"), eval(arg.text)) for arg in h.findall("kwargs/arg")])
                else:
                    kwargs = {}
                handler = loader.getClass(h.get("class"))(*args, **kwargs)
                handler.setLevel(logging.getLevelName(h.get("level", "DEBUG")))
                handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT, None))
                for l in h.findall("logger-ref"):
                    logging.getLogger(l.get("name")).addHandler(handler)
                
            # Pseudo-servlet parameters (and their defaults)
            #self.params = {
                #"form-encoding": "iso-8859-1",
            #}
            self.params = dict([(p.find("param-name").text,  p.find("param-value").text)
                for p in self.xconf.findall("web-app/servlet/init-param")])
                
            os.environ.update(dict([(p.get("name"), p.get("value"))
                for p in self.xconf.findall("properties/property")]))
                
            mimetypes.init()
            for m in self.xconf.findall("web-app/mime-mapping"):
                mimetypes.add_type(m.find("mime-type").text, ".%s" % m.find("extension").text)
    
            self.processorIsShared = os.getenv("threading.treeprocessor.shared", "no") == "yes"
            
            if self.processorIsShared:
                self.processor = self.createTreeProcessor()
        finally:
            root.removeHandler(sh)

    def __call__(self, environ, startResponse):
        try: 
            threading.currentThread.errors = environ.get("wsgi.errors")
            return self.process(environ, startResponse)
        except:
            status = "500 Internal Server Error"
            type, value, trace = sys.exc_info()
            response = [status]
            if value.args:
                info = value.args[0]
            else:
                info = "No additional info available"
            response.append("\n\n%s: %s\n\n" % (type.__name__, info))
            response.append("Stacktrace:\n")
            response.append("".join(traceback.format_tb(trace)))
            self.logStatusInfo(environ, 500)
            self.logInternalError(status, environ, response)
            startResponse(status, [("content-type", "text/plain")], sys.exc_info())
            return response
            
    def process(self, environ, startResponse):
        if self.processorIsShared:
            processor = self.processor
        else:
            processor = self.createTreeProcessor()

        uri = environ.get("PATH_INFO")
        if uri and uri.startswith("/"):
            uri = uri[1:]

        params = dict([(k, v[0])
            for k, v in cgi.parse(environ.get("wsgi.input"), environ, keep_blank_values=True, strict_parsing=False).items()])

        req = HttpRequest(uri, params)
        req.formEncoding = self.params.get("form-encoding")
        req.method = environ.get("REQUEST_METHOD")

        env = Environment(req, environ=environ)
        env.changeContext("", self.contextPath)

        try:
            if processor.process(env):
                responseHeaders = []
                if env.contentType:
                    responseHeaders.append(("content-type", env.contentType))
                if not env.response.exceptionAware and env.response.status / 100 not in [2, 3]:
                    raise Exception("Exception not processed by sitemap: HTTP %d\n%s" % (env.response.status, env.response.body))
                if env.response.status in self.httpStatusCodes:
                    message = self.httpStatusCodes[env.response.status]
                else:
                    message = self.httpStatusCodes.get(env.response.status / 100, "Unknows Status Message")
                status = "%d %s" % (env.response.status, message)
                self.logStatusInfo(environ, env.response.status)
                if env.response.status / 100 == 5:
                    self.logInternalError(status, environ, env.response.body)
                if env.response.body:
                    responseHeaders.append(("content-length", str(len(env.response.body))))
                responseHeaders += env.response.headers
                startResponse(status, responseHeaders)
                if env.response.body: return [env.response.body]
                else: return []
            else:
                raise Exception("Sitemap is returned False, but no exception was raised")
        except ResourceNotFoundException, e:
            processor.log.error(e.args[0])
            status = "404 Not Found"
            response = [status]
            response.append('\n\nResource "%(uri)s" not found. Reported by built-in error handler' % self.getRequestInfo(environ))
            self.logStatusInfo(environ, 404)
            startResponse(status, [("content-type", "text/plain")])
            return response
        
    def createTreeProcessor(self):
        processor = TreeProcessor(os.path.dirname(self.contextPath))
        processor.configure(self.xconf)
        processor.log.debug("Shared processor is created")
        return processor
        
    def getRequestInfo(self, environ):
        info = {
            "addr": environ.get("REMOTE_ADDR"),
            "method": environ.get("REQUEST_METHOD"),
            "protocol": environ.get("SERVER_PROTOCOL"),
            "time": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        }
        if "HTTP_X_FORWARDED_FOR" in environ:
            info["addr"] += " fw:%s" % environ.get("HTTP_X_FORWARDED_FOR")
        if environ.get("QUERY_STRING"):
            info["uri"] = "%(PATH_INFO)s?%(QUERY_STRING)s" % environ
        else:
            info["uri"] = environ.get("PATH_INFO")
        return info
        
    def logInternalError(self, status, environ, body):
        info = self.getRequestInfo(environ)
        info["status"] = status
        rec = '%(addr)s [%(time)s] "%(method)s %(uri)s" %(status)s' % info
        logging.getLogger().error("\n".join([
            rec,
            "\n".join(["    %s: %s" % (k, v) for k, v in environ.items()]),
            "".join(body),
        ]))

    def logStatusInfo(self, environ, status):
        info = self.getRequestInfo(environ)
        info["status"] = status
        logging.getLogger("access").info('%(addr)s [%(time)s] "%(method)s %(uri)s" %(status)s' % info)

class WsgiLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
    
    def emit(self, record):
        s = "[%s] %s [%s]: %s\n" % (record.levelname, record.name, threading.currentThread().getName(), record.getMessage().encode("utf-8"))
        if hasattr(threading.currentThread, "errors"):
            threading.currentThread.errors.write(s)
        else:
            raise Exception("WsgiLoggingHandler: Error file descriptor not found. The message was:\n%s\n" % s)

lock = threading.RLock()
pycoon = None

def pycoonFactory(globalConfig, **localConf):
    lock.acquire()
    try:
        global pycoon
        if pycoon is None:
            conf = globalConfig.get("server-xconf")
            pycoon = Pycoon(conf)
    finally:
        lock.release()
    return pycoon

