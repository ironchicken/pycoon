"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.transformers
from pycoon.components import invokation_syntax, ComponentError
import os
import lxml.etree
from StringIO import StringIO
from xml.sax import parseString

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "transform"
    invk_syn.allowed_parent_components = ["pipeline", "match"]
    invk_syn.required_attribs = ["type", "module", "handler"]
    invk_syn.required_attrib_values = {"type": "sax-handler"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("transform", "sax-handler")] = invk_syn
    return invk_syn

class sax_handler_transformer(pycoon.transformers.transformer):
    """
    sax_handler_transformer encapsulates a SAX handler which takes an XML document string as input
    and must return a well-formed XML document.
    """

    def __init__(self, parent, module, handler, root_path=""):
        """
        sax_handler_transformer constructor.

        @module: name of the module in which the SAX handler is implemented
        @handler: SAX handler class name
        """

        try:
            self.handler = __import__(module, globals(), locals(), module.split(".")[-1])()
        except ImportError:
            raise ComponentError("Could not import sax_handler_transform handler class \"%s\" (from module \"%s\")" % (handler, module))

        pycoon.transformers.transformer.__init__(self, parent, root_path)

        self.description = "sax_handler_transfomer(\"%s\", \"%s\")" % (module, handler)

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Parses the p_sibling_result using self.handler and returns the result as an Element object.
        """

        parameters = {}
        for c in child_results:
            parameters.update(c)

        self.handler.set_parameters(parameters)
        
        parseString(lxml.etree.tostring(p_sibling_result), self.handler)

        return (True, lxml.etree.parse(StringIO(self.handler.ostream)).getroot())
