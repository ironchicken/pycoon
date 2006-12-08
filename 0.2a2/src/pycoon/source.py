#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import os
import urlparse
import urllib2
import logging
from pycoon import ResourceNotFoundException

class Source:
    """
    Encapsulates source access by URI, no matter what URI type is.
    """
    uri = None

    def getLastModified(self):
        raise NotImplementedError()
    
    def read(self):
        raise NotImplementedError()

class FileSource(Source):
    def __init__(self, fileName, uri=None):
        if uri:
            self.uri = uri
        else:
            self.uri = fileName
        self.fileName = fileName
        logging.getLogger("source.file").debug("Created with filename %s" % fileName)

    def getLastModified(self):
        return os.path.getmtime(self.fileName)
    
    def read(self):
        if not os.path.exists(self.fileName):
            raise ResourceNotFoundException("File %s not found" % self.fileName)
        fd = open(self.fileName, "rb")
        try:
            return fd.read()
        finally:
            fd.close()
        
class HttpSource(Source):
    """
    Simple HTTP source that supports only GET requests, thus it is inappropriate
    for REST applications that need the complete set of CRUD actions.
    """
    def __init__(self, uri):
        self.uri = uri
        
    def read(self):
        encoding = os.getenv("file.property")
        if encoding is not None:
            uri = self.uri.encode(encoding)
        else:
            uri = self.uri

        try:
            request = urllib2.Request(uri)
            opener = urllib2.build_opener()
            fd = opener.open(request)
            try:
                return fd.read()
            finally:
                fd.close()
        except urllib2.HTTPError, e:
            # TODO: anrienord: Надо ещё помыслить, но вообще в случае простого
            # HttpSource мы не должны располагать инфой о коде ошибки HTTP.
            # Поэтому пока код ниже закомменчен
            raise ResourceNotFoundException("URI not found: %s" % self.uri)
            #if e.code == 404:
            #    raise ResourceNotFoundException("URI not found: %s" % e.geturl())
            #else:
            #    raise
        
class SitemapSource(Source):
    """
    Represents sitemap pipeline output accessible via cocoon: URI.
    """
    def __init__(self, uri, env):
        if uri.startswith("/"):
            self.processor = env.objectModel["processor"]
            self.uri = uri[1:]
        else:
            raise Exception("Malformed cocoon URI: %s" % uri)
        self.env = env.createWrapper(self.uri)
        self.processingPipeline = self.processor.buildPipeline(self.env)
        
    def read(self):
        self.processingPipeline.process(self.env)
        return self.env.response.body
        
class SourceResolver:
    """
    Allows to get a Source instance for any type of URI.
    """
    def __init__(self, env):
        self.env = env
        self.log = logging.getLogger("source.resolver")
    
    def resolveUri(self, uri, baseUri=None, params={}):
        if baseUri is None:
            baseUri = self.env.contextPath
        self.log.debug('Resolving URI "%s" with base "%s"' % (uri, baseUri))
        if not uri:
            return None
        if not urlparse.urlparse(uri)[0] and baseUri != "":
            uri = "%s/%s" % (baseUri, uri)
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(uri)
        if scheme == "file" or scheme == "":
            # Windows disk volumes letters handling
            if len(path) > 2 and path[2] == ":":
                path = path[1:]
            return FileSource(path, uri)
        elif scheme == "http":
            return HttpSource(uri)
        elif scheme == "cocoon":
            return SitemapSource(path, self.env)
        else:
            raise Exception("Unknown URI scheme: %s for URI %s" % (scheme, uri))

