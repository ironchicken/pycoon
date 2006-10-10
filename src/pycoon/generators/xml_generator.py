"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the xml (or file) generator which uses the content of an XML
file to generate the source for a pipeline.
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
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "file"}
    invk_syn.optional_attribs = ["content"]
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("generate", "file")] = invk_syn
    return invk_syn

class xml_generator(generator):
    """
    xml_generator encapsulates an XML source file using the generator interface.
    """

    def __init__(self, parent, src, content="xml", root_path=""):
        """
        xml_generator constructor.

        @src: the source file path (can be a string to be interpolated upon requests).
        @content: the type of content in the source file [xml|html]. Optional; xml is default.
        """

        self.src = src
        self.content = content.lower()
        
        generator.__init__(self, parent, root_path)

        self.description = "xml_generator(\"%s\")" % self.src

    def _descend(self, req, p_sibling_result=None):
        return False

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Returns an ElementTree representation of the XML document.
        """

        try:
            path = interpolate(self, self.src, as_filename=True, root_path=self.root_path)
            
            if self.content == "xml":
                return (True, lxml.etree.parse(open(path, "r")).getroot())
            elif self.content == "html":
                return (True, lxml.etree.parse(open(path, "r"), lxml.etree.HTMLParser()).getroot())
            
        except (IOError, OSError):
            raise GeneratorError("xml_generator: source file not found \"%s\"" % path)
        
        except lxml.etree.XMLSyntaxError, e:
            raise GeneratorError("xml_generator: syntax error in XML source, \"%s\": \"%s\"" % (path, str(e)))
