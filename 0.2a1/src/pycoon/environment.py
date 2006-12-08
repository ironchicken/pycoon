#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import os
import logging
from urlparse import urlparse
from pycoon.source import SourceResolver

class Environment:
    # TODO: Use WSGI environ with some kind of wrapper class instead
    prefix = ""
    contentType = None
    
    def __init__(self, req):
        self.log = logging.getLogger("environment")
        self.uriPrefix = "/" 
        
        self.request = req
        self.response = HttpResponse()
        self.sourceResolver = SourceResolver(self)
        self.componentManager = None
        self.isExternal = True
        
        self.objectModel = {}
        self.objectModel["request"] = self.request
        self.objectModel["response"] = self.response
        
        # Possibly non-standard
        self.objectModel["processor"] = None

    def changeContext(self, newPrefix, contextPath):
        if newPrefix:
            # TODO: Correct prefix
            self.prefix += newPrefix
        if contextPath:
            if contextPath.find(":") != -1:
                s = contextPath
            else:
                s = "%s/%s" % (self.contextPath, contextPath)
            s = os.path.dirname(s)
            self.contextPath = s
        self.log.debug("New context path is %s" % self.contextPath)
        
    def createWrapper(self, uri):
        params = self.request.params.copy()
        scheme, netloc, path, paramstr, query, fragment = urlparse(uri)
        if len(query) > 0:
            params.update(dict([p.split("=") for p in query.split("&")]))
        req = HttpRequest(path, params, request=self.request)
        env = Environment(req)
        env.contextPath = self.contextPath
        env.isExternal = False
        env.componentManager = self.componentManager
        env.objectModel["processor"] = self.objectModel["processor"]
        return env

class HttpRequest:
    def __init__(self, uri, params={}, **kwargs):
        self.params = params
        self.uri = uri
        if "request" in kwargs:
            req = kwargs.get("request")
            self.formEncoding = req.formEncoding
            self.method = req.method
        else:
            self.formEncoding = None
            self.method = None
    
class HttpResponse:
    status = 200
    body = None
    exceptionAware = False

