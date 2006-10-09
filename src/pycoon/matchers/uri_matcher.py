"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module provides the uri_matcher class which allows pipeline execution to be
conditional on URI patterns.
"""

from pycoon.matchers import matcher, MatcherError
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
    invk_syn.optional_attribs = ["allow-query"]
    invk_syn.allowed_child_components = ["generate","transform","serialize","match","select"]

    server.component_syntaxes[("match", "uri")] = invk_syn
    return invk_syn

class uri_matcher(matcher):
    """
    uri_matcher class allows pipeline execution to be conditional on URI patterns.

    @pattern: the URI pattern string
    @allow_query: if True, then a URI including a query string will match (default: True)
    """

    def __init__(self, parent, pattern, allow_query="yes", root_path=""):
        self.pattern = pattern

        if allow_query.upper() in ["YES", "1", "Y"]:
            self.allow_query = True
        elif allow_query.upper() in ["NO", "0", "N"]:
            self.allow_query = False
        
        self.regex = uri_pattern2regex(self.pattern)
        self.match_obj = None
        
        matcher.__init__(self, parent, root_path="")

        self.description = "uri_matcher(\"%s\")" % self.pattern

    def parse_uri(self, req):
        """
        Parses the request URI into its constituent parts and stores them for later use. Returns
        True if the request uri matches this object's pattern, returns False otherwise.
        """
        
        self.req = req

        if not self.allow_query:
            if self.req.parsed_uri[apache.URI_QUERY]:
                self.match_obj = None
                return False
            else:
                self.match_obj = self.regex.match(req.parsed_uri[apache.URI_PATH])
        else:
            #self.match_obj = self.regex.match(req.unparsed_uri)
            self.match_obj = self.regex.match(req.parsed_uri[apache.URI_PATH])

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
            if self.query != None:
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

    def _descend(self, req, p_sibing_result=None, child_results=[]):
        """
        Compare the given request object's URI against this pattern. Returns True
        (i.e. allows descent) if it matches.
        """

        return self.parse_uri(req)

    def _continue(self, req, p_sibling_result=None):
        """
        If this matcher matches the given request uri, then don't allow following siblings to execute
        (i.e. return False).
        """

        return not self.parse_uri(req)
