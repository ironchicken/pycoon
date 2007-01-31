#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import lxml.etree as etree
from lxml.etree import Element, SubElement
from pycoon.components import Generator, Component
import pycoon
from pycoon import ns
from datetime import datetime
from socket import gethostname
import os

ns["st"] = "http://apache.org/cocoon/status/2.0"

class StatusGenerator(Generator):
    def generate(self, env, source, params):
        self.log.debug('<map:generate type="status"> process()')
        root = Element("{%(st)s}statusinfo" % ns)
        root.set("date", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"))
        root.set("host", gethostname())
        root.set("pycoon-version", pycoon.__version__)
        
        if os.name == "posix":
            from resource import getpagesize
            
            proc = SubElement(root, "{%(st)s}group" % ns, name="process")
            mem = SubElement(proc, "{%(st)s}group" % ns, name="memory")
            total = SubElement(mem, "{%(st)s}value" % ns, name="total")
            mempages = int(file("/proc/self/statm").read().split()[0])
            SubElement(total, "{%(st)s}line" % ns).text = str(mempages * getpagesize())

        env.response.body = root

