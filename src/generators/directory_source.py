"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

import pycoon.sources
from pycoon import apache
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
import os
import lxml.etree

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "source"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "directory-list"}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("source", "directory-list")] = invk_syn
    return invk_syn

class directory_source(pycoon.sources.source):
    """
    directory_source class implements the source interface and returns an XML document containing a
    directory tree.
    """
    
    def __init__(self, parent, src, root_path=""):
        """
        directory_source constructor. Requires the path string.
        """

        self.path = src
        self.doc_str = ""
        pycoon.sources.source.__init__(self, parent, root_path)
        self.description = "directory_source(\"%s\")" % self.path

    def list_path(self, path):
        """
        Begin listing the path, calls a recursive function.
        """

        self.dirlist = lxml.etree.Element("dirlist")
        self.descend_path(path, self.dirlist)

    def descend_path(self, path, parent):
        """
        The recursive function: descend all the directories and add all the file names.
        """

        try:
            for root, dirnames, filenames in os.walk(path):
                dir_el = lxml.etree.Element("d")
                dir_el.attrib["name"] = root
                
                for d in dirnames:
                    self.descend_path(d, dir_el)
            
                for f in filenames:
                    file_el = lxml.etree.Element("f")
                    file_el.attrib["name"] = f
                    dir_el.append(file_el)

                parent.append(dir_el)
        except OSError:
            # if there's an error reading a directory, it doesn't matter (likely a 'permission denied')
            # it'll just return an incomplete tree
            pass

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        return False

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Generate the directory list and return the result as an Element object.
        """

        path = interpolate(self.context, self.path, uri_pattern, as_filename=True, root_path=self.root_path)
        
        if os.stat(path):
            self.list_path(path)
            return (True, self.dirlist)
        else:
            return (False, apache.HTTP_NOT_FOUND)
