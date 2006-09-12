"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

The helpers module contains some general functions which are used in various parts of
the Pycoon system.
"""

import re, string, datetime
from htmlentitydefs import entitydefs

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
        self.URI_SCHEME=0
        self.URI_HOSTINFO=1
        self.URI_USER=2
        self.URI_PASSWORD=3
        self.URI_HOSTNAME=4
        self.URI_PORT=5
        self.URI_PATH=6
        self.URI_QUERY=7
        self.URI_FRAGMENT=8
    def import_module(self, name):
        return __import__(name)
    def server_root(self):
        return ""

def uri_pattern2regex(pattern):
    """
    Converts the given URI pattern string into a Python regular expression object.
    """

    if pattern.startswith("/"):
        regex = "^" + pattern
    else:
        regex = "^/" + pattern
    
    escape_chars = [".", "(", ")", "[", "]", "{", "}", "?", "+"]
    for c in escape_chars:
        regex = regex.replace(c, "\\%s" % c)

    regex = regex.replace("/", "/+")

    regex = regex.replace("**", "([A-Za-z0-9_.+%-/]+)").replace("*", "([A-Za-z0-9_.+%-]+)")

    regex += "$"

    return re.compile(regex)

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

def attributes2options(attrs):
    """
    attributes2options turns the given xml.sax.Attributes into a dictionary. It is used to
    get initialisation options for generator and transformer components. It returns the value of
    the "type" attribute and a dictionary of the other attributes.
    """

    attrs_dict = {}
    for name, value in attrs.items():
        attrs_dict[str(name).replace("-", "_")] = str(value)

    if attrs_dict.has_key("type"):
        return (attrs_dict.pop("type"), attrs_dict)
    else:
        return (None, attrs_dict)
