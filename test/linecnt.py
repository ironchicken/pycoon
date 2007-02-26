#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shows line count in all files (specified by file mask) in the direcory. Useful
for counting source code lines in a software project.

Usage: linecnt.py <base directory> <file mask>
"""

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import sys
import os
from glob import glob

def subdirs(d):
    return [os.path.join(d, f) for f in os.listdir(d) if os.path.isdir(os.path.join(d, f))]
    
def alldirs(d):
    return [d] + flatten([alldirs(f) for f in subdirs(d)])

def allfiles(d, m):
    return flatten([glob(os.path.join(d, m)) for d in alldirs(directory)])

def strcnt(f):
    return len(open(f).read().splitlines())

def flatten(list):
    return reduce(lambda x, y: x + y, list, [])
    
if __name__ == "__main__":    
    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1)
    directory, mask = sys.argv[1:3]    
    print sum([strcnt(f) for f in allfiles(directory, mask)])

