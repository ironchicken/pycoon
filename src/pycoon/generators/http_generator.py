"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module provides the http_generator which allows an XML source to be
retrieve using an HTTP request.
"""

from pycoon.generators import generator, GeneratorError
from pycoon.interpolation import interpolate
from pycoon.components import invokation_syntax
import lxml.etree
import httplib, urllib, urlparse
from StringIO import StringIO

def register_invokation_syntax(server):
    """
    Allows the component to register the required XML element syntax for it's invokation
    in sitemap files with the sitemap_config_parse class.
    """
        
    invk_syn = invokation_syntax()
    invk_syn.element_name = "generate"
    invk_syn.allowed_parent_components = ["pipeline", "aggregate", "match", "when", "otherwise"]
    invk_syn.required_attribs = ["type", "src"]
    invk_syn.required_attrib_values = {"type": "http"}
    invk_syn.optional_attribs = ["method"]
    invk_syn.allowed_child_components = ["parameter"]

    server.component_syntaxes[("generate", "http")] = invk_syn
    return invk_syn

class http_generator(generator):
    """
    http_generator allows an XML source to be retrieved using an HTTP request. Child <parameter> elements
    can be used to set POST or GET parameters.
    """

    def __init__(self, parent, src, method="GET", root_path=""):
        """
        http_generator constructor.

        @src: the URI of the HTTP request
        @method: the HTTP method: [GET|POST]
        """

        self.src = src
        self.method = method.upper()
        
        generator.__init__(self, parent, root_path)

        self.description = "http_generator(\"%s\")" % self.src

    def _descend(self, req, p_sibling_result=None):
        return True

    def _result(self, req, p_sibling_result=None, child_results=[]):
        """
        Attempts to retrieve XML from the URI and return an ElementTree representation of it.
        """

        try:
            uri = interpolate(self, self.src)
            (protocol, host, path, p, q, f) = urlparse.urlparse(uri)
            
            parameters = urllib.urlencode(self.parameter_children(child_results)) + q

            conn = httplib.HTTPConnection(host)

            if self.method == "GET":
                conn.request("GET", urlparse.urlunparse((protocol, host, path, p, parameters, f)))
                response = conn.getresponse()
            elif self.method == "POST":
                conn.request("POST", urlparse.urlunparse((protocol, host, path, p, "", f)), parameters)
                response = conn.getresponse()

            if response.status == 200:
                return (True, lxml.etree.parse(StringIO(response.read())).getroot())
            else:
                raise GeneratorError("http_generator: request \"%s\" returned error code: %s" % (uri, response.status))

        except httplib.HTTPException, e:
            raise GeneratorError("http_generator: exception occured during HTTP request: \"%\"" % str(e))
        
        except lxml.etree.XMLSyntaxError, e:
            raise GeneratorError("http_generator: syntax error in XML source, \"%s\": \"%s\"" %\
                                 (interpolate(self, self.src, as_filename=True, root_path=self.root_path), str(e)))
