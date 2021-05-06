# CycleMon: automated generation of basic walking and cycling analysis from open data

Academic paper: see paper/ subdirectory

# Usage

## Prerequisites

* Currently, Windows (7 or higher). This is due to the requirements of sDNA, though we hope to change that soon.
* QGIS+GRASS. We used QGIS version 3.14 with GRASS 7.8.3.
    * To fix a bug in scripting QGIS, we needed to add the following line to `OSGeo4W.bat` in the QGIS install directory: `call "C:\Program Files\QGIS 3.14\apps\grass\grass78\etc\env.bat" `
* sDNA Open, version 4.2 or later https://github.com/fiftysevendegreesofrad/sdna_open/releases/tag/v4.2.0
* R
* Python 3, including pyrosm. https://pypi.org/project/pyrosm/
    * We managed dependencies with Anaconda, as such you could install our python environment with `conda env create -f code/conda_env.yml` then activate with `conda activate cyclemon`
* GNU Make or (for better debugging) remake http://bashdb.sourceforge.net/remake/; which therefore (in Windows) require MSYS
    
## Input data

The directory input-data/ should contain the following

* `input-data`
    * `towns`
        * (directory for each town, with name chosen by you e.g. `monmouth`)
            * `cycle-buffer.shp` containing a single polygon with the area of interest
            * `destinations.shp` containing a single point with destination of interest
            * `destination-zones.csv` containing trip counts from each origin zone to the destination of interest
    * `zone-polygons.shp` containing named polygons for all the origin zones
    * `terrain.tif` containing height data

## Configuring the model

* Open `code/Makefile` and check the paths at the top match your install locations of QGIS and sDNA_Open.    
* Open `code/osm_download.py` and edit the following line, changing `wales` to the appropriate region supported by pyrosm (see https://pyrosm.readthedocs.io/en/latest/basics.html#available-datasets), such as `great_britain` ... unless of course, your model falls entirely in Wales):
        `data = pyrosm.get_data("wales",directory="../intermediate-data-scratch") `
* Open QGIS, navigate to `Settings -> Options -> Processing -> Scripts -> Scripts folder(s)`: add the full path to `cyclemon\code\qgis_scripts` to the list of folders. Close and re-open QGIS to make sure your change persisted.

## Running the model

e.g. To generate all models from `input-data/towns/monmouth`:

`cd code`

`make monmouth-town-all`

Check intermediate-data-scratch/towns/(your town)/tag-decode-errors.gpkg (if it exists) to check for any OSM tags we thought might need manual interpretation.

Check `output-data/towns/(your town)` for the results. As a starting point have a look at

* `summary_walk_qgis.qgs`
* `summary_cycle_qgis.qgs`
* `all_outputs_qgis.qgs`

and see `metadata.html` for a description of each layer within these.

For more detail on how each output was computed, check the academic paper and/or comments in `Makefile`.