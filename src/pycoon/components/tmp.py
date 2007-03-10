#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import lxml.etree as etree
from pycoon.components import Generator, Component
from docutils.core import publish_parts

class RestructuredGenerator(Generator):
    def configure(self, element=None):
        Component.configure(self, element)
        if element is not None:
            self.encoding = element.find("encoding").text
        else:
            self.encoding = "utf-8"
    
    def generate(self, env, source, params):
        self.log.debug('<map:generate src="%s"> process()' % source.uri)
        data = source.read()
        overrides = {
            "input_encoding": self.encoding,
            "output_encoding": self.encoding,
        }
        data = publish_parts(data, writer_name="html", settings_overrides=overrides).get("html_body")
        env.response.body = etree.fromstring('<div xmlns="http://www.w3.org/1999/xhtml">\n  %s\n</div>' % data)
        
        #data = textile.textile(data, encoding=self.encoding, output="utf-8")
        #env.response.body = etree.fromstring('<div xmlns="http://www.w3.org/1999/xhtml">\n  %s\n</div>' % data)

