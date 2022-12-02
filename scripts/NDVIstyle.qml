<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" minScale="1e+8" hasScaleBasedVisibilityFlag="0" version="3.12.1-București" maxScale="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <rasterrenderer band="1" type="singlebandpseudocolor" opacity="1" alphaBand="-1" nodataColor="" classificationMin="-0.2" classificationMax="0.999999">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" clip="0" classificationMode="1">
          <colorramp type="gradient" name="[source]">
            <prop v="45,140,192,255" k="color1"/>
            <prop v="17,72,11,255" k="color2"/>
            <prop v="0" k="discrete"/>
            <prop v="gradient" k="rampType"/>
            <prop v="0.325721;60,57,51,255:0.559364;156,150,128,255:0.747858;103,204,99,255" k="stops"/>
          </colorramp>
          <item color="#2d8cc0" label="-0.2" value="-0.2" alpha="255"/>
          <item color="#3c3933" label="0.190864874279" value="0.190864874279" alpha="255"/>
          <item color="#9c9680" label="0.471236240636" value="0.471236240636" alpha="255"/>
          <item color="#67cc63" label="0.697428852142" value="0.697428852142" alpha="255"/>
          <item color="#11480b" label="0.999999" value="0.999999" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeStrength="100" colorizeRed="255" grayscaleMode="0" colorizeBlue="128" colorizeOn="0" colorizeGreen="128" saturation="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
