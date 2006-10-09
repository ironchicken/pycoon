"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the browser_class selector which allows pipeline processing to
be conditional upon the type of browser being used: [text|braille|aural|graphic]
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
    invk_syn.required_attrib_values = {"type": "browser-class"}
    invk_syn.optional_attribs = ["method"]
    invk_syn.allowed_child_components = ["when","otherwise"]

    server.component_syntaxes[("select", "browser-class")] = invk_syn
    return invk_syn

BROWSER_CLASSES = {
    re.compile(".*Links.*", re.I): "text",
    re.compile(".*Lynx.*", re.I): "text",
    re.compile(".*Konqueror.*", re.I): "graphic",
    re.compile(".*Galeon.*", re.I): "graphic",
    re.compile(".*MSIE.*", re.I): "graphic",
    re.compile(".*Safari.*", re.I): "graphic"}

class browser_class_selector(selector):
    """
    browser_class_selector allows pipeline processing to be conditional upon the type of
    browser being used: [text|braille|aural|graphic]
    """

    def __init__(self, parent, method="exclusive", root_path=""):
        """
        browser_class_selector constructor.
        """

        selector.__init__(self, parent, method, root_path)

        self.description = "browser_class_selector()"
        self.selector_type = "browser-class"

    def when_func(self, req, conditions):
        """
        This is the function which child <when> elements of this selector should use to implement
        their _descend function. It examines the request object's 'User-agent' header to ascertain
        which class of browser made the request and returns True if it matches any of the given
        conditions.
        """
    
        # loop over all the known browser classes
        for regex, bclass in BROWSER_CLASSES.items():
            # return True if one of them matches the 'User-agent' header
            if bclass in conditions and regex.match(req.headers_in["User-agent"]) is not None:
                return True

        # if this point is reached there was no matching known browser class
        # so return False
        return False
