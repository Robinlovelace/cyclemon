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
(options,args) = op.parse_args()

df = gp.read_file(options.input)

btfield, = [f for f in df.columns if f[0:2]=="Bt" or f[0:4]=="tfBt"]

wanted_fields = ["geometry","highway","SdWlkrT",btfield,df.index.name]
for fieldname in df.columns:
    if fieldname not in wanted_fields:
        del df[fieldname]

wkbfield = "geom_wkb_for_efficient_matching"
df[wkbfield] = df.apply(lambda row: row.geometry.wkb, axis=1)
dfsum = df.dissolve(by=wkbfield,aggfunc='sum')
dfsum = dfsum.reset_index()
df = df.dissolve(by=wkbfield,aggfunc='first')
df = df.reset_index()

df[btfield]=dfsum[btfield]

del df[wkbfield]

df.to_file(options.outfile)
