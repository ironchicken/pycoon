"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.generators
from pycoon import apache
from pycoon.components import invokation_syntax
from pycoon.interpolation import interpolate
import lxml.etree
import string

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "generate"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate"]
    invk_syn.required_attribs = ["type", "src", "query"]
    invk_syn.required_attrib_values = {"type": "xpath"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("generate", "xpath")] = invk_syn
    return invk_syn

class xpath_generator(pycoon.generators.generator):
    """
    xpath_generator encapsulates an XPath expression to be executed against the given XML document and
    implements the generator interface.
    """

    def __init__(self, parent, src, query, root_path=""):

        """
        xpath_generator constructor.

        @src: source XML file
        @query: an XPath expression.

        Both the XPath expression and the source file name may use Python formatting string elements and
        be interpolated with values from the request URI.
        """

        self.source_file = src
        self.xpath_expr = query
        pycoon.generators.generator.__init__(self, parent, root_path)
        self.description = "xpath_generator(\"%s\", \"%s\")" % (self.source_file, self.xpath_expr)

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return False

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Execute the XPath expression and return the results in an Element object.
        """

        try:
            source_tree = lxml.etree.parse(open(interpolate(self.context, self.source_file, uri_pattern,\
                                                            as_filename=True, root_path=self.root_path), 'r'))
        except OSError:
            return (False, apache.HTTP_NOT_FOUND)

        if uri_pattern is not None:
            xpath = interpolate(self.context, self.xpath_expr, uri_pattern)
        else:
            xpath = self.xpath_expr

        nodes = source_tree.xpath(xpath)

        ret_tree = lxml.etree.Element("result")

        for n in nodes:
            ret_tree.append(n)

        return (True, ret_tree)
