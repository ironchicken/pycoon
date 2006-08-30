"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The helpers module contains some general functions which are used in various parts of
the Pycoon system.
"""

import re, string, datetime
from htmlentitydefs import entitydefs
from pycoon.uri_pattern import uri_pattern

class fake_apache:
    """
    This class provides a pretend apache class for when the mod_python module is not available
    (i.e. command line testing).
    """
    def __init__(self):
        self.HTTP_INTERNAL_SERVER_ERROR = 500
        self.HTTP_NOT_FOUND = 404
        self.OK = 200
        self.DONE = 1000
        self.SERVER_RETURN = Exception
    def import_module(self, name):
        return __import__(name)
    def server_root(self):
        return ""

# this compiled regex is used by the strip_amps function
_strip_amps_regex = re.compile("&(?!(#[0-9]*|" + string.join(entitydefs.keys(), "|") + "))")

def strip_amps(s):
    """
    Replaces any ampersands which are not functioning as part of a character entity/reference in the given
    string with the ampersand character entity.
    """

    return _strip_amps_regex.sub("&amp;", s)

def correct_script_chars(s):
    """
    Replaces any ampersand, less-than and greater-than character entities in the given string with literal &, < and >
    characters.
    This function is a bit of a hack to make JavaScript code work properly.
    """
    
    script_start = s.find("<script")
    if script_start < 0: return s
    script_end = s.find("</script>")

    script_string = s[script_start:script_end]
    return s[:script_start] + script_string.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") + s[script_end:]

# this compiled regex is used by the unescape_url function
find_hex_codes = re.compile("(%[0-9A-Fa-f]{2})")

def repl_hex_with_char(m):
    """
    This is the replacement function for the regex used by unescape_url(). It converts hex numbers encoded
    in strings to characters.
    """

    return chr(string.atoi(m.group(0).replace("%",""), 16))

def unescape_url(s):
    """
    Converts %hex values in URL strings to literal characters.
    """

    return find_hex_codes.sub(repl_hex_with_char, s)

class log_buffer:
    """
    log_buffer class just implements a write method which writes to standard error
    with a date stamp and the server name.
    """

    def __init__(self, iostream, server_name):
        self.stream = iostream
        self.server_name = server_name
    
    def write(self, data):
        self.stream.write("[%s]: [\"%s\"] %s\n" % (str(datetime.datetime.today()), self.server_name, data))
        self.stream.flush()

# def create_pl_required_options(server, parent_sitemap, pipeline_type, attrs, order=0):
#     """
#     create_pl_required_options accepts an xml.sax.Attributes object and converts it into a
#     dictionary of only the _required_ parameters to construct a pipeline object. It is a
#     helper function for the sitemap and server _config_parse classes. It differs from
#     create_pl_extra_options in that it does not require a reference to a pipeline object.
#     """

#     pl_opts = {'name': str(attrs['name']), 'pipeline_type': pipeline_type}

#     if parent_sitemap != None:
#         pl_opts['parent'] = parent_sitemap
#     else:
#         pl_opts['parent'] = server

#     # add a uri_pattern object, if a pattern is specified
#     if attrs.has_key('uri-pattern'):
#         pl_opts['uri_pattern'] = uri_pattern(str(attrs['uri-pattern']))
#     else:
#         pl_opts['uri_pattern'] = uri_pattern("")

#     pl_opts['order'] = order

#     # add the "cache-as" value, if specified
#     if attrs.has_key('cache-as'): pl_opts['cache_as'] = str(attrs['cache-as'])

#     return pl_opts

# def create_pl_extra_options(server, parent_sitemap, pipeline, attrs):
#     """
#     create_pl_extra_options accepts a xml.sax.Attrbiutes object and converts it into a
#     dictionary of any non-required parameters available for pipeline objects. It is a
#     helper function for the sitemap and server _config_parse classes. It differs from
#     create_pl_required_options in that it accepts a reference to a pipeline object as a
#     parameter as so can construct any objects (such as serializers) which require a
#     reference to their parent pipeline.
#     """

#     pl_opts = {}
    
#     # add a serializer object, (using MIME type, or "text/html" if none is specified)
#     if attrs.has_key('mime'):
#         mime = str(attrs['mime'])
#     else:
#         # if no MIME type is specified, use "text/html"
#         mime = "text/html"

#     # try to load the approriate serializer class for the MIME type
#     if mime in server.serializers.keys():
#         pl_opts['mime'] = server.serializers[mime](pipeline)
#         if server.log_debug:
#             server.error_log.write("Added %s" % mime)
#     else:
#         # if there is no serializer, then just set mime as a string:
#         pl_opts['mime'] = mime

#     return pl_opts

def attributes2options(attrs):
    """
    attributes2options turns the given xml.sax.Attributes into a dictionary. It is used to
    get initialisation options for source and transformer components. It returns the value of
    the "type" attribute and a dictionary of the other attributes.
    """

    attrs_dict = {}
    for name, value in attrs.items():
        attrs_dict[str(name).replace("-", "_")] = str(value)

    if attrs_dict.has_key("type"):
        return (attrs_dict.pop("type"), attrs_dict)
    else:
        return (None, attrs_dict)
