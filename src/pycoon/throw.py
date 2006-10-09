"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The module provides the throw component which handles <throw> elements
in pipeline configurations causing the given error condition.
"""

import sys
#from pycoon import apache
from pycoon.components import syntax_component, invokation_syntax

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "throw"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["error-code"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("throw", None)] = invk_syn
    return invk_syn

class throw(syntax_component):
    """
    throw objects correspond to <throw> elements in a pipeline. They cause the error condition with
    the given error code to occur. If the sitemap or server defines a handler for the error then it
    will be handled.
    """
    
    function = "throw"

    def __init__(self, parent, error_code, root_path=""):
        syntax_component.__init__(self, parent, root_path)

        self.error_code = error_code

        self.description = "throw: \"%s\"" % error_code
        self.function = "throw"

    def _descend(self, req, p_sibling_result=None):
        return False
    
    def _result(self, req, p_sibling_result=None, child_results=[]):
        self.server.EXCEPTION = sys.exc_info()

        return (False, int(self.error_code))
