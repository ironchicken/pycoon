"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.sources
from pycoon.components import invokation_syntax
from pycoon.helpers import unescape_url
import os, string
import lxml.etree

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "source"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate"]
    invk_syn.required_attribs = ["type", "src", "query"]
    invk_syn.required_attrib_values = {"type": "swishe"}
    invk_syn.optional_attribs = ["custom-properties"]
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("source", "swishe")] = invk_syn
    return invk_syn

def init_datasource(sitemap, attrs):
    """
    This function is called by the site_config_parse class to load the Swish-e index file
    specified in the given XML element attributes.
    """
    
    # loads a swish-e index
    # the index's name is the index file name(s)
    index_name = str(attrs['name'])
    index_files = string.join([sitemap.document_root + os.sep + s for s in string.split(str(attrs['src']))])

    # import the swish-e module
    sitemap.ds_mods["SwishE"] = __import__("SwishE")

    # initialize the module
    sitemap.data_sources[index_name] = sitemap.ds_mods["SwishE"].new(index_files)
    sitemap.data_sources[index_name + "_source"] = index_files
    if sitemap.parent.log_debug: sitemap.parent.error_log.write("Added data-source: \"%s\"" % index_name)

class swishe_source(pycoon.sources.source):
    """
    swishe_source encapsulates a swish-e index, allowing searches to be made against it. It implements
    the source interface.
    """

    def __init__(self, parent, src, query, custom_properties, root_path=""):
        """
        swishe_source constructor. Requires the name of a swish-e index which has been specified as a swishe-index element
        in the sitemap configuration and a query_pattern string which will be interpolated with the request uri.
        """

        self.datasource_name = src
        self.query_pattern = query
        self.custom_properties = string.split(custom_properties)
        
        # seems the Python API doesn't allow you to get the available properties
        self.auto_properties = ["swishreccount", "swishtitle", "swishrank", "swishdocpath", "swishdocsize",\
                                "swishlastmodified", "swishdescription", "swishdbfile"]

        pycoon.sources.source.__init__(self, parent, root_path)

        self.description = "swishe_source(\"%s\", \"%s\")" % (self.datasource_name, self.query_pattern)

    def is_modified(self, req, uri_pattern):
        try:
            parsed_src = interpolate(self.context, self.sitemap.data_sources[self.datasource_name + "_source"],\
                                     uri_pattern, as_filename=True, root_path=self.root_path)
            src_modified = os.stat(parsed_src)[stat.ST_MTIME]
            return src_modified > req.request_time
        except OSError:
            return True

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return True

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Perform the search and return an Element object.
        """

        parameters = {}
        for c in child_results:
            parameters.update(c)

        query = unescape_url(self.query_pattern % parameters)

        # there may be parameters for swish-e such as max hits etc.
        #for p in parameters:
        #    pass
        
        results = self.sitemap.data_sources[self.datasource_name].query(query)

        ret_tree = lxml.etree.Element("swishe")
        ret_tree.attrib["query"] = query.replace("\"", "'").replace("+"," ")
        ret_tree.attrib["hits"] = str(results.hits())

        # first add the property names to the top of the result tree so that they
        # are not repeated for every result
        all_properties = self.auto_properties + self.custom_properties

        properties_header = lxml.etree.Element("properties")
        properties = {}
        
        for n, p_name in zip(range(len(all_properties)), all_properties):
            p = lxml.etree.Element("property")
            p.attrib["id"] = str(n)
            p.attrib["name"] = p_name
            properties_header.append(p)

            properties[p_name] = n

        ret_tree.append(properties_header)

        # now add the hits
        hits = lxml.etree.Element("results")
        
        for n, r in zip(range(results.hits()), results):
            hit = lxml.etree.Element("result")
            hit.attrib["n"] = str(n)
                
            for p_name in all_properties:
                try:
                    e_name = properties[p_name]
                    value = r.getproperty(p_name)
                    if value is None: break

                    p = lxml.etree.Element(str(properties[p_name]))
                    p.text = str(value)
                    hit.append(p)
                except:
                    # this is a Swish-e error; property didn't exist, doesn't matter
                    pass

            hits.append(hit)

        ret_tree.append(hits)

        return (True, ret_tree)
