from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProject
from qgis.core import QgsProcessing
from qgis.core import QgsMessageLog
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsRasterLayer
from datetime import datetime
import processing
import os.path
import re

class CountDaysOverLimit(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers('INPUT', 'Input rasters',
                                                               layerType=QgsProcessing.TypeRaster,defaultValue=None))
        self.addParameter(QgsProcessingParameterString('FILENAMEMASK', 'Matching rule (regexp)', multiLine=False,
                                                       defaultValue=r".*(([0-9]{8})_([0-9,A-Z]*).*\.tif)$"))
        self.addParameter(QgsProcessingParameterString('DATEFORMAT', 'Date format', multiLine=False,
                                                       defaultValue=r"%Y%m%d"))
        self.addParameter(
            QgsProcessingParameterNumber('THRESHOLD', 'Threshold', type=QgsProcessingParameterNumber.Double,
                                         defaultValue=0.5))
        self.addParameter(QgsProcessingParameterRasterDestination('OUTPUT', 'Output',
                          createByDefault=True, defaultValue=None),
                          createOutput = True
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        results = {}
        outputs = {}
        inputrasters = []
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        filenamepattern = re.compile(parameters['FILENAMEMASK'])
        height=None
        width=None
        for raster in parameters['INPUT']:
            feedback.pushDebugInfo("layer: " + str(raster))
            match = filenamepattern.match(raster)
            if not match:
                layers = QgsProject.instance().mapLayersByName(raster[:13])
                if not  layers:
                    continue
                layer = layers[0]
                filename = layer.dataProvider().dataSourceUri()
                match = filenamepattern.match(filename)
                if not match:
                    continue
            else:
                filename = raster
                layer = QgsRasterLayer(filename,match.group(1),"gdal")
                if not layer.isValid():
                    continue
            feedback.pushDebugInfo("size: " + str(layer.height()) + "x" + str(layer.width()))
            if height is None:
                height = layer.height()
            if width is None:
                width = layer.width()
            if layer.height() != height:
                continue
            if layer.width() != width:
                continue

            date =  datetime.strptime(match.group(2), parameters['DATEFORMAT'])
            inputrasters.append({'date': date, 'filename': filename})
        feedback = QgsProcessingMultiStepFeedback(len(inputrasters), model_feedback)

        def get_date(e):
            return e.get('date')

        inputrasters.sort(key=get_date)
        feedback.pushDebugInfo("inputrasters: " + str(inputrasters))
        previnput=None
        sumraster=None
        i=0
        for inputraster in inputrasters:
            if previnput is None:
                previnput = inputraster
                if sumraster is None:
                    sumraster = self.nullraster(inputraster['filename'],parameters['OUTPUT'], context, feedback)['OUTPUT']
                continue
            delta = inputraster['date'] - previnput['date']
            outputs['CalcDaysOverLimit'] = self.adddaysoverthreshold(sumraster, previnput['filename'], inputraster['filename'], delta.days, parameters['THRESHOLD'], context, feedback)
            sumraster = outputs['CalcDaysOverLimit']['OUTPUT']
            previnput = inputraster
            i=i+1
            feedback.setCurrentStep(i)
            if feedback.isCanceled():
                return {}
        results['OUTPUT'] = outputs['CalcDaysOverLimit']['OUTPUT']

        return results

    def nullraster(self, sample, outraster, context, feedback):
        if outraster is not None:
            output = outraster
        else:
            output = QgsProcessing.TEMPORARY_OUTPUT
        alg_params = {
            'CELLSIZE': 0,
            'CRS': None,
            'EXPRESSION': '0',
            'EXTENT': None,
            'LAYERS': [sample],
            'OUTPUT': output
        }
        return processing.run('qgis:rastercalculator', alg_params, context=context,
                              feedback=feedback, is_child_algorithm=True)

    def adddaysoverthreshold(self, sumraster, raster1, raster2, daysbetween, threshold, context, feedback):
        daycalcequation = 'C+((B-?thr?)/(B-A+0.000000001)*logical_and(A<?thr?,B>?thr?)+(A-?thr?)/(A-B+0.000000001)*logical_and(A>?thr?,B<?thr?)' \
                          '+logical_and(A>=?thr?,B>=?thr?))*?days?'

        equation = daycalcequation.replace("?thr?", str(threshold))
        equation = equation.replace("?days?", str(daysbetween))
        feedback.pushDebugInfo("equation: " + str(equation))
        # Raster calculator
        alg_params = {
            'BAND_A': 1,
            'BAND_B': 1,
            'BAND_C': 1,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': equation,
            'INPUT_A': raster1,
            'INPUT_B': raster2,
            'INPUT_C': sumraster,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': None,
            'OPTIONS': '',
            'RTYPE': 5,
            'OUTPUT': sumraster
        }
        return processing.run('gdal:rastercalculator', alg_params, context=context,
                                                     feedback=feedback, is_child_algorithm=True)

    def tr(self, string):
        return QCoreApplication.translate('Analyze', string)

    def name(self):
        return 'CountDaysOverLimit'

    def displayName(self):
        return self.tr('Count of days raster values over limit.')

    def group(self):
        return self.tr('Raster analysis')

    def groupId(self):
        return 'Analyze'

    def shortHelpString(self):
        return self.tr('Multi-temporal analysis\n\nCalculates the number of days on a time series of raster images where the values are above the given threshold.'
                       'e.g. NDVI index above 0.6')
    def createInstance(self):
        return CountDaysOverLimit()
