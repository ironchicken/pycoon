"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The selectors module provides the selector class which is the base class of all
selector classes.
"""

from pycoon.components import syntax_component, invokation_syntax, ComponentError
import lxml.etree

class SelectorError(ComponentError): pass

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "select"
    invk_syn.allowed_parent_components = ["pipeline", "match", "aggregate"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = ["method"]
    invk_syn.allowed_child_components = ["when","otherwise"]

    server.component_syntaxes[("select", None)] = invk_syn
    return invk_syn

class selector(syntax_component):
    """
    selector is the base class for all classes which are intended to be used as selector objects
    in pipelines.
    """

    role = "syntax"
    function = "select"
    
    def __init__(self, parent, method="exclusive", root_path=""):
        """
        @parent: the parent component of this selector (often a pipeline).
        @method: determines how the child <when> elements are treated. 'exclusive' (default): once a matching
                 condition is found all others are discarded; 'inclusive': every matching condition is
                 processed.
        @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default
        """

        syntax_component.__init__(self, parent, root_path="")

        self.method = method
        
        self.description = "Selector base class"
        self.selector_type = "none"

    def when_func(self, req, conditions):
        """
        This is the function which child <when> elements of this selector should use to implement
        their _descend function.

        @req: an Apache request object.
        @conditions: a list of strings to be used as conditions.
        """

        raise NotImplemented()

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        If the parent selector is 'exclusive' (default) _result simply returns either the last child
        result or the previous sibling result. If the parent selector is 'inclusive', all the child
        results are joined together as a return value.
        """

        if self.method == "exclusive":
            if len(child_results) > 0 and child_results[-1] is not None:
                return (True, child_results[-1])
            else:
                return (True, p_sibling_result)
        
        elif self.method == "inclusive":
            if len(child_results) > 0:
                first = None
                for c, i in zip(child_results, range(len(child_results))):
                    if c is not None:
                        first = c
                        break
                if first is not None:
                    top = lxml.etree.Element("inclusive-select")
                    top.append(first)
                    for c in child_results[i:]:
                        if c is not None:
                            top.append(c)
                    return (True, top)
                else:
                    return (True, p_sibling_result)
            else:
                return (True, p_sibling_result)
