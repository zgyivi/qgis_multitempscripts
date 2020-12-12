from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFileDestination
import processing
import os
import re
import yaml

class CreateIndexDefinitions(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString('LAYERNAME', 'Virtual raster layer name with all Sentinel2 bands', defaultValue='SentinelVRTLayer'))

        self.addParameter(
            QgsProcessingParameterFileDestination('OUTPUT', 'Destination file', defaultValue='indexes.yaml'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        #feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        layer = parameters['LAYERNAME']
        outputs = {
            'INDEXDEF': {
                'OUTPUT': {
                    'Index definitions':{
                        'Sentinel2': {
                            'NDVI': '(\"'+layer+'@8\" - \"'+layer+'@4\") / (\"'+layer+'@8\" + \"'+layer+'@4\")',
                            'NDRE5': '(\"'+layer+'@8\" - \"'+layer+'@5\") / (\"'+layer+'@8\" + \"'+layer+'@5\")',
                            'NDRE6': '(\"'+layer+'@8\" - \"'+layer+'@6\") / (\"'+layer+'@8\" + \"'+layer+'@6\")',
                            'NDRE7': '(\"'+layer+'@8\" - \"'+layer+'@7\") / (\"'+layer+'@8\" + \"'+layer+'@7\")',
                            'GRVI': '(\"'+layer+'@3\" - \"'+layer+'@4\") / (\"'+layer+'@3\" + \"'+layer+'@4\")',
                            'MSAVI2': '(2*\"'+layer+'@8\" + 1 - sqrt((2*\"'+layer+'@8\"+1)^2 - 8 * (\"'+layer+'@8\" - \"'+layer+'@4\"))) / 2',
                            'NDBR': '(\"'+layer+'@8\" - \"'+layer+'@12\") / (\"'+layer+'@8\" + \"'+layer+'@12\")',
                            'NDMI': '(\"'+layer+'@13\" - \"'+layer+'@11\") / (\"'+layer+'@13\" + \"'+layer+'@11\")',
                            'SAVI05': '(\"'+layer+'@8\" - \"'+layer+'@4\") / (\"'+layer+'@8\" + \"'+layer+'@4\" + .5) * 1.5',
                            'OSAVI': '(\"' + layer + '@8\" - \"' + layer + '@4\") / (\"' + layer + '@8\" + \"' + layer + '@4\" + .16) * 1.16',
                            'NDWI': '(\"'+layer+'@8\" - \"'+layer+'@11\") / (\"'+layer+'@8\" + \"'+layer+'@11\")',
                            'AVI': '(\"' + layer + '@8\" * ( 1 - \"' + layer + '@4\") * (\"' + layer + '@8\" - \"' + layer + '@4\"))^(1/3)',

                        }
                    }
                }
            }
        }

        with open(parameters['OUTPUT'], 'w') as outfile:
            yaml.dump(outputs['INDEXDEF']['OUTPUT'], outfile, default_flow_style=False)

        return outputs

    def name(self):
        return 'create_index_def'

    def displayName(self):
        return 'CreateIndexDefinitions'

    def group(self):
        return 'Calculations'

    def groupId(self):
        return 'Calculations'

    def createInstance(self):
        return CreateIndexDefinitions()
