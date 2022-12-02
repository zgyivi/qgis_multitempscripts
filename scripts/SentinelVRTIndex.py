from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessing
from qgis.core import QgsMessageLog
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterExpression
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterEnum
import processing
import os
import yaml

class SentinelVRTIndexCalc(QgsProcessingAlgorithm):

    indexdefs = {}

    def initAlgorithm(self, config=None):
        indexdeffile=os.path.join(os.path.dirname(__file__), "indexes.yaml")
        if os.path.exists(indexdeffile):
            with open(indexdeffile, 'r') as stream:
                try:
                    self.indexdefs = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
        else:
            layer = 'SentinelVRTLayer'
            self.indexdefs = {
                'Index definitions': {
                    'Sentinel2': {
                        'NDVI': '(\"' + layer + '@8\" - \"' + layer + '@4\") / (\"' + layer + '@8\" + \"' + layer + '@4\")',
                    }
                }
            }
        self.addParameter(QgsProcessingParameterRasterLayer('SentinelVrtLayer', 'SentinelVRTLayer', defaultValue=None))
        self.addParameter(QgsProcessingParameterEnum('INDEX', 'Index', options=self.indexdefs['Index definitions']['Sentinel2'].keys(), allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterFile('LayerStyledefinition', 'Layer Style definition', behavior=QgsProcessingParameterFile.File, fileFilter='Style Files (*.qml)', defaultValue=os.path.join(os.path.dirname(__file__), "NDVIstyle.qml")))
        self.addParameter(QgsProcessingParameterRasterDestination('OUTPUT', 'Output', createByDefault=True, defaultValue=None),
                          createOutput = True
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        indexequation = str(self.indexdefs['Index definitions']['Sentinel2'][list(self.indexdefs['Index definitions']['Sentinel2'].keys())[parameters['INDEX']]])
        vrtname = parameters['SentinelVrtLayer'].rsplit('_',1)[0]
        indexequation = indexequation.replace("SentinelVRTLayer", vrtname)
        feedback.pushDebugInfo("indexequation: " + str(indexequation))
        # Raster calculator
        alg_params = {
            'CELLSIZE': 0,
            'CRS': 'ProjectCrs',
            'EXPRESSION': indexequation,
            'EXTENT': parameters['SentinelVrtLayer'],
            'LAYERS': parameters['SentinelVrtLayer'],
            'OUTPUT': parameters['OUTPUT']
        }
        feedback.pushDebugInfo(str(alg_params))
        outputs['RasterCalculator'] = processing.run('qgis:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['RasterCalculator']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Set layer style
        if os.path.exists(parameters['LayerStyledefinition']) :
            alg_params = {
                'INPUT': outputs['RasterCalculator']['OUTPUT'],
                'STYLE': parameters['LayerStyledefinition']
            }
            outputs['SetLayerStyle'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        return results

    def name(self):
        return 'SentinelVRTIndex'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def displayName(self):
        return self.tr('Calculate index from Sentinel VRT file')

    def group(self):
        return self.tr('Sentinel calculations')

    def groupId(self):
        return 'SentinelTools'

    def shortHelpString(self):
        return self.tr('Calculates predefined index from VRT file contains Sentinel bands. (the index definitions are '
                       'bound to Sentinel-2 band set) Assigns the given style definition to the new layer.')




    def createInstance(self):
        return SentinelVRTIndexCalc()
