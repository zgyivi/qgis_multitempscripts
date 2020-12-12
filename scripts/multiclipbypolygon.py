from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterDefinition
from qgis.core import QgsProcessingOutputMultipleLayers
import os.path
import processing


class MultiClipByPolygon(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers('INPUT', 'Input rasters', layerType=QgsProcessing.TypeRaster, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('Masklayer', 'Mask layer', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        param=QgsProcessingParameterFile('OUTFOLDER', 'Folder to store clipped rasters',
                                       behavior=QgsProcessingParameterFile.Folder,
                                       defaultValue=None,
                                       optional = True
                                       )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param, createOutput = True)
        self.addOutput(QgsProcessingOutputMultipleLayers('OUTPUT', 'Clipped rasters'))


    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        steps = len(parameters['INPUT'])
        feedback = QgsProcessingMultiStepFeedback(steps, model_feedback)

        results = {'OUTPUT': []}
        outputs = {'ClipRasterByMaskLayer': []}
        i=0
        feedback.pushDebugInfo("OUTFOLDER: " + str(parameters['OUTFOLDER']))
        for filename in parameters['INPUT']:
            if os.path.isdir(str(parameters['OUTFOLDER'])):
                file, ext = os.path.splitext(os.path.basename(filename))
                outfilename = os.path.join(parameters['OUTFOLDER'],file + "_clipped" + ext)
            else:
                outfilename = QgsProcessing.TEMPORARY_OUTPUT
            # Clip raster by mask layer
            alg_params = {
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'DATA_TYPE': 0,
                'EXTRA': '',
                'INPUT': filename,
                'KEEP_RESOLUTION': False,
                'MASK': parameters['Masklayer'],
                'MULTITHREADING': False,
                'NODATA': None,
                'OPTIONS': '',
                'SET_RESOLUTION': False,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'X_RESOLUTION': None,
                'Y_RESOLUTION': None,
                'OUTPUT': outfilename
            }
            outputs['ClipRasterByMaskLayer'].append(processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True))
            i = i + 1
            feedback.setCurrentStep(i)
            if feedback.isCanceled():
                return {}

        for clipresult in outputs['ClipRasterByMaskLayer']:
            results['OUTPUT'].append(clipresult['OUTPUT'])
        return results

    def tr(self, string):
        return QCoreApplication.translate('Analyze', string)

    def name(self):
        return 'MultiRasterClip'

    def displayName(self):
        return self.tr('Clip multiple rasters by same vector mask')

    def group(self):
        return self.tr('Raster analysis')

    def groupId(self):
        return 'Analyze'

    def shortHelpString(self):
        return self.tr('Clips multiple raster files with the same vector polygon.'
                       )

    def createInstance(self):
        return MultiClipByPolygon()
