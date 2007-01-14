<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:ex="http://apache.org/cocoon/exception/1.0"
                exclude-result-prefixes="ex"
                xmlns="http://www.w3.org/1999/xhtml">

  <xsl:param name="page-title">An Error Has Occured</xsl:param>

  <xsl:template match="ex:exception-report">
    <html>
      <head>
        <title>
          <xsl:value-of select="$page-title"/>
        </title>
      </head>
      <body>
        <h1><xsl:value-of select="$page-title"/></h1>
        <p>
          <xsl:value-of select="@class"/>:
          <xsl:value-of select="ex:message"/>
        </p>
        <p>Python stacktrace:</p>
        <pre><xsl:value-of select="ex:stacktrace"/></pre>
        <address>The <a href="http://code.google.com/p/pycoon/">Pycoon</a> Project</address>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>

