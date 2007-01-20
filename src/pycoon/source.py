#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import os
import urlparse
import urllib2
import logging
import pkg_resources
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
    def __init__(self, filename, uri=None):
        if uri:
            self.uri = uri
        else:
            self.uri = filename
        self.filename = filename
        logging.getLogger("source.file").debug("Created with filename %s" % filename)

    def getLastModified(self):
        return os.path.getmtime(self.filename)
    
    def read(self):
        if not os.path.isfile(self.filename):
            raise ResourceNotFoundException("File %s not found" % self.filename)
        fd = open(self.filename, "rb")
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
        logging.getLogger("source.http").debug("Created with URI %s" % self.uri)        
        
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
        self.log = logging.getLogger("source.sitemap")
        self.uri = "cocoon:%s" % uri
        self.log.debug("Initializing source with URI: %s" % self.uri)
        if uri.startswith("//"):
            self.processor = env.objectModel["root-processor"]
            uri = uri[2:]
            self.env = env.createWrapper(uri)
            self.env.contextPath = self.processor.contextPath
        elif uri.startswith("/"):
            self.processor = env.objectModel["processor"]
            uri = uri[1:]
            self.env = env.createWrapper(uri)
        else:
            raise Exception("Malformed cocoon URI: %s" % self.uri)
        self.processingPipeline = self.processor.buildPipeline(self.env)
        
    def read(self):
        try:
            self.processingPipeline.process(self.env)
        except Exception, e:
            if hasattr(self.processingPipeline, "handleErrorsNode"):
                self.log.debug("Exception occured, found <map:handle-errros>, handling")
                self.processingPipeline.handleErrorsNode.invoke(self.env, None, e)
            else:                
                self.log.debug("Exception occured, no <map:handle-errros>, re-raising")
                raise
        return self.env.response.body
        
class SourceResolver:
    """
    Allows to get a Source instance for any type of URI.
    """
    def __init__(self, env=None):
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
        elif scheme == "rawegg":
            egg, filename = path.split(":", 1) 
            return FileSource(pkg_resources.resource_filename(egg, filename[1:]), uri)
        else:
            raise Exception("Unknown URI scheme: %s for URI %s" % (scheme, uri))

