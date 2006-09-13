"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module provides the uri_matcher class which allows pipeline execution to be
conditional on URI patterns.
"""

import pycoon.matchers
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
from pycoon.helpers import uri_pattern2regex

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "match"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["type", "pattern"]
    invk_syn.required_attrib_values = {"type": "uri"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["generate","transform","serialize","match"]

    server.component_syntaxes[("match", "uri")] = invk_syn
    return invk_syn

class uri_matcher(pycoon.matchers.matcher):
    """
    uri_matcher class allows pipeline execution to be conditional on URI patterns.

    @pattern: the URI pattern string
    """

    def __init__(self, parent, pattern, root_path=""):
        self.pattern = pattern
        self.regex = uri_pattern2regex(self.pattern)
        self.match_obj = None
        
        pycoon.matchers.matcher.__init__(self, parent, root_path="")

        self.description = "uri_matcher(\"%s\")" % self.pattern

    def _descend(self, req, p_sibing_result=None, child_results=[]):
        """
        Compare the given request object's URI against this pattern. Returns True
        (i.e. allows descent) if it matches. Also parses the request URI into its
        constituent parts and stores them for later use.
        """

        self.match_obj = self.regex.match(req.unparsed_uri)
        self.req = req

        if self.match_obj != None:
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
        If this matcher matches the given request uri, then don't allow following siblings to execute
        (i.e. return False).
        """
        
        self.match_obj = self.regex.match(req.unparsed_uri)
        return self.match_obj is None
