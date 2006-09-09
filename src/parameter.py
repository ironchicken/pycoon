"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The module provides the parameter component which handled <parameter> elements
in pipeline configurations.
"""

from pycoon.components import syntax_component, invokation_syntax
from pycoon.interpolation import interpolate

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "parameter"
    invk_syn.allowed_parent_components = ["generate", "transform"]
    invk_syn.required_attribs = ["name", "value"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("parameter", None)] = invk_syn
    return invk_syn

class parameter(syntax_component):
    """
    parameter objects are used to process <parameter> child elements of many of the Pycoon components.

    @parent: the parent component of this component.
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default.
    @name: the name of the parameter.
    @value: the value of the parameter (may include interpolation instructions).
    """

    function = "parameter"
    
    def __init__(self, parent, name, value, root_path=""):
        syntax_component.__init__(self, parent, root_path)

        self.param_name = name
        self.param_value = value

        self.description = "Parameter: %s: \"%s\"" % (self.param_name, self.param_value)
        #self.function = "parameter"

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return False

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Parameter components return the name of the parameter along with the parameter's
        interpolated value.
        """

        return (True, {self.param_name: interpolate(self.context, self.param_value, uri_pattern)})
