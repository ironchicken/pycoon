"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the the request_generator which encodes the given request
headers as XML source for pipelines.
"""

from pycoon.generators import generator, GeneratorError
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
    invk_syn.allowed_parent_components = ["pipeline", "aggregate", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "request"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("generate", "request")] = invk_syn
    return invk_syn

class request_generator(generator):
    """
    request_generator encodes the given request headers as an XML source.
    """

    def __init__(self, parent, root_path=""):
        """
        request_generator class constructor.
        """

        generator.__init__(self, parent, root_path)

        self.description = "Request generator"

    def _descend(self, req, p_sibling_result=None):
        return False

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Reads the headers of the give request object and returns them in an Element object.
        """

        headers_tree = lxml.etree.Element("request-headers")

        for name, value in req.headers_in.items():
            h = lxml.etree.Element("header")
            h.attrib["name"] = name
            h.text = value
            headers_tree.append(h)

        return (True, headers_tree)
