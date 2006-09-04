<?xml version="1.0" encoding="UTF-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:output method="html" />

<xsl:param name="uri" />
<xsl:param name="traceback" />

<xsl:template match="/">
<html>
  <head>
    <title>Pycoon - <xsl:value-of select="//title" /></title>
  </head>
  <body>
    <h1>Error</h1>
    <xsl:apply-templates />
  </body>
</html>
</xsl:template>

<xsl:template match="title">
  <h2><xsl:apply-templates /></h2>
</xsl:template>

<xsl:template match="code">
  <div><span style="font-weight:bold">Error code:</span><xsl:text> </xsl:text><xsl:apply-templates /></div>
</xsl:template>

<xsl:template match="description">
  <div>
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="p">
  <p><xsl:apply-templates /></p>
</xsl:template>

<xsl:template match="pre">
<pre>
<xsl:apply-templates />
</pre>
</xsl:template>

<xsl:template match="uri"><xsl:value-of select="$uri" /></xsl:template>
<xsl:template match="traceback"><xsl:value-of select="$traceback" /></xsl:template>

<!--<xsl:template match="*" priority="-1">
  <xsl:copy-of select="." />
</xsl:template>-->

</xsl:stylesheet>