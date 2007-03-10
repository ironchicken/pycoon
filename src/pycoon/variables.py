#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import re
import logging

def getResolver(expr):
    if needsResolve(expr):
        return PreparedVariableResolver(expr)
    else:
        return NopVariableResolver(expr)

def buildMap(exprs, context, objectModel):
    return dict((k.resolve(context, objectModel), v.resolve(context, objectModel))
        for k, v in exprs.items())

def needsResolve(expr):
    if expr is None or len(expr) == 0:
        return False
    if expr[0] == "{":
        return True
    if len(expr) < 2:
        return False
    pos = 1
    pos = expr.find("{", pos)
    while pos != -1:
        if expr[pos - 1] != "\\":
            return True
        pos = expr.find("{", pos + 1)
    return False

class VariableResolver:
    def __init__(self, expr):
        self.expr = expr
    
    def resolve(self, context, objectModel):
        raise NotImplementedError()
    
class NopVariableResolver(VariableResolver):
    def resolve(self, context, objectModel):
        return self.expr

class PreparedVariableResolver(VariableResolver):
    def resolve(self, context, objectModel):        
        # TODO: Still doesn't handle escape-characters, i. e. "\{"
        vars = re.findall(r"{([^}]*)}", self.expr)
        if len(vars) > 0 and len(context.mapStack) == 0:
            raise Exception("There are variables to be resolved, but the context stack is empty")
        expr = self.expr
        for v in vars:
            if v.find(":") != -1:
                scheme, name = v.split(":", 1)
                mgr = objectModel["processor"].componentManager
                m = mgr.getComponent("input-module", scheme)
                subst = m.get(name, objectModel, "")
            else:
                subst = context.mapStack[-1].get(v, "")
            expr = re.sub("\{%s}" % v, subst, expr)
            
        # DEBUG:
        #import logging
        #logging.getLogger().debug("Variable %s resolved: %s" % (self.expr, expr))
        #logging.getLogger().debug("Resolved bytes: %s" % repr(expr))

        return expr

class InputModule(object):
    def configure(self, element=None):
        if element is not None:
            self.log = logging.getLogger(element.get("logger"))
    
    def get(self, name, objectModel, default=None):
        return NotImplementedError()
    
class RequestParameterModule(InputModule):
    def get(self, name, objectModel, default=None):
        encoding = objectModel["request"].formEncoding
        param = objectModel["request"].params.get(name, default)
        if encoding is not None:
            return param.decode(encoding)
        else:
            return param

class GlobalInputModule(InputModule):
    def get(self, name, objectModel, default=None):
        ret = default
        processor = objectModel["processor"]
        while processor is not None:
            confs = processor.componentConfigurations
            if confs is not None:
                e = confs.find("global-variables/%s" % name)
                if e is not None:
                    ret = e.text
            processor = processor.parent
        return ret
