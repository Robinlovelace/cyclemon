school_data = readxl::read_excel("~/projects/cyclemon/Geocodes Abergavenny & Chepstow.xlsx")
school_data %>% summarise_all()
school_data %>% glimpse()
# install.packages("skimr")
school_data %>% skimr::skim() # 327 unique postcodes - probably student level data...
# ── Variable type: character ──────────────────────────────────────────────────────────────────────────
# skim_variable n_missing complete_rate   min   max empty n_unique whitespace
# 1 BASE_NAME             1         0.999    15    15     0        1          0
# 2 POSTCODE              1         0.999     7     8     0      327          0
# 3 EASTING              15         0.983     6     8     0      632          0
# 4 NORTHING             15         0.983     6     8     0      636          0
school_data_complete = school_data %>% na.omit() %>%
  select(POSTCODE, BASE_NAME, EASTING, NORTHING) %>%
  mutate(across(EASTING:NORTHING, as.numeric))
school_data_missing = school_data[!complete.cases(school_data), ]
nrow(school_data_complete) + nrow(school_data_missing) == nrow(school_data)
school_data_missing
# 14 missing postcodes:
# A tibble: 15 x 4
# BASE_NAME       POSTCODE EASTING NORTHING
# <chr>           <chr>    <chr>   <chr>
#   1 NA              NA       NA      NA
# 2 Chepstow School NP16 7LA NA      NA
# 3 Chepstow School GL15 6QQ NA      NA
# 4 Chepstow School NP16 6FB NA      NA
# 5 Chepstow School NP16 7FF NA      NA
# 6 Chepstow School NP19 4DG NA      NA
# 7 Chepstow School GL15 6QQ NA      NA
# 8 Chepstow School NP16 6LZ NA      NA
# 9 Chepstow School NP16 6QN NA      NA
# 10 Chepstow School NP16 5GH NA      NA
# 11 Chepstow School NP16 5GH NA      NA
# 12 Chepstow School NP19 0JS NA      NA
# 13 Chepstow School NP16 6FB NA      NA
# 14 Chepstow School NP16 6FA NA      NA
# 15 Chepstow School NP16 6RR NA      NA

school_data_aggregated = school_data_complete %>%
  group_by(POSTCODE, BASE_NAME) %>%
  summarise(
    n = n(),
    EASTING = mean(EASTING),
    NORTHING = mean(NORTHING)
    ) %>%
  ungroup()
school_data_aggregated

school_data_sf = school_data_aggregated %>% st_as_sf(coords = c("EASTING", "NORTHING"), crs = 27700) %>% st_transform(4326)

mapview::mapview(school_data_sf)
chepstow_comprehensive = tmaptools::geocode_OSM("chepstow comprehensive school", as.sf = TRUE)
mapview::mapview(chepstow_comprehensive) # looks right, edit to put on intersection between Welse st +school
# chepstow_comprehensive_edited = mapedit::editFeatures(chepstow_comprehensive, z = 18)
# mapview::mapview(chepstow_comprehensive_edited)
# sf::write_sf(chepstow_comprehensive_edited, "input-data/chepstow-comprehensive-entrance-point.geojson")
chepstow_comprehensive_edited = sf::read_sf("input-data/chepstow-comprehensive-entrance-point.geojson")

origin_points = school_data_aggregated %>% select(POSTCODE)
destination_points = chepstow_comprehensive_edited
destination_points$bbox = NULL
destination_points[[1]] = unique(school_data_sf$BASE_NAME)

# l = od::od_to_sf(x = school_data_complete, z = origin_points, zd = destination_points) # fails -> issue
# l_school = stplanr::od2line(flow = school_data_complete, zones = origin_points, destinations = destination_points) # fails

coords_o = sf::st_coordinates(school_data_sf)
coords_d = sf::st_coordinates(destination_points)[rep(1, nrow(coords_o)), ]

school_data_sfc = od::odc_to_sfc(odc = cbind(coords_o, coords_d))
sf::st_crs(school_data_sfc) = 4326
plot(school_data_sfc)
nrow(school_data_aggregated)

school_data_desire_lines = sf::st_sf(school_data_aggregated, geometry = school_data_sfc)
mapview::mapview(school_data_desire_lines) +
mapview::mapview(school_data_sf)
saveRDS(school_data_desire_lines, "input-data/school_data_desire_lines_chepstow.Rds")
# test
school_data_route_segments = stplanr::route(l = school_data_desire_lines[1:9, ], route_fun = cyclestreets::journey, plan = "balanced")
mapview::mapview(school_data_route_segments)
# all
school_data_route_segments = stplanr::route(l = school_data_desire_lines, route_fun = cyclestreets::journey, plan = "balanced")
mapview::mapview(school_data_route_segments)
school_data_route_segments


system.time({
  school_data_route_segments$geo_text = sf::st_as_text(school_data_route_segments$geometry)
})

system.time({
  school_data_route_network = school_data_route_segments %>%
    # group_by(geometry) %>% # fails
    group_by(geo_text) %>%
    summarise(
      n = sum(n)
      )
})
system.time({
  rnet = stplanr::overline(sf::st_cast(school_data_route_segments, "LINESTRING"), "n")
})
br = c(0, 1, 2, 4, 8, 16, 32, 64)
plot(rnet, breaks = br)
plot(school_data_route_network["n"], breaks = br)
nrow(rnet)
nrow(school_data_route_network)
summary(rnet$n)
summary(school_data_route_network$n)

b_pct = c(0, 1, 2, 5, 10, 20, 50, 100, 500)

tmap_mode("view")

tm_shape(rnet) +
  tm_lines(col = "n", breaks = b_pct,
           # lwd = "n",
           scale = 4,
           palette = "Blues") +
  tm_scale_bar()

saveRDS(school_data_route_segments, "input-data/school_data_route_segments_balanced_chepstow.Rds")

u_wpz = "https://opendata.arcgis.com/datasets/176661b9403a4c84ae6aedf8bb4127cf_0.kml?outSR=%7B%22latestWkid%22%3A27700%2C%22wkid%22%3A27700%7D"
download.file("https://opendata.arcgis.com/datasets/176661b9403a4c84ae6aedf8bb4127cf_0.kml", "~/hd/data/raw/geo/wpz.kml")
wpz_uk_centroids = sf::read_sf("~/hd/data/raw/geo/wpz.kml")
nrow(wpz_uk_centroids)
# [1] 53578
saveRDS(wpz_uk_centroids, "~/hd/data/uk/centroids/wpz_ew.Rds")
oa_centroids = sf::read_sf("~/hd/data/uk/centroids/OA_2011_EW_PWC.shp")
oa_centroids
oa_2011_ew_pwc_wgs_4326 = sf::st_transform(oa_centroids, 4326)
saveRDS(oa_2011_ew_pwc_wgs_4326, "~/hd/data/uk/centroids/oa_2011_ew_pwc_wgs_4326.Rds")

