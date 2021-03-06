"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

from pycoon.transformers import transformer, TransformerError
from pycoon.components import invokation_syntax, ComponentError
import os
import lxml.etree
from StringIO import StringIO
from xml.sax import parseString, SAXException

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "transform"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type", "module", "handler"]
    invk_syn.required_attrib_values = {"type": "sax-handler"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("transform", "sax-handler")] = invk_syn
    return invk_syn

class sax_handler_transformer(transformer):
    """
    sax_handler_transformer encapsulates a SAX handler which takes an XML document string as input
    and must return a well-formed XML document.
    """

    def __init__(self, parent, module, handler, root_path=""):
        """
        sax_handler_transformer constructor.

        @module: name of the module in which the SAX handler is implemented
        @handler: SAX handler class name. This class should be derived from xml.sax.handler.ContentHandler
        and should provide a 'set_parameters(params)' method, a 'result_tree' property or a
        'result_stream' property, one of which should contain the result as either an Element object or
        an XML string. The pycoon.helpers module provides a pycoon_sax_handler base class which should be
        used to create SAX handlers for this component.
        """

        try:
            self.handler = __import__(module, globals(), locals(), module.split(".")[-1]).__dict__[handler]()
        except ImportError:
            raise ComponentError("Could not import sax_handler_transform handler class \"%s\" (from module \"%s\")" % (handler, module))

        transformer.__init__(self, parent, root_path)

        self.description = "sax_handler_transfomer(\"%s\", \"%s\")" % (module, handler)

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Parses the p_sibling_result using self.handler and returns the result as an Element object.
        """

        try:
            parameters = self.parameter_children(child_results)

            self.handler.set_parameters(parameters)
        
            parseString(lxml.etree.tostring(p_sibling_result), self.handler)

            if isinstance(self.handler.result_tree, lxml.etree._Element):
                return (True, self.handler.result_tree)
            elif self.handler.result_stream != "<?xml version=\"1.0\"?>":
                return (True, lxml.etree.parse(StringIO(self.handler.result_stream)).getroot())
            else:
                raise TransformerError("sax_handler_transformer: SAX handler has not produced a result.")
        except SAXException, e:
            raise TransformerError("sax_handler_transformer: SAX transformation caused an exception: \"%s\"" % str(e))
        except lxml.etree.XMLSyntaxError, e:
            raise TransformerError("sax_handler_transformer: transformation result document contains a syntax error: \"%s\"" % str(e))
