#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import re

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
        encoding = objectModel["request"].formEncoding
        
        # TODO: Still doesn't handle escape-characters, i. e. "\{"
        vars = re.findall(r"{([^}]*)}", self.expr)
        if len(vars) > 0 and len(context.mapStack) == 0:
            raise Exception("There are variables to be resolved, but the context stack is empty")
        expr = self.expr
        for v in vars:
            if v.find(":") != -1:
                scheme, name = v.split(":", 1)
                found = True
                if scheme == "request-param":
                    param = objectModel["request"].params.get(name, "")
                    if encoding is not None:
                        subst = param.decode(encoding)
                    else:
                        subst = param                    
                elif scheme == "global":
                    subst = ""
                    processor = objectModel["processor"]
                    while processor is not None:
                        confs = processor.componentConfigurations
                        if confs is not None:
                            gvars = confs.findall("global-variables/*")
                            subst = "".join([var.text for var in gvars if var.tag == name])
                        processor = processor.parent
                else:
                    raise Exception("Unknown variable resolving scheme for: %s" % v)
            else:
                subst = context.mapStack[-1].get(v, "")
            expr = re.sub("\{%s}" % v, subst, expr)
            
        # DEBUG:
        #import logging
        #logging.getLogger().debug("Variable %s resolved: %s" % (self.expr, expr))
        #logging.getLogger().debug("Resolved bytes: %s" % repr(expr))
            
        return expr

