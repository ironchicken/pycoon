"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The sources module provides the source class which is the base class of all
source classes.
"""

from pycoon.components import stream_component, invokation_syntax
from pycoon.interpolation import interpolate

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "source"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = ["query"]
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("source", None)] = invk_syn
    return invk_syn

class source(stream_component):
    """
    source is the base class for all classes which are intended to be used as sources objects
    for pipelines.

    @parent: the parent component of this source (often a pipeline).
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default
    """

    role = "stream"
    function = "source"
    
    def __init__(self, parent, cache_as="", root_path=""):
        stream_component.__init__(self, parent, cache_as, root_path="")

        self.description = "Source base class"
