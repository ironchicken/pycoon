"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module impelements the 'interpolation' mechanism which allows sitemap component
attributes to include a special syntax (denoted by {}) for parameterizing their values.
"""

import string, re, os, traceback
from StringIO import StringIO
from pycoon.helpers import strip_amps

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

    def _match(self, statement):
        """
        test the given statement against the object's pattern and return True if it matches or
        False if it doesn't.
        """

        self.statement = statement
        return self.pattern.match(statement) != None

    def __call__(self, statement, uri_pattern, context):
        """
        implements the 'action' of this interpolation syntax. Should a tuple: first member is result
        of self._match, second is either interpolated string or None.

        @statement: is the syntax to be interpolated
        @uri_pattern: the uri_pattern instance of the request that is being processed
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
    
    def __call__(self, statement, uri_pattern, context):
        if self._match(statement):
            try:
                return (True, uri_pattern.match_obj.group(int(statement.replace("$", ""))))
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

    def __call__(self, statement, uri_pattern, context):
        if self._match(statement):
            try:
                # first, split the instruction up on ':'s
                uri_comps = statement.split(":")

                # if its just 'uri'
                if statement == "uri":
                    # then return the whole uri
                    return (True, uri_pattern.uri)

                # if its 'uri:path'
                elif uri_comps[1] == "path":
                    # and if there's a numerical argument as well
                    if len(uri_comps) >= 3:
                        # then return the numbered part of the path
                        # (where 0 is the left-most part)
                        return (True, uri_pattern.parsed["path"][int(uri_comps[2])])
                    else:
                        # if there's no argument, then return the whole path
                        # but using OS sepcific separators so that it can be a local filename
                        return (True, uri_pattern.parsed["path"].join(os.sep))

                # if its 'uri:filename' then return the filename portion of the uri
                elif uri_comps[1] == "filename":
                    return (True, uri_pattern.parsed["filename"])

                # if its 'uri:query'
                elif uri_comps[1] == "query":
                    # and if there's a named query element:
                    if len(uri_comps) >= 3:
                        # then return the value of that query element
                        return (True, uri_pattern.parsed["query"][uri_comps[2]])
                    else:
                        # otherwise, format and return the whole query string
                        return (True, "?" + string.join([n + "=" + v for n, v in uri_pattern.parsed["query"]], "&"))

                # if its 'uri:fragment' then return the fragment portion of the uri
                elif uri_comps[1] == "fragment":
                    return (True, uri_pattern.parsed["fragment"])
            except IndexError:
                # do I need to catch these?
                return (False, None)
        else:
            return (False, None)
                
class interpolate_pipeline(interpolation_syntax):
    """
    interpolate_pipeline interprets the '{|name}' syntax, where 'name' is the name of a pipeline whose result
    is returned. A URI argument may be passed to the named pipeline using this syntax '{|name:uri}' (however,
    note that 'nested' interpolation is not supported).
    """
    
    def __init__(self):
        interpolation_syntax.__init__(self, "^|\w+:?.*$")

    def __call__(self, statement, uri_pattern, context):
        if self._match(statement):
            try:
                # split the instruction on :'s
                instruct_comps = statement.split(":")

                # extract the pipeline name
                pl_name = instruct_comps[0].strip("|")

                # and the given uri (if there is one)
                if len(instruct_comps) > 1:
                    # this is where nested interpolation is _not_ happening
                    # (you'd need to pass the parent uri_pattern(s) to this function...)
                    given_uri = instruct_comps[1]
                else: given_uri = ""

                result = StringIO()
                # force the named pipeline to execute, using a buffer for the result and uri from
                # the interpolation instruction (if there was one)
                context.pipelines[pl_name].force_execute(result, given_uri)

                result_string += result.getvalue()
                result.close()

                return (True, result_string)
            except (KeyError, AttributeError):
                # this means that the named pipeline does not exist. 
                return (False, None)
        else:
            return (False, None)

class interpolate_traceback(interpolation_syntax):
    """
    interpolate_traceback interprets the '{traceback}' syntax and returns the current traceback as a string.
    """
    
    def __init__(self):
        interpolation_syntax.__init__(self, "^traceback$")

    def __call__(self, statement, uri_pattern, context):
        if self._match(statement):
            try:
                exc = context.server.EXCEPTION
            except AttributeError:
                exc = context.EXCEPTION
                
            tb = strip_amps(string.join(traceback.format_exception(*exc)))
            return (True, tb.replace("'", "\""))
        else:
            return (False, None)

def interpolate(context, string_arg, uri_pattern, as_filename=False, root_path=""):
    """
    parses the string_arg argument using the given uri_pattern to interpolate the special {} delimited
    parts of string_arg with values from the uri_pattern. Returns a string.

    @context: a sitemap_config or server_config instance
    @string_arg: the attribute value to be processed (should contain {} delimited syntax)
    @uri_pattern: the uri_pattern object of the current request
    @as_filename: if True, the result will be an absolute path name. Optional
    @root_path: use to specify a path root other than the sitemap's document root. Optional
    """

    if as_filename:
        if root_path == "": root_path = context.document_root
        # if its supposed to be a filename, then start the return string with the given root_path
        return_string = root_path + os.sep
    else:
        # otherwise, just create an empty return string
        return_string = ""

    statement = ""   # this will contain the current interpolation instruction
    interpol_val = ""   # this will contain the current interpolated value
    in_interpol = False # True when the s's current position is between a { and a }

    # loop over each character in the string_arg and keep a counter pointer
    for i, c in zip(range(len(string_arg)), string_arg):
        # if the current character is a '{' and we're not already processing an interpolation
        if not in_interpol and c == "{":
            # start a new interpolation by setting statement to be empty and in_interpol to True
            statement = ""
            in_interpol = True

        # if we're currently processing an interpolation and the current character is not a { or a }
        elif in_interpol and c not in ['{', '}']:
            # then add it to the current interpolation instruction string
            statement += c

        # if we're currently processing an interpolation and the current character is a }
        elif in_interpol and c == "}":
            # then we've got to the end of the interpolation instruction string,
            # so interpolate it:

            # first retrieve the available interpolation syntax objects from the server_config
            if context.__class__.__name__ == "sitemap_config":
                i_syntaxes = context.server.interpolation_syntaxes.values()
            elif context.__class__.__name__ == "server_config":
                i_syntaxes = context.interpolation_syntaxes.values()

            # then iterate over them until one matches
            for i in i_syntaxes:
                (success, result) = i(statement, uri_pattern, context)
                if success:
                    return_string += result
                    break

            # we've now finished with this interpolation so set the flag to False
            in_interpol = False

        # if we're not processing an interpolation and the current character is not a { or a }
        elif not in_interpol and c not in ['{', '}']:
            # then just add it unaltered to the return string
            return_string += c

    # return the completed return string
    return return_string
