"""
Copyright (C) Richard Lewis 2006

This software is licensed under the terms of the GNU GPL.

Pycoon is an Apache module which allows you to match URI pattern's from HTTP requests
to 'pipelines' of XML processing.

Pipelines consist of a 'source' element which generates the initial XML ElementTree. Provided
sources include: ordinary XML documents, XPath expressions against documents, XQuery
expressions against Berkeley DB XML containers and SQL databases.

After the source, pipelines may contain any number of 'transformers' which alter the
XML ElementTree. Provided transformers include: XSLT transformer, SAX handler transformer
and a shell command transformer.

Finally, the XML stream is 'serialized' according to the pipeline's serialize component.
Provided serializers include 'xhtml' and 'html' which use uTidyLib to convert the XML
ElementTree into an (X)HTML document before writing it back to the client and 'svg' uses
RSVG to perform an SVG rasterisation of the XML ElementTree to a PNG image.

Pycoon is configured using a 'sitemap' document (which has a simple XML syntax) and
should be assigned as the handler for an Apache VirtualHost directive.

It supports logging events of various levels (start-up/shutdown, errors, requests, debug)
to Apache's log files.

It also supports caching of processed requests and resource files such as CSS or images.

This module provides the Apache handler() and cleanup() functions, global variables for
the server and site settings.
"""

from helpers import fake_apache, log_buffer

try:
    from mod_python import apache
except ImportError:
    # if we're not running inside Apache (i.e. command line testing)
    # create a fake apache module
    apache = fake_apache()

from server import server_config, server_config_parse
from interpolation import interpolate
from sitemap import sitemap_config, sitemap_config_parse
import sys

server = server_config()
sitemap = sitemap_config(server)

def cleanup(req):
    """
    This method is called when the server shuts down. It tried to free all the open resources like
    database connections, files, etc.
    """
    # need to replace this with a connection pool mechanism

    if server.log_up_down: server.error_log.write("cleanup(req) called.")
    
    # iterate over all the open datasources
    for name, ds in sitemap.data_sources.items():
        # iterate over some possible destruction names
        for methodname in ["close", "disconnect", "quit"]:
            # try and retrieve a method named methodname from the datasource
            method = getattr(ds, methodname, None)
            if method:
                try:
                    # if its callable, call it
                    method()
                    if server.log_up_down:
                        server.error_log.write("Data source \"%s\" has been closed with %s() method." % (name, methodname))

                    # and stop trying method names
                    break
                except TypeError:
                    # if it wasn't callable, then try the next one
                    pass
        # delete the datasource
        del sitemap.data_sources[name]


    # set sitemap to None now that the handler module has been un-configured
    # (it is used as a 'module configured' flag)
    #sitemap = None
    
def handler(req):
    """
    This is the method which mod_python calls when it receives a request. The 'req' parameter is
    filled with an Apache request object.
    """

    if sitemap.document_root == "":
        # this is the first time a request has been made for this instance of the interpreter
        # so get the name of the sitemap.xml file from the Apache configuration file, the main
        # server configuration file and load them both
        req.server.register_cleanup(req, cleanup) # also register the cleanup function
        req.add_common_vars()
        env_dict = req.subprocess_env

        # if the handler is running in a VirtualHost, then fetch the *actual* SERVER_NAME and DOCUMENT_ROOT values
        if not env_dict.has_key('ServerName') and not env_dict.has_key('DocumentRoot'):
            use_server_name = req.server.server_hostname
            use_document_root = req.document_root()
        # otherwise, they need to have been set using SetEnv
        else:
            use_server_name = env_dict['ServerName']
            use_document_root = env_dict['DocumentRoot']
            
        # create the log streams
        server.access_log = log_buffer(sys.stderr, use_server_name) # what stream should this write to?
        server.error_log = log_buffer(sys.stderr, use_server_name)

        # if we're not running inside Apache
        # add the DOCUMENT_ROOT to the Python path
        if apache.__class__.__name__ == "fake_apache":
            sys.path.append(use_document_root)
        # (otherwise this is done with the mod_python PythonPath directive)

        server_config_parse("file://%s/%s" % ("/etc/pycoon", "server.xml"), server)
        if server.log_up_down:
            server.error_log.write("Successfully loaded server configuration, \"%s\", for \"%s\"" %\
                                   ("server.xml", use_server_name))
        
        sitemap.server_name = use_server_name
        sitemap_config_parse("file://%s/%s" % (use_document_root, env_dict['sitemap']), sitemap)
        if server.log_up_down:
            server.error_log.write("Successfully loaded sitemap configuration, \"%s\", for \"%s\"" %\
                                   (env_dict['sitemap'], use_server_name))

    # handle the request
    (success, status) = sitemap.handle(req)
    if success:
        return status
    else:
        (success, status) = server.handle_error(req, status)
        if success:
            return status
        else:
            return apache.HTTP_INTERNAL_SERVER_ERROR
