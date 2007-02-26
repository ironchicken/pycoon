#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xmlrpclib import Server, Binary
from datetime import datetime
import urllib

upd = """
<xupdate:modifications version="1.0" xmlns:xupdate="http://www.xmldb.org/xupdate">
  <xupdate:append select="doc('/db/pycoon-status')/data">
    %(data)s
  </xupdate:append>
</xupdate:modifications>
"""

def main():
    s = Server("http://admin:admin@localhost:8080/exist/xmlrpc")

    d = {
         "data": urllib.urlopen("http://localhost:8081/status").read(),
    }

    res = s.xupdate("/db", Binary(upd % d))
    
    if not res:
        s.parse("<data/>", "/db/pycoon-status")

if __name__ == "__main__":
    main()
