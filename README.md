# CycleMon: automated generation of basic walking and cycling analysis from open data

Academic paper: see paper/ subdirectory

# Usage

## Prerequisites

* QGIS+GRASS. We used QGIS version 3.14 with GRASS 7.8.3.
    * To fix a bug in scripting QGIS, we needed to add the following line to `OSGeo4W.bat` in the QGIS install directory: `call "C:\Program Files\QGIS 3.14\apps\grass\grass78\etc\env.bat" `
* sDNA Open, version 4.2 https://github.com/fiftysevendegreesofrad/sdna_open
* R
* Python 3, including pyrosm. https://pypi.org/project/pyrosm/
    * We managed dependencies with Anaconda, as such you could install our python environment with `conda env create -f code/conda_env.yml` then activate with `conda activate cyclemon`
* GNU Make or (for better debugging) remake http://bashdb.sourceforge.net/remake/
    
Open `code/Makefile` and check the paths at the top match your install locations of QGIS and sDNA_Open.    

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

## Running the model

e.g. To generate all models from `input-data/towns/monmouth`:

`cd code`

`make monmouth-town-all`