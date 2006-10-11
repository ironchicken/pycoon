<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:output method="html" />

<xsl:template match="/">

<html>
  <xsl:apply-templates select="/document/head" />
  <xsl:apply-templates select="/document/body" />
</html>

</xsl:template>

<xsl:template match="head">

<head>
  <xsl:apply-templates />
</head>

</xsl:template>

<xsl:template match="head/title">
  <title><xsl:apply-templates /></title>
</xsl:template>

<xsl:template match="head/author">
  <xsl:element name="meta">
    <xsl:attribute name="name">author</xsl:attribute>
    <xsl:attribute name="content"><xsl:apply-templates /></xsl:attribute>
  </xsl:element>
</xsl:template>

<xsl:template match="head/date">
  <xsl:element name="meta">
    <xsl:attribute name="name">date</xsl:attribute>
    <xsl:attribute name="content"><xsl:apply-templates /></xsl:attribute>
  </xsl:element>
</xsl:template>

<xsl:template match="head" mode="display">
  <h1><xsl:value-of select="/document/head/title" /></h1>
  <small><xsl:value-of select="/document/head/author" /></small>
  <hr />
</xsl:template>

<xsl:template match="body">

<body>
  <xsl:apply-templates select="/document/head" mode="display" />
  <xsl:apply-templates />
</body>

</xsl:template>

<xsl:template match="div">
  <div id="{@id}">
    <xsl:element name="h{count(ancestor::div)+2}"><xsl:value-of select="@title" /></xsl:element>
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="p">
  <p>
    <xsl:apply-templates />
  </p>
</xsl:template>

<xsl:template match="list">
  <ul>
    <xsl:apply-templates />
  </ul>
</xsl:template>

<xsl:template match="list/item">
  <li>
    <xsl:apply-templates />
  </li>
</xsl:template>

<xsl:template match="code">
<pre>
<xsl:apply-templates />
</pre>
</xsl:template>

<xsl:template match="link[@href]">
  <a href="{@href}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="link[@class and not(@method) and not(@property)]">
  <a href="#class-{@class}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="link[@class and @method]">
  <a href="#class-{@class}-method-{@method}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="link[@class and @property]">
  <a href="#class-{@class}-property-{@property}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="class-hierarchy">
  <div id="class-hierarchy-diagram">
    <ul>
      <xsl:apply-templates />
    </ul>
  </div>
</xsl:template>

<xsl:template match="class[@description]">
  <li>
    <a style="font-weight:bold" href="#class-{@name}"><xsl:value-of select="@name" /></a>: <xsl:value-of select="@description" />
    <xsl:if test="count(class) &gt; 0">
      <ul>
	<xsl:apply-templates />
      </ul>
    </xsl:if>
  </li>
</xsl:template>

<xsl:template match="class[not(@description)]">
  <div class="class" id="class-{@name}" style="border-top:1px solid #000000;border-bottom:1px solid #000000">
    <div style="font-weight:bold">Class</div>
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="class/name">
  <div>
    <span style="font-weight:bold">name:</span>
    <span><xsl:apply-templates /></span>
  </div>
</xsl:template>

<xsl:template match="class/source">
  <div>
    <span style="font-weight:bold">source:</span>
    <span style="font-family:monospace"><xsl:apply-templates /></span>
  </div>
</xsl:template>

<xsl:template match="class/inherits">
  <div>
    <span style="font-weight:bold">inherits:</span>
    <span><a href="#class-{.}"><xsl:apply-templates /></a></span>
  </div>
</xsl:template>

<xsl:template match="class/description">
  <p>
    <xsl:apply-templates />
  </p>
</xsl:template>

<xsl:template match="syntax">
<div style="font-weight:bold">syntax:</div>
<pre>
<xsl:apply-templates />
</pre>
</xsl:template>

<xsl:template match="method">
  <div id="class-{ancestor::class/@name}-method-{@name}">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="method/definition">
  <div style="font-weight:bold"><xsl:apply-templates /></div>
</xsl:template>

<xsl:template match="method/returns">
  <div style="margin-left:15px">
    <span style="font-weight:bold">returns:</span>
    <span><xsl:apply-templates /></span>
  </div>
</xsl:template>

<xsl:template match="method/overrides">
  <div style="margin-left:15px">
    <span style="font-weight:bold">overrides:</span>
    <span><xsl:apply-templates /></span>
  </div>
</xsl:template>

<xsl:template match="method/description">
  <div style="margin-left:15px">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="property">
  <div id="class-{ancestor::class/@name}-property-{name}">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="property/name">
  <div style="font-weight:bold"><xsl:apply-templates /></div>
</xsl:template>

<xsl:template match="property/description">
  <div style="margin-left:15px">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="class-property">
  <div id="class-{ancestor::class/@name}-class_property-{name}">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="class-property/name">
  <div style="font-weight:bold"><xsl:apply-templates /></div>
</xsl:template>

<xsl:template match="class-property/description">
  <div style="margin-left:15px">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="helper-func">
  <div id="class-{ancestor::class/@name}-helper-{@name}">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="helper-func/definition">
  <div>helper function:</div>
  <div style="font-weight:bold"><xsl:apply-templates /></div>
</xsl:template>

<xsl:template match="helper-func/returns">
  <div style="margin-left:15px">
    <span style="font-weight:bold">returns:</span>
    <span><xsl:apply-templates /></span>
  </div>
</xsl:template>

<xsl:template match="helper-func/description">
  <div style="margin-left:15px">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="identifier">
  <span style="font-style:italic"><xsl:apply-templates /></span>
</xsl:template>

</xsl:stylesheet>
