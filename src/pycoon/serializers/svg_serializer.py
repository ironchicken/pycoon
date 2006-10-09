"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.
"""

from pycoon.serializers import serializer, SerializerError
from pycoon.components import invokation_syntax
from lxml.etree import tounicode
import os, tempfile
try:
    from gtk import gdk
    GDK_AVAIL = True
except (ImportError, RuntimeError):
    GDK_AVAIL = False

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "serialize"
    invk_syn.allowed_parent_components = ["pipeline", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type"]
    invk_syn.required_attrib_values = {"type": "svg"}
    invk_syn.optional_attribs = ["mime"]
    invk_syn.allowed_child_components = []

    server.component_syntaxes[("serialize", "svg")] = invk_syn
    return invk_syn

class svg_serializer(serializer):
    """
    svg_serializer class encapsulates the RSVG rasterizer.
    """

    def __init__(self, parent, mime="image/png", root_path=""):
        """
        svg_serializer constructor.
        """

        serializer.__init__(self, parent, root_path)
        self.mime_str = mime
        self.description = "svg_serializer()"

    def _descend(self, req, p_sibling_result=None):
        return False

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Executes rsvg using the p_sibling_result and returns the resultant image.
        """

        try:
            if GDK_AVAIL:
                # in this case, use the gdk functions

                (svg_fd, svg_path) = tempfile.mkstemp()
                pixbuf = gdk.pixbuf_new_from_file(svg_path)
                os.close(svg_fd)
                os.remove(svg_path)

                (image_fd, image_path) = tempfile.mkstemp()
                
                if self.mime_str == "image/jpeg":
                    pixbuf.save(image_path, "jpeg", {"quality":"85"})
                elif self.mime_str == "image/png":
                    pixbuf.save(image_path, "png")
                else:
                    raise GError()

                result = os.read(image_fd)
                os.close(image_fd)
                os.remove(image_path)

                return (True, (result, self.mime_str))
            
            else:
                # otherwise, try using the rsvg external program
                (svg_fd, svg_path) = tempfile.mkstemp()
                os.write(svg_fd, tounicode(p_sibling_result))
                os.close(svg_fd)
                
                (png_fd, png_path) = tempfile.mkstemp()
                rsvg_cmd = os.popen("rsvg %s %s" % (svg_path, png_path))
                if rsvg_cmd.close() is None:
                    result = os.read(png_fd)

                os.remove(svg_path)
                os.close(png_fd)
                os.remove(png_path)

                # rsvg executable will only return PNG images
                return (True, (result, "image/png"))
        
        except (GError, OSError):
            return (True, (p_sibling_result, "text/xml"))
        except TypeError:
            if p_sibling_result is None:
                raise SerializerError("svg_serializer: preceding pipeline components have returned no content!")
