download.file("https://www.arcgis.com/sharing/rest/content/items/a644dd04d18f4592b7d36705f93270d8/data", "postcodes.zip")

unzip("postcodes.zip", exdir = "~/hd/data/uk/accessibility/postcodes")

list.files("~/hd/data/uk/accessibility/postcodes")
list.files("~/hd/data/uk/accessibility/postcodes/Data/")
list.files("~/hd/data/uk/accessibility/postcodes/Data/multi_csv/")
file.size("~/hd/data/uk/accessibility/postcodes/Data/multi_csv/ONSPD_AUG_2020_UK_AB.csv") / 1e6 # 19 MB
file.size("~/hd/data/uk/accessibility/postcodes/Data/ONSPD_AUG_2020_UK.csv") / 1e6 # 1.3 GB
postcodes = readr::read_csv("~/hd/data/uk/accessibility/postcodes/Data/ONSPD_AUG_2020_UK.csv") # warnings...
library(readr)
cols_postcodes = cols(
  .default = col_character(),
  dointr = col_double(),
  doterm = col_double(),
  usertype = col_double(),
  oseast1m = col_double(),
  osgrdind = col_double(),
  streg = col_double(),
  ur01ind = col_character(),
  ru11ind = col_character(),
  lat = col_double(),
  long = col_double(),
  imd = col_double()
)
postcodes = readr::read_csv("~/hd/data/uk/accessibility/postcodes/Data/ONSPD_AUG_2020_UK.csv", col_types = cols_postcodes) # warnings...
nrow(postcodes) / 1e6
# [1] 2.647046 # why so many? I thought there were only 1.7 million:
# https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom
class(postcodes)
postcodes
postcodes_ls7_3h = postcodes %>% filter(stringr::str_detect(string = pcd, pattern = "LS7 3H"))
nrow(postcodes_ls7_3h)
View(postcodes_ls7_3h)
postcodes_ls7_3h_sf = postcodes_ls7_3h %>% sf::st_as_sf(coords = c("long", "lat"), crs = 4326)
mapview::mapview(postcodes_ls7_3h_sf)
postcodes_ls7_3h %>%
  summarise_all(.funs = function(x) length(unique(x)))
postcode_summary = postcodes %>%
  select(-long, -lat, -osnrth1m, -oseast1m) %>%
  # sample_frac(size = 0.1) %>% # uncomment to test on 10% sample
  summarise_all(.funs = function(x) length(unique(x))) %>%
  tidyr::pivot_longer(everything()) %>%
  arrange(desc(value))
# View(postcode_summary)
postcode_summary
dir.create("~/hd/data/uk/postcodes")
saveRDS(postcodes, "~/hd/data/uk/postcodes/postcodes_all_2020_ONSPD_AUG_2020_UK.Rds")
saveRDS(postcode_summary, "~/hd/data/uk/postcodes/postcodes_summary_2020.Rds")
dir.create("~/hd/data/uk/boundaries-ew")
o = setwd("~/hd/data/uk/boundaries-ew/")
ew_parishes_2019 = ukboundaries::duraz("https://opendata.arcgis.com/datasets/895a50316c5d4be4be020fd545f9a013_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D")
nrow(ew_parishes_2019) # 11,341
ew_parishes_2019
norton_canon = ew_parishes_2019 %>% filter(par19nm == "Norton Canon")
mapview::mapview(norton_canon) # impressive detail!
saveRDS(ew_parishes_2019, "ew_parishes_2019.Rds")
ew_parishes_2019_4326 = st_transform(ew_parishes_2019, 4326)
saveRDS(ew_parishes_2019_4326, "ew_parishes_2019_4326.Rds")
setwd(o)

lsoa_ew_centroids_url = "https://opendata.arcgis.com/datasets/b7c49538f0464f748dd7137247bbc41c_0.zip?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
dir.create("~/hd/data/uk/boundaries-ew/lsoa-centroids")
o = setwd("~/hd/data/uk/boundaries-ew/lsoa-centroids")
ew_lsoa_centroids = ukboundaries::duraz(lsoa_ew_centroids_url)
nrow(ew_lsoa_centroids) # [1] 34753
ew_lsoa_centroids
summary(str_detect(ew_lsoa_centroids$lsoa11nm, pattern = "Chep"))
ew_parishes_2019$par19nm[str_detect(ew_parishes_2019$par19nm, pattern = "Chep")]
chepstow = ew_parishes_2019 %>% filter(str_detect(string = par19nm, pattern = "Chepstow"))
abergavenny = ew_parishes_2019 %>% filter(str_detect(string = par19nm, pattern = "Abergavenny"))
mapview::mapview(chepstow)
saveRDS(ew_lsoa_centroids, "ew_lsoa_centroids.Rds")
ew_lsoa_centroids_4326 = st_transform(ew_lsoa_centroids, 4326)
saveRDS(ew_lsoa_centroids_4326, "ew_lsoa_centroids_4326.Rds")

setwd(o)

# save outputs

getwd()
dir.create("input-data")
sf::write_sf(chepstow, "input-data/chepstow.geojson")
sf::write_sf(abergavenny, "input-data/abergavenny.geojson")
