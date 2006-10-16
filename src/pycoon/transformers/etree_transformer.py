"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the element tree transformer which allows a pipeline's working
Element object to be manipulated directly.
"""

from pycoon.transformers import transformer, TransformerError
from pycoon.components import invokation_syntax, ComponentError
import types
import lxml.etree

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "transform"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type", "module", "code-object"]
    invk_syn.required_attrib_values = {"type": "etree"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("transform", "etree")] = invk_syn
    return invk_syn

class etree_transformer(transformer):
    """
    etree_transformer allows a pipeline's working Element object to be manipulated directly.
    """

    def __init__(self, parent, module, code_object, root_path=""):
        """
        etree_transformer class constructor.

        @module: is the name of a module which contains the manipulation code.
        @code_object: is the name of the code object (function/class) in the module which performs
        the manipulation. It must be callable, accept an Element object as a parameter and return
        an Element object.
        """

        try:
            co = __import__(module, globals(), locals(), module.split(".")[-1]).__dict__[code_object]
            if type(co) == types.ClassType:
                self.transform = co()
                if not callable(self.transform):
                    raise ComponentError("etree_transformer: code object class instance is not callable; module: \"%s\", code_object: \"%s\"" % (module, code_object))
            elif type(co) == types.FunctionType:
                self.transform = co
            else:
                raise ComponentError("etree_transformer: code_object must be a class or a function; module: \"%s\", code_object: \"%s\"" % (module, code_object))
        except ImportError:
            raise ComponentError("etree_transformer: could not import code object \"%s\" (from module \"%s\")" % (code_object, module))

        self.module = module
        self.code_object = code_object

        transformer.__init__(self, parent, root_path)

    def _descend(self, req, p_sibling_result=None):
        return False

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Executes the transform function using the previous sibling result Element object.
        """

        try:
            result = self.transform(p_sibling_result)

            if isinstance(result, lxml.etree._Element):
                return (True, result)
            else:
                raise TransformerError("etree_transformer: transform function did not return an Element object.")
        except TypeError, e:
            if str(e).find("takes exactly"):
                raise TransformerError("etree_transformer: transform function does not have correct signature.")
            else:
                raise e
