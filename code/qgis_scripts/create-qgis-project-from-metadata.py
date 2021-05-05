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
                       QgsProcessingException,QgsStyle,QgsMarkerSymbol,QgsRendererCategory,QgsProject,QgsApplication,
                       QgsProcessingAlgorithm,QgsCategorizedSymbolRenderer,QgsSizeScaleTransformer,QgsProperty,
                       QgsProcessingParameterFile,QgsProcessingContext,QgsProcessingOutputMultipleLayers,QgsCoordinateReferenceSystem,
                       QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY)
from qgis import processing
import json,os

class ProjectFromCyclemonMetadata(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    FOLDER = 'FOLDER'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ProjectFromCyclemonMetadata()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'newprojectfromcyclemonmetadata'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Create QGIS Project from Cyclemon Metadata')

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
            QgsProcessingParameterFile(self.FOLDER, self.tr("Input and output folder"), behavior=QgsProcessingParameterFile.Folder)
        )
        self.addOutput(
            QgsProcessingOutputMultipleLayers(self.OUTPUT)
        )

    def processAlgorithm(self, parameters, context, feedback):
        project = QgsProject()
        project.setFileName(os.path.join(parameters[self.FOLDER],"all-outputs-qgis.qgs"))
        project.setCrs(QgsCoordinateReferenceSystem('EPSG:27700'))
        
        def getMaxValue(layer,fieldname):
            maxfound = float("-inf")
            for f in layer.getFeatures():
                attr = f.attribute(fieldname)
                assert attr>=0
                if attr>maxfound:
                    maxfound=attr
            return maxfound
        
        with open(os.path.join(parameters[self.FOLDER],"all-town-metadata.json")) as f:
            metadata = json.load(f)
        
        classmethods = {'quantile':QgsClassificationQuantile,'jenks':QgsClassificationJenks,'equal':QgsClassificationEqualInterval}
        
        html = ""
        output = []
        views_sorted_by_mode = sorted(metadata["views"],key=lambda v:v["mode"])
        for view in views_sorted_by_mode:
            keysymbol = u'ðŸ”‘'
            viewname = view["label"]
            keysign = ""
            if viewname.find(keysymbol)!=-1:
                viewname =  viewname.replace(keysymbol,'',1)
                keysign = "*** "
            viewname = keysign+view["mode"]+" "+viewname
            
            html += f"""
                    <h2>{viewname}</h2>
                    {view["description"]}
                    <ul>
                    """
            for layer in view["layers"]:
                layername = viewname+" - "+layer["scalar_field_units"]
                
                layerpath = os.path.join(parameters[self.FOLDER],layer["file"])
                vlayer = QgsVectorLayer(layerpath, layername, "ogr")
                if not vlayer.isValid():
                    feedback.pushInfo("Layer failed to load: "+layerpath)
                else:                    
                    context.temporaryLayerStore().addMapLayer(vlayer)
                    html+=f"""<li><b>file:</b> {layer["file"]}"""
                    if "symbol_field" in layer:
                        html+=f"""<ul>
                                    <li><b>symbol field:</b> {layer["symbol_field"]}
                                  </ul>
                                """
                        categories = []
                        scalar_fieldname = layer["scalar_field"]
                        maxvalue=getMaxValue(vlayer,scalar_fieldname)
                        feedback.pushInfo("Max value for %s is %f"%(scalar_fieldname,maxvalue))
                        for formality in ["I","F"]:
                            for severity,colour in [(3,'red'),(2,'yellow'),(1,'green')]:
                                colour = {("I","red"):"#FF0000",("I","yellow"):"#FFFF00",("I","green"):"#00FF00",
                                            ("F","red"):"#FF9999",("F","yellow"):"#FFFF66",("F","green"):"#99FF99",
                                            }[(formality,colour)]
                                symbol_code = "%s%d"%(formality,severity)
                                if formality=="F":
                                    symbol = QgsMarkerSymbol.createSimple({'color': colour, 'size': '3', 'outline_color': '#888888'})
                                else:
                                    assert(formality=="I")
                                    symbol = QgsMarkerSymbol.createSimple({'color': colour, 'size': '3', 'outline_color': '#000000', 'name' : 'star'})
                                
                                objTransf = QgsSizeScaleTransformer(
                                    QgsSizeScaleTransformer.Flannery,
                                    0, #minvalue
                                    maxvalue, #maxvalue
                                    3, #minsize
                                    10, #maxsize
                                    0, #nullsize
                                    1) #exponent
                                objProp = QgsProperty()
                                objProp.setField(scalar_fieldname)
                                objProp.setTransformer(objTransf)
                                symbol.setDataDefinedSize(objProp)
                                label = {"F":"Formal","I":"Informal"}[formality]+" "+{3:"Major",2:"Secondary",1:"Tertiary"}[severity]
                                cat = QgsRendererCategory(symbol_code,symbol,label,True)
                                categories.append(cat)
                        renderer = QgsCategorizedSymbolRenderer("Crossings", categories)
                        renderer.setClassAttribute(layer["symbol_field"])
                        vlayer.setRenderer(renderer)
                    else:
                        html+=f"""<ul>
                                    <li><b>field:</b> {layer["scalar_field"]}
                                    <li><b>units:</b> {layer["scalar_field_units"]}
                                    <li><b>recommended classification:</b> {layer["classes"]}
                                  </ul>
                                """
                        default_style = QgsStyle().defaultStyle()
                        color_ramp = default_style.colorRamp('bt')
                        renderer = QgsGraduatedSymbolRenderer()
                        renderer.setClassAttribute(layer["scalar_field"])
                        classmethod = classmethods[layer["classes"]]()
                        renderer.setClassificationMethod(classmethod)
                        renderer.updateClasses(vlayer, 5)
                        renderer.updateColorRamp(color_ramp)
                        vlayer.setRenderer(renderer)
                    
                    project.addMapLayer(vlayer)
                    feedback.pushInfo("Loaded "+layerpath)
            html+="</ul>"
                    
        project.write()
        town = views_sorted_by_mode[0]["town"]
        with open(os.path.join(parameters[self.FOLDER],"metadata.html"),"w") as htmlfile:
            htmlfile.write(f"<html><head><title>{town} metadata</title></head><body><h1>{town}</h1>{html}</body></html>")
        return {self.OUTPUT: output}