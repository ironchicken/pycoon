"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.sources
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
import lxml.etree

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "source"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "file"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("source", "file")] = invk_syn
    return invk_syn

class xml_source(pycoon.sources.source):
    """
    xml_source encapsulates an XML source file using the source interface.
    """

    def __init__(self, parent, src, root_path=""):
        """
        xml_source constructor. Requires the source file path (can be a string to be interpolated
        upon requests).
        """

        self.src = src
        pycoon.sources.source.__init__(self, parent, root_path)
        self.description = "xml_source(\"%s\")" % self.src

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return False

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Returns an lxml.etree representation of the XML document, interpolating the XML source
        filename with the given uri_pattern.
        """

        try:
            return (True, lxml.etree.parse(open(interpolate(self.sitemap, self.src, uri_pattern, as_filename=True, root_path=self.root_path), "r")).getroot())
        except:
            return (False, apache.HTTP_NOT_FOUND)
