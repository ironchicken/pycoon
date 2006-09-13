"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The module provides the read component which handles <read> elements
in pipeline configurations by loading an external file.
"""

import os
from pycoon import apache
from pycoon.components import stream_component, invokation_syntax
from pycoon.interpolation import interpolate

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "read"
    invk_syn.allowed_parent_components = ["pipeline"]
    invk_syn.required_attribs = ["src"]
    invk_syn.required_attrib_values = {}
    invk_syn.optional_attribs = []
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("read", None)] = invk_syn
    return invk_syn

class read(stream_component):
    """
    read objects correspond to <read> elements in a pipeline. They simply read the contents of the given file and
    write it to the response stream.

    @parent: the parent component of this component.
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default.
    @src: the path of the file to read (may include interpolation instructions).
    """
    
    function = "read"

    def __init__(self, parent, src, root_path=""):
        stream_component.__init__(self, parent, root_path)

        self.file_name = root_path + os.sep + src

        self.description = "Read: \"%s\"" % src
        self.function = "read"

    def _descend(self, req, p_sibling_result=None):
        return False
    
    def _result(self, req, p_sibling_result=None, child_results=[]):
        # it makes most sense simply to call req.sendfile(). However, it fits the architecture better to read the contents of the file
        # into a memory stream first so that it can go through the rest of the pipeline (especially for XML/HTML docs.)
        # However, this is going to to be *bad* for binary files. Could we make this some sort of exception?

        try:
            fn = interpolate(self, self.file_name)
            #os.stat(fn)

            return (True, file(fn, 'r').read())

        except IOError:
            return (False, apache.HTTP_NOT_FOUND)
