from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsMessageLog
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterExtent
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingOutputMultipleLayers
from qgis import processing
import os.path
import re

class MultiClipRename(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers('INPUT', 'Rasters to clip', layerType= QgsProcessing.TypeFile))
        self.addParameter(QgsProcessingParameterExtent('CLIPEXTENT', 'Selected area',
                                                       defaultValue='310943.7976987961,319113.2415897856,5245878.353460406,5254768.630635895 [EPSG:32634]'))
        self.addParameter(QgsProcessingParameterString('MASK', 'Matching rule (regexp)', multiLine=False, defaultValue=r".+_([0-9]{8})T[0-9]{6}_(B[0-9]{1}[0-9,A]{1})\.jp2$"))
        self.addParameter(
            QgsProcessingParameterFile('OUTFOLDER', 'Folder to store clipped rasters', behavior=QgsProcessingParameterFile.Folder,
                                       defaultValue='/AdatSSD/PREGA/Szakdolgozat/V2/2021/Data'),
            createOutput=True
        )
        self.addOutput(QgsProcessingOutputMultipleLayers('OUTPUT', 'Clipped rasters'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        steps = len(parameters['INPUT'])
        feedback = QgsProcessingMultiStepFeedback(steps, model_feedback)
        results = {
            'OUTFOLDER': "",
            'OUTPUT': []
        }

        i = 0
        outputs = {
            'cliprasterbyextent': {},
            'LISTOFCLIPPEDRASTERS': []
        }
        i=0

        #pattern = re.compile(r".+_([0-9]{8})T[0-9]{6}_(B[0-9]{1}[0-9,A]{1})\.jp2$")
        pattern = re.compile(parameters['MASK'])
        for filename in parameters['INPUT']:
            match = pattern.match(filename)
            if not match:
                continue
            clippedfilename = os.path.join(parameters['OUTFOLDER'],match.group(1)+"_"+match.group(2)+".tif")

            alg_params = {
                'DATA_TYPE': 0,
                'EXTRA': '',
                'INPUT': filename,
                'NODATA': None,
                'OPTIONS': '',
                'PROJWIN': parameters['CLIPEXTENT'],
                'OUTPUT': clippedfilename,
            }
            if feedback.isCanceled():
                return {}
            outputs['cliprasterbyextent'][filename] = processing.run('gdal:cliprasterbyextent', alg_params,
                                                                     context=context, feedback=feedback,
                                                                     is_child_algorithm=True)['OUTPUT']
            feedback.setCurrentStep(i)
            i=i+1
            outputs['LISTOFCLIPPEDRASTERS'].append(clippedfilename)

        results['OUTFOLDER'] = parameters['OUTFOLDER']
        results['OUTPUT'] = outputs['LISTOFCLIPPEDRASTERS']
        return results


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'MultiClipRename'

    def displayName(self):
        return self.tr('MultiClip&Rename')

    def group(self):
        return self.tr('Satellite product preparation')

    def groupId(self):
        return 'SATprepare'

    def shortHelpString(self):
        return self.tr('Clips multiple raster files with the same extent and stores them in output folder, renamed by the given pattern. '
                       'The mask rule must define 2 groups, usually date part and band name. Output file will be named as [group1]_[group2].tif')

    def createInstance(self):
        return MultiClipRename()
