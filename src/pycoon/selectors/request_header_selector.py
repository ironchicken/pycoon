"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the request_header selector which allows pipeline processing to
be conditional upon the value of a request header.
"""

from pycoon.selectors import selector, SelectorError
from pycoon.selectors.when_element import WhenError
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "select"
    invk_syn.allowed_parent_components = ["pipeline", "match", "aggregate"]
    invk_syn.required_attribs = ["type", "header"]
    invk_syn.required_attrib_values = {"type": "request-header"}
    invk_syn.optional_attribs = ["method"]
    invk_syn.allowed_child_components = ["when","otherwise"]

    server.component_syntaxes[("select", "request-header")] = invk_syn
    return invk_syn

class request_header_selector(selector):
    """
    request_header_selector allows pipeline processing to be conditional upon the
    value of a request header.
    """

    def __init__(self, parent, header, root_path=""):
        """
        request_header_selector class constructor.

        @header: is the name of the header value to be tested
        """

        self.header = header

        selector.__init__(self, parent, root_path)

        self.description = "Request header selector(\"%s\")" % self.header

    def when_func(self, req, conditions):
        """
        This is the function which child <when> elements of this selector should use to implement
        their _descend function. It examines the request object's GET/POST parameter of the
        specified name and compares it against the given conditions. If any of them match the
        parameter's value True is returned.
        """

        header_name = interpolate(self, self.header)
        if req.headers_in.has_key(header_name):
            header_value = req.headers_in[header_name]
        else:
            return False

        if header_value in conditions:
            return True

        return False
