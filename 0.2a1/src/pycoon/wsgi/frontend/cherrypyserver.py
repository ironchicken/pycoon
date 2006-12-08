#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Usage: pycoon -s cherrypy <host> <port> [<pycoon.xconf absolute file URI>]"""

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import sys
import os
from pycoon.wsgi.servers.cherrypy.wsgiserver import CherryPyWSGIServer
from pycoon import wsgi

def main(*args):
    if len(args) == 2:
        from pkg_resources import resource_filename
        conf = resource_filename("pycoon", "pycoon.xconf")
        # Some Windows-specific file path handling
        if conf[0] != "/":
            conf = "file:///%s" % conf.replace("\\", "/")
        else:
            conf = "file://%s" % conf
    elif len(args) == 3:
        conf = args[2]
    else:
        print __doc__
        sys.exit(1)
    pycoon = wsgi.pycoonFactory({"server-xconf": conf})
    addr = (args[0], int(args[1]))
    server = CherryPyWSGIServer(addr, pycoon)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

