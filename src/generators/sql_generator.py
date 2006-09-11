"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module provides the sql_generator component which allows SQL statements to be executed
against databases to provide sources for pipelines. The module also contains whose names
follow the pattern "init_datasource_*(sitemap, attrs)" which are used to acquire a cursor
for the '*' named database. This is part of the 'backends' framework. In order to add new
backends, it is necessary to add the appropriate function to this module.
"""

import pycoon.generators
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
import lxml.etree

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "generate"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate", "match"]
    invk_syn.required_attribs = ["type", "src", "query"]
    invk_syn.required_attrib_values = {"type": "sql"}
    invk_syn.optional_attribs = ["template"]
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("generate", "sql")] = invk_syn
    return invk_syn

def init_datasource_mysql(sitemap, attrs):
    """
    This function is called by the site_config_parse class to acquire a cursor to the MySQL database
    specified in the given XML element attributes. It is part of the 'backends' framework.
    """
    
    # load a MySQL data source
    # the source's name is just the name of the database
    ds_name = str(attrs['name'])
    database = str(attrs['src'])

    # import the MySQLdb module
    if not sitemap.ds_mods.has_key("MySQLdb"):
        sitemap.ds_mods["MySQLdb"] = __import__("MySQLdb")

    # initialize the module
    sitemap.data_sources[ds_name] = self.sitemap.ds_mods["MySQLdb"].connect(host=str(attrs['host']),\
                                                                            login=str(attrs['login']),\
                                                                            passwd=str(attrs['passwd']),\
                                                                            db_name=database).cursor()
    if sitemap.parent.log_debug: sitemap.parent.error_log.write("Added data-source: \"%s\" using %s" % (ds_name, database))

class sql_generator(pycoon.generators.generator):
    """
    sql_generator encapsulates an SQL query to be executed against the given SQL cursor.
    """

    def __init__(self, parent, src, query, template="", root_path=""):
        """
        sql_generator constructor.

        @src: the name of a data source from the server_config.data_sources dictionary
        @query: file name of a SQL statement
        @template: file name of an XML template for the result. Optional [not implemented].
        """
        
        self.datasource_name = src
        self.sql_filename = query
        self.template_filename = template_filename
        pycoon.generators.generator.__init__(self, parent, root_path)
        self.description = "sql_generator(\"%s\", \"%s\")" % (self.db_name, self.sql_filename)

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        sql_file = open(interpolate(self, self.sql_filename, as_filename=True, root_path=self.root_path), "r")
        sql_str = sql_file.read()
        sql_file.close()
        
        parameters = {}
        for c in child_results:
            parameters.update(c)

        cursor = self.sitemap.data_sources[self.datasource_name]
        cursor.execute(sql_str % parameters)

        result = lxml.etree.Element("result")
        result.attrib["query"] = sql_str
        result.attrib["rowcount"] = str(cursor.rowcount)

        col_names = [row_desc[0] for row_desc in cursor.description]
        
        for row in cursor.fetchall():
            result.append(lxml.etree.Element("row"))
            for n, v in zip(col_names, row):
                result[-1].append(lxml.etree.Element(n))
                result[-1][-1].text = unicode(str(v), encoding="utf-8", errors="replace")

        return (True, result)
