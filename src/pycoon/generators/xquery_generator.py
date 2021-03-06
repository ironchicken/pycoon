"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

from pycoon.generators import generator, GeneratorError
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
    invk_syn.allowed_parent_components = ["pipeline", "aggregate", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type", "src", "query"]
    invk_syn.required_attrib_values = {"type": "xquery"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("generate", "xquery")] = invk_syn
    return invk_syn

def init_datasource_dbxml(sitemap, attrs):
    """
    This function is called by the sitemap_config_parse class to acquire a connection to the DB XML database
    specified in the given XML element attributes.

    The suffix of the function name distinguishes it as the function intended to be used to acquite connections
    for xquery sources with the backend type 'dbxml'.
    """
    
    # load a Berkeley DB XML data source
    # the source's name is the absolute path to the container file
    container_file = sitemap.document_root + os.sep + str(attrs['src'])
    ds_name = str(attrs['name'])

    # import the dbxml module
    if not sitemap.ds_mods.has_key("dbxml"):
        sitemap.ds_mods["dbxml"] = __import__("dbxml")

    # initialize the module
    sitemap.data_sources[ds_name] = sitemap.ds_mods["dbxml"].XmlManager()
    sitemap.data_sources[ds_name + "_source"] = container_file
    sitemap.data_sources[ds_name + "_container"] = sitemap.data_sources[ds_name].openContainer(container_file)
    sitemap.data_sources[ds_name + "_qc"] = sitemap.data_sources[ds_name].createQueryContext()

    if sitemap.parent.log_debug:
        sitemap.parent.error_log.write("Added data-source: \"%s\" from %s" % (ds_name, container_file))

class xquery_generator(generator):
    """
    xquery_generator encapsulates an XQuery to be executed against the given dbxml container and implements
    the generator interface.
    """

    def __init__(self, parent, src, query, root_path=""):
        """
        xquery_generator constructor.

        @src: the name of a dbxml which has been specified as a data-source element in the sitemap configuration
        @query: the name of an xquery file (which can be a string to be interpolated)

        XQuery files may use named string formatting to integrate parameters when executed.
        """

        self.datasource_name = src
        self.xq_filename = query
        generator.__init__(self, parent, root_path)
        self.dbxml_fn = self.sitemap.data_sources[self.datasource_name + "_source"]
        self.description = "xquery_generator(\"%s\", \"%s\")" % (self.datasource_name, self.xq_filename)

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Perform the xquery and return the result as an ElementTree.
        """

        try:
            xq_file = open(interpolate(self, self.xq_filename, as_filename=True, root_path=self.root_path), "r")
            xq_str = xq_file.read()
            xq_file.close()

            parameters = {'dbxml': self.dbxml_fn}
            parameters.update(self.parameter_children(child_results))

            results = self.sitemap.data_sources[self.datasource_name].query(str(xq_str % parameters),\
                                                                        self.sitemap.data_sources[self.datasource_name + "_qc"])
        
            results.reset()

            if results.size() == 0:
                return (False, apache.HTTP_NOT_FOUND)
                # or should this raise a GeneratorError? or return an empty document?
            else:
                return (True, lxml.etree.parse(StringIO(results.peek().asString())).getroot())
        except KeyError:
            raise GeneratorError("xquery_generator: no datasource called \"%s\"" % self.datasource_name)
