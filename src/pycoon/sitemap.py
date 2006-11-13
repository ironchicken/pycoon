"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The sitemap module contains the sitemap_config class and its configuration file
parser class.
"""

import string, os
from xml.sax import parse, SAXException
from xml.sax.handler import ContentHandler
from pycoon import apache, PycoonConfigurationError
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

        self.pipelines = []            # a list of pipeline objects

        #self.requests_cache = {}       # a dictionary of request reponses; indexed by uri
        #self.requests_cache_queue = [] # a list of cached request uris in order of when they were cached

        #self.files_cache = {}          # a dictionary of ordinary files cached in memory; indexed by file name
        #self.files_cache_queue = []    # a list of cached file names in order of when they were cached

    def handle(self, req):
        """
        Attempt to use the pipelines to handle the given request. Returns two values: first is flag which
        is True if the request has been handled; the second is the status/error code.

        @req: an Apache request object
        """
        
        # iterate over the pipelines
        for p in self.pipelines:
            (success, result, mime) = p.execute(req)

            if success:
                # if its successful it writes its result to the request object
                req.content_type = mime
                req.set_content_length(len(result))
                req.write(result)
                
                if self.server.log_requests:
                    self.server.access_log.write("Handled request: \"%s\"" % req.unparsed_uri)

                return (True, apache.OK)
            elif result is None:
                # in this case there was no error
                pass
            elif result is not None:
                # if its not successful but the result is not None, then it is an error code
                req.status = result
                return self.handle_error(req, result)

        # if execution reaches this point then the request was not handled
        req.status = apache.HTTP_NOT_FOUND
        return self.handle_error(req, apache.HTTP_NOT_FOUND)

    def handle_error(self, req, error_code):
        """
        Attempt to use the error_pipelines to handle the given error code.

        @req: an Apache request object
        @error_code: an Apache error code
        """

        for p in self.pipelines:
            (success, result, mime) = p.handle_error(req)
        
            if success:
                req.status = error_code

                if self.server.log_errors:
                    self.server.error_log.write("Sitemap handling error %s; request: \"%s\"" % (error_code, req.unparsed_uri))

                req.content_type = mime
                req.set_content_length(len(result))
                req.write(result)

                return (True, apache.DONE)

        # if execution reaches this point then the error was not handled
        return (False, error_code)

class SitemapError(PycoonConfigurationError): pass

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
            # some SAX flags
            self.in_components = False
            self.in_pipelines = False
            
            # try to set the document_root property
            if not attrs.has_key('document-root'):
                raise SitemapError("<site-map> element must have a 'document-root' attribute.")

            self.sitemap.document_root = str(attrs['document-root'])

            if self.sitemap.document_root != apache.server_root() and self.sitemap.parent.log_errors:
                self.sitemap.parent.error_log.write("sitemap's document-root property is \"%s\". Is this correct?" %\
                                                    self.sitemap.document_root)

        elif name == "components":
            self.in_components = True
            
        elif name == "data-source":
            # process a specified data source
            if not self.in_components:
                raise SitemapError("<data-source> element may only appear inside the <components> element.")
            
            # call the registered datasource initialisation function for the type of this data-source
            if self.sitemap.parent.ds_initialisers.has_key(str(attrs['type'])):
                self.sitemap.parent.ds_initialisers[str(attrs['type'])](self.sitemap, attrs)

        elif name == "pipelines":
            # set the in_pipelines flag to True
            self.in_pipelines = True
            
        elif name == "pipeline":
            # process a pipeline
            if not self.in_pipelines:
                raise SitemapError("<pipeline> element may only appear inside <pipelines> element.")
            
            # create a pipeline object and set it as the first member of the temporary storage
            # stack self.proc_comp_stack
            self.proc_comp_stack = [build_pipeline(self.server, self.sitemap, attrs)]

        elif name in self.server.component_enames:
            # process a pipeline component

            # creates a component from the current element's attributes using the server_config.get_new_component
            # method; adds the component as a child to the previously created component and also appends it
            # to the temporary storage stack
            self.proc_comp_stack.append(self.proc_comp_stack[-1].add_component(\
                self.server.get_new_component(name, self.proc_comp_stack[-1], attrs, self.sitemap.document_root)))

            if self.server.log_debug:
                if len(self.proc_comp_stack) > 2:
                    self.server.error_log.write("%s appended to %s" %\
                                                (self.proc_comp_stack[-1].description, self.proc_comp_stack[-2].description))
                else:
                    self.server.error_log.write("%s appended" % self.proc_comp_stack[-1].description)

        else:
            raise SitemapError("Unrecognised sitemap element: <%s>" % name)
                                                

    def endElement(self, name):
        if name == "pipeline":
            if self.sitemap.parent.log_debug:
                self.sitemap.parent.error_log.write("Added pipeline: \"%s\"" % self.proc_comp_stack[-1].description)

        elif name in self.server.component_enames:
            self.proc_comp_stack.pop()

        elif name == "pipelines":
            self.in_pipelines = False

        elif name == "components":
            self.in_components = False
