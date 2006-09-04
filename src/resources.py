"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module contains the classes used to generalise access to external
resources as well as those used to implement the caching mechanism.
"""

import os, stat, tempfile, cPickle

# the is_modified_* functions can be used as 'is_modified_func' properties for resource objects.
def is_modified_file_changed(req, parsed_src):
    """
    This function can be used as the 'is_modified_func' property for a resource object.
    It determines whether or not the modified state is true by ascertaining if the file
    has changed since the last request.

    @req: an Apache request object
    @parsed_src: path of the file
    """

    try:
        src_modified = os.stat(parsed_src)[stat.ST_MTIME]
        print "is_modified_file_changed: parsed_src=\"%s\"; src_modified=%s; request_time=%s; returning=%s" % (parsed_src, src_modified, req.request_time, src_modified > req.request_time)
        return src_modified > req.request_time
    except OSError:
        return True

def is_modified_dbxml_changed(req, parsed_src):
    """
    [works identically to is_modified_file_changed]
    
    @req: an Apache request object
    @parsed_src: path of the dbxml file
    """

    try:
        src_modified = os.stat(parsed_src)[stat.ST_MTIME]
        return src_modified > req.request_time
    except OSError:
        return True

def is_modified_pipeline_changed(req, pl):
    """
    Attempts to establish whether any of the resources on which components of the given
    pipeline rely have changed. Returns True if any have, otherwise (if /all/ are
    unaltered) returns False.

    @req: an Apache request object
    @pl: a pipeline object    
    """

    def descend(comp):
        for c in comp.children:
            if c.resource.requires_reload(req):
                return True
            if len(c.children) > 0:
                descend(c)
        return False

    return descend(pl)

def hash_cache_fn(fn):
    """
    Converts the given string, fn, into a representation to be used as a file name for
    the cache file.
    """

    return "pycoon_%s" % fn.replace(os.sep, "_")

def dehash_cache_fn(hash_fn):
    """
    Reverse process of hash_cache_fn function.
    """

    # this probably won't work
    return hash_fn.replace("pycoon_", "").replace("_", os.sep)

class resource(object):
    """
    resource encapsulates an external resource. It provides mechanisms to obtain data
    from that resource (allowing parameterized invokation for resources such as
    database queries) and to make the resource reload itself.

    ?It is used as a mix-in class for stream_components.
     if it is, will it have better access to component's 'result' object for caching?
     how will its construction be handled?
     hmm, if its a db source, its holding too much information to have one per every
     stream_component instance, probably. Perhaps use these more like how we currently
     use sitemap.ds_mods?
    """
    
    def __init__(self, component, reload_policy="always", **kwargs):
        """
        resource constructor.

        @component: the component object which uses this resource object
        @reload_policy: on what condition the resource should be reloaded;
                        ['always', 'modified', 'wait', 'repeated', 'never']
        kwargs: additional arguments needed depending on reload_policy:
        @reload_parameter: value depends on reload_policy:
          'modified': requires a function providing a method to assess whether or not
                      a source has been modified and the method for retrieving the path
                      of the resource to check for modification
          'wait': amount of time, in milliseconds, which must have passed before reloading
          'repeated': the number of repeated requests that must be made before reloading
        """

        self.component = component
        # can server error handling pipelines use resource objects?
        self.sitemap = self.component.sitemap
        
        if reload_policy in ['always', 'modified', 'wait', 'repeated', 'never']:
            self.reload_policy = reload_policy
        else:
            raise TypeError("reload_policy argument must be one of ['always', 'modified', 'wait', 'repeated', 'never']")

        if self.reload_policy == "wait":
            if kwargs.has_key['interval']:
                self.interval = long(kwargs['interval'])
            else:
                raise TypeError("reload_policy 'wait' requires 'interval' argument")

        elif self.reload_policy == "repeated":
            if kwargs.has_key['times']:
                self.times = long(kwargs['times'])
            else:
                raise TypeError("reload_policy 'repeated' requires 'times' argument")

    def store(self, req, result, cache_as=""):
        """
        Uses tempfile to store (cache) the given result. result may be any Python object such as
        a character string or an lxml.etree.Element object, or it may be a file-like object.

        @req: the Apache request object
        @result: the result data to be stored
        @cache_as: used as part of the file name for caching this result. The parent component's
                   cache_as property is used in preference, however.
        """

        try:
            if self.component.cache_as != "":
                cache_as = self.component.cache_as
            
            (handle, cache_path) = tempfile.mkstemp(prefix=hash_cache_fn(cache_as))
            tfile = os.fdopen(handle, 'w')

            if isinstance(result, file):
                tfile.write(result.read())
                cache_class = "file"
            else:
                cPickle.dump(result, tfile)
                cache_class = "pickle"

            tfile.close()
            os.close(handle)
            
            self.sitemap.cache[cache_as] = (cache_path, cache_class)

            if self.sitemap.server.log_errors:
                self.sitemap.server.error_log.write("Component: \"%s\" cached in \"%s\"" %\
                                                    (self.component.description, cache_path))

        except (cPickle.PicklingError, TypeError, OSError):
            self.cache_class = None
            os.remove(cache_path)
        
    def _retrieve(self, cache_as=""):
        """
        Retrieves the data for this resource from the cache. Returns False upon failure.

        @cache_as: used as part of the file name for caching this result. The parent component's
                   cache_as property is used in preference, however.
        """

        try:
            if self.component.cache_as != "":
                cache_as = self.component.cache_as

            (cache_path, cache_class) = self.sitemap.cache[cache_as]

            if cache_class == "file":
                return file(cache_path, 'r')
            elif cache_class == "pickle":
                return cPickle.load(file(cache_path, 'r'))

            if self.sitemap.server.log_errors:
                self.sitemap.server.error_log.write("Component: \"%s\" retrieve from cache in \"%s\"" %\
                                                    (self.component.description, cache_path))

        except cPickle.UnpicklingError:#AttributeError, IndexError, IOError, OSError, EOFError, ImportError
            return False

    def requires_reload(self, req, uri_pattern):
        """
        Examines the reload policy against the given request. If the resource needs to be reloaded returns True.
        """

        if self.reload_policy == "always":
            # returns True so that caller is forced to reload
            # (this is actually pretty redundant, because a component's _result method could just not
            # use caching at all to achieve the same result.)
            return True
        
        elif self.reload_policy == "modified":
            # returns result of self.is_modified_func
            return self.component.is_modified(req, uri_pattern)

        elif self.reload_policy == "wait":
            # loops over the sitemap's previously handled requests and, for each one, compares its time
            # stamp to now. If there is an identical request to this and the difference between their
            # time stamps is less than the self.interval, return False.
            now = time.time()
            for t, uri in self.sitemap.prev_requests:
                if uri == req.unparsed_uri and now - t >= self.interval:
                    return False
            return True

        elif self.reload_policy == "repeated":
            # loops over the previous requests incrementing a counter for each contiguous identical request.
            # If there are self.times contigous identical requests, then return True
            count = 0
            for t, uri in self.sitemap.prev_requests:
                if uri != req.unparsed_uri:
                    return True
                else:
                    count += 1
                    if count == self.times:
                        return False
            return True

        elif self.reload_policy == "never":
            # always return the cached result. Returns False
            return False

    def __call__(self, req, uri_pattern, **kwargs):
        """
        If the resource needs to be reloaded (determined using the requires_reload method) attempts to
        retrieve and return the cached result. Returns two values: first is a flag indicating whether or
        not the result has been retrieved from the cache, and the second is the result (or None).
        
        @req: the Apache request object
        kwargs: any additional arguments required by the is_modified function
        """

        if self.requires_reload(req, uri_pattern):
            res = self._retrieve(kwargs['src'])
            if not res:
                return (False, None)
            else:
                return (True, res)
        else:
            return (False, None)
