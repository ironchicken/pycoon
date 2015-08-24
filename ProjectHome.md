Current version: **0.2a5 (alpha for developers)**, 2007-04-12

**Attention**: The project has been suspended for a while. For further information contact us via the mailing list.

**Pycoon** is a [Python](http://www.python.org/) [WSGI](http://www.python.org/dev/peps/pep-0333/) web development framework which allows [XML processing pipelines](http://en.wikipedia.org/wiki/XML_pipeline) to handle HTTP requests based on URI pattern matching. It is similar in intention to the [Apache Cocoon](http://cocoon.apache.org/) framework. Pycoon uses sitemap file format compatible with [Apache Cocoon Sitemap 1.0](http://cocoon.apache.org/2.1/userdocs/concepts/sitemap.html).

The architecture of Pycoon focuses on:

  * Full **sitemap file format compatibility** with Apache Cocoon
  * Heavy usage of **WSGI modularity** ideas
  * Simplicity of deployment
  * Optimization issues

Pycoon is a WSGI middleware that dispatches requests based on Apache Cocoon sitemap logic. Data is processed by an XML pipeline composed of several WSGI applications and middleware components. An HTTP server WSGI interface and it's implementations (_Pycoon front-end_) are already complete. WSGI interfaces of _sitemap components_ and implementations of them (_Pycoon back-end_) are in progress.

## Starting points ##

  * [Pycoon Wiki](http://pycoon.pbwiki.com/)
    * [Quick starter guide](http://pycoon.pbwiki.com/Quick+starter+guide)
    * [Roadmap](http://pycoon.pbwiki.com/Roadmap)
    * [Changelog](http://pycoon.pbwiki.com/Changelog)
  * [Pycoon downloads](http://cheeseshop.python.org/pypi/pycoon/)

## Documentation ##

  * [List of implemented features](http://pycoon.pbwiki.com/List+of+implemented+features) (compared with Apache Cocoon)
  * [Developer guide](http://pycoon.pbwiki.com/Developer+guide)