"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the component used to handle <when> element children of selector
components.
"""

from pycoon.components import syntax_component, invokation_syntax, ComponentError
from pycoon.interpolation import interpolate
import re

class WhenError(ComponentError): pass

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "when"
    invk_syn.allowed_parent_components = ["select"]
    invk_syn.required_attribs = ["test"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["generate","transform","serialize"]

    server.component_syntaxes[("when", None)] = invk_syn
    return invk_syn

class when(syntax_component):
    """
    when is a child component (or element) of selector components. It allows the conditions
    of a selector to be implemented.
    """

    function = "when"

    def __init__(self, parent, test, root_path=""):
        """
        when constructor.

        @test: the 'test' attribute string. OR logic is handled by provided multiple conditions
               separated by white space. The test string will be interpolated against the request
               uri whenever a request is handled so the {} syntax may be used to parameterize
               the test.
        """

        self.test = test

        syntax_component.__init__(self, parent, root_path)

        self.description = "when(\"%s\")" % self.test

        # attempt to find the parent selector component and
        # store it in self.selector
        self.selector = None
        
        p = self.parent
        while p is not None:
            if p.__class__.__name__.find("selector") >= 0:
                self.selector = p
                break
            try:
                p = p.parent
            except AttributeError:
                p = None
                break

        if self.selector is None:
            raise WhenError("when \"%s\": Could not find a parent selector component." % self.test)

    def _descend(self, req, p_sibling_result=None):
        return self.selector.when_func(req, re.split("\s+", interpolate(self, self.test)))

    def _continue(self, req, p_sibling_result=None):
        if self.selector.method == "inclusive":
            return True
        else:
            return not self.selector.when_func(req, re.split("\s+", interpolate(self, self.test)))
