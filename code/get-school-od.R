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
school_data_sf = school_data %>% na.omit() %>% st_as_sf(coords = c("EASTING", "NORTHING"), crs = 27700)

mapview::mapview(school_data_sf)
