"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.serializers
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate
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
    invk_syn.required_attrib_values = {"type": "pdf"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("serialize", "pdf")] = invk_syn
    return invk_syn

class pdf_serializer(pycoon.serializers.serializer):
    """
    pdf_serializer class is not yet implemented. Requires an XSL FO implementation.
    """

    def __init__(self, parent, root_path=""):
        """
        pdf_serializer constructor.
        """

        pycoon.serializers.serializer.__init__(self, parent, root_path)
        self.mime_str = "application/pdf"
        self.description = "pdf_serializer()"

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return False

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Executes ?? on the p_sibling_result and returns the resultant PDF.
        """

        return (True, tounicode(p_sibling_result))
