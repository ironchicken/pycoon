"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The serializers module provides the serializer class which is the base class of all
serializer classes.
"""

from pycoon.components import stream_component, invokation_syntax, ComponentError

class SerializerError(ComponentError): pass

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "serialize"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("serialize", None)] = invk_syn
    return invk_syn

class serializer(stream_component):
    """
    serializer is the base class for classes which are to be used as serializers in a pipeline.
    """

    role = "stream"
    function = "serialize"
    
    def __init__(self, parent, root_path=""):
        stream_component.__init__(self, parent, root_path)

        self.description = "Serializer base class"
