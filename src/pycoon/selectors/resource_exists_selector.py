"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the resource_exists selector which allows pipeline processing to
be conditional upon the existence of a named resources.
"""

from pycoon.selectors import selector, SelectorError
from pycoon.selectors.when_element import WhenError
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate
import os

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "select"
    invk_syn.allowed_parent_components = ["pipeline", "match", "aggregate"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "resource-exists"}
    invk_syn.optional_attribs = ["method"]
    invk_syn.allowed_child_components = ["when","otherwise"]

    server.component_syntaxes[("select", "resource-exists")] = invk_syn
    return invk_syn

class resource_exists_selector(selector):
    """
    resource_exists_selector allows pipeline processing to be conditional upon the
    existence of a named resources.
    """

    def __init__(self, parent, method="exclusive", root_path=""):
        """
        resource_exists_selector constructor.
        """

        selector.__init__(self, parent, method, root_path)

        self.description = "resource_exists_selector([%s])" % self.method
        self.selector_type = "resource_exists"

    def when_func(self, req, conditions):
        """
        This is the function which child <when> elements of this selector should use to implement
        their _descend function. It examines each of the resource names in the given conditions
        list and returns True if any of them references an existing resource.
        """

        for res in conditions:
            path = interpolate(self, res, as_filename=True, root_path=self.root_path)
            try:
                os.stat(path)
            except OSError:
                continue
            return True
