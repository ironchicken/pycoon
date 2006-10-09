"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the component used to handle <otherwise> element children of selector
components.
"""

from pycoon.components import syntax_component, invokation_syntax, ComponentError

class OtherwiseError(ComponentError): pass

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "otherwise"
    invk_syn.allowed_parent_components = ["select"]
    invk_syn.required_attribs = []
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["generate","transform","serialize"]

    server.component_syntaxes[("otherwise", None)] = invk_syn
    return invk_syn

class otherwise(syntax_component):
    """
    otherwise is a child component (or element) of selector components. It allows a default behaviour
    to be specified.
    """

    function = "otherwise"

    def __init__(self, parent, root_path=""):
        """
        otherwise constructor.
        """

        syntax_component.__init__(self, parent, root_path)

        self.description = "otherwise()"

        # attempt to find the parent selector component and
        # store it in self.selector
        self.selector = None
        
        p = self.parent
        while p is not None:
            if p.__class__.__name__.find("selector") >= 0:
                self.selector = p
                break
            try:
                p = p.parent
            except AttributeError:
                p = None
                break

        if self.selector is None:
            raise OtherwiseError("otherwise: Could not find a parent selector component.")

    def _descend(self, req, p_sibling_result=None):
        return True

    def _continue(self, req, p_sibling_result=None):
        return False
