<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:param name="uri" />

<xsl:output method="xml" omit-xml-declaration="no" />

<xsl:template match="/">
<html>
  <head>
    <title><xsl:value-of select="//title" /></title>
  </head>
  <body>
    <xsl:apply-templates />
  </body>
</html>
</xsl:template>

<xsl:template match="title">
  <h1><xsl:apply-templates /></h1>
  <p>given parameter uri: "<xsl:value-of select="$uri" />"</p>
</xsl:template>

<xsl:template match="div">
  <div id="{@id}">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="p">
  <p><xsl:apply-templates /></p>
</xsl:template>

<xsl:template match="list">
  <ul>
    <xsl:apply-templates />
  </ul>
</xsl:template>

<xsl:template match="list/item">
  <li><xsl:apply-templates /></li>
</xsl:template>

</xsl:stylesheet>
