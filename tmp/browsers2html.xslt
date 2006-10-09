<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:output method="xml" />

<xsl:param name="browser" />

<xsl:template match="/">
  <xsl:apply-templates />
</xsl:template>

<xsl:template match="p">
  <p><xsl:apply-templates /></p>
</xsl:template>

<xsl:template match="browser">
  <b><xsl:value-of select="$browser" /></b>
  <xsl:apply-templates />
</xsl:template>

</xsl:stylesheet>
