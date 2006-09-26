"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The transformers module provides the transformer class which is the base class of
all transformers.
"""

from pycoon.components import stream_component, invokation_syntax, ComponentError

class TransformerError(ComponentError): pass

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "transform"
    invk_syn.allowed_parent_components = ["pipeline", "match"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("transform", None)] = invk_syn
    return invk_syn

class transformer(stream_component):
    """
    transformer is the base class for classes which are to be used as transformers in a pipeline.

    @parent: the parent component of this source (often a pipeline).
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default
    """

    role = "stream"
    function = "transform"
    
    def __init__(self, parent, root_path=""):
        stream_component.__init__(self, parent, root_path="")

        self.description = "Transformer base class"
