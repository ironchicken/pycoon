"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

from pycoon.serializers import serializer, SerializerError
from pycoon.components import invokation_syntax
from pycoon.helpers import correct_script_chars
from lxml.etree import tounicode
import os

try:
    import tidy
    UTIDYLIB_AVAIL = True
except ImportError:
    UTIDYLIB_AVAIL = False

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "serialize"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "xhtml"}
    invk_syn.optional_attribs = ["mime"]
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("serialize", "xhtml")] = invk_syn
    return invk_syn

class xhtml_serializer(serializer):
    """
    xhtml_serializer class encapsulates the uTidyLib class.
    """

    def __init__(self, parent, mime="text/html", root_path=""):
        """
        xhtml_serializer constructor.
        """

        serializer.__init__(self, parent, root_path)
        self.mime_str = mime
        self.description = "xhtml_serializer()"

    def _descend(self, req, p_sibling_result=None):
        return False

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Executes tidy.parseString on the p_sibling_result and returns the resultant XHTML.
        """

        try:
            if os.name != "nt" and UTIDYLIB_AVAIL:
                options = dict(output_xhtml=1, add_xml_decl=1, doctype="strict", indent=1, wrap=120, tidy_mark=0,\
                               input_encoding="utf8", output_encoding="utf8")
            
                return (True, (correct_script_chars(str(tidy.parseString(tounicode(p_sibling_result).encode("utf-8"), **options))), self.mime_str))
            else:
                return (True, (correct_script_chars(tounicode(p_sibling_result).encode("utf-8")), self.mime_str))
        except TypeError:
            if p_sibling_result is None:
                raise SerializerError("xhtml_serializer: preceding pipeline components have returned no content!")
