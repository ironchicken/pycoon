"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module impelements the 'interpolation' mechanism which allows sitemap component
attributes to include a special syntax (denoted by {}) for parameterizing their values.
"""

import string, re, os, traceback
from StringIO import StringIO
from pycoon import apache
from pycoon.helpers import strip_amps

class InterpolationException(Exception): pass

class interpolation_syntax(object):
    """
    interpolation_syntax encapsulates the syntax of an element of valid syntax for use
    in the interpolate function.
    """

    def __init__(self, pattern, component=None):
        """
        interpolation_syntax constructor.

        @pattern: a regular expression string
        @component: a sitemap component from which this interpolation_syntax may draw information
                    upon execution.
        """
        
        self.pattern = re.compile(pattern)
        self.component = component

    def _match(self, instruction):
        """
        test the given instruction against the object's pattern and return True if it matches or
        False if it doesn't.
        """

        self.instruction = instruction
        self.match_obj = self.pattern.match(instruction)
        return self.match_obj != None

    def __call__(self, instruction, uri_matcher, context):
        """
        implements the 'action' of this interpolation syntax. Should return a tuple: first member
        is result of self._match, second is either interpolated string or None.

        @instruction: is the syntax to be interpolated
        @uri_matcher: a uri_matcher instance for the request that is being processed
        @context: a sitemap_config or server_config instance
        """

        raise NotImplemented()

def register_interpolation_syntax(server, syntax, name):
    """
    Used to add an interpolation_syntax object to the server's interpolation_syntax
    dictionary.

    @server: the server_config instance
    @syntax: the interpolation_syntax instance
    @name: a unique name for the interpolation syntax
    """
    
    if name not in server.interpolation_syntaxes.keys():
        server.interpolation_syntaxes[name] = syntax

# define the basic interpolation syntax elements:
class interpolate_pattern_match_number(interpolation_syntax):
    """
    interpolate_pattern_match_number interprets the '{$n}' syntax, where the number
    'n' is the n'th '*' denoted portion of the URI.
    """
    
    def __init__(self):
        interpolation_syntax.__init__(self, "^\$[0-9]+$")
    
    def __call__(self, instruction, uri_matcher, context):
        if self._match(instruction):
            try:
                return (True, uri_matcher.match_obj.group(int(instruction.replace("$", ""))))
            except IndexError:
                return (False, None)
        else:
            return (False, None)

class interpolate_uri(interpolation_syntax):
    """
    interpolate_uri interprets the '{uri:...}' syntax. This syntax has the following possible forms:

    {uri} : returns the whole URI
    {uri:filename} : returns the filename portion of the URI
    {uri:path} : returns the whole path portion of the URI
    {uri:path:n} : returns the n'th part of the path portion of the URI (where 0 is the leftmost part)
    {uri:query} : returns the whole query string
    {uri:query:name} : returns the value of the query string parameter named 'name'
    {uri:fragment} : returns the fragment portion of the URI
    """
    
    def __init__(self):
        interpolation_syntax.__init__(self, "^uri:?.*$")

    def __call__(self, instruction, uri_matcher, context):
        if self._match(instruction):
            try:
                # first, split the instruction up on ':'s
                uri_comps = instruction.split(":")

                # if its just 'uri'
                if instruction == "uri":
                    # then return the whole uri
                    return (True, uri_matcher.uri)

                # if its 'uri:path'
                elif uri_comps[1] == "path":
                    # and if there's a numerical argument as well
                    if len(uri_comps) >= 3:
                        # then return the numbered part of the path
                        # (where 0 is the left-most part)
                        return (True, string.split(uri_matcher.path, "/")[int(uri_comps[2])])
                    else:
                        # if there's no argument, then return the whole path
                        # but using OS sepcific separators so that it can be a local filename
                        return (True, uri_matcher.path)

                # if its 'uri:filename' then return the filename portion of the uri
                elif uri_comps[1] == "filename":
                    return (True, uri_matcher.filename)

                # if its 'uri:query'
                elif uri_comps[1] == "query":
                    # and if there's a named query element:
                    if len(uri_comps) >= 3:
                        # then return the value of that query element
                        return (True, uri_matcher.query_dict[uri_comps[2]])
                    else:
                        # otherwise, format and return the whole query string
                        return (True, "?" + uri_matcher.query)

                # if its 'uri:fragment' then return the fragment portion of the uri
                elif uri_comps[1] == "fragment":
                    return (True, uri_matcher.fragment)
            except IndexError:
                # do I need to catch these?
                return (False, None)
        else:
            return (False, None)
                
class interpolate_context(interpolation_syntax):
    """
    interpolate_context interprets the '{context:...}' syntax, where '...' should be a URI which will be
    handled by the sitemap and its result will be returned. (However, note that 'nested' interpolation
    is not supported.)
    """
    
    def __init__(self):
        interpolation_syntax.__init__(self, "^context:.+$")

    def __call__(self, instruction, uri_matcher, context):
        if self._match(instruction):
            try:
                # split the instruction on :'s
                instruct_comps = instruction.split(":")

                # and get given uri
                if len(instruct_comps) > 1:
                    # this is where nested interpolation is _not_ happening
                    given_uri = instruct_comps[1]
                else:
                    raise InterpolationException("context: instruction requires a URI")

                result = StringIO()
                # force the named pipeline to execute, using a buffer for the result and uri from
                # the interpolation instruction (if there was one)
                context.pipelines.force_execute(result, given_uri)

                result_string += result.getvalue()
                result.close()

                return (True, result_string)
            except (KeyError, AttributeError):
                return (False, None)
        else:
            return (False, None)

class interpolate_traceback(interpolation_syntax):
    """
    interpolate_traceback interprets the '{traceback}' syntax and returns the current traceback as a string.
    """
    
    def __init__(self):
        interpolation_syntax.__init__(self, "^traceback$")

    def __call__(self, instruction, uri_matcher, context):
        if self._match(instruction):
            try:
                exc = context.server.EXCEPTION
            except AttributeError:
                exc = context.EXCEPTION
                
            tb = strip_amps(string.join(traceback.format_exception(*exc)))
            return (True, tb.replace("'", "\""))
        else:
            return (False, None)

# this regex is used to extract the interpolation instructions from a string
_find_instructions = re.compile("\{[^}]+\}")

def interpolate(component, string_arg, as_filename=False, root_path=""):
    """
    parses the string_arg argument using the current request uri to interpolate the special {} delimited
    parts of string_arg with values from the uri. Returns a string.

    @component: the component which has called this function
    @string_arg: the attribute value to be processed (should contain {} delimited syntax)
    @as_filename: if True, the result will be an absolute path name. Optional
    @root_path: use to specify a path root other than the sitemap's document root. Optional
    """

    # first attempt to find an active uri_matcher instance in the pipeline hierarchy
    uri_matcher = None
    p = component.parent
    while p is not None:
        if p.__class__.__name__ in ["uri_matcher", "error_matcher"]:
            uri_matcher = p
            break
        try:
            p = p.parent
        except AttributeError:
            p = None
            break
    if uri_matcher is None:
        raise InterpolationException("interpolate called by component, \"%s\", with no uri_matcher or error_matcher instance in pipeline"
                                     % component.description)
        
    if as_filename:
        if root_path == "": root_path = component.context.document_root
        # if its supposed to be a filename, then start the return string with the given root_path
        return_string = root_path + os.sep
    else:
        # otherwise, just create an empty return string
        return_string = ""

    # retrieve the available interpolation syntax objects from the server_config
    if component.context.__class__.__name__ == "sitemap_config":
        i_syntaxes = component.context.server.interpolation_syntaxes.values()
    elif component.context.__class__.__name__ == "server_config":
        i_syntaxes = component.context.interpolation_syntaxes.values()

    # first insert the characters up to the first interpolation instruction (could be the whole string):

    last_pos = string_arg.find("{")

    if last_pos == -1:
        # in this case there are no interpolation instructions in the string so just use all of string_arg
        return_string += string_arg

    else:
        # in this case there are some interpolation instructions

        start_pos = 0
        
        # iterate over the interpolation instructions in the string_arg
        for instruction in _find_instructions.finditer(string_arg):
            last_pos = instruction.start()# - 1
            if last_pos < 0: last_pos = 0

            # first, add the characters between the previous instruction and this one to the return_string
            return_string += string_arg[start_pos:last_pos]

            # then iterate over the interpolation syntax objects until one matches
            for i in i_syntaxes:
                (success, result) = i(instruction.group()[1:-1], uri_matcher, component.context)

                if success:
                    return_string += result
                    break

            start_pos = instruction.end()

        return_string += string_arg[start_pos:]

    # return the completed return string
    return return_string
