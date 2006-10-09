"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The matchers module provides the matcher class which is the base class of all
matcher classes.
"""

from pycoon.components import syntax_component, invokation_syntax, ComponentError

class MatcherError(ComponentError): pass

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "match"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["generate","transform","serialize","match"]

    server.component_syntaxes[("match", None)] = invk_syn
    return invk_syn

class matcher(syntax_component):
    """
    matcher is the base class for all classes which are intended to be used as matcher objects
    for pipelines.

    @parent: the parent component of this matcher (often a pipeline).
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default
    """

    role = "syntax"
    function = "match"
    
    def __init__(self, parent, root_path=""):
        syntax_component.__init__(self, parent, root_path="")

        self.description = "Matcher base class"
