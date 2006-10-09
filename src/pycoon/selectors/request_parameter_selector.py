"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module implements the request_parameter selector which allows pipeline processing to
be conditional upon the value of a query string or POSTed parameter.
"""

from pycoon.selectors import selector, SelectorError
from pycoon.selectors.when_element import WhenError
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "select"
    invk_syn.allowed_parent_components = ["pipeline", "match", "aggregate"]
    invk_syn.required_attribs = ["type", "parameter"]
    invk_syn.required_attrib_values = {"type": "request-parameter"}
    invk_syn.optional_attribs = ["method"]
    invk_syn.allowed_child_components = ["when","otherwise"]

    server.component_syntaxes[("select", "request-parameter")] = invk_syn
    return invk_syn

class request_parameter_selector(selector):
    """
    request_parameter_selector allows pipeline processing to be conditional upon the
    value of a query string or POSTed parameter.
    """

    def __init__(self, parent, parameter, method="exclusive", root_path=""):
        """
        request_parameter_selector constructor.
        
        @parameter: name of the request parameter to be tested.
        """

        self.parameter = parameter

        selector.__init__(self, parent, method, root_path)

        self.description = "request_parameter_selector(\"%s\")" % self.parameter
        self.selector_type = "request_parameter"

        self.uri_matcher = None
        p = self.parent
        while p is not None:
            if p.__class__.__name__ in ["uri_matcher", "error_matcher"]:
                self.uri_matcher = p
                break
            try:
                p = p.parent
            except AttributeError:
                p = None
                break
        if self.uri_matcher is None:
            raise SelectorError("%s has no uri_matcher or error_matcher instance in pipeline" % self.description)

    def when_func(self, req, conditions):
        """
        This is the function which child <when> elements of this selector should use to implement
        their _descend function. It examines the request object's GET/POST parameter of the
        specified name and compares it against the given conditions. If any of them match the
        parameter's value True is returned.
        """

        parameter = interpolate(self, self.parameter)
        param_value = ""
        
        if req.method == "GET":
            if self.uri_matcher.query_dict.has_key(parameter):
                param_value = self.uri_matcher.query_dict[parameter]
            
        elif req.method == "POST":
            # whats the correct method for reading POSTed data?
            parameters = req.read()

            param_dict = {}
            for p in parameters.split("&"):
                if p.find("=") >= 0:
                    (name, value) = p.split("=")
                else:
                    name = p
                    value = ""
                self.param_dict[name] = value

            if param_dict.has_key(parameter):
                param_value = param_dict[parameter]

        if param_value == "":
            return False
        
        for cond in conditions:
            if cond == param_value:
                return True

        return False
