import string, re

class uri_pattern(object):
    """uri_pattern class encapsulates a URI pattern string and provides methods to match given URIs
    to the pattern and parse URIs into dictionaries of their component parts."""
    def __init__(self, pattern):
        """uri_pattern constructor. Requires a uri pattern string as a parameter."""
        self.compile(pattern)

    def compile(self, pattern):
        """Translate the given uri pattern string into a regular expression string, compile it and store
        the result in self.pattern member."""
        regex_str = "^"

        # first, if the given pattern doesn't start with a '/' then begin regex with
        # match '/' 0 or 1 times:
        if len(pattern) == 0 or pattern[0] != "/":
            regex_str += "\/?"

        big_glob = False   # set to true when the '**' pattern is being processed
        c_lookahead = None # current_lookahead_assertion insertion position: after a big_glob, insert lookahead characters here
        escape = False     # set to treu when a '\' is used in the pattern (only preceding a '*')

        # the main bit:
        # loop over each character in the pattern and also over a counter so that 'i' is
        # is the position of the current character during the loop
        for i, c in zip(range(len(pattern)), list(pattern)):

            # if the current char is a '\' then set escape to be True
            if c == "\\": escape = True

            # if the current char is a '*' and escape is True then add '\*' to the regex
            elif c == "*" and escape is True:
                regex_str + "\\*"
                escape = False

            # if the current char is a '*' and it is followed by a non-* or the end of the pattern
            # then add a 'match word' to the regex
            elif c == "*" and (i == len(pattern)-1 or pattern[i + 1] != "*") and (i == 0 or pattern[i - 1] != "*"):
                regex_str += "([a-zA-Z0-9_\-\.]+)"

            # if the current char is a '*' and it is followed by another '*' then it is a 'big_glob'
            elif c == "*" and (i == len(pattern)-1 or pattern[i + 1] == "*") and (i == 0 or pattern[i - 1] != "*"):
                big_glob = True
                # if the big_glob is at the end of the pattern then add a 'match everything'
                # to the regex
                if (i == len(pattern)-1) or (pattern[i + 1] == "*" and i+1 == len(pattern)-1):
                    regex_str += "(.*)"
                # if there is more pattern after the big_glob then insert a 'match everything'
                # followed by a 'lookahead assertion' and store the position of the assertion
                else:
                    regex_str += "(.*)(?="
                    c_lookahead = len(regex_str)
                    regex_str += ")"

            # if the current char is a '*' and it is preceded by another '*' then ignore
            # it because it is a big_glob and is being handled anyway.
            # (this may not be correct...)
            elif c == "*" and (i == 0 or pattern[i - 1] == "*"): pass

            # if the current character is one of the specials:
            elif c in ['.', '(', ')', '{', '}', '+', '?', '|', '^', '$', '&', '#', '=', '-', '~']:
                # and if a big_glob is currently being processed:
                if big_glob:
                    # then insert an escaped version of the current char into the lookahead
                    # assertion for the big_glob and advance the lookahead assertion insertion
                    # position by 2 (one for the '\' and one for the char)
                    regex_str = regex_str[:c_lookahead] + "\\" + c + regex_str[c_lookahead:]
                    c_lookahead += 2

                # add an escaped version of the character to the end of the pattern
                # (does this whether we're processing a big_glob or not)
                regex_str += "\\" + c

            # if the character is a '/' then allow it to match adjecent ones as well
            elif c == "/":
                if big_glob:
                    regex_str = regex_str[:c_lookahead] + "\\/+" + regex_str[c_lookahead:]
                    c_lookahead += 3

                regex_str += "\\/+"

            # if the current char is just an ordinary alpha-numeric character:
            elif c in string.letters + string.digits:
                # and if a big_glob is currently being processed:
                if big_glob:
                    # then insert the current char into the lookahead assertion for the
                    # big_glob and advance the lookahead assertion insertion position by 1
                    regex_str = regex_str[:c_lookahead] + c + regex_str[c_lookahead:]
                    c_lookahead += 1

                # add the character to the end of the pattern
                # (does this whether we're processing a big_glob or not)
                regex_str += c

        # ignore trailing slashes
        # append an 'end of line' to the regex
        regex_str += "\\/*$"

        # compile and save it. phew!
        self.pattern = re.compile(regex_str)

    def parse(self, uri):
        """Parses the given uri string into a dictionary stored in self.parsed containing
        the following elements:
        'path': a list of parts of the path portion of the uri in order from left to right;
        'filename': the last portion of the uri;
        (note when using 'path' and 'filename': trailing slashes are always removed)
        'query': a dictionary of the query parameters;
        'fragment': the fragment portion of the uri"""
        
        self.uri = uri
        self.parsed = {'path': [], 'filename': "", 'query': {}, 'fragment': ""}

        # remove trailing slashes
        uri = re.sub("\/+$", "", uri)
        
        # split the uri on '/'s
        path_parts = uri.split("/")

        # add all the non-empty path parts except the last one to the "path" list
        # NOTE: the last part will be stored in filename even if its not intended
        # to represent a file by the uri designer
        for p in path_parts[:-1]:
            if p != "": self.parsed['path'].append(p)

        # the part of the uri following the last '/'
        last_part = path_parts[-1:][0]

        # find the position of the '?' and '#' to determine the positions
        # of the query string and fragment if present
        query_pos = last_part.find("?")
        frag_pos = last_part.find("#")
        query_str = None

        # extract the filename, query string and fragment:
        if query_pos >= 0 and frag_pos >= 0:
            self.parsed['filename'] = last_part[0:query_pos]
            query_str = last_part[query_pos+1:frag_pos-1]
            self.parsed['fragment'] = last_part[frag_pos+1:]
        elif query_pos >= 0 and frag_pos == -1:
            self.parsed['filename'] = last_part[0:query_pos]
            query_str = last_part[query_pos+1:]
        elif query_pos == -1 and frag_pos >= 0:
            self.parsed['filename'] = last_part[0:frag_pos]
            self.parsed['fragment'] = last_part[frag_pos+1:]
        else:
            self.parsed['filename'] = last_part

        if query_str is not None:
            for q in query_str.split("&"):
                if q.find("=") >= 0:
                    (name, value) = q.split("=")
                else:
                    name = q
                    value = ""
                self.parsed['query'][name] = value
        
    def match(self, uri):
        """Tests the uri_pattern object's pattern regex property against the given uri string. If it
        matches, it stores the match object in self.match_obj, stores a parsed version of the uri
        (using the self.parse() method) in self.parsed and returns the match object. Otherwise it returns
        None."""
        self.uri = uri
        m = self.pattern.match(uri)
        if m:
            self.parse(uri)
            self.match_obj = m
            return m
        else: return None
    
    def __call__(self, uri):
        """Calls self.match(uri) and returns the result. Implementing __call__ means that a uri_pattern
        object can be invoked to test a uri as if it were a function."""
        return self.match(uri)
