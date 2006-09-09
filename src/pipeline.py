"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The pipeline module contains the pipeline class.
"""

import sys, string, traceback
import lxml.etree
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.uri_pattern import uri_pattern
from pycoon.components import component, invokation_syntax

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "pipeline"
    invk_syn.allowed_parent_components = ["sitemap", "server"]
    invk_syn.required_attribs = ["name", "mime"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = ["uri-pattern", "on-error-code"]
    invk_syn.allowed_child_components = ["aggregate", "file", "xpath", "xquery", "swishe", "command", "sql",\
                                         "directory-list", "xslt", "sax-handler"]

    server.component_syntaxes[("component", "pipeline")] = invk_syn

def build_pipeline(server, sitemap, attrs, **kw_args):
    """
    Creates a new pipeline object using the given xml.sax.Attributes object and stores
    it the given server/sitemap

    @server: parent server_config object
    @sitemap: parent sitemap_config object (may be None)
    @attrs: xml.sax.Attributes object containing pipeline configuration

    kw_args can include: 'on-error-code' for error pipelines
    """
    
    pipeline_name = str(attrs['name'])
    pl_opts = {'name': pipeline_name}
               
    # determine the type of pipeline
    if attrs.has_key('uri-pattern'):
        if sitemap is None:
            raise Exception("Server may only contain error handling pipelines.")

        pipeline_type = "public"
        pl_opts['pipeline_type'] = pipeline_type

    elif attrs.has_key('on-error-code'):
        pipeline_type = "error"
        #pl_opts['on_error_code'] = int(attrs['on-error-code'])
        pl_opts['pipeline_type'] = pipeline_type
        
    else:
        if sitemap is None:
            raise Exception("Server may only contain error handling pipelines.")

        pipeline_type = "private"
        pl_opts['pipeline_type'] = pipeline_type


    # add a uri_pattern object, if a pattern is specified
    if attrs.has_key('uri-pattern'):
        pl_opts['uri_pattern'] = uri_pattern(str(attrs['uri-pattern']))
    else:
        pl_opts['uri_pattern'] = uri_pattern("")

    if attrs.has_key('cache-as'):
        pl_opts['cache_as'] = str(attrs['cache-as'])

    if attrs.has_key('mime'):
        pl_opts['mime'] = str(attrs['mime'])

    # determine the parent type and create and add the new pipeline to its parent
    if sitemap != None:
        pl_opts['parent'] = sitemap
        if pipeline_type == "public":
            if pipeline_name in sitemap.pipelines.keys():
                raise Exception("Attempted to add pipeline to sitemap with non-unique name: \"%s\"" % pipeline_name)
            pl = sitemap.pipelines[pipeline_name] = pipeline(**pl_opts)
            sitemap.pipeline_iter.append(pipeline_name)
        elif pipeline_type == "error":
            pl = sitemap.error_pipelines[int(attrs['on-error-code'])] = pipeline(**pl_opts)
        elif pipeline_type == "private":
            if pipeline_name in sitemap.pipelines.keys():
                raise Exception("Attempted to add pipeline to sitemap with non-unique name: \"%s\"" % pipeline_name)
            pl = sitemap.pipelines[pipeline_name] = pipeline(**pl_opts)
    else:
        pl_opts['parent'] = server
        pl = server.error_pipelines[int(attrs['on-error-code'])] = pipeline(**pl_opts)
    
    return pl

class pipeline(component):
    """
    pipeline encapsulates a pipeline.
    """

    role = "pipeline"
    function = "pipeline"
    
    def __init__(self, parent, name, pipeline_type, uri_pattern, mime, cache_as=""):
        """
        pipeline constructor.

        @parent: sitemap or server
        @attrs: an xml.sax.Attributes instance containing the pipeline information
        @uri_pattern: uri_pattern object which the pipeline should match
        @mime: the pipeline's MIME type
        """

        component.__init__(self, parent)

        self.name = name
        self.pipeline_type = pipeline_type
        self.pattern = uri_pattern
        self.mime = mime
        self.cache_as = cache_as

        self.description = "Pipeline: \"%s\"" % self.name

    def match(self, uri):
        """
        Returns a match object if the pipeline's uri_pattern matches the given uri,
        otherwise returns None.
        """

        return self.pattern.match(uri)

    def force_execute(self, output, uri):
        """
        Used to execute the pipeline without matching it against a uri and without returning the result
        directly to the HTTP response.

        @output: a file-like object
        @uri: a URI string
        """

        if self.server.log_debug:
            self.server.error_log.write("Pipeline \"%s\" forced to execute for uri: \"%s\"" % (self.name, uri))
        
        # create a little pretend apache request object
        class fake_request:
            def __init__(self, ostream, uri):
                self.write = ostream.write
                self.unparsed_uri = uri
                self.content_type = None

            def set_content_length(self, l): pass
            def sendfile(self, fn): pass

        # when execution is forced, its likely that self.pattern hasn't been executed and that,
        # therefore, its .uri property is empty:
        self.pattern.uri = uri
        
        return self.execute(fake_request(output, uri))

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return True

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        return (True, child_results[-1])
    
    def execute(self, req):
        """
        Execute the pipeline.

        @req: an Apache request object
        """

        # when execution is forced, its likely that self.pattern hasn't been executed and that,
        # therefore, its .uri property is empty:
        self.pattern.uri = req.unparsed_uri

        try:
            return self.__call__(req, self.pattern)
        except Exception:
            # if there was an error during execution, return error 500
            # store the exception in case there is a 500 handler pipeline
            self.server.EXCEPTION = sys.exc_info()

            if self.server.log_errors:
                self.server.error_log.write(string.join(traceback.format_exception(*sys.exc_info()), "\n"))

            return (False, apache.HTTP_INTERNAL_SERVER_ERROR)
