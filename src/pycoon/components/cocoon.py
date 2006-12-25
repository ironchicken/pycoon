#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import re
import os
import sys
import mimetypes
import traceback
import logging
import lxml.etree as etree
from lxml.etree import Element, SubElement, XSLT
from StringIO import StringIO
from pycoon.components import Component, Serializer, Selector, Matcher, Generator, Transformer, Reader, Action
from pycoon import ns

ns["ex"] = "http://apache.org/cocoon/exception/1.0"

mimetypes.init()

class XmlSerializer(Serializer):
    def configure(self, element=None):
        Component.configure(self, element)
        if element is not None:
            def get(element, default=None):
                if element is not None: return element.text
                else: return default
            self.mimeType = element.get("mime-type", "application/xml")
            self.encoding = get(element.find("encoding"), "utf-8")
            self.doctypePublic = get(element.find("doctype-public"))
            self.doctypeSystem = get(element.find("doctype-system"))
    
    def serialize(self, env, params):
        self.log.debug('<map:serialize> process()')
        if env.isExternal:
            self.log.debug('Serializing XML infoset to string')
            body = etree.tostring(env.response.body, self.encoding)
            if self.doctypePublic is not None:
                response = [
                    '<?xml version="1.0" encoding="%s"?>' % self.encoding,
                    '<!DOCTYPE html PUBLIC "%s" "%s">' % (self.doctypePublic, self.doctypeSystem),
                    body,
                ]
                env.response.body = "\n".join(response)
            else:
                env.response.body = body
        if self.statusCode >= 0:
            env.response.status = self.statusCode
        env.contentType = "%s; charset=%s" % (self.mimeType, self.encoding)
        
class RequestMethodSelector(Selector):
    def select(self, expr, objectModel, params):
        return expr == objectModel["request"].method
        
class RequestParameterSelector(Selector):
    def select(self, expr, objectModel, params):
        name = params["parameter-name"]
        return expr == objectModel["request"].params.get(name)

class ExceptionSelector(Selector):
    def configure(self, element=None):
        Component.configure(self, element)
        if element is not None:
            exceptions = element.findall("exception")
            self.classes = dict([(e.get("name"), e.get("{%(py)s}class" % ns)) for e in exceptions])
        else:
            self.classes = {}
    
    def select(self, expr, objectModel, params):
        classname = objectModel.get("throwable").__class__.__name__
        return self.classes.get(expr) == classname

class WildcardUriMatcher(Matcher):
    def match(self, pattern, objectModel, params):
        uri = objectModel["request"].uri
        pattern = re.sub("\*\*", "~~", pattern)
        pattern = re.sub("\*", "([^/]*)", pattern)
        pattern = re.sub("~~", "(.*)", pattern)
        pattern = "^%s$" % pattern
        
        m = re.search(pattern, uri)
        if m is not None:
            return dict(zip([str(i) for i in range(1, len(m.groups()) + 1)], m.groups()))
        else:
            return None

class FileGenerator(Generator):        
    def generate(self, env, source, params):
        self.uri = source.uri
        self.log.debug('<map:generate src="%s"> process()' % source.uri)
        data = source.read()
        if isinstance(data, str):
            env.response.body = etree.fromstring(data)
        else:
            env.response.body = data
            
    def __str__(self):
        return '<map:generate src="%s"/>' % self.uri

class ExceptionGenerator(Generator):
    def generate(self, env, source, params):
        self.log.debug('<map:generate type="exception"> process()')
        type, value, trace = sys.exc_info()
        root = Element("{%(ex)s}exception-report" % ns)
        root.set("class", type.__name__)
        if len(value.args) > 0 and value.args[0]:
            SubElement(root, "{%(ex)s}message" % ns).text = unicode(value.args[0])
        SubElement(root, "{%(ex)s}stacktrace" % ns).text = "".join(traceback.format_tb(trace))
        env.response.body = root
        env.response.status = 500
        
class TraxTransformer(Transformer):
    def configure(self, element=None):
        Component.configure(self, element)
        self.useRequestParameters = False
        if element is not None:
            p = element.find("use-request-parameters")
            if p is not None:
                self.useRequestParameters = (p.text == "true")
    
    def transform(self, env, source, params):
        self.log.debug('<map:transform src="%s"> process()' % source.uri)
        if "use-request-parameters" in params:
            self.useRequestParameters = (params["use-request-parameters"] == "true")
        fd = StringIO(source.read())
        if hasattr(source, "filename"):
            fd.filename = source.filename
        else:
            fd.filename = source.uri
        xslt = etree.parse(fd)
        transform = etree.XSLT(xslt)
        doc = env.response.body
        if self.useRequestParameters:
            rparams = env.objectModel["request"].params
            encoding = env.objectModel["request"].formEncoding
            if encoding is not None:
                params.update(dict([(k, v.decode(encoding)) for k, v in rparams.items()]))
            else:
                params.update(rparams)
        params = dict([(k, '"%s"' % v) for k, v in params.items()])
        self.log.debug("Stylesheet parameters:\n%s" % "\n".join(["  %s: %s" % (k, v) for k, v in params.items()]))
        env.response.body = transform(doc, **params).getroot()

class ContentAggregator(Generator):
    def __init__(self):
        self.element = None
        self.ns = None
        self.parts = None
    
    def configure(self, element=None):
        Component.configure(self, element)
        self.log = logging.getLogger("sitemap.aggregator.built-in")
    
    def generate(self, env, source, params):
        self.log.debug('<map:aggregate element="%s"> process()' % self.element)
        if self.ns is not None:
            document = Element("{%s}%s" % (self.ns, self.element))
        else:
            document = Element(self.element)            
        for part in self.parts:
            self.log.debug('<map:part src="%s"> process()' % part)
            source = env.sourceResolver.resolveUri(part)
            data = source.read()
            if isinstance(data, str):
                document.append(etree.fromstring(data))
            else:
                document.append(data)
        env.response.body = document
        
    def __str__(self):
        return "\n".join([
            '<map:aggregate element="%s" ns="%s">' % (self.element, self.ns),
            "\n".join(['  <map:part src="%s"/>' % part for part in self.parts]),
            '</map:aggregate>',
        ])

class ResourceReader(Reader):
    def read(self, env, source, params):
        if self.mimeType is None:
            root, ext = os.path.splitext(source.uri)
            self.log.debug("ext: %s" % ext)
            self.mimeType = mimetypes.types_map.get(ext, "application/octet-stream")
        env.contentType = self.mimeType
        env.response.body = source.read()
        self.log.debug('<map:read src="%s"> process()' % source.uri)
        self.log.debug("status: %d" % env.response.status)

class Pipeline(Component):
    def __init__(self):
        self.generator = None
        self.transformers = []
        self.serializer = None
        self.reader = None
        
    def configure(self, element=None):
        Component.configure(self, element)
        self.log = logging.getLogger("sitemap.pipeline.noncaching")
        
    def process(self, env):
        self.log.debug('<map:pipeline> process()')
        
        if self.generator is not None:
            if self.serializer is None: raise SitemapException("Serializer is not set")
            source = env.sourceResolver.resolveUri(self.generator.src)
            self.generator.generate(env, source, self.generator.params)
            for t in self.transformers:
                source = env.sourceResolver.resolveUri(t.src)
                t.transform(env, source, t.params)
            self.serializer.serialize(env, self.serializer.params)
        elif self.reader is not None:
            source = env.sourceResolver.resolveUri(self.reader.src)
            self.reader.read(env, source, self.reader.params)
        else:
            raise SitemapException("There is no generator or reader")
        return True

    def __str__(self):
        return "\n".join([
            "<map:pipeline>",
            "\n".join(["  %s" % line for line in str(self.generator).splitlines()]),
            "  ...",
            "</map:pipeline>",
        ])

class SendmailAction(Action):    
    hmap = {
        "from": "From",
        "to": "To",
        "replyTo": "Reply-To",
        "cc": "Cc",
        "bcc": "Bcc",
        "subject": "Subject",
    }
    
    def act(self, objectModel, params):
        assert params.get("smtp-host")
        assert params.get("from")
        assert params.get("to")
        assert params.get("body")

        charset = params.get("charset", "iso-8859-1")
        msg = "\r\n".join(
            ["%s: %s" % (self.hmap[k], v) for k, v in params.items() if k in self.hmap and v] +
            [
                "Content-Type: text/plain; charset=%s; format=flowed" % charset,
                "Content-Transfer-Encoding: 8bit",
                "\r\n%s" % params.get("body"),
            ]
        )
        import smtplib
        server = smtplib.SMTP(params.get("smtp-host"))
        if "smtp-user" in params:
            server.login(params.get("smtp-user"), params.get("smtp-password"))
        server.sendmail(params.get("from"), params.get("to"), msg.encode(charset), ["body=8bitmime"])
        server.quit()
        return {"status": "success"}
