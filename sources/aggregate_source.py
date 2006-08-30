"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.sources
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
import lxml.etree
from StringIO import StringIO

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "aggregate"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = []
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = ["root-node"]
    invk_syn.allowed_child_components = ["source"]

    server.component_syntaxes[("aggregate", None)] = invk_syn
    return invk_syn

class aggregate_source(pycoon.sources.source):
    """
    aggregate_source encapsulates a container XML document which can have the return values of other
    pipelines interpolated into it using named Python formatting strings and implements the source interface.
    """

    function = "aggregate"
    
    def __init__(self, parent, root_node="aggregation", root_path=""):
        """
        aggregate_source constructor.

        @root_node: the name of the root node of the aggregated document. Optional.
        """

        self.root_node = root_node
        pycoon.sources.source.__init__(self, parent, root_path)
        self.description = "aggregate_source(\"%s\")" % self.root_node

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return True

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        root = lxml.etree.Element(self.root_node)

        for c in child_results:
            root.append(c)

        return (True, root)
