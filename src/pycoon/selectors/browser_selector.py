"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the browser selector which allows pipeline processing to
be conditional upon the name of the browser being used
"""

from pycoon.selectors import selector, SelectorError
from pycoon.selectors.when_element import WhenError
from pycoon.components import invokation_syntax
import re

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "select"
    invk_syn.allowed_parent_components = ["pipeline", "match", "aggregate"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "browser"}
    invk_syn.optional_attribs = ["method"]
    invk_syn.allowed_child_components = ["when","otherwise"]

    server.component_syntaxes[("select", "browser")] = invk_syn
    return invk_syn

class browser_selector(selector):
    """
    browser_selector allows pipeline processing to be conditional upon the name of
    browser being used.
    """

    def __init__(self, parent, method="exclusive", root_path=""):
        """
        browser_selector constructor.
        """

        selector.__init__(self, parent, method, root_path)

        self.description = "browser_selector()"
        self.selector_type = "browser"

    def when_func(self, req, conditions):
        """
        This is the function which child <when> elements of this selector should use to implement
        their _descend function. It examines the request object's 'User-agent' header to ascertain
        the name of the browser which made the request and returns True if it matches any of the
        given conditions.
        """

        for cond in conditions:
            if re.match(".+%s.*" % cond, req.headers_in["User-agent"], re.I) is not None:
                return True

        return False
