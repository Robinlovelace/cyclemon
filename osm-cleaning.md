# OSM Preparation

## Initial Download

20km buffers round school entry points. 

Not automated: using OSM Downloader plugin in QGIS

Download tags:
* highway is NOT NULL
* bridge,tunnel - needed for correct connectivity
* access - generic access restrictions
* bicycle,foot,motor_vehicle - mode specific access restrictions
* maxspeed,oneway - may be useful
* cycleway, cycleway:left, cycleway:right, cycleway:both - contains extra info we need to pick out light segregation
* sidewalk

As alphabetical list for checking in OSM downloader:

* access
* bicycle
* bridge
* cycleway (and cycleway:subclasses)
* foot
* highway (NOT NULL)
* maxspeed
* motor_vehicle
* oneway
* sidewalk
* tunnel

## Tag processing

Process access rules:

* Default rules: https://wiki.openstreetmap.org/wiki/OSM_tags_for_routing/Access_restrictions#United_Kingdom
* Primarily filter by highway tag as per the above table
* Traffic free cycle routes: highway=path,bridleway,cycleway or cycleway=track,opposite_track (the latter two indicating light segregation on other highway types)
* Include access restrictions: access, bicycle, foot, motor_vehicle
* This initial spec has been revised following pilot results - the code in osm_at_tag_process.py is the definitive version

In upscaling this we will need to check local interpretations of OSM tags.
* failed tag decodes - seem to arise because OSMDownloader limits size of tag field
* access tags

Also produce dummy traffic flows based on road class to use as cyclist deterrent.

Output new fields bikenet, pednet, cyclist_deterrence

## Connectivity

Either,
* Official stance: break all links where a node ID is shared (OSM doesn't store linestrings but lists of point IDs)
* Or, do this based on node coordinates instead. If using either this or the above method will need to check intersections afterwards. bpol in grass v.clean seems to do this, if it can cope with data size
* Or, my old method break all intersections except bridges and tunnels, put back bridges/tunnels and check they join correctly. More robust to some errors, less to others.
* Or, use osm2pgrouting

## Terrain

Drape network - Grass v.drape seems to work (could fallback to QGIS equivalent if not)

Tried free 30m nasa srtm data - significant errors. will try proprietary os 5m.

## Todo

Automate calling tools above

# sDNA calls

sDNA currently can't run in QGIS3 (we are working on it). For now, use QGIS2 plugin or the command line.

Putting in batch file in code directory.

# Actual analysis

Cycle path to Bulwark shows huge metric - possible error from draping

What radius type to use?

# Display results

QGIS - filter BtH>0; graduated display, take log10 of BtH, classify equal interval