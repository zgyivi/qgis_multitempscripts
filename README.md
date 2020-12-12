# qgis_multitempscripts
QGIS Phyton scripts to support multi-temporal analysis

The scripts  can be used individually from QGIS Processing Toolbox or can be added to models too. 

| Name of the tool                              | Description                                                  | Filename                         |
| --------------------------------------------- | ------------------------------------------------------------ | -------------------------------- |
| List satellite products                       | List all files in the given directory that match the pattern. | productlister.py                 |
| MultiClip&Rename                              | Clips multiple raster files with the same extent and stores them in output folder, renamed by the given pattern. | multicliprename.py               |
| Build multiple custom VRT files               | Builds multiple virtual raster files from the list of raster images. | BuildCustomVRTs.py               |
| Calculate index from Sentinel VRT file        | Calculates predefined index from VRT file contains Sentinel bands. (the index definitions are bound to Sentinel-2 band set) Assigns the given style definition to the new layer. | SentinelVRTIndex.py indexes.yaml |
| Count of days raster values over limit        | Calculates the number of days on a time series of raster images where the values are above the given threshold. | CountDaysOverLimit.py            |
| Clip multiple 	rasters by same vector mask | Clips multiple raster files with the same vector polygon.    | multiclipbypolygon.py            |
| CreateSentinelVRT                             | A model which links above scripts to create VRTs from downloaded Sentinel products | CreateVRT.model3                 |
| ClipAndSegment                                | A model to execute i.segment procedure on the given rasters, but clips them first with the vector mask | ClipAndSegment.model3            |

