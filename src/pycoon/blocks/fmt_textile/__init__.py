#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import lxml.etree as etree
from pycoon.components import Generator, Component
import textile

class TextileGenerator(Generator):
    def configure(self, element=None):
        Component.configure(self, element)
        if element is not None:
            self.encoding = element.find("encoding").text
        else:
            self.encoding = "utf-8"
    
    def generate(self, env, source, params):
        self.log.debug('<map:generate src="%s"> process()' % source.uri)
        data = source.read()
        # XXX: (#23) There is a possible threading bug here. If this code is
        # accessed from multiple threads simultaneously (10 requests per second
        # is usually enough), then sometimes not all the syntax terms are
        # parsed correctly. For example, *imp* could remain *imp* after parsing
        # instead of <strong>imp</strong>, or even could become <ins>imp</ins>!
        data = textile.Textiler(data).process(encoding=self.encoding, output="utf-8")
        env.response.body = etree.fromstring('<div xmlns="http://www.w3.org/1999/xhtml">\n%s\n</div>' % data)

