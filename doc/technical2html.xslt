<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

<xsl:output method="xml"
	    doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
	    doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"
	    indent="yes"
	    encoding="utf-8" />

<xsl:template match="/">

<html lang="{/document/head/language}" xml:lang="{/document/head/language}">
  <xsl:apply-templates select="/document/head" />
  <xsl:apply-templates select="/document/body" />
</html>

</xsl:template>

<xsl:template match="head">

<head>
  <xsl:apply-templates />
  <style type="text/css">
td{vertical-align:top;padding:3px}
  </style>
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

<xsl:template match="head/created">
  <xsl:element name="meta">
    <xsl:attribute name="name">created</xsl:attribute>
    <xsl:attribute name="content"><xsl:apply-templates /></xsl:attribute>
  </xsl:element>
</xsl:template>

<xsl:template match="head/modified">
  <xsl:element name="meta">
    <xsl:attribute name="name">modified</xsl:attribute>
    <xsl:attribute name="content"><xsl:apply-templates /></xsl:attribute>
  </xsl:element>
</xsl:template>

<xsl:template match="head/language" />

<xsl:template match="head" mode="display">
  <h1><xsl:value-of select="/document/head/title" /></h1>
  <p>
    <small style="display:block"><xsl:value-of select="/document/head/author" /></small>
    <small style="display:block">Modified: <xsl:value-of select="/document/head/modified" /></small>
  </p>
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

<xsl:template match="link[@class and count(@*)=1]">
  <a href="#class-{@class}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="link[@class and @method]">
  <a href="#class-{@class}-method-{@method}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="link[@class and @property]">
  <a href="#class-{@class}-property-{@property}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="link[@class and @class-property]">
  <a href="#class-{@class}-class_property-{@class-property}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="link[@class and @helper-func]">
  <a href="#class-{@class}-helper_func-{@helper-func}"><xsl:apply-templates /></a>
</xsl:template>

<xsl:template match="class-hierarchy">
  <div id="{@name}-class-hierarchy-diagram">
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
  <div class="class" id="class-{@name}" style="border-top:1px solid #000000;border-bottom:1px solid #000000;margin-top:5px">
    <xsl:apply-templates select="name" />
    <xsl:if test="count(source|inherits) &gt; 0">
      <table>
	<xsl:apply-templates select="source|inherits" />
      </table>
    </xsl:if>
    <xsl:apply-templates select="*[name()!='name' and name()!='source' and name()!='inherits']" />
  </div>
</xsl:template>

<xsl:template match="class/name">
  <div style="font-size:120%;font-style:italic;margin-top:10px;margin-bottom:10px"><xsl:apply-templates /></div>
</xsl:template>

<xsl:template match="class/source">
  <tr>
    <td style="font-weight:bold">source</td>
    <td style="font-family:monospace;background-color:#FFF0D8"><xsl:apply-templates /></td>
  </tr>
</xsl:template>

<xsl:template match="class/inherits">
  <tr>
    <td style="font-weight:bold">inherits</td>
    <td style="background-color:#FFF0D8"><a href="#class-{.}"><xsl:apply-templates /></a></td>
  </tr>
</xsl:template>

<xsl:template match="class/description">
  <p>
    <xsl:apply-templates />
  </p>
</xsl:template>

<xsl:template match="syntax">
<div style="font-weight:bold">syntax</div>
<pre>
<xsl:apply-templates />
</pre>
</xsl:template>

<xsl:template match="method">
  <div id="class-{ancestor::class/@name}-method-{@name}" style="margin-bottom:5px;background-color:#E2F6FF">
    <xsl:apply-templates select="definition" />
    <xsl:if test="count(overrides|returns) &gt; 0">
      <table style="margin-left:15px">
	<xsl:apply-templates select="overrides|returns" />
      </table>
    </xsl:if>
    <xsl:apply-templates select="*[name()!='definition' and name()!='overrides' and name()!='returns']" />
  </div>
</xsl:template>

<xsl:template match="method/definition">
  <div style="font-weight:bold"><xsl:apply-templates /></div>
</xsl:template>

<xsl:template match="method/returns">
  <tr>
    <td style="font-weight:bold">returns</td>
    <td style="background-color:#FFF0D8"><xsl:apply-templates /></td>
  </tr>
</xsl:template>

<xsl:template match="method/overrides">
  <tr>
    <td style="font-weight:bold">overrides</td>
    <td style="background-color:#FFF0D8"><xsl:apply-templates /></td>
  </tr>
</xsl:template>

<xsl:template match="method/description">
  <div style="margin-left:15px">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="property">
  <div id="class-{ancestor::class/@name}-property-{name}" style="margin-bottom:5px;background-color:#FCFFAA">
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
  <div id="class-{ancestor::class/@name}-class_property-{name}" style="margin-bottom:5px;background-color:#FFEBE6">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="class-property/name">
  <div style="font-weight:bold"><xsl:apply-templates /></div>
  <div style="margin-left:15px;margin-top:5px;font-style:italic">class property</div>
</xsl:template>

<xsl:template match="class-property/description">
  <div style="margin-left:15px">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="helper-func">
  <div id="class-{ancestor::class/@name}-helper_func-{@name}" style="margin-bottom:5px;background-color:#E0DEFF">
    <xsl:apply-templates />
  </div>
</xsl:template>

<xsl:template match="helper-func/definition">
  <div style="font-weight:bold">
    <xsl:apply-templates />
  </div>
  <div style="margin-left:15px;margin-top:5px;font-style:italic">helper function</div>
</xsl:template>

<xsl:template match="helper-func/returns">
  <div style="margin-left:15px">
    <span style="font-weight:bold">returns</span>
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
