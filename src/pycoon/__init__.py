#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Pycoon Web Development Framework
# Copyright (C) 2006 Andrey Nordin, Richard Lewis
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"
__version__ = "pysitemap/0.2a1"

ns = {
    "map": "http://apache.org/cocoon/sitemap/1.0",
    "py": "http://pycoon.org/ns/pysitemap/0.1/",
}

class ResourceNotFoundException(Exception): pass

class SitemapException(Exception): pass

def synchronized(func):
    def decorator(self, *args, **kwargs):
        try:
            rlock = self._lock
        except AttributeError:
            from threading import RLock
            rlock = self.__dict__.setdefault("_lock", RLock())
        rlock.acquire()
        try:
            return func(self, *args, **kwargs)
        finally:
            rlock.release()
    return decorator

