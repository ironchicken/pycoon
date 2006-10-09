"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The generators module provides the generator class which is the base class of all
generator classes.
"""

from pycoon.components import stream_component, invokation_syntax, ComponentError
from pycoon.interpolation import interpolate

class GeneratorError(ComponentError): pass

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "generate"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = ["query"]
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("generate", None)] = invk_syn
    return invk_syn

class generator(stream_component):
    """
    generator is the base class for all classes which are intended to be used as generator objects
    for pipelines.

    @parent: the parent component of this generator (often a pipeline).
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default
    """

    role = "stream"
    function = "generate"
    
    def __init__(self, parent, root_path=""):
        stream_component.__init__(self, parent, root_path="")

        self.description = "Generator base class"
