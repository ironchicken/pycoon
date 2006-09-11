"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.generators
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
import os
import lxml.etree
from StringIO import StringIO

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "generate"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate", "match"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "command"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("generate", "command")] = invk_syn
    return invk_syn

class command_generator(pycoon.generators.generator):
    """
    command_generator encapsulates a shell command which must return a well-formed XML document
    string. It implements the generator interface and can be used as a generator component in a pipeline.
    """

    def __init__(self, parent, src, root_path=""):
        """
        command_generator constructor. Requires 'pwd' (present working directory) and command string. Commands
        may use named string formatting to integrate request parameters when executed.
        """

        self.command = src
        pycoon.generators.generator.__init__(self, parent, root_path)
        self.description = "command_generator(\"%s\")" % self.command

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Execute the command and parse the output stream as an lxml.etree.
        """

        parameters = {}
        for c in child_results:
            parameters.update(c)

        try:
            ostream = os.popen(self.command % parameters)
        
            # for some reason it won't accept the ostream file object here,
            # so convert it to a StringIO instead
            ret_tree = lxml.etree.parse(StringIO(ostream.read())).getroot()
            ostream.close()
            
            return (True, ret_tree)
        except OSError:
            return (False, apache.HTTP_NOT_FOUND)
