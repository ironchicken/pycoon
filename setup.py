#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Andrey Nordin <http://claimid.com/anrienord>"

from setuptools import setup, find_packages
setup(
    name = "pycoon-pysitemap",
    version = "0.2a1",
    packages = find_packages("src"),
    package_dir = {"": "src"},
    install_requires = ['lxml >= 1.1.1, < 1.1.2'],
    entry_points = {
        "console_scripts": [
            "pycoon = pycoon:main",
        ],
    },
    include_package_data = True,
    
    # Metadata for upload to PyPI
    author = "Andrey Nordin, Richard Lewis",
    description = "Pythonic web development framework based on XML pipelines and WSGI",
    license = "GNU GPL",
    keywords = "web framework xml pipeline wsgi middleware cocoon sitemap",
    url = "http://code.google.com/p/pycoon/",
    long_description = "Pycoon is a Python web development framework which allows XML processing pipelines to handle HTTP requests based on URI pattern matching. It is similar in intention to the Apache Cocoon framework.",
)

