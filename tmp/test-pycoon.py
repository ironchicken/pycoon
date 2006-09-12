#!/usr/bin/python

import sys
import pycoon

SITES = {"home": {'SERVER_NAME': "localhost.localdomain",\
                  'DOCUMENT_ROOT': "/home/richard/Documents/python/pycoon/tmp",\
                  'sitemap': "test-sitemap.xml"},\
        "studio": {'SERVER_NAME': "localhost.localdomain",\
                   'DOCUMENT_ROOT': "/var/www-studio",\
                   'sitemap': "sitemap.xml"},\
        "cursus": {'SERVER_NAME': "localhost.localdomain",\
                   'DOCUMENT_ROOT': "/var/www-cursus",\
                   'sitemap': "sitemap.xml"}}

class server:
    def __init__(self):
        self.cleanup_func = None
        self.server_hostname = ""

    def register_cleanup(self, req, func):
        self.cleanup_func = func

class request:
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
        sys.stderr.write("Content-type: %s\n" % s)
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

r = request(sys.argv[2])

res = pycoon.handler(r)
print "Return code: %s" % res
print "Return status: %s" % r.status

r.server.cleanup_func(r)
