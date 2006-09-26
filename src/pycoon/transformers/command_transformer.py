"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

from pycoon.transformers import transformer, TransformerError
from pycoon import apache
from pycoon.components import invokation_syntax
import lxml.etree
import os
from StringIO import StringIO

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "transform"
    invk_syn.allowed_parent_components = ["pipeline", "match"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "command"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("transform", "command")] = invk_syn
    return invk_syn

class command_transformer(transformer):
    """
    command_transformer encapsulates a shell command which takes an XML document as input and must
    return a well-formed XML document.
    """

    def __init__(self, parent, src, root_path=""):
        """
        command_transformer constructor.

        @src: the command string.
        """

        self.command = src
        transformer.__init__(self, parent, root_path)
        self.description = "command_transfomer(\"%s\")" % self.command

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Execute the command using the p_sibling_result as input along with any child
        parameter elements.
        """

        try:
            parameters = self.parameter_children(child_results)
            
            if len(parameters) > 0:
                (istream, ostream) = os.popen2(self.command % parameters)
            else:
                (istream, ostream) = os.popen2(self.command)

                istream.write(lxml.etree.tostring(p_sibling_result))
                istream.close()
        
                ret_tree = lxml.etree.parse(StringIO(ostream.read()))

                ostream.close()

                return (True, ret_tree)
        
        except OSError:
            #return (False, apache.HTTP_NOT_FOUND)
            raise TransformerError("command_transformer: error occured when executing command: \"%s\"" % self.command % parameters)
        except etree.XMLSyntaxError, e:
            raise TransformerError("command_transformer: transformation result document contains a syntax error: \"%s\"" % str(e))
