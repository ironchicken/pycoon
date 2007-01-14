#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple multi-threaded stress test for HTTP servers, that generates a request
queue. Requests are statistically distributed according to Poisson exponential
distribution. Stress test parameters are hard-coded.
"""

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

import sys
from urllib import urlopen
import urllib2
from threading import Thread
import time
import random
import math

class UriReader(Thread):
    def __init__(self, uri):
        Thread.__init__(self)
        self.uri = uri
        self.exception = None

    def run(self):
        t0 = time.clock()
        try:
            try:
                request = urllib2.Request(uri)
                opener = urllib2.build_opener()
                fd = opener.open(self.uri)
                try:
                    self.data = fd.read()
                    print "[%s] OK" % self.getName()
                finally:
                    fd.close()
            except Exception, e:
                self.exception = e
        finally:
            t1 = time.clock()
            self.time = t1 - t0

def rcmp(r0, r1):
    if r0 is None or r0.data != r1.data: return None
    else: return r0

def mean(samples):
    if len(samples) == 0: return 0
    return float(sum(samples)) / len(samples)
    
def stddev(samples):
    if len(samples) <= 1: return 0
    m = mean(samples)
    sum = reduce(lambda sum, x: sum + (x - m) ** 2, samples, 0)
    return math.sqrt(float(sum) / (len(samples) - 1))
    
if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise Exception("Wrong command line parameters")
    uri, count, lam = sys.argv[1:4]
    readers = [UriReader(uri) for i in range(int(count))]
    for r in readers:
        # Lambda parameter of the exponential distribution -- request rate (secs ** -1)
        # E. g. 5.0 means 5 requests per second (1 request per 0.2 secs) on average 
        time.sleep(random.expovariate(float(lam)))
        r.start()
    for r in readers: r.join()
    for r in readers:
        if r.exception is not None:
            raise r.exception
    print "\n results:"
    print "\n".join(["len: %d B, time: %.3f s" % (len(r.data), r.time) for r in readers])
    print "content is the same: %s" % (reduce(rcmp, readers) is not None)
    print "mean: %.3f s, variance: %.3f" % (mean([r.time for r in readers]), stddev([r.time for r in readers]) ** 2)

    correct = readers[0]
    for r in readers[1:]:
        if len(r.data) != len(correct.data):
            print "\nWrong data:\n%s\n" % r.data

