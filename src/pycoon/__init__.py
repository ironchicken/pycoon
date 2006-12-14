#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Pycoon Web Development Framework
Copyright (C) 2006 Andrey Nordin, Richard Lewis
This is free software, and you are welcome to redistribute it under certain
conditions; use --license option for details.

Usage: pycoon <options>

Options:
    -s, --serve <srv>   , where srv is:
    
        cherrypy <host> <port> [<pycoon.xconf absolute file URI>]
                        run Pycoon in CherryPy WSGI server
    
    --help              print help message
    --license           print legal info"""

__license__ = \
"""Pycoon Web Development Framework
Copyright (C) 2006 Andrey Nordin, Richard Lewis

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"
__version__ = "0.2a3"

ns = {
    "map": "http://apache.org/cocoon/sitemap/1.0",
    "py": "http://pycoon.org/ns/pysitemap/0.1/",
}

class ResourceNotFoundException(Exception): pass

class SitemapException(Exception): pass

def synchronized(func):
    def decorator(self, *args, **kwargs):
        try:
            rlock = self._lock
        except AttributeError:
            from threading import RLock
            rlock = self.__dict__.setdefault("_lock", RLock())
        rlock.acquire()
        try:
            return func(self, *args, **kwargs)
        finally:
            rlock.release()
    return decorator

def main():    
    import sys
    import getopt
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:", ["help", "license", "serve="])
        for opt, arg in opts:
            if opt == "--help":
                print __doc__
                sys.exit(0)
            elif opt == "--license":
                print __license__
                sys.exit(0)
            elif opt in ("-s", "--serve"):
                if arg == "cherrypy":
                    from pycoon.wsgi.frontend import cherrypyserver
                    cherrypyserver.main(*args)
                    sys.exit(0)
                else:
                    raise getopt.GetoptError("")
            else:
                raise getopt.GetoptError("")
        print __doc__
        sys.exit(1)
    except getopt.GetoptError:
        print "Wrong command line options, use --help"
        sys.exit(1)

