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

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY)
from qgis import processing
import numpy as np
from collections import defaultdict,namedtuple
from itertools import combinations

class Sidewalker(QgsProcessingAlgorithm):
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    SIDEWALK_FIELD_NAME = "SdWlkrT"
    SIDEWALK_FIELD_LEFT = "l"
    SIDEWALK_FIELD_RIGHT = "r"
    SIDEWALK_FIELD_CROSSING = "x"
    SIDEWALK_FIELD_FORMAL_CROSSING = "X"
    SIDEWALK_FIELD_JUNCTION = "j"
    SIDEWALK_FIELD_BUFFER = "b"
    SIDEWALK_FIELD_NONE = ""
    
    SIDEWALK_METRIC_FIELD_NAME = "SdWlkrM"
    
    SIDEWALK_WEIGHT_FIELD_NAME = "SdWlkrWt"
    
    ID_FIELD_NAME = "fidnew"
    
    CROSSING_INPUT_FIELD_PREFIX = "X"
    
    INPUT = 'INPUT'
    INPUT_POINTS = 'INPUT_POINTS'
    OUTPUT = 'OUTPUT'
    ERROR_OUTPUT = 'ERROR_OUTPUT'
    
    DIVIDE_FIELDNAME = 'divide'
    

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Sidewalker()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'sidewalker'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Sidewalker')

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
        return self.tr("Automate sidewalk generation from road network")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input network lines'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                self.tr('Input crossing points'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ERROR_OUTPUT,
                self.tr('Error layer')
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        # Constants (probably parameters in future)
        JUNCTION_WIDTH = 4
        ROAD_WIDTH = 1
        CLUSTER_THRESHOLD = 1
        LOOP_LINK_THRESHOLD = 2.5 # should be min. 2 as loops can cross junction and back
        CIRCLE_APPROX_SEGMENTS = 16
        OUTPUT_DEBUG_NODE_BUFFERS = False
        POINT_ERROR_BUFFER_RADIUS = 10
    
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        crossing_source = self.parameterAsSource(
            parameters,
            self.INPUT_POINTS,
            context
        )
        
        crossing_fields = []
        crossing_points_to_features = {}
        if crossing_source is not None:
            crossing_fields = [QgsField(f) for f in crossing_source.fields()]
            for cf in crossing_fields:
                cf.setName(self.CROSSING_INPUT_FIELD_PREFIX+cf.name())
            feedback.pushInfo("Reading crossings")
            total = 100.0 / crossing_source.featureCount() if crossing_source.featureCount() else 0
            features = crossing_source.getFeatures()
            for current, in_feature in enumerate(features):
                if feedback.isCanceled():
                    break
                
                geom = in_feature.geometry()
                if not geom.convertToSingleType():
                    feedback.pushInfo("Error: Multipoint found in crossings layer")
                    raise Exception("Multipoint found in crossings layer")
                    
                crossing_points_to_features[geom.asPoint()]=in_feature
                feedback.setProgress(int(current * total))

        outfields = QgsFields()
        for f in source.fields():
            outfields.append(f)
        for f in crossing_fields:
            outfields.append(f)
        outfields.append(QgsField(self.SIDEWALK_FIELD_NAME,QVariant.String, len=1)) 
        outfields.append(QgsField(self.SIDEWALK_METRIC_FIELD_NAME,QVariant.Double,"double",10,3))
        outfields.append(QgsField(self.SIDEWALK_WEIGHT_FIELD_NAME,QVariant.Double,"double",10,3))
        outfields.append(QgsField(self.ID_FIELD_NAME,QVariant.Int))
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            outfields,
            source.wkbType(),
            source.sourceCrs()
        )

        errfields = QgsFields()
        errfields.append(QgsField("Error",QVariant.String))
        errfields.append(QgsField("Details",QVariant.String))
            
        (err_sink, err_dest_id) = self.parameterAsSink(
            parameters,
            self.ERROR_OUTPUT,
            context,
            errfields,
            source.wkbType(),
            source.sourceCrs()
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        if err_sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.ERROR_OUTPUT))

        
        def add_error(feature,message,details=""):
            if OUTPUT_DEBUG_NODE_BUFFERS:
                feedback.pushInfo(f"{message}{details}: {feature}")
            new_feature =  QgsFeature()
            new_feature.setGeometry(feature.geometry()) 
            new_feature.setAttributes([message,details])
            err_sink.addFeature(new_feature,QgsFeatureSink.FastInsert)
        
        def add_point_error(point,message,details=""):
            buffer = QgsGeometry.fromPointXY(point).buffer(POINT_ERROR_BUFFER_RADIUS,CIRCLE_APPROX_SEGMENTS)
            feature = QgsFeature()
            feature.setGeometry(buffer)
            add_error(feature,message,details)
        
        START,END = False,True
        LinkEnd = namedtuple("LinkEnd",["id","end"])
        def linkend_to_point(linkend):
            line = link_id_to_feature[linkend.id].geometry().asPolyline()
            return line[0] if linkend.end == START else line[-1]
                
        node_coords_to_link_ends = defaultdict(list) #(x,y ) as index, list of original link ends as contents
        link_id_to_feature = {} # link id (tuple of (number,type)) for index, feature as contents
        loop_link_ids = set()
        
        LINK_TYPE_ORIGINAL,LINK_TYPE_LEFT,LINK_TYPE_RIGHT,LINK_TYPE_OTHER,LINK_TYPE_BUFFER = list(range(5))
        
        feedback.pushInfo("Reading links and building node graph")
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        for current, in_feature in enumerate(features):
            if feedback.isCanceled():
                break
            
            geom = in_feature.geometry()
            if not geom.convertToSingleType():
                add_error(feature,"Multipart line")
                continue
            
            feature = QgsFeature()
            feature.setFields(outfields)
            for name in in_feature.fields().names():
                feature.setAttribute(name,in_feature.attribute(name))
            feature.setGeometry(geom)
            
            points = geom.asPolyline()
            linkid = (current,LINK_TYPE_ORIGINAL)
            link_id_to_feature[linkid] = feature
            endpoints = [(START,points[0]),(END,points[-1])]
            if points[0]==points[-1]:
                loop_link_ids.add(current)
            for end,point in endpoints:
                le = LinkEnd(linkid,end)
                node_coords_to_link_ends[point] += [le]
            
            feedback.setProgress(int(current * total))
        
        next_index_for_split_link_id = current + 1

        def break_link_on_first_crossing_found(link_id): 
            nonlocal next_index_for_split_link_id,node_coords_to_link_ends,link_id_to_feature,outfields,loop_link_ids
            feature = link_id_to_feature[link_id]
            geom = feature.geometry()
            points = geom.asPolyline()
            for point in points[1:-1]:
                if point in crossing_points_to_features:
                    # break line, splitting extra part to new feature
                    index = points.index(point)
                    points1 = points[0:index+1]
                    points2 = points[index:]
                    feature.setGeometry(QgsGeometry.fromPolylineXY(points1))
                    newfeature = QgsFeature()
                    newfeature.setFields(outfields)
                    newfeature.setAttributes(feature.attributes())
                    newfeature.setGeometry(QgsGeometry.fromPolylineXY(points2))
                    new_feature_id = (next_index_for_split_link_id,LINK_TYPE_ORIGINAL)
                    next_index_for_split_link_id += 1
                    link_id_to_feature[new_feature_id] = newfeature
                    # update node_coords_link_ends for the split point and end point (start point remains the same)
                    if point in node_coords_to_link_ends:
                        add_point_error(point,"Crossing on both link and node is ambiguous")
                    node_coords_to_link_ends[point] += [LinkEnd(link_id,END),LinkEnd(new_feature_id,START)]
                    end_link_end_list = node_coords_to_link_ends[points[-1]]
                    end_link_end_list.remove(LinkEnd(link_id,END))
                    end_link_end_list += [LinkEnd(new_feature_id,END)]
                    if link_id[0] in loop_link_ids:
                        loop_link_ids.remove(link_id[0])
                    if points1[0]==points1[-1]:
                        loop_link_ids.add(new_feature_id[0])
                    
                    for f in [feature,newfeature]:
                        if point in feature.geometry().asPolyline()[1:-1]:
                            add_error(feature,"Crossing intersects at multiple points")
                            
                    return new_feature_id
                
            return False
        
        feedback.pushInfo("Splitting links with crossings inside")
        total = 100.0 / len(link_id_to_feature) if len(link_id_to_feature) else 0
        for current, link_id in enumerate(list(link_id_to_feature.keys())): # copy the keys
            if feedback.isCanceled():
                break
            
            link_id_to_try_splitting = link_id
            while link_id_to_try_splitting:
                link_id_to_try_splitting = break_link_on_first_crossing_found(link_id_to_try_splitting)

            feedback.setProgress(int(current * total))
        
        feedback.pushInfo("Matching crossings to link ends")
        linkend_to_crossing_feature = {}
        crossing_points_matched = set()
        total = 100.0 / len(link_id_to_feature) if len(link_id_to_feature) else 0
        for current, (link_id,feature) in enumerate(link_id_to_feature.items()):
            if feedback.isCanceled():
                break
            
            points = feature.geometry().asPolyline()
            endpoints = [(START,points[0]),(END,points[-1])]
            for end,point in endpoints:
                if point in crossing_points_to_features:
                    crossing_points_matched.add(point)
                    linkend_to_crossing_feature[LinkEnd(link_id,end)] = crossing_points_to_features[point]
                    
            feedback.setProgress(int(current * total))
        
        for point in crossing_points_to_features:
            if point not in crossing_points_matched:
                add_point_error(point,"Unmatched crossing")
        
        feedback.pushInfo("Testing node distances")
        total = 100.0 / len(node_coords_to_link_ends) if len(node_coords_to_link_ends) else 0
        node_neighbours = defaultdict(list)
        for current,n1 in enumerate(node_coords_to_link_ends.keys()):
            if feedback.isCanceled():
                break
                
            for n2 in node_coords_to_link_ends.keys():
                if n1.distance(n2) <= JUNCTION_WIDTH*CLUSTER_THRESHOLD:
                    node_neighbours[n1] += [n2]
                    node_neighbours[n2] += [n1]
                    
            feedback.setProgress(int(current * total))
        
        feedback.pushInfo("Computing node clusters")
        node_clusters = []
        while node_neighbours:
            node,searchlist = node_neighbours.popitem()
            cluster = set()
            cluster.add(node)
            while searchlist:
                node = searchlist.pop()
                if node in node_neighbours: 
                    neighbours = node_neighbours.pop(node)
                    for n in neighbours:
                        if n not in cluster:
                            cluster.add(n)
                            searchlist += [n]
            node_clusters += [cluster]
        
        feedback.pushInfo("Merging node clusters")
        
        def get_node_buffer(point):
            return QgsGeometry.fromPointXY(point).buffer(JUNCTION_WIDTH/2,CIRCLE_APPROX_SEGMENTS) 
            
        old_to_new_node_points = {}
        linkends_that_got_nodes_moved = set()
        total = 100.0 / len(node_clusters) if len(node_clusters) else 0
        for current,cluster in enumerate(node_clusters):
            if feedback.isCanceled():
                break
            
            cluster_arr = np.array([[p.x(),p.y()] for p in cluster]) 
            if (cluster_arr[0]==cluster_arr[1:]).all():
                continue # these links already share the same endpoints
            newx,newy = np.mean(cluster_arr,axis=0)
            new_node_point = QgsPointXY(newx,newy)
            cluster_linkends = []
            for node in cluster:
                assert node in node_coords_to_link_ends
                cluster_linkends += node_coords_to_link_ends[node]
                del node_coords_to_link_ends[node]
                old_to_new_node_points[node]=new_node_point
            
            # stretch the links to meet the new cluster
            for linkend in cluster_linkends:
                feature = link_id_to_feature[linkend.id]
                points = feature.geometry().asPolyline()
                if linkend.end==START:
                    points.insert(0,new_node_point)
                else:
                    assert linkend.end==END
                    points.append(new_node_point)
                feature.setGeometry(QgsGeometry.fromPolylineXY(points))
            
            for le in cluster_linkends:
                linkends_that_got_nodes_moved.add(le)
            
            # delete any links 
            # (a) wholly inside the cluster 
            # (b) with both ends in the cluster unless they're (1) originally loop links or (2) long loop links not present originally, in which case warn
            links_to_delete = []
            for le1,le2 in combinations(cluster_linkends,2):
                if le1.id==le2.id:
                    geom = link_id_to_feature[le1.id].geometry()
                    assert le1.end != le2.end
                    node_buffer = get_node_buffer(new_node_point)
                    trimmed_linkgeom = geom.difference(node_buffer)
                    if trimmed_linkgeom.isEmpty():
                        links_to_delete += [le1.id]
                    elif le1.id[0] not in loop_link_ids:
                        if geom.length() < LOOP_LINK_THRESHOLD*CLUSTER_THRESHOLD*JUNCTION_WIDTH:
                            links_to_delete += [le1.id]
                        else:
                            add_error(link_id_to_feature[le1.id],"Loop link formed by node merge",f"{le1}")
                            loop_link_ids.add(le1.id[0])
            for link in links_to_delete:
                for end in [START,END]:
                    cluster_linkends.remove(LinkEnd(link,end))
                assert all([le.id!=link for le in cluster_linkends])
                del link_id_to_feature[link]
            
            node_coords_to_link_ends[new_node_point] = cluster_linkends
                
            feedback.setProgress(int(current * total))
        
        feedback.pushInfo("Computing radial orderings")
        node_link_ordering = {}
        total = 100.0 / len(node_coords_to_link_ends) if len(node_coords_to_link_ends) else 0
        for current,node_point in enumerate(node_coords_to_link_ends):
            if feedback.isCanceled():
                break
            
            link_end_list = node_coords_to_link_ends[node_point]
            
            node_buffer = get_node_buffer(node_point)
            
            bearing_and_link_end_pairs_list = []
            for le in link_end_list:
                link = link_id_to_feature[le.id]
                linkgeom = link.geometry()
                trimmed_linkgeom = linkgeom.difference(node_buffer)
                if trimmed_linkgeom.isMultipart():
                        trimmed_linkgeom = QgsGeometry.fromPolyline(list(trimmed_linkgeom.constParts())[0]) # this may be wrong but the error is flagged up later
                pl = trimmed_linkgeom.asPolyline()
                endpoint_near_node = pl[0] if le.end==START else pl[-1]
                bearing_and_link_end_pairs_list += [(node_point.azimuth(endpoint_near_node),le)]
                    
            bearing_and_link_end_pairs_list.sort()
            node_link_ordering[node_point] = bearing_and_link_end_pairs_list
        
        feedback.pushInfo("Dividing links")
        nodes_of_divided_links = set()
        divided_linkends = {}
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        link_ids_to_process = list(link_id_to_feature.keys())
        for current, orig_id in enumerate(link_ids_to_process): 
            if feedback.isCanceled():
                break
            
            feature = link_id_to_feature[orig_id]
            if feature.attribute(self.DIVIDE_FIELDNAME):
                left,right = self.divide(feature,ROAD_WIDTH/2,outfields)
                # these tuple ids are used later to identify that left and right originated from the same feature
                orig_index,_ = orig_id
                left_id = (orig_index,LINK_TYPE_LEFT)
                right_id = (orig_index,LINK_TYPE_RIGHT)
                del link_id_to_feature[orig_id]
                link_id_to_feature[left_id] = left
                link_id_to_feature[right_id] = right
                points = feature.geometry().asPolyline()
                endpoints = [(START,points[0]),(END,points[-1])]
                for end,point in endpoints:
                    if not point in node_coords_to_link_ends:
                        point = old_to_new_node_points[point]
                    assert point in node_coords_to_link_ends
                    node_link_end_list = node_coords_to_link_ends[point] 
                    node_link_end_list.remove(LinkEnd(orig_id,end))
                    node_link_end_list += [LinkEnd(left_id,end),LinkEnd(right_id,end)]
                    nodes_of_divided_links.add(point)
                    divided_linkends[LinkEnd(orig_id,end)]=[LinkEnd(left_id,end),LinkEnd(right_id,end)]
            else:
                feature.setAttribute(self.SIDEWALK_FIELD_NAME,self.SIDEWALK_FIELD_NONE)

            feedback.setProgress(int(current * total))
            
        def left_right_pair(type1,type2):
            return (type1==LINK_TYPE_LEFT and type2==LINK_TYPE_RIGHT) or (type1==LINK_TYPE_RIGHT and type2==LINK_TYPE_LEFT)
        def over_180_degrees(b1,b2):
            return (b2-b1)%360 > 180
        def count_backtracks(bleplist):
            bleplist = bleplist.copy()
            backtracks = 0
            bleplist += [bleplist[0]]
            for ((b1,_),(b2,_)) in zip(bleplist[0:-1],bleplist[1:]):
                if over_180_degrees(b1,b2):
                    backtracks += 1
            return backtracks    
            
        feedback.pushInfo("Generating crossings and junction links")
        total = 100.0 / len(nodes_of_divided_links) if len(nodes_of_divided_links) else 0
        next_new_link_index = 0
        links_we_deleted_in_intersection = set()
        for current,node_point in enumerate(nodes_of_divided_links):
            if feedback.isCanceled():
                break
            
            link_end_list = node_coords_to_link_ends[node_point]
            
            if len(link_end_list)==1:
                continue # don't trim ends off path cul-de-sacs
            if len(link_end_list)==2:
                ((id1,type1),end1),((id2,type2),end2)=link_end_list
                if id1==id2:
                    assert left_right_pair(type1,type2)
                    continue # don't trim ends off divided cul-de-sacs
            
            # from here on we no longer need to update node_coords_to_link_ends except to check for intersections outside nodes
            # - it becomes invalid but link_id_to_feature contains the result
            # - and for the intersection outside node check we remove deleted links during that check

            node_buffer = get_node_buffer(node_point)
            
            # report intersections with buffer that aren't part of node
            for id,link in link_id_to_feature.items():
                if link.geometry().intersects(node_buffer) and all([le.id!=id for le in link_end_list]):
                    add_error(link,"Link intersects unrelated junction")
            
            # trim joining links 
            links_already_trimmed = set()
            
            for le in link_end_list:
                if not le.id in link_id_to_feature:
                    assert le.id in links_we_deleted_in_intersection
                    continue
                link = link_id_to_feature[le.id]
                linkgeom = link.geometry()
                inter = node_buffer.intersection(linkgeom)
                if inter.constGet().partCount() > 0:
                    trimmed_linkgeom = linkgeom.difference(node_buffer)
                    if trimmed_linkgeom.isMultipart():
                        add_error(link,"Link intersects junction more than once")
                        feedback.pushInfo(f"Link {le} intersects junction {node_point} more than once")
                        trimmed_linkgeom = QgsGeometry.fromPolyline(list(trimmed_linkgeom.constParts())[0])
                    if trimmed_linkgeom.isEmpty():
                        add_error(link,"Divided link half fully within junction buffer",f"{le.id}") #above**
                        del link_id_to_feature[le.id]
                        links_we_deleted_in_intersection.add(le.id)
                    else:
                        link.setGeometry(trimmed_linkgeom)
                        links_already_trimmed.add(le.id)
                else:
                    if not (le.id in links_already_trimmed and le.id[0] in loop_link_ids):
                        if LinkEnd((le.id[0],LINK_TYPE_ORIGINAL),le.end) in linkends_that_got_nodes_moved:
                            add_error(link,"Link does not intersect its own junction buffer")
                        else:
                            add_error(link,"Link does not intersect its own UNMERGED junction buffer")
                    
            old_bearing_and_link_end_pairs_list = node_link_ordering[node_point]
            
            bearing_and_link_end_pairs_list = []
            # update bearing_and_link_end_pairs_list by inserting divided halves where needed
            for ob,le in old_bearing_and_link_end_pairs_list:
                if le in divided_linkends:
                    divided_linkend_pair = divided_linkends[le]
                    assert len(divided_linkend_pair)==2
                    linkends_from_this_division = [x for x in divided_linkend_pair if x.id in link_id_to_feature] # filter out halves we deleted already
                    bearing_link_end_pairs_from_this_division = [(node_point.azimuth(linkend_to_point(le)),le) for le in linkends_from_this_division]
                    if len(bearing_link_end_pairs_from_this_division)==2:
                        # if both halves still present, order correctly
                        (b1,_),(b2,_) = bearing_link_end_pairs_from_this_division
                        if over_180_degrees(b1,b2):
                            bearing_link_end_pairs_from_this_division.reverse()
                    # if one or both halves are missing, this is probably an error state, but we report it above**
                    bearing_and_link_end_pairs_list += bearing_link_end_pairs_from_this_division
                else:
                    bearing_and_link_end_pairs_list += [(ob,le)]  
            
            # test for backtracks - if more backtracks in bearing_and_link_end_pairs_list than sorted bearing_and_link_end_pairs_list
            if count_backtracks(bearing_and_link_end_pairs_list)>count_backtracks(sorted(bearing_and_link_end_pairs_list)):
                f = QgsFeature()
                f.setGeometry(node_buffer)
                add_error(f,"Junction/crossing link backtrack")
            
            # iterate pairwise around circle, repeating first element, to add crossings SIDEWALK_FIELD_CROSSING SIDEWALK_FIELD_JUNCTION
            bearing_and_link_end_pairs_list += [bearing_and_link_end_pairs_list[0]] 
            for ((b1,le1),(b2,le2)) in zip(bearing_and_link_end_pairs_list[0:-1],bearing_and_link_end_pairs_list[1:]):
                
                startpoint,endpoint = [linkend_to_point(le) for le in [le1,le2]]
                if startpoint==endpoint:
                    error="Endpoints already match when adding crossings/junction links"
                    add_error(link_id_to_feature[le1.id],error)
                    add_error(link_id_to_feature[le2.id],error)
                    
                geom = QgsGeometry.fromPolylineXY([startpoint,endpoint])
                feature = QgsFeature()
                feature.setGeometry(geom)
                feature.setFields(outfields)

                id1,type1 = le1.id
                id2,type2 = le2.id
                if id1==id2 and left_right_pair(type1,type2):
                    crossed_road = link_id_to_feature[le1.id]
                    for name in crossed_road.fields().names():
                        feature.setAttribute(name,crossed_road.attribute(name)) # some to be overwritten below
                    assert le1.end==le2.end
                    crossed_road_orig_id = (le1.id[0],LINK_TYPE_ORIGINAL)
                    crossed_road_orig_linkend = LinkEnd(crossed_road_orig_id,le1.end)
                    if crossed_road_orig_linkend in linkend_to_crossing_feature:
                        feature.setAttribute(self.SIDEWALK_FIELD_NAME,self.SIDEWALK_FIELD_FORMAL_CROSSING)
                        formal_crossing_feature = linkend_to_crossing_feature[crossed_road_orig_linkend]
                        for name in formal_crossing_feature.fields().names():
                            feature.setAttribute(self.CROSSING_INPUT_FIELD_PREFIX+name,formal_crossing_feature.attribute(name))
                        feature.setAttribute("pednet",1) # formal crossings of non pedesetrian roads are allowed
                    else:
                        feature.setAttribute(self.SIDEWALK_FIELD_NAME,self.SIDEWALK_FIELD_CROSSING)

                else:
                    feature.setAttribute(self.SIDEWALK_FIELD_NAME,self.SIDEWALK_FIELD_JUNCTION)
                    feature.setAttribute("pednet",1) # junction links always allowed
                    if id1==id2 and id1 not in loop_link_ids: 
                        error="Matching ids are not left/right pair or loop link"
                        add_error(link_id_to_feature[le1.id],error)
                        add_error(link_id_to_feature[le2.id],error)
                
                new_link_id = (next_new_link_index,LINK_TYPE_OTHER)
                next_new_link_index += 1
                link_id_to_feature[new_link_id] = feature
            
            if OUTPUT_DEBUG_NODE_BUFFERS:
                feature = QgsFeature()
                feature.setGeometry(node_buffer)
                feature.setFields(outfields)
                feature.setAttribute(self.SIDEWALK_FIELD_NAME,self.SIDEWALK_FIELD_BUFFER)
                new_link_id = (next_new_link_index,LINK_TYPE_BUFFER)
                next_new_link_index += 1
                link_id_to_feature[new_link_id] = feature
            
            feedback.setProgress(int(current * total))
        
        feedback.pushInfo("Checking for link intersections outside nodes")
        total = 100.0 / len(nodes_of_divided_links) if len(nodes_of_divided_links) else 0
        next_new_link_index = 0
        for current,node_point in enumerate(nodes_of_divided_links):
            if feedback.isCanceled():
                break
            
            link_end_list = [le for le in node_coords_to_link_ends[node_point] if le.id in link_id_to_feature] # remove what we deleted before check
            
            for le1,le2 in combinations(link_end_list,2):
                if le1.id!=le2.id:
                    feature1,feature2 = [link_id_to_feature[le.id] for le in [le1,le2]]
                    if feature1.geometry().intersects(feature2.geometry()):
                        message = "Intersection of links outside junction"
                        details = "{!r}{!r}".format(le1,le2)
                        add_error(feature1,message,details)
                        add_error(feature2,message,details)
        
        feedback.pushInfo("Computing sidewalker metric and writing output")
        total = 100.0 / len(link_id_to_feature) if len(link_id_to_feature) else 0
        for current,link in enumerate(link_id_to_feature.values()):
            if feedback.isCanceled():
                break
            
            length = link.geometry().length()
            extra_length = 0
            crossed_road_deterrence = link.attribute("cyclist_de")
            if link.attribute(self.SIDEWALK_FIELD_NAME)==self.SIDEWALK_FIELD_CROSSING:
                if crossed_road_deterrence >= 260: # picks up tertiary, secondary
                    extra_length = 191
                if crossed_road_deterrence >= 1500: #picks up trunk, primary
                    extra_length = 340
            if link.attribute(self.SIDEWALK_FIELD_NAME)==self.SIDEWALK_FIELD_FORMAL_CROSSING and crossed_road_deterrence >= 260:
                extra_length = 60
                
            link.setAttribute(self.SIDEWALK_METRIC_FIELD_NAME,length+extra_length)
            
            link.setAttribute(self.SIDEWALK_WEIGHT_FIELD_NAME,0)
            if link.attribute(self.SIDEWALK_FIELD_NAME) in [None,"NULL",""]:
                link.setAttribute(self.SIDEWALK_WEIGHT_FIELD_NAME,length)
            if link.attribute(self.SIDEWALK_FIELD_NAME) in [self.SIDEWALK_FIELD_LEFT,self.SIDEWALK_FIELD_RIGHT]:
                link.setAttribute(self.SIDEWALK_WEIGHT_FIELD_NAME,length/2)
            
            link.setAttribute(self.ID_FIELD_NAME,current)
            
            sink.addFeature(link,QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))
            
        return {self.OUTPUT: dest_id, self.ERROR_OUTPUT:err_dest_id}

    def divide(self,feature,offset,outfields):
        '''Takes a polyline and produces left and right offsets,
        copying over data and adding 'l' and 'r' to the sidewalk field'''
        geom = feature.geometry()
        assert not geom.isMultipart()
        line = geom.asPolyline()
        displacement_angles = np.array([geom.angleAtVertex(i) for i in range(len(line))])+np.pi/2
        normals = np.array([np.sin(displacement_angles),np.cos(displacement_angles)]).T
        
        result = []
        for sense,label in [(-1,self.SIDEWALK_FIELD_LEFT),(1,self.SIDEWALK_FIELD_RIGHT)]:
            newpoints = line+sense*normals*offset
            
            new_feature =  QgsFeature()
            new_feature.setFields(outfields)
            new_feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x,y) for x,y in newpoints]))
            for name in feature.fields().names():
                new_feature.setAttribute(name,feature.attribute(name))
            new_feature.setAttribute(self.SIDEWALK_FIELD_NAME,label)
            result += [new_feature]
            
        return result
        
        