"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.serializers
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate
from lxml.etree import tounicode
import os

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "serialize"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "svg"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("serialize", "svg")] = invk_syn
    return invk_syn

class svg_serializer(pycoon.serializers.serializer):
    """
    svg_serializer class encapsulates the RSVG rasterizer.
    """

    def __init__(self, parent, root_path=""):
        """
        svg_serializer constructor.
        """

        pycoon.serializers.serializer.__init__(self, parent, root_path)
        self.mime_str = "image/png"
        self.description = "svg_serializer()"

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return False

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Executes rsvg using the p_sibling_result and returns the resultant image.
        """

        svg_fd, svg_path = tempfile.mkstemp()
        svg_file = open(svg_path, 'w+b')
        svg_file.write(tounicode(p_sibling_result))
        svg_file.close()
                        
        png_fd, png_path = tempfile.mkstemp()
        rsvg_cmd = os.popen("rsvg %s %s" % (svg_path, png_path))
        if rsvg_cmd.close() is None:
            png_file = open(png_path, 'r+b')
            source_stream = png_file.read()
            png_file.close()

        os.remove(svg_path)
        os.remove(png_path)

        return (True, source_stream)
