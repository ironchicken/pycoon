"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The sitemap module contains the sitemap_config class and its configuration file
parser class.
"""

import string, os
from xml.sax import parse, SAXException
from xml.sax.handler import ContentHandler
from pycoon import apache
from pycoon.helpers import attributes2options
from pycoon.pipeline import pipeline, build_pipeline

class sitemap_config(object):
    """
    sitemap_config holds configuration options, pipeline objects and cache data for Pycoon sitemap
    instances.
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.server = self.parent
        
        self.server_name = ""          # the name of the VirtualHost on which the handler is running
        self.document_root = ""        # the absolute path of the web application

        self.data_sources = {}         # a dictionary of database connections
        self.ds_mods = {}              # a dictionary of Python modules which implement database bindings

        self.pipelines = {}            # a dictionary of pipeline objects indexed by name
        self.error_pipelines = {}      # a dictionary of pipeline objects indexed by error code, used as error handlers
        self.pipeline_iter = []        # a list of pipeline names in the order that they should be evalulated

        self.requests_cache = {}       # a dictionary of request reponses; indexed by uri
        self.requests_cache_queue = [] # a list of cached request uris in order of when they were cached

        self.files_cache = {}          # a dictionary of ordinary files cached in memory; indexed by file name
        self.files_cache_queue = []    # a list of cached file names in order of when they were cached

    def handle(self, req):
        """
        Attempt to use the pipelines to handle the given request. Returns two values: first is flag which
        is True if the request has been handled; the second is the status/error code.

        @req: an Apache request object
        """
        
        # iterate over the pipelines
        for pi in self.pipeline_iter:
            p = self.pipelines[pi]

            # the first one that matches the req uri is executed
            if p.match(req.unparsed_uri):
                (success, result) = p.execute(req)

                if success:
                    # if its successful it writes its result to the request object
                    req.content_type = p.mime
                    req.set_content_length(len(result))
                    req.write(result)

                    if self.server.log_requests:
                        self.server.access_log.write("Pipeline \"%s\" handled request: \"%s\"" % (p.name, req.unparsed_uri))

                    return (True, apache.OK)
                else:
                    # if its not successful then it tries to find an error pipeline for the returned error code
                    return self.handle_error(req, result)

        # if execution reaches this point then no matching pipeline was found
        return self.handle_error(req, apache.HTTP_NOT_FOUND)

    def handle_error(self, req, error_code):
        """
        Attempt to use the error_pipelines to handle the given error code.

        @req: an Apache request object
        @error_code: an Apache error code
        """
        
        if error_code in self.error_pipelines.keys():
            # and if there is an error pipeline in the sitemap to handle the error code
            # then execute it.
            req.status = error_code

            if self.server.log_errors:
                self.server.error_log.write("Sitemap handling error %s; request: \"%s\"" % (error_code, req.unparsed_uri))

            (success, result) = self.error_pipelines[error_code].execute(req)

            if success:
                req.content_type = self.error_pipelines[error_code].mime
                req.set_content_length(len(result))
                req.write(result)

                return (True, apache.DONE)
            else:
                return (False, error_code)
        else:
            return (False, error_code)

class sitemap_config_parse(ContentHandler):
    """
    sitemap_config_parse parses a sitemap XML file to populate the sitemap's dictionaries
    of pipelines, data_sources, etc.
    """
    
    def __init__(self, filename, sitemap):
        """
        config_file_parse constructor. Require the filename of the sitemap.xml file. Parses the file
        immediately upon instantiation.
        """

        self.sitemap = sitemap
        self.server = self.sitemap.parent

        self.proc_comp_stack = []  # a stack for components being constructed
        
        parse(filename, self)

    def startElement(self, name, attrs):
        if name == "site-map":
            # try to set the document_root property
            if not attrs.has_key('document-root'):
                raise SAXException("<site-map> element must have a 'document-root' attribute.")
            self.sitemap.document_root = str(attrs['document-root'])
            if self.sitemap.document_root != apache.server_root() and self.sitemap.parent.log_errors:
                self.sitemap.parent.error_log.write("sitemap's document-root property is \"%s\". Is this correct?" %\
                                                    self.sitemap.document_root)

        elif name == "data-source":
            # call the registered datasource initialisation function for the type of this data-source
            if self.sitemap.parent.ds_initialisers.has_key(str(attrs['type'])):
                self.sitemap.parent.ds_initialisers[str(attrs['type'])](self.sitemap, attrs)

        elif name == "pipeline":
            # process a pipeline specification

            self.proc_comp_stack = [build_pipeline(self.server, self.sitemap, attrs)]

        elif name in self.server.component_enames:
            # process a pipeline component

            self.proc_comp_stack.append(self.proc_comp_stack[-1].add_component(\
                self.server.get_new_component(name, self.proc_comp_stack[-1], attrs, self.sitemap.document_root)))

            if self.server.log_debug:
                if len(self.proc_comp_stack) > 2:
                    self.server.error_log.write("Pipeline: %s: %s appended to %s" %\
                                                (self.proc_comp_stack[0].name, self.proc_comp_stack[-1].description, self.proc_comp_stack[-2].description))
                else:
                    self.server.error_log.write("Pipeline: %s: %s appended" %\
                                                (self.proc_comp_stack[0].name, self.proc_comp_stack[-1].description))
                                                

    def endElement(self, name):
        if name == "pipeline":
            if self.sitemap.parent.log_debug:
                self.sitemap.parent.error_log.write("Added pipeline: \"%s\"" % self.proc_comp_stack[-1].name)

        elif name in self.server.component_enames:
            self.proc_comp_stack.pop()
