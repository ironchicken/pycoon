"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module provides the special_matcher class which allows for easy processing of
requests made by a number of automated or common Web tools such as favicon.ico and
robots.txt.
"""

from pycoon.matchers import matcher, MatcherError
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
from pycoon.helpers import uri_pattern2regex
import re

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "match"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["type", "object"]
    invk_syn.required_attrib_values = {"type": "special"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["generate","transform","serialize","match","select","read"]

    server.component_syntaxes[("match", "special")] = invk_syn
    return invk_syn

def object_uri_patterns(object):
    """
    Given an object name ("favicon.ico", "robots.txt") returns a URI pattern string.
    """

    if object == "favicon.ico":
        return "/**favicon.ico"
    elif object == "robots.txt":
        return "/**robots.txt*"

class special_matcher(matcher):
    """
    special_matcher class allows for easy processing of requests made by a number of automated
    or common Web tools such as favicon.ico and robots.txt.
    """

    def __init__(self, parent, object, root_path=""):
        """
        sepcial_matcher constructor.

        @object: name of the special object to match; "favicon.ico", "robots.txt"
        """
        
        self.object = object

        self.regex = uri_pattern2regex(object_uri_patterns(self.object))
        self.match_obj = None
        
        matcher.__init__(self, parent, root_path="")

        self.description = "special_matcher(\"%s\")" % self.object

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
            if self.regex.pattern.find("?") >= 0:
                self.match_obj = self.regex.match(req.unparsed_uri)
            else:
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

            # check whether the required parameters have been given
            if self.allow_query and self.required_parameters is not None:
                if len(self.query_dict) > 0:
                    if len(set(self.required_parameters) - set(self.query_dict.keys())) > 0:
                        return False
                else:
                    return False

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
