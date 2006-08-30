"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.transformers
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate
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
    invk_syn.allowed_parent_components = ["pipeline"]
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
        sax_handler_transformer constructor. Requires the name of the module in which the SAX handler
        is implemented and the name of the SAX handler class.
        """

        # WARNING: apparently os.sep will _not_ work on OS X with mod_python and Win32 is untested

        try:
            self.handler = __import__(module).__dict__[handler]()
        except ImportError:
            self.handler = __import__(module.replace(".", os.sep)).__dict__[handler]()

        pycoon.transformers.transformer.__init__(self, parent, root_path)

        self.description = "sax_handler_transfomer(\"%s\", \"%s\")" % (module, handler)

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return True

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Parses the p_sibling_result using self.handler and returns the result as an Element object.
        """

        parameters = {}
        for c in child_results:
            parameters.update(c)

        if uri_pattern:
            self.handler.set_parameters(parameters)
        
        parseString(lxml.etree.tostring(p_sibling_result), self.handler)

        return (True, lxml.etree.parse(StringIO(self.handler.ostream)).getroot())
