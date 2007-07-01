#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import logging
import sys
from pycoon import ResourceNotFoundException, ns, variables

class Node:
    def __init__(self):
        self.params = {}

    def build(self, element):
        self.elementName = element.tag
        self.type = element.get("type")

    def invoke(self, env, context):
        return False

    def _buildParams(self, element):
        for c in element.findall("{%(map)s}parameter" % ns):
            name = variables.getResolver(c.get("name"))
            value = variables.getResolver(c.get("value"))
            self.params[name] = value

class ContainerNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.children = []

    def invokeChildren(self, env, context, currentMap=None, children=None):
        if children is None: children = self.children
        if currentMap is not None: context.pushMap(currentMap)
        try:
            for c in children:
                if c.invoke(env, context):
                    return True
        finally:
            if currentMap is not None: context.popMap()
        return False

class InvokeContext:
    def __init__(self, isBuildingPipelineOnly=False):
        self.isBuildingPipelineOnly = isBuildingPipelineOnly
        self.mapStack = []
        self.processingPipeline = None

    def pushMap(self, map):
        self.mapStack.append(map)
        
    def popMap(self):
        self.mapStack.pop()

class HandleErrorsNode(ContainerNode):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.handle-errors")
        
    def build(self, element):
        Node.build(self, element)
        self.when = variables.getResolver(element.get("when", "external"))
    
    def invoke(self, env, context, exception=None):
        resolvedWhen = self.when.resolve(context, env.objectModel)
        self.log.debug("<map:handle-errors> invoke(), when: %s" % resolvedWhen)
        
        if resolvedWhen == "external" and not env.isExternal:
            raise exception
        elif resolvedWhen == "internal" and env.isExternal:
            raise exception        
        env.objectModel["throwable"] = exception

        if "exc_info" not in env.objectModel:
            env.objectModel["exc_info"] = sys.exc_info()
        
        context = InvokeContext()
        context.processingPipeline = env.componentManager.getComponent("{%(map)s}pipeline" % ns, "default")
        if self.invokeChildren(env, context):
            env.response.exceptionAware = True
            return True
        else:
            raise exception

class MountNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.mount")    
    
    def build(self, element):
        Node.build(self, element)
        self.src = variables.getResolver(element.get("src"))
        self.prefix = variables.getResolver(element.get("uri-prefix"))
    
    def invoke(self, env, context):
        resolvedSource = self.src.resolve(context, env.objectModel)
        resolvedPrefix = self.prefix.resolve(context, env.objectModel)
        self.log.debug('<map:mount src="%s" prefix-uri="%s"> invoke()' % (resolvedSource, resolvedPrefix))
 
        if resolvedSource.endswith("/"):
            resolvedSource += "sitemap.xmap"

        processor = env.objectModel["processor"].createChildProcessor(resolvedSource, env)
        
        oldPrefix = env.prefix
        oldUri = env.request.uri
        oldContextPath = env.contextPath
        pipelineWasBuilt = False
        
        try:
            env.changeContext(resolvedPrefix, resolvedSource)
            if context.isBuildingPipelineOnly:
                processor.setupProcessor(env)
                pipeline = processor.buildPipeline(env)
                if pipeline is not None:
                    context.processingPipeline = pipeline                    
                    pipelineWasBuilt = True
            else:
                self.log.debug("Processing")
                pipelineWasBuilt = processor.process(env)
        finally:
            if not pipelineWasBuilt:
                env.setContext(oldPrefix, oldUri, oldContextPath)
                env.objectModel["processor"] = processor.parent
        return pipelineWasBuilt
            
class PipelinesNode(ContainerNode):
    def __init__(self):
        ContainerNode.__init__(self)
        self.log = logging.getLogger("sitemap.pipelines")
        self.handleErrorsNode = None

    def invoke(self, env, context):
        try:
            return self.invokeChildren(env, context)
        except Exception, e:
            if self.handleErrorsNode is not None:
                return self.handleErrorsNode.invoke(env, context, e)
            else:
                raise

class PipelineNode(ContainerNode):
    def __init__(self):
        ContainerNode.__init__(self)
        self.log = logging.getLogger("sitemap.pipeline")
        self.isLast = False
        self.handleErrorsNode = None

    def build(self, element):
        Node.build(self, element)
        self.isInternalOnly = (element.get("internal-only", "no") == "yes")

    def invoke(self, env, context):
        if self.isInternalOnly and env.isExternal:
            if not self.isLast:
                return False
            else:
                raise ResourceNotFoundException('No pipeline matched request: "%s%s"' % (env.prefix, env.request.uri))
        context.processingPipeline = env.componentManager.getComponent(self.elementName, self.type)
        self.log.debug('<map:pipeline> invoke(): %d' % id(context.processingPipeline))
        try:
            if self.invokeChildren(env, context):
                # For handling errors in SitemapSource, where invoke() and
                # process() are separated and context.isBuildingPipelineOnly.
                # Otherwise PipelineNode instance will catch exception itself
                if self.handleErrorsNode is not None and context.isBuildingPipelineOnly:
                    context.processingPipeline.handleErrorsNode = self.handleErrorsNode
                    self.log.debug("Setting handleErrorsNode: %s" % context.processingPipeline.handleErrorsNode)
                return True
            elif not self.isLast:
                return False
            raise ResourceNotFoundException('No pipeline matched request: "%s%s"' % (env.prefix, env.request.uri))
        except Exception, e:
            if self.handleErrorsNode is not None:
                return self.handleErrorsNode.invoke(env, context, e)
            else:
                raise

class ResourceCall(ContainerNode):
    def __init__(self):
        ContainerNode.__init__(self)
        self.log = logging.getLogger("sitemap.resource-call")
    
    def build(self, element):
        Node.build(self, element)
        self.name = element.get("resource")
        self._buildParams(element)
        
    def invoke(self, env, context):
        self.log.debug('<map:call resource="%s"> invoke()' % self.name)
        params = variables.buildMap(self.params, context, env.objectModel)
        return self.invokeChildren(env, context, params)

class MatchNode(ContainerNode):
    def __init__(self):
        ContainerNode.__init__(self)
        self.log = logging.getLogger("sitemap.matcher")    
    
    def build(self, element):
        Node.build(self, element)
        self._buildParams(element)
        self.pattern = element.get("pattern")

    def invoke(self, env, context):
        resolvedParams = variables.buildMap(self.params, context, env.objectModel)
        matcher = env.componentManager.getComponent(self.elementName, self.type)
        result = matcher.match(self.pattern, env.objectModel, resolvedParams)
        if result is not None:
            self.log.debug('<map:match pattern="%s">: invoke(%s)' % (self.pattern, env.request.uri))
            return self.invokeChildren(env, context, result)
        else:
            return False

class TransformNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.transformer")    
    
    def build(self, element):
        Node.build(self, element)
        self.src = variables.getResolver(element.get("src"))
        self._buildParams(element)
        
    def invoke(self, env, context):
        t = env.componentManager.getComponent(self.elementName, self.type)
        t.src = self.src.resolve(context, env.objectModel)
        t.params = variables.buildMap(self.params, context, env.objectModel)
        context.processingPipeline.transformers.append(t)
        self.log.debug('<map:transform src="%s"> invoke()' % t.src)
        
class GenerateNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.generator")
        
    def build(self, element):
        Node.build(self, element)
        self._buildParams(element)
        self.src = variables.getResolver(element.get("src"))
    
    def invoke(self, env, context):
        g = env.componentManager.getComponent(self.elementName, self.type)
        g.src = self.src.resolve(context, env.objectModel)
        g.params = variables.buildMap(self.params, context, env.objectModel)
        context.processingPipeline.generator = g
        self.log.debug('<map:generate src="%s"> invoke()' % g.src)

class AggregateNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.aggregator")
    
    def build(self, element):
        Node.build(self, element)
        self.element = variables.getResolver(element.get("element"))
        self.ns = variables.getResolver(element.get("ns"))
        self.parts = [variables.getResolver(c.get("src")) for c in element.findall("{%(map)s}part" % ns)]
        
    def invoke(self, env, context):
        g = env.componentManager.getComponent(self.elementName, self.type)
        g.configure()
        g.src = None        
        g.element = self.element.resolve(context, env.objectModel)
        g.ns = self.ns.resolve(context, env.objectModel)
        g.parts = [p.resolve(context, env.objectModel) for p in self.parts]
        g.params = {}
        context.processingPipeline.generator = g
        self.log.debug('<map:aggregate element="%s"> invoke()' % g.element)
        return False

class SerializeNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.serializer")

    def build(self, element):
        Node.build(self, element)
        self._buildParams(element)
        self.statusCode = int(element.get("status-code", -1))
        self.mimeType = element.get("mime-type")
    
    def invoke(self, env, context):
        self.log.debug('<map:serialize> invoke()')
        s = env.componentManager.getComponent(self.elementName, self.type)
        s.params = variables.buildMap(self.params, context, env.objectModel)
        s.statusCode = self.statusCode
        if self.mimeType is not None:
            s.mimeType = self.mimeType
        context.processingPipeline.serializer = s
        if not context.isBuildingPipelineOnly:
            return context.processingPipeline.process(env)
        else:
            return True
            
class ReadNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.reader")
        
    def build(self, element):
        Node.build(self, element)
        self._buildParams(element)
        self.src = variables.getResolver(element.get("src"))
        self.mimeType = element.get("mime-type")
    
    def invoke(self, env, context):
        r = env.componentManager.getComponent(self.elementName, self.type)
        r.src = self.src.resolve(context, env.objectModel)
        r.params = variables.buildMap(self.params, context, env.objectModel)
        r.mimeType = self.mimeType
        context.processingPipeline.reader = r
        self.log.debug('<map:read src="%s"> invoke()' % r.src)
        return context.processingPipeline.process(env)
        
class SelectNode(ContainerNode):    
    def __init__(self):
        ContainerNode.__init__(self)
        self.log = logging.getLogger("sitemap.select")
        self.whenElements = None
        self.otherwiseNodes = None
        
    def build(self, element):
        Node.build(self, element)
        self._buildParams(element)
        
    def invoke(self, env, context):
        resolvedParams = variables.buildMap(self.params, context, env.objectModel)
        for test, nodes in self.whenElements:
            expr = test.resolve(context, env.objectModel)
            selector = env.componentManager.getComponent(self.elementName, self.type)
            self.log.debug("selector: %s" % selector)
            if selector.select(expr, env.objectModel, resolvedParams):
                return self.invokeChildren(env, context, None, nodes)
        if self.otherwiseNodes is not None:
            return self.invokeChildren(env, context, None, self.otherwiseNodes)
        else:
            return False

class ActNode(ContainerNode):
    def __init__(self):
        ContainerNode.__init__(self)
        self.log = logging.getLogger("sitemap.action")
    
    def build(self, element):
        Node.build(self, element)
        self._buildParams(element)

    def invoke(self, env, context):
        self.log.debug('<map:act type="%s">: invoke()' % self.type)
        resolvedParams = variables.buildMap(self.params, context, env.objectModel)
        action = env.componentManager.getComponent(self.elementName, self.type)
        result = action.act(env.objectModel, resolvedParams)
        if result is not None:
            return self.invokeChildren(env, context, result)
        else:
            return False

class RedirectNode(Node):
    def __init__(self):
        Node.__init__(self)
        self.log = logging.getLogger("sitemap.redirection")
        
    def build(self, element):
        Node.build(self, element)
        self.uri = variables.getResolver(element.get("uri"))
        self.permanent = (element.get("permanent", "no") == "yes")
        
    def invoke(self, env, context):
        env.response.headers.append(("location", self.uri.resolve(context, env.objectModel)))
        if self.permanent:
            env.response.status = 301
        else:
            env.response.status = 302
        return True
