####################################################################################################################################
# Makefile for cyclemon - autogenerate walking and cycling visulisations both for specific destinations and everywhere-to-everywhere

# Tell Make to never delete intermediates (many of which are computationally expensive to produce)
.SECONDARY: 

#####################################################################
# Paths - ensure these match your install locations for sDNA and qgis
sdnaopenbase=D:/sdna_open/arcscripts/bin
qgis-process=cmd //C "C:\Program Files\QGIS 3.14\OSGeo4W.bat" qgis_process-qgis

#############################################################################################################
# sDNA configuration strings, explained in a little detail in comments.
# Note that for destination analyses, origin and destination are reversed for efficiency

# Cycling flows to destination
#
# CYCLE_ROUNDTRIP metric is used to determine route choice
# Parameters for CYCLE_ROUNDTRIP metric (following https://doi.org/10.1016/j.jtrangeo.2016.12.003 )
#  Directional change sensitivity a=0.2 
#  Slope sensitivity s=1
#  Traffic sensitivity t=0.04
#  aadtfield=cyclist_de specifies that we look for traffic flow estimates in the cyclist_de field on network (cyclist_deterrence trancated to 10 characters in shapefile)
#
# 10km radius (Euclidean network distance)
# Disable links that can't be cycled
# Distribute trips in each zone over all links within the zone, by length. Zone is specified by 'code' field on network; trips by 'trips' column in csv file input
# skipzeroweightorigins - much more efficient as we only consider 1 'origin' (actually the destination)
# nojunctions; nohull - don't compute things we don't need
#
# Putting that all together:
sdna-cycle-destination-config=metric=CYCLE_ROUNDTRIP;weight_type=Link;radii=10000;;nojunctions;nohull;disable=bikenet==0; zonesums=eucsum=euc@code;  destweightformula = trips*proportion(euc,eucsum);  skipzeroweightorigins; a=0.2;s=1;t=0.04; aadtfield=cyclist_de

# Cycling flows to destination, no-traffic scenario. As above but t=0 and prefix output field names with 'tf' (traffic free)
sdna-cycle-destination-notraf-config=metric=CYCLE_ROUNDTRIP;weight_type=Link;radii=10000;;nojunctions;nohull;disable=bikenet==0; zonesums=eucsum=euc@code;  destweightformula = trips*proportion(euc,eucsum);  skipzeroweightorigins;pre=tf; a=0.2;s=1;t=0; aadtfield=cyclist_de

# Cycling flows everywhere. As for 'cycling flows to destination' but smaller radius and no zone trips to distribute
sdna-cycle-everywhere-config="metric=CYCLE_ROUNDTRIP;radii=5000;nojunctions;nohull;disable=bikenet==0; a=0.2;s=1;t=0.04; aadtfield=cyclist_de"

# Cycling flows everywhere, no-traffic scenario. As for 'cycling flows everywhere' but now t=0 and prefix output field names with 'tf' (traffic free)
sdna-cycle-everywhere-notraf-config="metric=CYCLE_ROUNDTRIP;radii=5000;nojunctions;nohull;disable=bikenet==0;pre=tf; a=0.2;s=1;t=0; aadtfield=cyclist_de"

# Walking flows and severance everywhere
#
# CUSTOM metric taken from field SdWlkrM on network determines the route choice
# Radius of 1.5km
# Origin and destination weight determined by field SdWlkrWt (to correctly handle roads, sides of roads, crossings output from sidewalker)
# 'cont' specifies continuous space to increase accuracy on small scales, see https://doi.org/10.1016/j.softx.2020.100525
# textdatatokeep specifies to copy SdWlkrT (link type - formal/informal crossing, etc) and highway (OSM highway tag) to output, for later extraction to display crossings
# Other keywords explained above in cycling flows to destination
sdna-walk-everywhere-config="metric=CUSTOM;custommetric=SdWlkrM;radii=1500;nojunctions;nohull;skipzeroweightorigins;weight=SdWlkrWt;cont;textdatatokeep=SdWlkrT,highway"

# Walking flows to destination
# As for 'walking flows and severence everywhere' but
# radius of 3km
# Distribute trips in each zone over all links within the zone, by SdWlkrWt (sidewalker weight). Zone is specified by 'code' field on network; trips by 'trips' column in csv file input
sdna-walk-destination-flow-config=metric=CUSTOM;custommetric=SdWlkrM;radii=3000;nojunctions;nohull;zonesums=wtsum=SdWlkrWt@code;  destweightformula = trips*proportion(SdWlkrWt,wtsum);skipzeroweightorigins;textdatatokeep=SdWlkrT,highway

# Walking severance to destination
# As for 'walking flows to destination' but without weighting (it's not used for severance)
# we include the keyword 'outputdestinations' (n.b. origins, in reverse analysis) to show stats for each individual origin
# skipzeroweightorigins is now very essential as it not only increases speed but also prevents output of a similar volume of data for every possible destination
sdna-walk-destination-severance-config=metric=CUSTOM;custommetric=SdWlkrM;outputdestinations;radii=3000;skipzeroweightorigins;

###################
# Top level targets
# These all live in output-data/towns/{name-of-town}
# Each mode (walking/cycling) has a variety of views (some for 'everywhere', some for specific 'destination')
#  - each view consists of:
#    - one or more layers held in shapefiles
#    - metadata appended to the combined .json for all views for that town, to define how the views are displayed and described to the end user
# Additionally some QGIS project files are created for each town:
#  - all-output-qgis contains all layers for town with appropriate symbology
#  - summary-walk-qgis contains a few key walking views ready for presentation
#  - summary-cycle-qgis contains a few key cycling views ready for presentation

%-town-all: %-town-directories %-town-contents ;

%-town-directories:
	town_name=$(subst -town-directories,,$@) &&\
	mkdir -p ../intermediate-data-scratch/towns/$${town_name} &&\
	mkdir -p ../output-data/towns/$${town_name}

%-town-contents: %-town-data %-town-metadata ;

%-town-metadata: ../output-data/towns/%/all-town-metadata.json ../output-data/towns/%/all-outputs-qgis.qgs ../output-data/towns/%/summary-walk-qgis.qgs ../output-data/towns/%/summary-cycle-qgis.qgs ;

%-town-data: %-town-walking %-town-cycling ;

# Walking

%-town-walking: %-town-walking-destination %-town-walking-everywhere ;

%-town-walking-destination: %-town-walking-destination-flows-view %-town-walking-destination-severance-view ;

%-town-walking-everywhere: %-town-walking-everywhere-flows-view %-town-walking-everywhere-severance-view ;

%-town-walking-destination-flows-view: ../output-data/towns/%/walking-destination-flows.shp.justcrossingsD.shp ../output-data/towns/%/walking-destination-flows.shp ../intermediate-data-scratch/towns/%/metadata-walking-destination-flows.single-layer-metadata.json ;

%-town-walking-destination-severance-view: ../output-data/towns/%/walking-destination-severance.shp ../intermediate-data-scratch/towns/%/metadata-walking-destination-severance.single-layer-metadata.json ;

%-town-walking-everywhere-flows-view: ../output-data/towns/%/walking-everywhere-flows-severance.shp.justcrossingsE.shp ../output-data/towns/%/walking-everywhere-flows-severance.shp ../intermediate-data-scratch/towns/%/metadata-walking-everywhere-flows.single-layer-metadata.json ;

%-town-walking-everywhere-severance-view: ../output-data/towns/%/walking-everywhere-flows-severance.shp ../intermediate-data-scratch/towns/%/metadata-walking-everywhere-severance.single-layer-metadata.json ;

# Cycling

%-town-cycling: %-town-cycling-destination %-town-cycling-everywhere %-town-dutch ;

%-town-dutch: ../intermediate-data-scratch/towns/%/metadata-cycling-go-dutch.single-layer-metadata.json ; # todo add when we have a rule for it: ../output_data/towns/%/rnet_pct_dutch.shp

%-town-cycling-everywhere: ../output-data/towns/%/cycling-everywhere-combined.shp ../intermediate-data-scratch/towns/%/metadata-cycling-everywhere-flows.single-layer-metadata.json ../intermediate-data-scratch/towns/%/metadata-cycling-everywhere-flowsdiff.single-layer-metadata.json ;

%-town-cycling-destination: ../output-data/towns/%/cycling-destination-combined.shp ../intermediate-data-scratch/towns/%/metadata-cycling-destination-flows.single-layer-metadata.json ../intermediate-data-scratch/towns/%/metadata-cycling-destination-flowsdiff.single-layer-metadata.json ;

##################
# Metadata targets

# *.single-layer-metadata.json files actually refer to metadata for a single *view*
%.single-layer-metadata.json: ../metadata-templates/view-metadata-template.jsontemplate fill-metadata-template.py
	python fill-metadata-template.py --TEMPLATE=$(word 1,$^) --OUTPUT=$@

# Combines all single-layer-metadata files to a single .json for the town    
../output-data/towns/%/all-town-metadata.json: ../metadata-templates/view-metadata-template.jsontemplate ../intermediate-data-scratch/towns/% aggregate-town-metadata.py
	python aggregate-town-metadata.py --TEMPLATE=$(word 1,$^) --INPUTDIR=$(word 2,$^) --OUTPUT=$@
    
../output-data/towns/%/all-outputs-qgis.qgs: ../output-data/towns/%/all-town-metadata.json qgis_scripts/create-qgis-project-from-metadata.py
	$(qgis-process) run script:newprojectfromcyclemonmetadata --FOLDER=$(dir $@)

../output-data/towns/%/summary-walk-qgis.qgs: ../output-data/towns/%/walking-destination-flows.shp ../output-data/towns/%/walking-destination-flows.shp.justcrossingsD.shp ../output-data/towns/%/walking-everywhere-flows-severance.shp ../output-data/towns/%/walking-everywhere-flows-severance.shp.justcrossingsE.shp qgis_scripts/create-qgis-walk-summary.py
	$(qgis-process) run script:walksummaryproject --FOLDER=$(dir $@) --DESTFLOWSSHP=$(word 1,$^) --DESTCROSSINGSSHP=$(word 2,$^) --ALLFLOWSSHP=$(word 3,$^) --ALLCROSSINGSSHP=$(word 4,$^) --ALLFLOWSFIELD=BtC1500c --DESTFLOWSFIELD=BtCWe3000

../output-data/towns/%/summary-cycle-qgis.qgs: ../output-data/towns/%/rnet_pct_dutch.shp ../output-data/towns/%/cycling-everywhere-combined.shp qgis_scripts/create-qgis-cycle-summary.py
	$(qgis-process) run script:cyclesummaryproject --FOLDER=$(dir $@) --PCTSHAPE=$(word 1,$^) --ALLCYCLESHAPE=$(word 2,$^) --PCTFIELD=n_cycle --ALLFLOWSFIELD=BtH5000 
    
#####################
# Output data targets

# TODO: Robin insert rule to make ../output-data/towns/%/rnet_pct_dutch.shp from ../input-data/towns/%/trip-origin-zones.csv and ../input-data/towns/%/destinations.shp

# Combines with- and without-traffic cycling models into a single shapefile holding both models and the difference in flows between them
../output-data/towns/%/cycling-everywhere-combined.shp: ../intermediate-data-scratch/towns/%/cycling-everywhere-notraffic-flows.shp ../intermediate-data-scratch/towns/%/cycling-everywhere-flows.shp combine_cycle_layers.py
	python combine_cycle_layers.py --INFILE1=$(word 1,$^) --INFILE2=$(word 2,$^) --OUTFILE=$@ --DIFFFIELD=diff --FIELD1=tfBtH5000 --FIELD2=BtH5000 

# Combines with- and without-traffic cycling models into a single shapefile holding both models and the difference in flows between them
../output-data/towns/%/cycling-destination-combined.shp: ../intermediate-data-scratch/towns/%/cycle-flows-multipc-destination-notraf.shp-aggregate.shp ../intermediate-data-scratch/towns/%/cycle-flows-multipc-destination.shp-aggregate.shp combine_cycle_layers.py
	python combine_cycle_layers.py --INFILE1=$(word 1,$^) --INFILE2=$(word 2,$^) --OUTFILE=$@ --DIFFFIELD=diff --FIELD1=tfBtHWe100 --FIELD2=BtHWe10000 

# Run the walk-everywhere model
../output-data/towns/%/walking-everywhere-flows-severance.shp: ../intermediate-data-scratch/towns/%/sidewalks.shp 
	python $(sdnaopenbase)/sdnaintegral.py --im "net=$(word 1,$^)" --om "net=$@" $(sdna-walk-everywhere-config) 

# Run severance model for destination
../output-data/towns/%/walking-destination-severance.shp: ../intermediate-data-scratch/towns/%/sidewalks-destmarked.shp 
	python $(sdnaopenbase)/sdnaintegral.py --im "net=$^" --om destinations=$@ "$(sdna-walk-destination-severance-config);origweight=destinatio;nonetdata"

# Copy destination flows shapefile from intermediate-data-scratch and give it a simpler name
../output-data/towns/%/walking-destination-flows.shp: ../intermediate-data-scratch/towns/%/walk-flows-multipc-destination.shp-aggregate.shp
	for e in shp shx dbf prj; do cp $(basename $^).$$e $(basename $@).$$e; done

# Pull out crossings only from walk-everywhere model and filter to top 50 flows only (justcrossingsE = just crossings for everywhere)
%.justcrossingsE.shp: % filter_crossings.py
	python filter_crossings.py --INPUT=$(word 1,$^) --OUTPUT=$@ --FILTER-FIELD=BtC1500c --FILTER-TYPE=rank --FILTER-THRESH=50
    
# Pull out crossings only from walk-destination model filter for flows greater than 10 trips (justcrossingsD = just crossings for destination)
%.justcrossingsD.shp: % filter_crossings.py
	python filter_crossings.py --INPUT=$(word 1,$^) --OUTPUT=$@ --FILTER-FIELD=BtCWe3000 --FILTER-TYPE=abs --FILTER-THRESH=10

#####################################
# Destination analyses (intermediate)
# nb these are all based on *-multizonejoin.shp networks (see below)

# Model of cycle flows to destination
../intermediate-data-scratch/towns/%/cycle-flows-multipc-destination.shp : ../intermediate-data-scratch/towns/%/network-draped-destmarked.shp-multizonejoin.shp ../input-data/towns/%/trip-origin-zones.csv
	python $(sdnaopenbase)/sdnaintegral.py --im "net=$(word 1,$^);tables=$(word 2,$^)" --om net=$@ "$(sdna-cycle-destination-config);origweightformula=destinatio"
    
# Model of cycle flows to destination without traffic
../intermediate-data-scratch/towns/%/cycle-flows-multipc-destination-notraf.shp : ../intermediate-data-scratch/towns/%/network-draped-destmarked.shp-multizonejoin.shp ../input-data/towns/%/trip-origin-zones.csv
	python $(sdnaopenbase)/sdnaintegral.py --im "net=$(word 1,$^);tables=$(word 2,$^)" --om net=$@ "$(sdna-cycle-destination-notraf-config);origweightformula=destinatio"

# Model of walking flows to destination
../intermediate-data-scratch/towns/%/walk-flows-multipc-destination.shp : ../intermediate-data-scratch/towns/%/sidewalks-destmarked.shp-multizonejoin.shp ../input-data/towns/%/trip-origin-zones.csv
	python $(sdnaopenbase)/sdnaintegral.py --im "net=$(word 1,$^);tables=$(word 2,$^)" --om net=$@ "$(sdna-walk-destination-flow-config);origweightformula=destinatio"

#####################
# Destination marking

# Mark destination on cycling network (as a field set to 1 for the relevant link only)
../intermediate-data-scratch/towns/%/network-draped-destmarked.shp : ../input-data/towns/%/destinations.shp ../intermediate-data-scratch/towns/%/network-draped.shp mark_destinations.py
	python mark_destinations.py --POINTS=$(word 1,$^) --NETWORK=$(word 2,$^) --OUTPUT=$@

# Mark destination on walking network (as a field set to 1 for the relevant link only)
../intermediate-data-scratch/towns/%/sidewalks-destmarked.shp : ../input-data/towns/%/destinations.shp ../intermediate-data-scratch/towns/%/sidewalks.shp mark_destinations.py
	python mark_destinations.py --POINTS=$(word 1,$^) --NETWORK=$(word 2,$^) --OUTPUT=$@

######################################################################
# Split to zone based networks / combine back to aggregate network
# Networks named like %-multizonejoin.shp have been joined one-to-many with zones,
#  i.e. where a single link appears in multiple zones _the link is duplicated multiple times in the network_
# Networks named like %-aggregate.shp are multizonejoin networks that have been analyzed, 
#  then aggregated by summing flows on all duplicate links (representing different zones) to a single record per link

%-aggregate.shp : % aggregate_multi_layer.py
	python aggregate_multi_layer.py --INPUT=$(word 1,$^) --OUTPUT=$@ 

%-multizonejoin.shp: % ../input-data/all-zone-polys.shp
	$(qgis-process) run native:joinattributesbylocation --INPUT=$(word 1,$^) --JOIN=$(word 2,$^) --PREDICATE=0 --JOIN_FIELDS=code --METHOD=0 --DISCARD_NONMATCHING=0 --OUTPUT=$@

#############################################################################################
# Cycling analyses (intermediate - the with- and without-traffic versions are later combined)

../intermediate-data-scratch/towns/%/cycling-everywhere-flows.shp: ../intermediate-data-scratch/towns/%/network-draped.shp
	python $(sdnaopenbase)/sdnaintegral.py --im "net=$(word 1,$^)" --om "net=$@" $(sdna-cycle-everywhere-config)
    
../intermediate-data-scratch/towns/%/cycling-everywhere-notraffic-flows.shp: ../intermediate-data-scratch/towns/%/network-draped.shp
	python $(sdnaopenbase)/sdnaintegral.py --im "net=$(word 1,$^)" --om "net=$@" $(sdna-cycle-everywhere-notraf-config)

#####################
# Network preparation

# Drape network over terrain to get 3d network for cycling models
../intermediate-data-scratch/towns/%/network-draped.shp: ../intermediate-data-scratch/towns/%/network-prepared.shp
	$(qgis-process) run grass7:v.drape --elevation=../input-data/terrain.tif --input=$^ --method=1 --null_value=0 --output=$@ --scale=1 --type=1

# Auto-split roads with 'divide' field ==1 into separate links representing each side, informal crossings at link ends and formal crossings where present in data
../intermediate-data-scratch/towns/%/sidewalks.shp : ../intermediate-data-scratch/towns/%/network-prepared.shp ../intermediate-data-scratch/towns/%/crossings_snapped.shp qgis_scripts/sidewalker.py
	rm -f $(subst .shp,,$@).* && $(qgis-process) run script:sidewalker --INPUT=$(word 1,$^) --INPUT_POINTS=$(word 2,$^) --OUTPUT=$@ --ERROR_OUTPUT=$(subst sidewalks.shp,sidewalk-errors.shp,$@)

# Snap crossing points to nearest node in network - workaround for bug in pyrosm: https://github.com/HTenkanen/pyrosm/issues/114
# (should be able to ditch this step when the issue is fixed)
../intermediate-data-scratch/towns/%/crossings_snapped.shp: ../intermediate-data-scratch/towns/%/crossings.shp ../intermediate-data-scratch/towns/%/network-prepared.shp
	$(qgis-process) run native:snapgeometries --INPUT=$(word 1,$^) --REFERENCE_LAYER=$(word 2,$^) --TOLERANCE=0.5 --BEHAVIOR=2 --OUTPUT=$@

# sDNA prepare network - reduce link count by joining pseudonodes (which sDNA calls split links) except where they are needed due to differences in fields for link subsections
# Also remove isolated systems
../intermediate-data-scratch/towns/%/network-prepared.shp : ../intermediate-data-scratch/towns/%/network-routable.shp
	python $(sdnaopenbase)/sdnaprepare.py --im net=$^ --om net=$@ "action=repair;isolated;splitlinks;data_text=highway;data_unitlength=cyclist_de,bikenet,pednet,divide;merge_if_identical=highway,cyclist_de,bikenet,pednet,divide"

# Break OSM polylines where they share a node, thus producing a network routable with endpoint connectivity rules 
# https://sdna-open.readthedocs.io/en/latest/network_preparation.html#connectivity-rules
../intermediate-data-scratch/towns/%/network-routable.shp : ../intermediate-data-scratch/towns/%/network-with-decoded-tags.shp
	rm -f $(subst .shp,,$@).* $(subst network-routable.shp,bpol-errors.*,$@) && $(qgis-process) run grass7:v.clean --input=$^ --tool=8 --output=$@ --error=$(subst network-routable.shp,bpol-errors.shp,$@)
    
# Auto download network and crossings inside input-data/towns/X/cycle-buffer.shp from OSM
# Also compute following fields based on OSM tags:
#  - cyclist deterrence (cyclist_de as used in sDNA cycling configs)
#  - pednet (1 for links in pedestrian network)
#  - bikenet (1 for links in cycling network)
#  - divide (1 for links we wish to model each side of separately; set where road class is TERTIARY or higher)
../intermediate-data-scratch/towns/%/network-with-decoded-tags.shp ../intermediate-data-scratch/towns/%/crossings.shp: ../input-data/towns/%/cycle-buffer.shp osm_download.py
	outroot=$(subst input-data,intermediate-data-scratch,$(subst cycle-buffer.shp,,$(word 1,$^))) && \
	python osm_download.py --BUFFER=$(word 1,$^) --NET_OUTPUT=$${outroot}/network-with-decoded-tags.shp --CROSSINGS_OUTPUT=$${outroot}/crossings.shp --ERROR_OUTPUT=$${outroot}/tag-decode-errors.gpkg
