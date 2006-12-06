#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import logging
from pycoon import ns, SitemapException

class ComponentManager:
    def __init__(self):
        self.log = logging.getLogger("component-manager")
        self.modules = {}
        self.components = {
            "{%(map)s}generate" % ns: ({}, "{%(map)s}generator", "{%(map)s}generators" % ns),
            "{%(map)s}read" % ns: ({}, "{%(map)s}reader", "{%(map)s}readers" % ns),
            "{%(map)s}transform" % ns: ({}, "{%(map)s}transformer", "{%(map)s}transformers" % ns),
            "{%(map)s}serialize" % ns: ({}, "{%(map)s}serializer", "{%(map)s}serializers" % ns),
            "{%(map)s}match" % ns: ({}, "{%(map)s}matcher", "{%(map)s}matchers" % ns),
            "{%(map)s}select" % ns: ({}, "{%(map)s}selector", "{%(map)s}selectors" % ns),
            "{%(map)s}pipeline" % ns: ({}, "{%(map)s}pipe", "{%(map)s}pipes" % ns),
        }

    def configure(self, element):
        for classes, name, container in self.components.values():
            container = element.find(container)
            if container is None: continue
            self.log.debug("container: %s" % container)
            default = container.get("default")
            for e in container.findall(name % ns):
                name = e.get("name")
                klass = self.getClass(e.get("{%(py)s}src" % ns))
                classes[name] = klass, e
                if name == default:
                    classes["default"] = klass, e
        # TODO: Possibly we need to add ContentGenerator in the constructor,
        # because there will be several instances of ComponentManager for
        # mounted sitemaps in the fututre
        self.components["{%(map)s}aggregate" % ns] = ({"default": (self.getClass("pycoon.components.cocoon.ContentAggregator"), None)}, None, None)
        self.log.debug(self.components)
        
    def getComponent(self, role, type):
        entry = self.components[role][0]
        klass, element = entry.get(type, entry.get("default", (None, None)))
        if klass is None:
            raise SitemapException("There is no component of role %s and no default component of type %s" % (role, type))
        c = klass()
        c.configure(element)
        return c
    
    def getClass(self, name):
        self.log.debug("Getting class object by name: %s" % name)
        comps = name.split(".")
        if len(comps) > 1:
            moduleQName = ".".join(comps[:-1])
            className = comps[-1]
            if self.modules.has_key(moduleQName):
                return getattr(self.modules[moduleQName], className)
            else:
                moduleName = comps[-2]
                packageName = ".".join(comps[:-2])
                self.modules[moduleQName] = __import__(moduleQName, None, None, packageName)
                return getattr(self.modules[moduleQName], className)
        else:
            return getattr(sys.modules[__name__], name)

