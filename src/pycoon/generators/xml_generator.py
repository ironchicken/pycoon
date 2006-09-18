"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.generators
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
    invk_syn.element_name = "generate"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate", "match"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "file"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("generate", "file")] = invk_syn
    return invk_syn

class xml_generator(pycoon.generators.generator):
    """
    xml_generator encapsulates an XML source file using the generator interface.
    """

    def __init__(self, parent, src, root_path=""):
        """
        xml_generator constructor.

        @src: the source file path (can be a string to be interpolated
        upon requests).
        """

        self.src = src
        pycoon.generators.generator.__init__(self, parent, root_path)
        self.description = "xml_generator(\"%s\")" % self.src

    def _descend(self, req, p_sibling_result=None):
        return False

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Returns an ElementTree representation of the XML document.
        """

        try:
            return (True, lxml.etree.parse(open(interpolate(self, self.src, as_filename=True, root_path=self.root_path), "r")).getroot())
        except (IOError, OSError):
            return (False, apache.HTTP_NOT_FOUND)
