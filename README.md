# CycleMon: automated generation of basic walking and cycling analysis from open data

Academic paper: see paper/ subdirectory

# Usage

## Prerequisites

* QGIS. We used version 3.14. 
    * To fix a bug in scripting QGIS, we needed to add the following line to `OSGeo4W.bat` in the QGIS install directory: `call "C:\Program Files\QGIS 3.14\apps\grass\grass78\etc\env.bat" `
* sDNA Open https://github.com/fiftysevendegreesofrad/sdna_open
* R
* Python 3, including pyrosm. https://pypi.org/project/pyrosm/
    * We managed dependencies with Anaconda, as such you could install our python environment with `conda env create -f code/conda_env.yml` then activate with `conda activate cyclemon`
    
## Input data

The directory input-data/ should contain the following

* input-data
    * towns
        * (directory for each town, with name chosen by you e.g. `monmouth`)
            * `cycle-buffer.shp` containing a single polygon with the area of interest
            * `destinations.shp` containing a single point with destination of interest
    * `zone-polygons.shp` containing named polygons for all the origin zones
    * `terrain.tif` containing height data

## Running the model

e.g. To generate all models from `input-data/towns/monmouth`:

`cd code`
`make monmouth-town-all`