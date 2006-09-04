"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.serializers
from pycoon.components import invokation_syntax
from lxml.etree import tounicode

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "serialize"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "xml"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("serialize", "xml")] = invk_syn
    return invk_syn

class xml_serializer(pycoon.serializers.serializer):
    """
    xml_serializer class simply returns the XML source as a character stream.
    """

    def __init__(self, parent, root_path=""):
        """
        xml_serializer constructor.
        """

        pycoon.serializers.serializer.__init__(self, parent, root_path)
        self.mime_str = "text/xml"
        self.description = "xml_serializer()"

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return False

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Executes lxml.etree.tounicode with the p_sibling_result and returns the resultant XML.
        """

        return (True, "<?xml version=\"1.0\"?>%s" % tounicode(p_sibling_result))
