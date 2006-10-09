#!/usr/bin/python
# -*- coding: utf-8 -*-
"""test-pycoon.py -- tests the Pycoon framework without apache web server
running

Usage:
    python test-pycoon.py <site-name> <method> <request-uri> <user-agent> <environment-type>
    
Arguments:
    site-name           an element from the SITES.keys() list, see the source
    method              the request method: [GET|POST]
    request-uri         an HTTP URI to which the request is made
    user-agent          an element from the USER_AGENTS.keys() list, see the source
    environment-type    devel -- if the framework is just exported from svn
                        lib   -- if the framework is installed as library and
                                 is accessible via sys.path
"""
import sys, datetime

ARGS = {"site": 1, "method": 2, "request-uri": 3, "user-agent": 4, "environment": 5}

SITES = {"home": {'SERVER_NAME': "localhost.localdomain",
                  'DOCUMENT_ROOT': "/home/richard/Documents/python/pycoon/tmp",
                  'PycoonSitemap': "test-sitemap.xml",
                  'PycoonConfigRoot': "/etc/pycoon"},
        "studio": {'SERVER_NAME': "localhost.localdomain",
                   'DOCUMENT_ROOT': "/var/www-studio",
                   'PycoonSitemap': "sitemap.xml",
                   'PycoonConfigRoot': "/etc/pycoon"},
        "cursus": {'SERVER_NAME': "localhost.localdomain",
                   'DOCUMENT_ROOT': "/var/www-cursus",
                   'PycoonSitemap': "sitemap.xml",
                   'PycoonConfigRoot': "/etc/pycoon"}}

USER_AGENTS = {"firefox": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.2) Gecko/Debian-1.5.dfsg+1.5.0.2-3 Firefox/1.5.0.2",
               "msie": "Mozilla/5.0 (compatible; NT; en-US; 6.0) MSIE (Windows NT 5)",
               "konqueror": "Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.2 (like Gecko) (Debian)",
               "galeon": "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.1) Gecko/Debian-1.8.0.1-8 Galeon/2.0.1 (Debian package 2.0.1-3)"}

class server(object):
    def __init__(self):
        self.cleanup_func = None
        self.server_hostname = ""

    def register_cleanup(self, req, func):
        self.cleanup_func = func

class request(object):
    def __init__(self, method, uri, headers_in=None):
        self.subprocess_env = SITES[sys.argv[1]]
        self.server = server()
        self.server.server_hostname = self.subprocess_env['SERVER_NAME']

        self.method = method.upper()
        
        pos_qm = uri.find("?")
        if pos_qm == -1: pos_qm = len(uri)
        pos_hash = uri.find("#")
        if pos_hash == -1: pos_hash = len(uri)

        self.path = uri[:pos_qm]
        self.query = uri[pos_qm+1:pos_hash]
        self.fragment = uri[pos_hash+1:]

        self.uri = uri
        self.unparsed_uri = uri
        self.parsed_uri = ("context", "", "", "", self.server.server_hostname, 80, self.path, self.query, self.fragment)

        self._content_type = ""

        self.headers_in = headers_in
        
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
    if len(sys.argv) < len(ARGS) + 1:
        print "Wrong command line arguments"
        print __doc__
        sys.exit(1)
        
    if sys.argv[ARGS["environment"]] == "lib":
        import pycoon
        from pycoon.helpers import fake_table
    elif sys.argv[ARGS["environment"]] == "devel":
        import os
        sys.path.append(os.path.join("..", "src"))
        import pycoon
        from pycoon.helpers import fake_table
    else:
        print "Wrong environment type, see usage"
        sys.exit(1)

    headers_in = fake_table()
    headers_in.add("Date", str(datetime.date.today()))
    headers_in.add("Request", "GET %s HTTP/1.1" % sys.argv[ARGS["request-uri"]])
    headers_in.add("Status", "200")
    headers_in.add("User-agent", USER_AGENTS[sys.argv[ARGS["user-agent"]]])
    headers_in.add("Accept-language", "EN")

    pycoon.apache._server_root = SITES[sys.argv[1]]['DOCUMENT_ROOT']
    
    r = request(sys.argv[ARGS["method"]], sys.argv[ARGS["request-uri"]], headers_in)

    res = pycoon.handler(r)
    print "Return code: %s" % res
    print "Return status: %s" % r.status
    
    r.server.cleanup_func(r)
