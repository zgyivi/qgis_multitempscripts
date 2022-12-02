from qgis.PyQt.QtCore import QCoreApplication
from osgeo import gdal, osr, ogr, gdalconst as gc
from qgis.core import QgsProject
from qgis.core import QgsMessageLog
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingOutputMultipleLayers
import processing
import pathlib
import re
import xml.etree.ElementTree as ET

class BuildCustomVRTs(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        defaultFileMask = r".+\/([0-9]{8})_(B[0-9]{1}[0-9,A]{1})\.tif$"
        defaultBands = "B01,B02,B03,B04,B05,B06,B07,B08,B09,B10,B11,B12,B8A"
        defaultOutFolder = QgsProject.instance().homePath()

        self.addParameter(QgsProcessingParameterMultipleLayers('INPUT', 'Raster layers to include in VRT', layerType= QgsProcessing.TypeFile))
        self.addParameter(QgsProcessingParameterString('MASK', 'Name parts to use as filename and band (regexp)', multiLine=False,
                                                       defaultValue=defaultFileMask))
        self.addParameter(
            QgsProcessingParameterString('BANDS', 'List of bands', multiLine=False,
                                         defaultValue=defaultBands))
        self.addParameter(
            QgsProcessingParameterFolderDestination('OUTFOLDER', 'Virtual raster output folder',
                                       defaultValue=defaultOutFolder),
            createOutput = True
        )
        self.addOutput(QgsProcessingOutputMultipleLayers('OUTPUT', 'Virtual rasters'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        results = {
            'OUTPUT': []
        }
        outputs = {}
        Bandlist = parameters['BANDS'].split(',')
        pattern = re.compile(parameters['MASK'])
        # Build virtual raster
        inputlist = list(parameters['INPUT'])
        inputlist.append("..last..")
        thisgroup = None
        group = 0
        for raster in inputlist:
            match = pattern.match(raster)
            if raster == "..last..":
                break
            if not match:
                continue
            if match.group(1) == thisgroup:
                continue
            thisgroup = match.group(1)
            group+=1
        feedback = QgsProcessingMultiStepFeedback(group, model_feedback)
        feedback.pushDebugInfo("inputlist: " + str(inputlist))
        filegroup = {}
        filelist = []
        vrtmap = {}
        thisgroup = None
        group=0
        for raster in inputlist:
            match = pattern.match(raster)
            if raster != "..last..":
                if not match:
                    continue
                feedback.pushDebugInfo("accepted: " + str(raster))
                if thisgroup==None:
                    thisgroup = match.group(1)
                if match.group(1) == thisgroup:
                    filepath = pathlib.Path(raster)
                    filegroup[match.group(2)] = filepath.as_posix()
                    continue
            if feedback.isCanceled():
                return {}
            for i,band in enumerate(Bandlist):
                if band in filegroup.keys():
                    filelist.append(filegroup[band])
                    vrtmap[i+1]=(band, filegroup[band])
                else:
                    filelist.append(filelist[0])
                    vrtmap[i+1] = vrtmap[1]

            feedback.pushDebugInfo("thisgroup: " + str(thisgroup))
            feedback.pushDebugInfo("filegroup: " + str(filegroup))
            feedback.pushDebugInfo("filelist: " + str(filelist))
            feedback.pushDebugInfo("vrtmap: " + str(vrtmap))
            if thisgroup:
                group+=1
                outputs[thisgroup] = {}
                alg_params = {
                    'ADD_ALPHA': False,
                    'ASSIGN_CRS': None,
                    'EXTRA': '',
                    'INPUT': filelist,
                    'PROJ_DIFFERENCE': False,
                    'RESAMPLING': 0,
                    'RESOLUTION': 1,
                    'SEPARATE': True,
                    'SRC_NODATA': '',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                
                outputs[thisgroup]['BuildVirtualRaster'] = processing.run('gdal:buildvirtualraster', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                outfilename = pathlib.Path(parameters['OUTFOLDER'], thisgroup+".vrt")
                outputs[thisgroup]['CustomVRT'] = self.buildCustomVrt(outfilename, outputs[thisgroup]['BuildVirtualRaster']['OUTPUT'], vrtmap)
                results['OUTPUT'].append(outputs[thisgroup]['CustomVRT'])
                feedback.setCurrentStep(group)
            if feedback.isCanceled():
                return {}
            if raster == "..last..":
                break
            thisgroup = match.group(1)
            filegroup.clear()
            filelist.clear()
            vrtmap.clear()
            filegroup[match.group(2)] = raster

        results['OUTFOLDER'] = parameters['OUTFOLDER']
        return results

    def buildCustomVrt(self, outVRT, rawVRT, mBands):

        #Read parameters from the raw VRT
        dsVRTRaw = gdal.Open(rawVRT)
        nXSize, nYSize = dsVRTRaw.RasterXSize, dsVRTRaw.RasterYSize
        srs = dsVRTRaw.GetProjection()
        gt = dsVRTRaw.GetGeoTransform()
        SOURCE_TEMPLATES = dict()
        eType = gdal.GDT_Unknown
        for i, (vBand, vFile) in mBands.items():
            band = dsVRTRaw.GetRasterBand(i)
            #if not isinstance(band, gdal.Band):
            #    s = ""
            assert isinstance(band, gdal.Band)
            if eType == gdal.GDT_Unknown:
                eType = band.DataType
            vrt_sources = dsVRTRaw.GetRasterBand(i).GetMetadata(str('vrt_sources'))
            assert len(vrt_sources) == 1
            srcXML = vrt_sources['source_0']
            assert '<SourceBand>1</SourceBand>' in srcXML
            source = ET.fromstring(srcXML)
            sourceFilename = source.find('SourceFilename')
            sourceFilename.set('relativeToVRT','1')
            sourceFilename.text = pathlib.Path(sourceFilename.text).relative_to(outVRT.parent).as_posix()
            SOURCE_TEMPLATES[vFile] = ET.tostring(source)
        gdal.Unlink(rawVRT)

        #Create a new VRT with band descriptions
        drvVRT = gdal.GetDriverByName('VRT')
        assert isinstance(drvVRT, gdal.Driver)

        dsVRTDst = drvVRT.Create(outVRT.as_posix(), nXSize, nYSize, 0, eType=eType)
        assert isinstance(dsVRTDst, gdal.Dataset)

        if srs is not None:
            dsVRTDst.SetProjection(srs)
        dsVRTDst.SetGeoTransform(gt)

        #Add bands
        for i, (vBand, vFile) in mBands.items():
            assert dsVRTDst.AddBand(eType, options=['subClass=VRTSourcedRasterBand']) == 0
            vrtBandDst = dsVRTDst.GetRasterBand(i)
            assert isinstance(vrtBandDst, gdal.Band)
            vrtBandDst.SetDescription(vBand)
            md = {}
            #assume only one band in each source
            xml = SOURCE_TEMPLATES[vFile]
            md['source_1'] = xml
            vrtBandDst.SetMetadata(md, 'vrt_sources')

        assert dsVRTDst.RasterCount == len(mBands)
        dsVRTDst.FlushCache()
        #dsCheck = gdal.Open(outVRT)
        #assert isinstance(dsCheck, gdal.Dataset)

        return outVRT.as_posix()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'buildcustomvrts'

    def displayName(self):
        return self.tr('Build multiple custom VRT files')

    def group(self):
        return self.tr('Satellite product preparation')

    def groupId(self):
        return 'SATprepare'

    def shortHelpString(self):
        return self.tr('Builds multiple virtual raster files from the list of raster images. File name and the bands of '
                       'the set are derived from the input file names by the given regular expression. '
                       'The first group in the mask will identify the output name, the second group defines '
                       'the label of the bands within the virtual raster file. The list of bands defines the band order '
                       'within the file. Band names, as captured by regexp group2, should be separeted by comma.')

    def createInstance(self):
        return BuildCustomVRTs()
