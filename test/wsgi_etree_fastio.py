#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree
from StringIO import StringIO

from yaro import Yaro

@Yaro
def hello_world(req):
    req.res.headers["Content-Type"] = "text/plain"
    req.res.headers["X-Pycoon-Version"] = "0.3 pre-alpha"
    data = "Hello World!\n"
    data += "\n".join("%s: %s" % (k, v.value) for k, v in req.cookie.items())
    return data

class EnvironApp(object):
    def __init__(self, glob, **loc): pass
        
    def __call__(self, environ, start_response):
        start_response('200 OK', [("Content-Type", "text/plain")])
        return ["\n".join("%s: %s" % (k, v) for k, v in environ.items())]

class Application(object):
    def __init__(self, global_conf, **local_conf):
        self.uri = local_conf.get("http-uri", "http://del.icio.us/rss/anrienord")
        
    def __call__(self, environ, start_response):
        from pycoon.source import HttpSource
        source = HttpSource(self.uri)
        data = source.read()
        xml = etree.fromstring(data)
        
        start_response('200 OK', [("Content-Type", "application/xml")])
        
        if "wsgi.file_wrapper" in environ:
            return environ['wsgi.file_wrapper'](EtreeIO(xml))
        else:
            return [etree.tostring(xml)]
        
class EtreeMiddleware(object):
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        # Setup fast Etree I/O (pass etree._Element instances w/o serializing)
        environ["wsgi.file_wrapper"] = FileWrapper
        
        def resp(status, headers, exc_info=None):
            headers.append(("Content-Type", "application/xhtml+xml"))
            #headers = [(n, v) for n, v in headers if n != "content-type"]
            #headers.append(("content-type", "application/xhtml+xml"))
            return start_response(status, headers, exc_info)
        
        data = self.app(environ, resp)
        xml = toetree(data)

        xslt = etree.parse(open("rss10_items.xslt"))
        transform = etree.XSLT(xslt)
        res = transform(xml).getroot()
        yield etree.tostring(res)

class SimpleRouter(object):
    def __init__(self):
        app_kwargs = {"http-uri": "http://del.icio.us/rss/anrienord/wsgi"}
        self.table = {
            "/rss/wsgi": Application({}, **app_kwargs),
            "/tag/wsgi": EtreeMiddleware(Application({}, **app_kwargs)),
            "/rss": Application({}),
            "/environ": EnvironApp({}),
            "/yaro/hello-world": hello_world,
        }
    
    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path in self.table:
            environ["SCRIPT_NAME"] += path
            environ["PATH_INFO"] = ""
            return self.table[path](environ, start_response)
        else:
            status = "404 Not Found"
            start_response(status, [("Content-Type", "text/html")])
            links = "<ul>%s</ul>" % "".join(['<li><a href="%s">%s</a></li>' % (p, p) for p in self.table])
            return ["<h1>%s</h1><p>Resource %s not found.</p><p>See also:</p>%s" % (status, path, links)]
        
class EtreeIO(object):
    def __init__(self, elem):
        self.elem = elem
        self.fd = None
        
    def read(self, size=-1):
        if not self.fd:
            self.fd = StringIO(etree.tostring(self.elem))
        return self.fd.read(size)

class FileWrapper(object):
    def __init__(self, filelike, blksize=-1):
        self.filelike = filelike
        if hasattr(filelike, "close"):
            self.close = filelike.close

    def __iter__(self):
        yield self.filelike.read()

def toetree(iterable):
    if hasattr(iterable, "filelike") and isinstance(iterable.filelike, EtreeIO):
        return iterable.filelike.elem
    else:
        return etree.fromstring("".join(iterable))
        
if __name__ == "__main__":
    """
    from wsgiref.simple_server import make_server
    httpd = make_server("localhost", 8080, SimpleRouter())
    httpd.serve_forever()
    """

    """"""
    from cherrypy.wsgiserver import CherryPyWSGIServer
    server = CherryPyWSGIServer(("localhost", 8080), SimpleRouter())
   
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
    """"""
