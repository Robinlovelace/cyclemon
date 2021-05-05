# -*- coding: utf-8 -*-

"""
    Sidewalker - autogeneration of sidewalk network from road network
    Copyright (C) 2021 Crispin Cooper

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from qgis.PyQt.QtCore import *

from qgis.core import (QgsProcessing,QgsVectorLayer,QgsProject,QgsClassificationQuantile,QgsClassificationEqualInterval,QgsClassificationJenks,QgsGraduatedSymbolRenderer,
                       QgsProcessingException,QgsStyle,QgsMarkerSymbol,QgsRendererCategory,QgsProject,QgsApplication,QgsLineSymbol,QgsSingleSymbolRenderer,
                       QgsProcessingAlgorithm,QgsCategorizedSymbolRenderer,QgsSizeScaleTransformer,QgsProperty,QgsProcessingParameterField,
                       QgsProcessingParameterFile,QgsProcessingContext,QgsProcessingOutputMultipleLayers,QgsCoordinateReferenceSystem,
                       QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY)
from qgis import processing
import json,os

class WalkSummaryForCyclemon(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    FOLDER = 'FOLDER'
    OUTPUT = 'OUTPUT'
    ALLFLOWSSHP = "ALLFLOWSSHP"
    ALLFLOWSFIELD = "ALLFLOWSFIELD"
    ALLCROSSINGSSHP = "ALLCROSSINGSSHP"
    DESTCROSSINGSSHP = "DESTCROSSINGSSHP"
    DESTFLOWSSHP = "DESTFLOWSSHP"
    DESTFLOWSFIELD = "DESTFLOWSFIELD"
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return WalkSummaryForCyclemon()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'walksummaryproject'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Create QGIS Walk Summary Project for Cyclemon')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Active Travel Tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'scripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(self.FOLDER, self.tr("Output folder"), behavior=QgsProcessingParameterFile.Folder)
        )
        self.addParameter(
            QgsProcessingParameterFile(self.ALLFLOWSSHP, self.tr("shapefile for all flows"), behavior=QgsProcessingParameterFile.File)
        )
        self.addParameter(
            QgsProcessingParameterFile(self.ALLCROSSINGSSHP, self.tr("shapefile for all crossings"), behavior=QgsProcessingParameterFile.File)
        )
        self.addParameter(
            QgsProcessingParameterFile(self.DESTFLOWSSHP, self.tr("shapefile for destination flows"), behavior=QgsProcessingParameterFile.File)
        )
        self.addParameter(
            QgsProcessingParameterFile(self.DESTCROSSINGSSHP, self.tr("shapefile for destination crossings"), behavior=QgsProcessingParameterFile.File)
        )
        self.addParameter(
            QgsProcessingParameterField(self.ALLFLOWSFIELD,self.tr("All flows field"))
        )
        self.addParameter(
            QgsProcessingParameterField(self.DESTFLOWSFIELD,self.tr("Destination flows field"))
        )
        self.addOutput(
            QgsProcessingOutputMultipleLayers(self.OUTPUT)
        )

    def processAlgorithm(self, parameters, context, feedback):
        project = QgsProject()
        project.setFileName(os.path.join(parameters[self.FOLDER],"summary-walk-qgis.qgs"))
        project.setCrs(QgsCoordinateReferenceSystem('EPSG:27700'))
        
        def getMaxValue(layer,fieldname):
            maxfound = float("-inf")
            for f in layer.getFeatures():
                attr = f.attribute(fieldname)
                assert attr>=0
                if attr>maxfound:
                    maxfound=attr
            return maxfound
        
        def addFlowLayerLineWidth(layerpath,fieldname,colour,transparent,layername,widthscale=1):
            vlayer = QgsVectorLayer(layerpath, layername, "ogr")
            if not vlayer.isValid():
                feedback.pushInfo("Layer failed to load: "+layerpath)
            else:                    
                context.temporaryLayerStore().addMapLayer(vlayer)
                
                maxvalue=getMaxValue(vlayer,fieldname)
                
                symbol = QgsLineSymbol.createSimple({'color':colour,'size':'1'})
                objTransf = QgsSizeScaleTransformer(
                                    QgsSizeScaleTransformer.Flannery,
                                    0, #minvalue
                                    maxvalue, #maxvalue
                                    0.1, #minsize
                                    5*widthscale, #maxsize
                                    0, #nullsize
                                    1) #exponent
                objProp = QgsProperty()
                objProp.setField(fieldname)
                objProp.setTransformer(objTransf)
                symbol.setDataDefinedWidth(objProp)
            
                renderer = QgsSingleSymbolRenderer(symbol)
                vlayer.setRenderer(renderer)
                vlayer.setOpacity(1-transparent)
                
                project.addMapLayer(vlayer)
                feedback.pushInfo("Loaded "+layerpath)
                    
        def addCrossingsLayerSeveritySize(layerpath,colour,transparent,layername):
                vlayer = QgsVectorLayer(layerpath, layername, "ogr")
                if not vlayer.isValid():
                    feedback.pushInfo("Layer failed to load: "+layerpath)
                else:                    
                    context.temporaryLayerStore().addMapLayer(vlayer)
            
                    categories = []
                    for formality in ["I","F"]:
                        for severity,size in [(3,8),(2,6),(1,4)]:
                            symbol_code = "%s%d"%(formality,severity)
                            if formality=="F":
                                symbol = QgsMarkerSymbol.createSimple({'color': colour, 'size': str(size), 'outline_color': '#888888'})
                            else:
                                assert(formality=="I")
                                symbol = QgsMarkerSymbol.createSimple({'color': colour, 'size': str(size), 'outline_color': '#000000', 'name' : 'star'})
                            
                            label = {"F":"Formal","I":"Informal"}[formality]+" "+{3:"Major",2:"Secondary",1:"Tertiary"}[severity]
                            cat = QgsRendererCategory(symbol_code,symbol,label,True)
                            categories.append(cat)
                    renderer = QgsCategorizedSymbolRenderer("Crossings", categories)
                    renderer.setClassAttribute("symbol")
                    vlayer.setRenderer(renderer)
                    vlayer.setOpacity(1-transparent)
                    
                    project.addMapLayer(vlayer)
                    feedback.pushInfo("Loaded "+layerpath)

        addFlowLayerLineWidth(parameters[self.DESTFLOWSSHP],parameters[self.DESTFLOWSFIELD],"red",0,"School walking flows (pupils)",widthscale=0.5)
        addFlowLayerLineWidth(parameters[self.ALLFLOWSSHP],parameters[self.ALLFLOWSFIELD],"blue",0.65,"All walking flows (relative)")
        addCrossingsLayerSeveritySize(parameters[self.DESTCROSSINGSSHP],"red",0,"School crossings")
        addCrossingsLayerSeveritySize(parameters[self.ALLCROSSINGSSHP],"blue",0.65,"All crossings")
        
        project.write()
        return {}