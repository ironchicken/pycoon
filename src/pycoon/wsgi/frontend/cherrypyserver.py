#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage: cherrypyserver.py <host> <port> <pycoon.xconf absolute file: URI> 
"""

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import sys
import os
sys.path.append(os.path.join(os.path.dirname(sys.modules[__name__].__file__), "..", "..", ".."))
from pycoon.wsgi.servers.cherrypy.wsgiserver import CherryPyWSGIServer
from pycoon import wsgi

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print __doc__
        sys.exit(1)
    pycoon = wsgi.pycoonFactory({"server-xconf": sys.argv[3]})
    addr = (sys.argv[1], int(sys.argv[2]))
    server = CherryPyWSGIServer(addr, pycoon)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

