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
from pycoon.components import Component, Serializer, Selector, Matcher, Generator, Transformer, Reader
from pycoon import ns

ns["ex"] = "http://apache.org/cocoon/exception/1.0"

mimetypes.init()

class XmlSerializer(Serializer):
    def configure(self, element=None):
        Component.configure(self, element)
        if element is not None:
            self.encoding = element.find("encoding").text
    
    def serialize(self, env, params):
        self.log.debug('<map:serialize> process()')
        if env.isExternal:
            self.log.debug('Serializing XML infoset to string')
            env.response.body = etree.tostring(env.response.body, self.encoding)
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
        self.log.debug('<map:generate src="%s"> process()' % source.uri)
        data = source.read()
        if isinstance(data, str):
            env.response.body = etree.fromstring(data)
        else:
            env.response.body = data

class ExceptionGenerator(Generator):
    def generate(self, env, source, params):
        self.log.debug('<map:generate type="exception"> process()')
        type, value, trace = sys.exc_info()
        root = Element("{%(ex)s}exception-report" % ns)
        root.set("class", type.__name__)
        if value.args[0]:
            self.log.debug("value.args[0]: %s" % str(value))
            SubElement(root, "{%(ex)s}message" % ns).text = str(value)
        SubElement(root, "{%(ex)s}stacktrace" % ns).text = "".join(traceback.format_tb(trace))
        env.response.body = root
        env.response.status = 500
        
class TraxTransformer(Transformer):
    def transform(self, env, source, params):
        self.log.debug('<map:transform src="%s"> process()' % source.uri)
        fd = StringIO(source.read())
        fd.filename = source.uri
        xslt = etree.parse(fd)
        transform = etree.XSLT(xslt)
        doc = env.response.body
        params = dict([(k, '"%s"' % v) for k, v in params.items()])
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

