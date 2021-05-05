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
op.add_option("--OUTPUT",dest="outfile",help="Output file",metavar="FILE")
(options,args) = op.parse_args()

# search for metadata template with matching filename field (this is filename for metadata file)

with open(options.template) as f:
  data = json.load(f)

desired_filename = os.path.basename(options.outfile)

views = data["views"]
matching_views = [v for v in views if v["filename"]==desired_filename]
assert(len(matching_views)==1)
view = matching_views[0]

town = os.path.basename(os.path.dirname(options.outfile))
town = town.capitalize()
view["town"]=town

with open(options.outfile, 'w') as json_file:
  json.dump({"views":[view]}, json_file)