#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import logging

class Component:
    def __init__(self):
        self.params = {}
        
    def configure(self, element=None):
        if element is not None:
            self.type = element.get("type")
            self.name = element.get("name")
            self.log = logging.getLogger(element.get("logger"))

class Serializer(Component):
    def serialize(self, env, params):
        raise NotImplementedError()

class Selector(Component):
    def select(self, expr, objectModel, params):
        u"""
        Проверяет соответствие выражения каким-то объектам в objectModel и
        сообщает об успехе, возвращая True.
        params -- параметры, указанные в элементах <map:parameter>.
        """
        raise NotImplementedError()

class Generator(Component):
    def generate(self, env, source, params):
        raise NotImplementedError()

class Transformer(Component):
    def transform(self, env, source, params):
        raise NotImplementedError() 
    
class Matcher(Component):
    def match(self, pattern, objectModel, params):
        raise NotImplementedError()

class Reader(Component):
    def read(self, env, source, params):
        raise NotImplementedError()

