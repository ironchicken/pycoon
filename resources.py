"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

This module contains the classes used to generalise access to external
resources as well as those used to implement the caching mechanism.
"""

import os, tempfile, cPickle

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
    
    def __init__(self, rtype, src, query="", custom_result=False, reload_policy="always"):
        """
        resource constructor.

        @rtype: the type of resource; ['file', 'db', 'exec']
        @src: the source for the resource; path name for 'file' and 'exec' types, for 'db' type
              must be triple (database module, method to acquire db cursor in terms of module,
              db query method in terms of cursor)
        @query: a query template needed to access the resource; e.g. SQL query. Optional
        @custom_result: if True, then resource's store() method must be called in order for
                        a result to be cached for this resource. If False, resource caches the
                        result from _load() automatically.
        @reload_policy: on what condition the resource should be reloaded;
                        ['always', 'modified', 'wait', 'repeated', 'never']
        """

        if rtype not in ['file', 'db', 'exec']:
            raise TypeError("resource.__init__ rtype parameter must be one of: 'file', 'db', 'exec'.")
        else:
            self.rtype = rtype
        
        if self.rtype == "db" and not isinstance(src, tuple):
            raise TypeError("'db' type resources require tuple src parameter: (db mod, get_cursor(mod), get_query(cursor)).")
        elif self.rtype == "db":
            self.src = {}
            self.src['mod'] = src[0]()
            # or should it get the module name instead?
            #self.src['mod'] = __import__(src[0])
            self.src['cursor'] = src[1](self.src['mod'])
            self.src['query'] = src[2](self.src['cursor'])
            # what if query func requires more than just a query string? (like dbxml requires a query context object)
        else:
            self.src = src
        
        self.query = query
        self.custom_result = custom_result

        if reload_policy not in ['always', 'modified', 'wait', 'repeated', 'never']:
            raise TypeError("resource.__init__ reload_policy parameter must be one of: 'always', 'modified', 'wait', 'repeated', 'never'.")
        self.reload_policy = reload_policy

    def _load(self, **params):
        """
        Execute the resource and return the result. Behaviour depends on type. 'file' types return
        a file object; 'db' objects return a cursor on which the query has been made; 'exec' types
        return a file-like object which is the result of executing the command.
        """

        if self.rtype == "file":
            return file(self.src % params, 'r')
        elif self.rtype == "db":
            return self.src['query'](self.query % params)
            # what if query func requires more than just a query string? (like dbxml requires a query context object)
        elif self.rtype == "exec":
            return os.popen(self.src % params)
            # we could allow for using self.query here as well, by giving it as stdin using popen2
        
    def store(self, result):
        """
        Uses tempfile to store (cache) the given result. result may be any Python object such as
        a character string or an lxml.etree.Element object, or it may be a file-like object.
        """

        try:
            (handle, self.cache_path) = tempfile.mkstemp(prefix="pycoon")
            if isinstance(result, file):
                handle.write(result.read())
                self.cache_class = "file"
            else:
                pickler = cPickle.Pickler(handle)
                pickler.dump(result)
                self.cache_class = "pickle"
        except PicklingError:
            self.cache_class = None
        
    def _retrieve(self, **params):
        """
        Retrieves the data for this resource from the cache. Returns False upon failure.
        """

        try:
            if self.cache_class == "file":
                return file(self.cache_path, 'r')
            elif self.cache_class == "pickle":
                unpickler = cPickle.Unpickler(file(self.cache_path, 'r'))
                return unpickle.load()
        except (AttributeError, IOError, OSError, UnpicklingError, EOFError, ImportError, IndexError):
            return False

    def __del__(self):
        """
        resource destructor. Attempt to remove any existing cache files.
        """

        try:
            os.remove(self.cache_path)
        except (AttributeError, OSError):
            pass
        
    def __call__(self, **params):
        """
        Determine whether to call self._load() or self._retrieve() on this resource to obtain data
        based on the caching policy. Returns data.
        """
