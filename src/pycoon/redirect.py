"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module provides the redirect component which allows requests to be
redirected to other URIs.
"""

import sys
try:
    from mod_python import util
except ImportError:
    from pycoon.helpers import fake_util
    util = fake_util()
    
from pycoon.components import syntax_component, invokation_syntax
from pycoon.interpolation import interpolate

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "redirect"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["uri"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = ["permanent", "message"]
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("redirect", None)] = invk_syn
    return invk_syn

class redirect(syntax_component):
    """
    redirect allows requests to be redirected to another URI, rather than being processed by Pycoon.
    """
    
    function = "redirect"

    def __init__(self, parent, uri, permanent="yes", message="", root_path=""):
        syntax_component.__init__(self, parent, root_path)

        self.new_uri = uri
        if permanent == "yes":
            self.permanent = True
        else:
            self.permanent = False

        if message.strip() != "":
            self.message = message
        else:
            self.message = None

        self.description = "redirect: \"%s\"" % uri
        self.function = "redirect"

    def _descend(self, req, p_sibling_result=None):
        return False
    
    def _result(self, req, p_sibling_result=None, child_results=[]):
        util.redirect(req, interpolate(self, self.new_uri), self.permanent, self.message)
