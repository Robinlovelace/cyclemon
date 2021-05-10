# previous caption:
# simple buffer and three stage buffering approaches to identify areas of interest within which travel to destinations in the zones could take place. The D represents the desination of interest.
chepstow = sf::read_sf("../input-data/chepstow.geojson")
# aim: generate buffers (update stplanr)
# chepstow_buffer = stplanr::geo_buffer(chepstow, dist = 10000) # fails
buffer_dist = 5000
region_buffer_dist = 2000
zone_buffer = chepstow_comp %>%
  sf::st_transform(27700) %>%
  sf::st_buffer(buffer_dist) %>%
  sf::st_transform(4326)
region_buffer = monmouthshire %>%
  sf::st_transform(27700) %>%
  sf::st_buffer(region_buffer_dist) %>%
  sf::st_transform(4326)
zone_buffer_in_region = sf::st_intersection(zone_buffer, region_buffer)

# tm_shape(zone_buffer, bbox = tmaptools::bb(zone_buffer, 1.5)) +
#   tm_polygons(col = "green", alpha = 0.4) +
#   tm_shape(monmouthshire) +
#   tm_polygons(lwd = 5) +
#   tm_shape(region_buffer) +
#   tm_borders(lwd = 5, lty = 2) +
#   tm_shape(zone_buffer) +
#   tm_polygons(col = "green", alpha = 0.4) +
#   tm_shape(monmouthshire) +
#   tm_borders(lwd = 5) +
#   tm_shape(chepstow) +
#   tm_polygons(col = "red") +
#   tm_scale_bar(position = "left") +
#   qtm(chepstow_comp %>% mutate(txt = "D")) + tm_text("txt", bg.color = "white", size = 2)
#
# tm_shape(zone_buffer_in_region, bbox = tmaptools::bb(zone_buffer_in_region, 1.5)) +
#   tm_polygons(col = "green", alpha = 0.4) +
#   tm_shape(monmouthshire) +
#   tm_polygons(lwd = 5) +
#   tm_shape(region_buffer) +
#   tm_borders(lwd = 5, lty = 2) +
#   tm_shape(zone_buffer_in_region) +
#   tm_polygons(col = "green", alpha = 0.4) +
#   tm_shape(monmouthshire) +
#   tm_borders(lwd = 5) +
#   tm_shape(chepstow) +
#   tm_polygons(col = "red") +
#   tm_scale_bar(position = "left") +
#   qtm(chepstow_comp %>% mutate(txt = "D")) + tm_text("txt", bg.color = "white", size = 2)

# mapview::mapview(chepstow_buffer_in_region)
# plot(chepstow)
# abber = readRDS("../input-data/abergavenny.geojson")


# # text:
#
# <!-- Todo: resolve this comment (CC): -->
#   <!-- I haven’t buffered in this way – I’m still reluctant to discard out-of-region flows (although I do cut everything off at the severn bridge) -->
#   <!-- From a data quantity perspective I have fixed a lot of issues in recent automation. Turns out OSM had a lot of pseudonodes leading to much higher link counts than necessary especially after running through my sidewalk tool. These are fixed now.  -->
#   <!-- We tested two approaches to define the 'area of interest' defining the area within which routes were calculated: a simple buffer and a three-stage buffering process, as illustrated in Figure \@ref(fig:buffers). -->
#   <!-- The simple buffer approach involved creating polygon with borders a fixed distance (5 km in the first instance) around the destination (in this case the parishes of Chepstown and Abergavenny). -->
#   <!-- Model run times (and visualisation load times in interactive maps) depend on the amount of data served, creating an incentive reduce the size of the input data, and from a policy perspective, it makes sense to focus on the area over which local planners have control (and budget). -->
#   <!-- In this context, the three-stage process was developed as follows: -->
#
#   <!-- 1. Create a buffer around the zone of interest with a threshold distance (set to 5 km) -->
#   <!-- 2. Create a separate buffer around the region of interest to allow for some (more limited) inter-regional flow (set to 2 km) -->
#   <!-- 3. Calculate the intersection between the two buffers outlined in the previous stages -->
#
#   <!-- The advantages of the simple buffer approach included simplicity and minimisation of parameters that had to be hard-coded into the analysis.  -->
#   <!-- Taking both factors into account, we use the simple approach represented in the left hand plot of Figure \@ref(fig:buffers), saving the three stage approach for contexts where it is advantageous to model cross-region flow but also to reduce the proportion of trips modelled crossing regional/state boundaries. -->
#
#   <!-- This process is now available as a function, ... in the package stplanr. -->
