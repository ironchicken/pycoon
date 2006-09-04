"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.transformers
from pycoon.components import invokation_syntax
import os
import lxml.etree

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "transform"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "xslt"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("transform", "xslt")] = invk_syn
    return invk_syn

class xslt_transformer(pycoon.transformers.transformer):
    """
    xslt_transformer class encapsulates an XSLT object from the lxml module and implements the
    transformer interface.

    Note: lxml XSLT parameters must be passed inside single quotes if they are literal, otherwise
    the transformation will treat tham as XPath expressions.
    """

    def __init__(self, parent, src, root_path=""):
        """
        xslt_transformer constructor.

        @src: name of an XSLT stylesheet file. Note that this filename will _not_ be
              interpolated as it is loaded at configuration-time, not when the pipeline
              is executed.
        """

        self.transform = lxml.etree.XSLT(lxml.etree.parse(root_path + os.sep + src))
        
        pycoon.transformers.transformer.__init__(self, parent, root_path)

        self.description = "xslt_transfomer(\"%s\")" % src

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return True

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Parse the p_sibling_result through the XSLT stylesheet.
        """

        parameters = {}
        for c in child_results:
            parameters.update(c)

        if len(parameters) > 0:
            return (True, self.transform(p_sibling_result, **parameters).getroot())
        else:
            return (True, self.transform(p_sibling_result).getroot())
