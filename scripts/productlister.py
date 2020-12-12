from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingOutputString
import processing
import os
from fnmatch import fnmatch

class ProductLister(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile('Sourcefolder', 'Source folder', behavior=QgsProcessingParameterFile.Folder,
                                       fileFilter='All files (*.*)', defaultValue='/Adat/PREGA/Download/2019'))
        self.addParameter(QgsProcessingParameterString('mask', 'File name mask', multiLine=False,
                                                       defaultValue="*.jp2"))
        self.addOutput(QgsProcessingOutputString('OUTPUT', 'Product list'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}

        outputs = {
            'ProductLister': {
                'OUTPUT': []
            }
        }

        pattern = parameters['mask']

        for path, subdirs, files in os.walk(parameters['Sourcefolder']):
            for name in files:
                if fnmatch(os.path.join(path, name), pattern):
                    outputs['ProductLister']['OUTPUT'].append(os.path.join(path, name))
        feedback.setCurrentStep(1)
        results['OUTPUT'] = outputs['ProductLister']['OUTPUT']
        return results


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def name(self):
        return 'ProductLister'

    def displayName(self):
        return self.tr('List satellite products')

    def group(self):
        return self.tr('Satellite product preparation')

    def groupId(self):
        return 'SATprepare'

    def shortHelpString(self):
        return self.tr('List all files in the given directory that match the pattern.')

    def createInstance(self):
        return ProductLister()
