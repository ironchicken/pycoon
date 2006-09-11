"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module provides the error_matcher class which allows pipeline execution to be
conditional on Apache error codes.
"""

import pycoon.matchers
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "match"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["type", "error-code"]
    invk_syn.required_attrib_values = {"type": "error"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["generate","transform","serialize","match"]

    server.component_syntaxes[("match", "error")] = invk_syn
    return invk_syn

class error_matcher(pycoon.matchers.matcher):
    """
    error_matcher class allows pipeline execution to be conditional on Apache error codes.

    @pattern: the URI pattern string
    """

    def __init__(self, parent, error_code, root_path=""):
        self.error_code = error_code
        
        pycoon.matchers.matcher.__init__(self, parent, root_path="")

        self.description = "error_matcher(\"%s\")" % self.error_code

    def _descend(self, req, p_sibing_result=None, child_results=[]):
        """
        Examines the req object's status property to determine which error code is being handled.

        The error_matcher also needs to provide information about the request URI, so it
        repeats code from uri_matcher.
        """

        if req.status == self.error_code:
            self.req = req
            self.uri = req.unparsed_uri

            # store the path portion of the URI
            path = self.req.parsed_uri[apache.URI_PATH]
            self.path = path[:path.rfind("/")]

            # store the filename portion of the URI
            self.filename = path[path.rfind("/"):]

            # store the query portion of the URI as a string
            self.query = self.req.parsed_uri[apache.URI_QUERY]

            # and as a dictionary
            self.query_dict = {}
            for q in self.query.split("&"):
                if q.find("=") >= 0:
                    (name, value) = q.split("=")
                else:
                    name = q
                    value = ""
                self.query_dict[name] = value

            # store the fragment portion of the URI
            self.fragment = self.req.parsed_uri[apache.URI_FRAGMENT]

            return True
        else:
            return False

    def _continue(self, req, p_sibling_result=None):
        """
        If the given req object's status is this matcher's error code, return False so that
        none of the following sibling component's are executed.
        """
        
        return req.status != self.error_code
