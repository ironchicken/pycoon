"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module contains top level classes and helper functions for working with components
used in the Pycoon system.
"""

import os
from pycoon.interpolation import interpolate

COMPONENT_TYPES = {"stream": {"generator": {"module": "pycoon.generators", "super_class": "generator"},\
                              "transformer": {"module": "pycoon.transformers", "super_class": "transformer"},\
                              "serializer": {"module": "pycoon.serializers", "super_class": "serializer"}},\
                   "syntax": {"selector": {"module": "pycoon.selectors", "super_class": "selector"},\
                              "authenticator": {"module": "pycoon.authenticators", "super_class": "authenticator"}}}
                            
                   
def register_component(server, super_type, attrs):
    """
    Reads a component described by the content of the given XML element attributes object and
    stores it in the given server.components.
    """

    name = str(attrs['name'])
    
    if server.components.has_key(name):
        # registered component names must be unique within their type
        raise SAXException("Attempted to add %s component with non-unique name: \"%s\"" % (super_type, name))

    # attempt to import the specified container module
    mod = __import__(str(attrs['module']).replace(".", os.sep))

    # add the component class from the module to the given dictionary
    comp = mod.__dict__[str(attrs['class'])]

    if comp.function == name:
        server.components[(name, None)] = comp
    else:
        server.components[(comp.function, name)] = comp


    # add the module's init_datasource_*() function(s) (if it has any) to the server_config object's ds_initialisers dictionary
    for func_name in mod.__dict__:
        if func_name.find("init_datasource") >= 0:
            if attrs.has_key("backend"):
                ds_init_name = str(attrs['backend'])
                if func_name.find(ds_init_name) < 0: return
            else:
                ds_init_name = name
        
            server.ds_initialisers[ds_init_name] = mod.__dict__[func_name]


    # call the component module's register_invokation_syntax function
    if mod.__dict__.has_key("register_invokation_syntax"):
        invk_syn = mod.register_invokation_syntax(server)

        if invk_syn.element_name not in server.component_enames:
            server.component_enames.append(invk_syn.element_name)

    if server.log_debug:
        server.error_log.write("Added %s component: \"%s\" from %s.%s." %\
                               (super_type, name, str(attrs['module']), str(attrs['class'])))

class invokation_syntax(object):
    """
    Used to encapsulate details of the valid XML element syntax for including a component
    in a pipeline file.
    """

    def __init__(self):
        self.element_name = ""
        self.allowed_parent_components = []
        self.required_attribs = []
        self.required_attrib_values = {}
        self.optional_attribs = []
        self.allowed_child_components = []

    def validate(self, parent_name, name, attrs):
        """
        Check if the given element name/xml.sax.Attributes combination describes a valid component
        of the type encapsulated in this invokation_syntax instance.
        """

        return name == self.element_name and \
               parent_name in self.allowed_parent_components and \
               reduce(lambda a, b: a and b, [attrib in attrs.keys() for attrib in self.required_attribs], True) and \
               reduce(lambda a, b: a and b, [attrs[n] == v for n, v in self.required_attrib_values.items()], True)
           
        #raise SAXException("%s may not have child components of the type: \"%s\"" % (self.curr_component.type, component_type))
        #raise SAXException("Unknown %s type: \"%s\"" % (super_type, component_type))
        #raise SAXException("Invalid component syntax for \"%s\"" % name)

class component(object):
    """
    Super class for all component classes.

    @parent: the parent component of this component.
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default.
    """

    # role class property is: [stream|syntax]; corresponds to stream_component and syntax_component
    role = "none"

    # function class property is: [generate|transform|serialize|select|...];
    # corresponds to classes immediately derived from stream_component and syntax_component
    # and to component's invokation element name
    function = "none"
        
    def __init__(self, parent, root_path=""):
        self.parent = parent

        # create aliases for the parent pipeline, sitemap and server
        self.pipeline = None
        self.sitemap = None
        self.server = None
        
        p = self.parent
        while p is not None:
            if p.__class__.__name__ == "pipeline":
                self.pipeline = p
            elif p.__class__.__name__ == "sitemap_config":
                self.sitemap = p
            elif p.__class__.__name__ == "server_config":
                self.server = p
            try:
                p = p.parent
            except AttributeError:
                p = None
                break

        # create an additional alias called 'context' which is either the parent sitemap or,
        # if there is no sitemap, the parent server
        if self.sitemap is not None:
            self.context = self.sitemap
        elif self.server is not None:
            self.context = self.server

        # set the root_path property
        if root_path == "":
            if self.sitemap is not None:
                self.root_path = self.sitemap.document_root
            elif self.server is not None:
                self.root_path = self.server.document_root
        else:
            self.root_path = root_path

        # a list of child components
        self.children = []
        
        self.description = "Component base class"

    def __call__(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Calling a component causes it to activate its function by calling its _descend and _result methods.
        Depending on the return value of its _descend method, it also attempts to call its child components.

        __call__ returns a tuple whose first member is a flag indicating whether execution was 'successful'
        and whose second is the 'result'.

        @req: is the current apache request object
        @uri_pattern: is the current request uri_pattern object
        @p_sibling_result: is the result of the pipeline so far (i.e. up to the previous sibling
        component) (optional)
        @child_result: is the result of the child pipelines of this component (optional)
        """

        if self.server.log_debug:
            self.server.error_log.write("%s called with previous sibling: %s; child results: %s" % (self.description, p_sibling_result, child_results))
        
        c_tree = []
        if self._descend(req, uri_pattern, p_sibling_result):
            for comp in self.children:
                if len(c_tree) > 0:
                    (success, result) = comp(req, uri_pattern, c_tree[-1])
                else:
                    (success, result) = comp(req, uri_pattern, None)
                
                if success:
                    c_tree.append(result)
                else:
                    return (False, result)

        return self._result(req, uri_pattern, p_sibling_result, c_tree)

    def _descend(self, req, uri_pattern, p_sibling_result=None):
        """
        Given the current execution context, allows the component to determine whether or not it will
        allow its child components to be executed. Returns True if child components are to be executed,
        or False otherwise. Allows for pre-execution handling of component (e.g. for authentication
        components to collect user data).
        """

        return True

    def _result(self, req, uri_pattern, p_sibling_result=None, child_results=[]):
        """
        Given the current execution context, the component should carry out its main function and
        return a tuple whose first member is a 'successful' flag and whose second member is its
        result (e.g. an ElementTree for stream components).
        """

        raise NotImplemented()
    
    def add_component(self, c, pos=None):
        if c is None:
            raise TypeError("component argument to add_component was None: %s" % str(c))
        
        if pos is None:
            self.children.append(c)
        else:
            self.children.insert(pos, c)
        return c

class stream_component(component):
    """
    Super class for all components which handle XML data in pipelines (e.g. generators,
    transformers and serializers)

    @parent: the parent component of this component.
    @root_path: the base path this component should prepend to any paths it uses when accessing files.
                Optional argument. Uses current sitemap (or server) document_root by default.
    """

    role = "stream"
    function = "none"

    def __init__(self, parent, root_path=""):
        component.__init__(self, parent, root_path)
        self.description = "Streamed component base class"

    def _tap(self):
        """
        Returns a stream of the current state of the pipeline of which this component is a member after
        applying this component's action.
        """

        pass
    
    def reload_source(self):
        pass
    
    def cache(self):
        pass

class syntax_component(component):
    """
    Super class for all components which provide syntax elements in pipelines (e.g.
    selectors, authenticators)

    @parent: the parent component of this component.
    @root_path: the base path this component should prepend to any paths it uses when accessing files. Optional
                argument. Uses current sitemap (or server) document_root by default.
    """

    role = "syntax"
    function = "none"
    
    def __init__(self, parent, root_path=""):
        component.__init__(self, parent, root_path)
        self.description = "Syntax component base class"
