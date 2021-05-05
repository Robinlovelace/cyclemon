# -*- coding: utf-8 -*-

"""
***************************************************************************
*   Copyright Crispin Cooper 2021                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import optparse,re
from optparse import OptionParser

import pyrosm,shapefile,shapely
import geopandas as gp
import pandas as pd

op = OptionParser()
op.add_option("--BUFFER",dest="buffer",help="Input file defining spatial buffer",metavar="FILE")
op.add_option("--NET_OUTPUT",dest="net_outfile",help="Output file",metavar="FILE")
op.add_option("--CROSSINGS_OUTPUT",dest="crossings_outfile",help="Output file",metavar="FILE")
op.add_option("--ERROR_OUTPUT",dest="errfile",help="Output error file",metavar="FILE")
(options,args) = op.parse_args()

data = pyrosm.get_data("wales",directory="../intermediate-data-scratch") # don't worry, it caches - was great_britain

# import buffer polygon
shape = shapefile.Reader(options.buffer)
feature = shape.shapeRecords()[0] # first (presuambly only) feature
first = feature.shape.__geo_interface__  
shapely_polygon = shapely.geometry.shape(first)

osm = pyrosm.OSM(data,bounding_box = shapely_polygon)

output_tags = ["access","bicycle","bridge","cycleway","cycleway:left","cycleway:right","cycleway:both","foot","highway",
                "maxspeed","motor_vehicle","oneway","sidewalk","tunnel"]

net = osm.get_data_by_custom_criteria(custom_filter={},filter_type='exclude',osm_keys_to_keep='highway',
                                        keep_nodes=False, 
                                        keep_ways=True, 
                                        tags_as_columns = output_tags
                                        )

print (f"Got network with projection: %{net.crs}")

del net['tags'] # the other tags column
del net['timestamp']
del net['version']
del net['osm_type']

for tag in output_tags:
    if tag not in net.columns:
        net[tag]=None

roadclass_lookup = {'motorway':7,'motorway_link':7,'trunk':5,'trunk_link':5,'primary':4,'primary_link':4,
                            'secondary':3,'secondary_link':3,'tertiary':2,'tertiary_link':2,
                            'living_street':1,'residential':1,'unclassified':1,"service":1,
                            "bridleway":0,"cycleway":0,"path":0,"footway":0,"pedestrian":0,"track":0,"steps":0}
highway_tags_to_manually_check = ["road"]

for hwt in highway_tags_to_manually_check: # we output warning elsewhere to manually check these
    roadclass_lookup[hwt]=1

def dummy_aadt_experienced_by_cyclists(row):
    for tag in ["cycleway","cycleway:left","cycleway:right","cycleway:both"]:
        if row[tag] in ["track","opposite_track"]:
            return 0
    if row["motor_vehicle"]=="no":
        return 0
    roadclass = roadclass_lookup[row["highway"]]
    return [9798,8698,4385,2253,300,267,13,0][7-roadclass]

def bikenet(row):
    # path is controversial. track is unsurfaced, assuming no commute cyclists. 
    return row["bicycle"] in ["yes","permissive","designated","dismount"] or \
                (row["highway"] in ["trunk","trunk_link","primary","primary_link","secondary","secondary_link",
                                                 "tertiary","tertiary_link","unclassified","residential","service",
                                                 "living_street","bridleway","cycleway","path"]\
                and row["bicycle"] in ["unknown",None,"","NULL"])

def pednet(row):
    return row["foot"] in ["yes","permissive","designated"] or \
                (row["highway"] in ["trunk","trunk_link","primary","primary_link","secondary","secondary_link",
                                                 "tertiary","tertiary_link","unclassified","residential","service",
                                                 "living_street","bridleway","cycleway","path","footway","pedestrian","steps","track"]\
                and row["foot"] in ["unknown",None,"","NULL"])
                            
def divide(row):
    return row["highway"] in ["trunk","trunk_link","primary","primary_link","secondary","secondary_link",
                                                 "tertiary","tertiary_link"]
       
# error_messages = []
# error_geometries = []

# def add_error(row,message):
    # error_messages += [message]
    # error_geometries += [row["geometry"]]
    
# def write_errors():
    # edf = pd.DataFrame.from_dict({message:error_messages,geometry:error_geometries})
    # egdf = gp.GeoDataFrame(edf, geometry=df.geometry)
    # egdf.to_file(options.errfile)

def write_to_file(gdf,file,wanted_outfields):
    gdf = gdf.to_crs("EPSG:7405")
    wanted_outfields += ["geometry"]
    for c in gdf.columns:
        if c not in wanted_outfields:
            del gdf[c]
    if len(gdf)==0:
        print("Empty file not written: "+file)
    else:
        gdf.to_file(file)#,driver="GPKG") # gpkg seems to get touched when GRASS uses as input which messes up makefile dependencies, so stick to shp

net = net[~net.highway.isin([None,"construction","proposed","raceway","","NULL"])]
net = net[net.access.isin(["yes","permissive","unknown",None,"","NULL"])]

errors = net[net.highway.isin(highway_tags_to_manually_check)]
errors['message'] = 'manually check highway tag'
write_to_file(errors,options.errfile,["message"])

net['cyclist_de'] = net.apply(lambda row: dummy_aadt_experienced_by_cyclists(row), axis=1)
net['bikenet'] = net.apply(lambda row: bikenet(row), axis=1)
net['pednet'] = net.apply(lambda row: pednet(row), axis=1)
net['divide'] = net.apply(lambda row: divide(row), axis=1)

write_to_file(net,options.net_outfile,["pednet","bikenet","cyclist_de","highway","id","divide"])

crossings = osm.get_data_by_custom_criteria(custom_filter={ 'highway': ['crossing'] }, filter_type='keep',
                                        keep_nodes=True, 
                                        keep_ways=False
                                        )
                                        
print (f"Got crossings with projection: %{crossings.crs}")
                                        
del crossings['tags'] # the other tags column
del crossings['timestamp']
del crossings['version']
del crossings['osm_type']

write_to_file(crossings,options.crossings_outfile,[])
