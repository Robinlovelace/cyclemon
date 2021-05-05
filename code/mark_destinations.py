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
op.add_option("--POINTS",dest="points",help="Input points",metavar="FILE")
op.add_option("--NETWORK",dest="net",help="Network",metavar="FILE")
op.add_option("--OUTPUT",dest="outfile",help="Output file",metavar="FILE")
(options,args) = op.parse_args()

net = gp.read_file(options.net)
points = gp.read_file(options.points)

points = points.to_crs("EPSG:7405")

distfield="sdlkfjsdl"

for _,point in points.iterrows():
    net[distfield] = net.apply(lambda row: point.geometry.distance(row.geometry),axis=1)
    mindist = net[distfield].min()
    net[point.label] = net[distfield]==mindist
    
del net[distfield]
net.to_file(options.outfile)
