"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the text serializer.
"""

from pycoon.serializers import serializer, SerializerError
from pycoon.components import invokation_syntax
from lxml.etree import tounicode
import os

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "serialize"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "text"}
    invk_syn.optional_attribs = ["mime"]
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("serialize", "text")] = invk_syn
    return invk_syn

class text_serializer(serializer):
    """
    text_serializer class allows the pipeline result to be serialized into plain text.
    """

    def __init__(self, parent, mime="text/plain", root_path=""):
        """
        text_serializer constructor.
        """

        serializer.__init__(self, parent, root_path)
        self.mime_str = mime
        self.description = "text_serializer()"

    def _descend(self, req, p_sibling_result=None):
        return False

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Executes lxml.etree.tounicode() on the pipeline's result tree.
        """

        try:
            return (True, (tounicode(p_sibling_result).encode("utf-8"), self.mime_str))
        except TypeError:
            if p_sibling_result is None:
                raise SerializerError("text_serializer: preceding pipeline components have returned no content!")
