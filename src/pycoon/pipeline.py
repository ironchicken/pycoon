"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The pipeline module contains the pipeline class.
"""

import sys, string, traceback
import lxml.etree
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.components import component, invokation_syntax

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "pipeline"
    invk_syn.allowed_parent_components = ["sitemap", "server"]
    invk_syn.required_attribs = []
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["match"]

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

    pl_opts = {}
    
    if attrs.has_key('cache-as'):
        pl_opts['cache_as'] = str(attrs['cache-as'])

    # determine the parent type and create and add the new pipeline to its parent
    if sitemap != None:
        pl_opts['parent'] = sitemap
        sitemap.pipelines.append(pipeline(**pl_opts))
        pl = sitemap.pipelines[-1]
    else:
        pl_opts['parent'] = server
        server.pipelines.append(pipeline(**pl_opts))
        pl = server.pipelines[-1]
    
    return pl

class pipeline(component):
    """
    pipeline encapsulates a pipeline.
    """

    role = "pipeline"
    function = "pipeline"
    
    def __init__(self, parent, cache_as=""):
        """
        pipeline constructor.

        @parent: sitemap or server
        @cache_as: (optional)
        """

        component.__init__(self, parent)

        self.cache_as = cache_as

        self.description = "Pipeline"

    def force_execute(self, output, uri):
        """
        Used to execute the pipeline without returning the result directly to the HTTP response.

        @output: a file-like object
        @uri: a URI string
        """

        if self.server.log_debug:
            self.server.error_log.write("Pipeline forced to execute for uri: \"%s\"" % uri)
        
        # create a little pretend apache request object
        class fake_request:
            def __init__(self, ostream, uri):
                self.write = ostream.write

                pos_qm = uri.find("?")
                if pos_qm == -1: pos_qm = len(uri)
                pos_hash = uri.find("#")
                if pos_hash == -1: pos_hash = len(uri)

                self.path = uri[:pos_qm]
                self.query = uri[pos_qm+1:pos_hash]
                self.fragment = uri[pos_hash+1:]
                
                self.uri = uri
                self.unparsed_uri = uri
                self.parsed_uri = ("context", "", "", "", self.server.server_hostname, 80, self.path, self.query, self.fragment)
                
                self.content_type = None

            def set_content_length(self, l): pass
            def sendfile(self, fn): pass

        return self.execute(fake_request(output, uri))

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        if len(child_results) > 0 and child_results[-1] is not None:
            return (True, child_results[-1])
        else:
            return (False, None)
    
    def execute(self, req):
        """
        Execute the pipeline.

        @req: an Apache request object
        """

        try:
            (success, result) = self.__call__(req)
            if isinstance(result, tuple):
                # split the result and the mime type
                return (success, result[0], result[1])
            else:
                return (success, result, "unknown")
        except Exception:
            # if there was an error during execution, return error 500
            # store the exception in case there is a 500 handler pipeline
            self.server.EXCEPTION = sys.exc_info()

            if self.server.log_errors:
                self.server.error_log.write(string.join(traceback.format_exception(*sys.exc_info()), "\n"))

            return (False, apache.HTTP_INTERNAL_SERVER_ERROR, None)

    def handle_error(self, req):
        """
        Execute the pipeline, but only using its error handler matcher for the given error code.

        @req: an Apache request object
        """

        # um, we could make all matchers check the req.status to make sure its not an error condition
        # so that this function is then the same as execute...

        for m in self.find_components("error_matcher"):
            matches = m._descend(req, None, None)
            if matches:
                (success, result) = m(req)
                if success:
                    if isinstance(result, tuple):
                        # split the result and the mime type
                        return (success, result[0], result[1])
                    else:
                        return (success, result, "unknown")

        return (False, None, None)
