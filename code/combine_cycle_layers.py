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
op.add_option("--INFILE1",dest="file1",help="Input file",metavar="FILE")
op.add_option("--INFILE2",dest="file2",help="Input file",metavar="FILE")
op.add_option("--OUTFILE",dest="outfile",help="Output file",metavar="FILE")
op.add_option("--DIFFFIELD",dest="difffield",help="Diff field",metavar="FIELDNAME")
op.add_option("--FIELD1",dest="field1",help="Field1",metavar="FIELDNAME")
op.add_option("--FIELD2",dest="field2",help="Field2",metavar="FIELDNAME")
(options,args) = op.parse_args()

file1 = gp.read_file(options.file1)
file2 = gp.read_file(options.file2)

#join = pd.concat([file1,file2], axis=1, join="inner")
join = file1.join(file2,rsuffix="2")

if "ID" in join.columns:
    assert all(join.ID==join.ID2)
assert all(join.geometry==join.geometry2)
join[options.difffield]=join[options.field1]-join[options.field2]

keepfields = ["geometry",options.field2,options.field1,options.difffield]
for fieldname in join.columns:
    if fieldname not in keepfields:
        del join[fieldname]
        
join.to_file(options.outfile)
