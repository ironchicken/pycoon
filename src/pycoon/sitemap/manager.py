#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import logging
from pycoon import ns, SitemapException

class ComponentManager:
    def __init__(self):
        self.parent = None
        self.log = logging.getLogger("component-manager")
        self.classLoader = ClassLoader()
        self.components = {
            "{%(map)s}generate" % ns: ({}, "{%(map)s}generator", "{%(map)s}generators" % ns),
            "{%(map)s}read" % ns: ({}, "{%(map)s}reader", "{%(map)s}readers" % ns),
            "{%(map)s}transform" % ns: ({}, "{%(map)s}transformer", "{%(map)s}transformers" % ns),
            "{%(map)s}serialize" % ns: ({}, "{%(map)s}serializer", "{%(map)s}serializers" % ns),
            "{%(map)s}match" % ns: ({}, "{%(map)s}matcher", "{%(map)s}matchers" % ns),
            "{%(map)s}select" % ns: ({}, "{%(map)s}selector", "{%(map)s}selectors" % ns),
            "{%(map)s}act" % ns: ({}, "{%(map)s}action", "{%(map)s}actions" % ns),
            "{%(map)s}pipeline" % ns: ({}, "{%(map)s}pipe", "{%(map)s}pipes" % ns),
            "{%(map)s}aggregate" % ns: ({"default": (self.classLoader.getClass("pycoon.components.cocoon.ContentAggregator"), None)}, None, None),
        }

    def configure(self, element):
        for classes, name, containterName in self.components.values():
            if containterName is None: continue
            container = element.find(containterName)
            if container is None: continue
            self.log.debug("container: %s" % container)
            default = container.get("default")
            for e in container.findall(name % ns):
                name = e.get("name")
                klass = self.classLoader.getClass(e.get("{%(py)s}src" % ns))
                classes[name] = klass, e
                if name == default:
                    classes["default"] = klass, e
        self.log.debug(self.components)
        
    def getComponent(self, role, type):
        entry = self.components[role][0]
        if type is None:
            klass, element = entry.get("default", (None, None))
        else:
            klass, element = entry.get(type, (None, None))
        if klass is None:
            if self.parent is not None:
                return self.parent.getComponent(role, type)
            else:
                raise SitemapException("There is no component of role %s and no default component of type %s" % (role, type))
        c = klass()
        c.configure(element)
        return c
    
class ClassLoader:
    def __init__(self):
        self.modules = {}
        
    def getClass(self, name):
        comps = name.split(".")
        if len(comps) > 1:
            moduleQName = ".".join(comps[:-1])
            className = comps[-1]
            if moduleQName in self.modules:
                return getattr(self.modules[moduleQName], className)
            else:
                moduleName = comps[-2]
                packageName = ".".join(comps[:-2])
                self.modules[moduleQName] = __import__(moduleQName, None, None, packageName)
                return getattr(self.modules[moduleQName], className)
        else:
            return getattr(sys.modules[__name__], name)
