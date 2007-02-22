#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Both sitemap logic and pipeline components. The first ones (L{Generator}s,
L{Reader}s, L{Transformer}s and L{Serializer}s) do the actual data processing,
while the second ones (L{Matcher}s, L{Selector}s and L{Action}s) control the
sitemap tree walking. The sitemap tree walking itself is implemented in
L{pycoon.sitemap} package.

Components are associated with their XML elements in sitemap by a
L{TreeProcessor<pycoon.sitemap.treeprocessor.TreeProcessor>}.

See also:

 - U{http://cocoon.apache.org/2.1/userdocs/concepts/sitemap.html}
"""

__author__ = "Andrey Nordin <mailto:anrienord@inbox.ru>"

import logging

class Component:
    """The base class for all components."""
    def __init__(self):
        self.params = {}
        
    def configure(self, element=None):
        """Configures the component from C{element} XML infoset which is
        located in C{<map:components>}.
        
        @param element: XML infoset with the component parameters.
        """
        if element is not None:
            self.type = element.get("type")
            self.name = element.get("name")
            self.log = logging.getLogger(element.get("logger"))

class Serializer(Component):
    """A pipeline component associated with C{<map:serialize>}    
    that serializes a pipeline output from XML infoset to
    string.
    """
    def serialize(self, env, params):
        """Serializes an XML infoset.
        
        @param env: a pipeline execution
            L{Environment<pycoon.environment.Environment>}
        @param params: parameters specified in nested C{<map:parameter>}
            elements.
        """
        raise NotImplementedError()

class Selector(Component):
    """A logic component associated with C{<map:select>}
    that selects one of the sets of nested sitemap nodes.
    """
    def select(self, expr, objectModel, params):
        """Matches C{expr} against some objects from C{objectModel} and
        returns the result of matching.
        
        @param expr: an expression from C{test} attribute of the component's XML
            element.
        @param objectModel: a dictionary of objects defined in
            L{Environment<pycoon.environment.Environment>}.
        @param params: parameters specified in nested C{<map:parameter>}
            elements.
        @return: C{True} if C{expr} matches C{objectModel} in a particular way.
        """
        raise NotImplementedError()

class Generator(Component):
    """A pipeline component associated with C{<map:generate>}
    that generates an XML infoset from a source.
    """
    def generate(self, env, source, params):
        """Generates an XML infoset.
        
        @param env: a pipeline execution
            L{Environment<pycoon.environment.Environment>}
        @param source: a L{Source<pycoon.source.Source>} specified by C{src}
            attribute of the component's XML element.
        @param params: parameters specified in nested C{<map:parameter>}
            elements.
        """
        raise NotImplementedError()

class Transformer(Component):
    """A pipeline component associated with C{<map:transform>}
    that transforms an XML infoset into another one.
    """
    def transform(self, env, source, params):
        """Transforms an XML infoset.
        
        @param env: a pipeline execution
            L{Environment<pycoon.environment.Environment>}
        @param source: a L{Source<pycoon.source.Source>} specified by C{src}
            attribute of the component's XML element.
        @param params: parameters specified in nested C{<map:parameter>}
            elements.
        """
        raise NotImplementedError()

class Reader(Component):
    """A pipeline component associated with C{<map:read>}
    that reads the content of a source.
    """
    def read(self, env, source, params):
        """Reads a source.
        
        @param env: a pipeline execution
            L{Environment<pycoon.environment.Environment>}
        @param source: a L{Source<pycoon.source.Source>} specified by C{src}
            attribute of the component's XML element.
        @param params: parameters specified in nested C{<map:parameter>}
            elements.
        """
        raise NotImplementedError()

class Matcher(Component):
    """A logic component associated with C{<map:match>}
    that either selects nested sitemap nodes or doesn't select them.
    """
    def match(self, pattern, objectModel, params):
        """Matches C{expr} against some objects from C{objectModel} and
        returns the result of matching.
        
        @param expr: an expression from C{test} attribute of the component's XML
            element.
        @param objectModel: a dictionary of objects defined in
            L{Environment<pycoon.environment.Environment>}.
        @param params: parameters specified in nested C{<map:parameter>}
            elements.
        @return: C{dict} of substituted parameters in C{pattern} if C{expr}
            matches C{objectModel} in a particular way, otherwise C{None}.
        """
        raise NotImplementedError()

class Action(Component):
    """A logic component associated with C{<map:act>}
    that executes a particular action. It selects nested sitemap nodes if the
    action completed successfully, otherwise it doesn't.
    """
    def act(self, objectModel, params):
        """Executes a particular action such as sending email or authorizing a
        user.
        
        @param objectModel: a dictionary of objects defined in
            L{Environment<pycoon.environment.Environment>}.
        @param params: parameters specified in nested C{<map:parameter>}
            elements.
        @return: C{dict} with action status specified in the C{"status"} key.
        """
        raise NotImplementedError()
