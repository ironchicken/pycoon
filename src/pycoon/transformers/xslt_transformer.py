"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

from pycoon.transformers import transformer, TransformerError
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate
import os
import lxml.etree

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "transform"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "xslt"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("transform", "xslt")] = invk_syn
    return invk_syn

class xslt_transformer(transformer):
    """
    xslt_transformer class encapsulates an XSLT object from the lxml module and implements the
    transformer interface.

    Note: lxml XSLT parameters must be passed inside single quotes if they are literal, otherwise
    the transformation will treat tham as XPath expressions.
    """

    def __init__(self, parent, src, root_path=""):
        """
        xslt_transformer constructor.

        @src: name of an XSLT stylesheet file.
        """

        self.src = src
        
        transformer.__init__(self, parent, root_path)

        self.description = "xslt_transfomer(\"%s\")" % src

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Parse the p_sibling_result through the XSLT stylesheet.
        """

        try:
            self.transform = lxml.etree.XSLT(lxml.etree.parse(interpolate(self, self.src, as_filename=True, root_path=self.root_path)))

            parameters = {}
            for c in child_results:
                if isinstance(c, dict):
                    for k, v in c.items():
                        c[k] = "'%s'" % v
                    parameters.update(c)

            if len(parameters) > 0:
                return (True, self.transform(p_sibling_result, **parameters).getroot())
            else:
                return (True, self.transform(p_sibling_result).getroot())
        except lxml.etree.XMLSyntaxError, e:
            raise TransformerError("xslt_transformer: XML syntax error in stylesheet file, \"%s\": \"%s\"" %\
                                   (interpolate(self, self.src, as_filename=True, root_path=self.root_path), str(e)))
