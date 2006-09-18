#!/usr/bin/python
# -*- coding: utf-8 -*-
"""test-pycoon.py -- tests the Pycoon framework without apache web server
running

Usage:
    python test-pycoon.py <site-name> <request-uri> <environment-type>
    
Arguments:
    site-name           an element from the SITES.keys() list, see the source
    request-uri         an HTTP URI to which the request is made
    environment-type    devel -- if the framework is just exported from svn
                        lib   -- if the framework is installed as library and
                                 is accessible via sys.path
"""
import sys

SITES = {"home": {'SERVER_NAME': "localhost.localdomain",
                  'DOCUMENT_ROOT': "/home/richard/Documents/python/pycoon/tmp",
                  'sitemap': "test-sitemap.xml"},
        "studio": {'SERVER_NAME': "localhost.localdomain",
                   'DOCUMENT_ROOT': "/var/www-studio",
                   'sitemap': "sitemap.xml"},
        "cursus": {'SERVER_NAME': "localhost.localdomain",
                   'DOCUMENT_ROOT': "/var/www-cursus",
                   'sitemap': "sitemap.xml"}}

class server(object):
    def __init__(self):
        self.cleanup_func = None
        self.server_hostname = ""

    def register_cleanup(self, req, func):
        self.cleanup_func = func

class request(object):
    def __init__(self, uri):
        self.subprocess_env = SITES[sys.argv[1]]
        self.server = server()
        self.server.server_hostname = self.subprocess_env['SERVER_NAME']
        self.uri = uri
        self.unparsed_uri = uri
        self.parsed_uri = ("context", "", "", "", self.server.server_hostname, 80, uri, "", "")
        self._content_type = ""
        self.status = 200

    def document_root(self):
        return self.subprocess_env['DOCUMENT_ROOT']
    
    def set_content_type(self, c):
        sys.stderr.write("Content-type: %s\n" % c)
        self._content_type = c

    def get_content_type(self): return self._content_type

    content_type = property(fget=get_content_type, fset=set_content_type)
    
    def write(self, *args):
        for a in args:
            print a

    def sendfile(self, fn):
        f = open(fn, "r")
        print f.read()
        f.close()

    def set_content_length(self, l):
        sys.stderr.write("Content-length: %d\n" % l)

    def add_common_vars(self):
        pass

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "Wrong command line arguments"
        print __doc__
        sys.exit(1)
        
    if sys.argv[3] == "lib":
        import pycoon
    elif sys.argv[3] == "devel":
        import os
        sys.path.append(os.path.join("..", "src"))
        import pycoon
    else:
        print "Wrong environment type, see usage"
        sys.exit(1)
        
    r = request(sys.argv[2])

    res = pycoon.handler(r)
    print "Return code: %s" % res
    print "Return status: %s" % r.status
    
    r.server.cleanup_func(r)
