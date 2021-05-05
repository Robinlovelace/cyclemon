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

import optparse,json,os
from optparse import OptionParser

op = OptionParser()
op.add_option("--TEMPLATE",dest="template",help="Input templates",metavar="FILE")
op.add_option("--INPUTDIR",dest="inputdir",help="Input dir for existing metadata",metavar="DIR")
op.add_option("--OUTPUT",dest="outfile",help="Output file",metavar="FILE")
(options,args) = op.parse_args()

# read template to determine ordering
with open(options.template) as f:
  data = json.load(f)

output_view_list = []

# search for each input metadata file implied by the template in same directory as output file
views = data["views"]
for view in views:
    fullpath = os.path.join(options.inputdir,view["filename"])
    # warn if file does not exist
    if not os.path.exists(fullpath):
        print('Metadata file not found, ignoring layer:',fullpath)
    else:
        with open(fullpath) as f:
            single_layer_data = json.load(f)
            assert len(single_layer_data["views"])==1
            output_view_list += single_layer_data["views"]
        
with open(options.outfile, 'w') as json_file:
    json.dump({"views":output_view_list}, json_file)
    