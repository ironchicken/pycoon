#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import logging
import time
import lxml.etree as etree
from pycoon import ns, synchronized
from pycoon.source import FileSource, SourceResolver
from pycoon.sitemap.nodes import PipelinesNode, PipelineNode, AggregateNode, SerializeNode, ResourceCall, SelectNode, HandleErrorsNode, GenerateNode, MatchNode, TransformNode, ReadNode, MountNode
from pycoon.sitemap.nodes import Node, ContainerNode, InvokeContext
from pycoon.sitemap.manager import ComponentManager
from pycoon import variables

class TreeProcessor(Node):    
    def __init__(self, contextPath=None):
        Node.__init__(self)
        self.contextPath = contextPath
        self.rootNode = None
        self.children = {}
        self.parent = None
        self.parentComponentManager = None
        self.componentConfigurations = None
        self.lastModified = 0
        self.log = logging.getLogger("sitemap.processor")
        self.checkReload = True
    
    def configure(self, element):
        self.checkReload = (element.get("check-reload", "yes") == "yes")
        self.uri = element.get("file", "sitemap.xmap")
        self.source = SourceResolver().resolveUri(self.uri, self.contextPath)
        self.log = logging.getLogger(element.get("logger"))
        self.log.debug("Tree processor is configured")

    def process(self, env):
        t0 = time.clock()
        try:
            env.objectModel["processor"] = self
            if env.objectModel.get("root-processor") is None:
                env.objectModel["root-processor"] = self.parent
            self.setupProcessor(env)
            context = InvokeContext()
            return self.rootNode.invoke(env, context)
        finally:
            t1 = time.clock()
            if self.parent is None:
                self.log.debug("'%s': rendered in %.3f s" % (env.request.uri, t1 - t0))
    
    def buildPipeline(self, env):
        env.objectModel["processor"] = self
        if env.objectModel.get("root-processor") is None:
            env.objectModel["root-processor"] = self.parent
        context = InvokeContext(True)
        if self.rootNode.invoke(env, context):
            return context.processingPipeline
        else:
            return None
        
    def setupProcessor(self, env):
        log = logging.getLogger("%s.setup" % self.log.name)
        log.debug("Setting up processor for: %s" % self.source.uri)
        if self.parent is None:
            env.changeContext("", self.source.uri)
        
        if self.checkReload and self.source.getLastModified() != self.lastModified:
            log.debug("Source: %s" % self.source.uri)
            log.debug("Source mtime: %d" % self.source.getLastModified())
            log.debug("Processor mtime: %d" % self.lastModified)
            self.buildProcessor(env)
        env.componentManager = self.componentManager

    @synchronized
    def buildProcessor(self, env):
        # We are now in the critical section, so check the conditions once again
        if self.rootNode is not None and self.source.getLastModified() == self.lastModified:
            return
        builder = TreeBuilder()
        builder.processor = self
        root = builder.build(self.source)
        self.rootNode = root
        self.componentManager = builder.componentManager
        if self.parentComponentManager is not None:
            self.componentManager.parent = self.parentComponentManager
        if self.parent is None:
            self.contextPath = env.contextPath
        self.lastModified = self.source.getLastModified()
        self.log.debug("Processor (re)built")
        
    @synchronized
    def createChildProcessor(self, src, env):
        if src in self.children:
            child = self.children[src]
        else:
            child = TreeProcessor()
            child.parent = self
            child.log = logging.getLogger("sitemap.processor")
            child.uri = src
            child.source = SourceResolver(env).resolveUri(child.uri)
            self.children[src] = child
        #child.componentConfigurations = self.componentConfigurations
        child.parentComponentManager = self.componentManager
        return child
        
class ComponentConfigurations:
    def build(self, element):
        self.element = element
        
class TreeBuilder:

    nodeClasses = {
        "pipelines": PipelinesNode,
        "pipeline": PipelineNode,
        "match": MatchNode,
        "aggregate": AggregateNode,
        "serialize": SerializeNode,
        "call": ResourceCall,
        "generate": GenerateNode,
        "transform": TransformNode,
        "select": SelectNode,
        "read": ReadNode,
        "handle-errors": HandleErrorsNode,
        "mount": MountNode,
        "component-configurations": ComponentConfigurations,
    }
    
    def __init__(self):
        self.componentManager = None
        self.log = logging.getLogger("sitemap.builder")
    
    def build(self, source):
        t0 = time.clock()
        try:
            self.root = etree.fromstring(source.read())
            self.componentManager = ComponentManager()
            components = self.root.find("{%(map)s}components" % ns)
            if components is not None:
                self.componentManager.configure(components)
            return self.buildNode(self.root.find("{%(map)s}pipelines" % ns))
        finally:
            t1 = time.clock()
            self.log.debug("%s is built in %.3f s" % (source.uri, t1 - t0))
        
    def buildNode(self, element):
        if not isinstance(element.tag, str) or not element.tag.startswith("{%(map)s}" % ns):
            return None

        suffix = element.tag[len("{%(map)s}" % ns):]
        try:
            node = self.nodeClasses[suffix]()
        except KeyError:
            raise Exception("Unknown sitemap element tag: %s" % suffix)
        
        node.build(element)
        
        if isinstance(node, SelectNode):
            node.whenElements = []

            for when in element.findall("{%(map)s}when" % ns):
                test = variables.getResolver(when.get("test"))
                nodes = [self.buildNode(c) for c in when]
                actualNodes = [n for n in nodes if n is not None]
                node.whenElements.append((test, actualNodes))
            
            otherwise = element.find("{%(map)s}otherwise" % ns)
            if otherwise is not None:
                nodes = [self.buildNode(c) for c in otherwise]
                node.otherwiseNodes = [n for n in nodes if n is not None]
            
            return node
        
        if isinstance(node, ResourceCall):
            element = None
            for r in self.root.findall("{%(map)s}resources/{%(map)s}resource" % ns):
                if r.get("name") == node.name:
                    element = r
                    break
            if element is None:
                raise Exception('<map:resource name="%s"> not found' % node.name)
        
        if isinstance(node, ContainerNode):
            children = [self.buildNode(c) for c in element]
            def isRegularNode(c):
                return isinstance(c, Node) and not isinstance(c, HandleErrorsNode)
            node.children = [c for c in children if isRegularNode(c)]
            handleNodes = [c for c in children if isinstance(c, HandleErrorsNode)]
            if len(handleNodes) > 0:
                node.handleErrorsNode = handleNodes.pop()
                
        if isinstance(node, PipelinesNode):
            if len(node.children) > 0:
                node.children[-1].isLast = True

        if isinstance(node, ComponentConfigurations):
            self.processor.componentConfigurations = node.element

        return node

