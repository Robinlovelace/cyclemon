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

import geopandas as gp
import pandas as pd

op = OptionParser()
op.add_option("--INPUT",dest="input",help="Input file",metavar="FILE")
op.add_option("--OUTPUT",dest="outfile",help="Output file",metavar="FILE")
op.add_option("--FILTER-FIELD",dest="field")
op.add_option("--FILTER-THRESH",dest="thresh")
op.add_option("--FILTER-TYPE",dest="filtype")
(options,args) = op.parse_args()

df = gp.read_file(options.input)

df = df[df.SdWlkrT.isin(['x','X'])]

if options.filtype.upper()=="ABS":
    df["keep"]=df[options.field]>float(options.thresh)
else:
    assert options.filtype.upper()=="RANK"
    df["rank"]=df[options.field].rank(ascending=False)
    df["keep"]=df["rank"]<int(options.thresh)

df = df[df.keep]

roadclass_lookup = {'motorway':3,'motorway_link':3,'trunk':3,'trunk_link':3,'primary':3,'primary_link':3,
                            'secondary':2,'secondary_link':2,'tertiary':1,'tertiary_link':1,
                            'living_street':0,'residential':0,'unclassified':0,"service":0,
                            "bridleway":0,"cycleway":0,"path":0,"footway":0,"pedestrian":0,"track":0,"steps":0}

crossing_type = {'x':'I','X':'F'}
def compute_crossing_symbol(row):
    severity = roadclass_lookup[row.highway]
    assert severity > 0
    ctype = crossing_type[row.SdWlkrT]
    return "%s%d"%(ctype,severity)
    
df["RCSeverity"]=df.apply(lambda row: roadclass_lookup[row.highway],axis=1)
df["RoadClass"]=df.highway
df["Crosstype"]=df.apply(lambda row: crossing_type[row.SdWlkrT],axis=1)
df["symbol"]=df.apply(compute_crossing_symbol,axis=1)

df["geometry"]=df.apply(lambda row: row.geometry.centroid,axis=1)

wanted_fields = ["geometry","RCSeverity","RoadClass","CrossType","symbol"]
for fieldname in df.columns:
    if fieldname not in wanted_fields and fieldname[0:2]!="Bt" and fieldname!=df.index.name:
        del df[fieldname]

df.to_file(options.outfile)
