<?xml version="1.0" encoding="utf-8"?>
<xsl:transform xmlns="http://www.w3.org/1999/xhtml"
               xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
               xmlns:rss="http://purl.org/rss/1.0/"
               xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
               exclude-result-prefixes="rdf rss"
               version="1.0">
  
  <xsl:output indent="yes" method="xml" encoding="utf-8"/>

  <xsl:template match="text()"/>
  
  <xsl:template match="/">
    <xsl:variable name="title">
      <xsl:value-of select="/rdf:RDF/rss:channel/rss:title"/>
    </xsl:variable>
    <html>
      <head>
        <title><xsl:value-of select="$title"/></title>
      </head>
      <body>
        <h1><xsl:value-of select="$title"/></h1>
        <ul>
          <xsl:apply-templates/>
        </ul>
      </body>
    </html>
  </xsl:template>
  
  <xsl:template match="/rdf:RDF/rss:channel/rss:items/rdf:Seq/rdf:li">
    <li>
      <a href="{./@rdf:resource}"><xsl:value-of select="./@rdf:resource"/></a>
    </li>
  </xsl:template>
</xsl:transform>

