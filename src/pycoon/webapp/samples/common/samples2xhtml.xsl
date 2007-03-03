<xsl:stylesheet xmlns="http://www.w3.org/1999/xhtml"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">
  <xsl:param name="contextPath"/>
  <xsl:template match="/">
    <html>
      <head>
        <title>Pycoon 0.2</title>
        <!--
        <link href="{$contextPath}/styles/main.css" type="text/css" rel="stylesheet"/>
        -->
      </head>
      <body>
        <h1>
          <xsl:value-of select="samples/@name"/>
        </h1>
        <xsl:apply-templates/>
        <address>The <a href="http://code.google.com/p/pycoon/">Pycoon</a> Project</address>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="group">
    <div class="group">
      <h2>
        <xsl:value-of select="@name"/>
      </h2>
      <dl>
        <xsl:apply-templates/>
      </dl>
    </div>
  </xsl:template>
  
  <xsl:template match="sample">
    <div class="sample">
      <dt>
        <xsl:variable name="link">
          <xsl:choose>
            <xsl:when test="starts-with(@href,'/')">
              <xsl:value-of select="concat($contextPath, @href)"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="@href"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:choose>
          <xsl:when test="string-length($link) &gt; 0">
            <a href="{$link}">
              <xsl:value-of select="@name"/>
            </a>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="@name"/>
          </xsl:otherwise>
        </xsl:choose>
      </dt>
      <dd>
        <xsl:copy-of select="*|text()"/>
      </dd>
    </div>
  </xsl:template>

  <xsl:template match="note">
    <div class="note">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
