# Usage Guide — INPE BDC MCP Server

Complete guide with optimized prompts for all 68 tools of the MCP server. Each section contains the tool description, available parameters, and ready-to-use prompt examples for AI agents (Claude, etc.).

---

## Table of Contents

1. [Catalog](#1-catalog)
2. [Collections](#2-collections)
3. [Item Search](#3-item-search)
4. [Items and Assets](#4-items-and-assets)
5. [Data Cubes](#5-data-cubes)
6. [Satellites](#6-satellites)
7. [Biomes and Regions](#7-biomes-and-regions)
8. [Analysis and Code Generation](#8-analysis-and-code-generation)
9. [Spectral Indices](#9-spectral-indices)
10. [Preprocessing](#10-preprocessing)
11. [CRS Projection and Geometries](#11-crs-projection-and-geometries)
12. [Time Series](#12-time-series)
13. [LULC Classification](#13-lulc-classification)
14. [Change Detection](#14-change-detection)
15. [Administration](#15-administration)
16. [Combined Workflows](#16-combined-workflows)

---

## 1. Catalog

### `catalog_info()`

Returns STAC version, total collections, endpoints, and authentication status.

**Prompts:**

```
Show the general information of the INPE/BDC STAC catalog.

What is the STAC API version of the Brazil Data Cube? How many collections are available?

Check if my API key is correctly configured for BDC.
```

---

### `list_conformance_classes()`

Lists the implemented OGC conformance classes.

**Prompts:**

```
Which OGC conformance classes does the BDC STAC API implement?

Does the BDC API support CQL2 for advanced filters? Check the conformance classes.

List the OGC standards supported by the INPE data API.
```

---

### `get_api_capabilities()`

Summarizes API capabilities: CQL2, fields, sortby, authentication, pagination.

**Prompts:**

```
What are the capabilities of the BDC STAC API? Does it support sorting, pagination, and filters?

Can I use sortby and fields in the BDC API? What capabilities does it offer?

Summarize the advanced features of the INPE STAC API.
```

---

## 2. Collections

### `list_collections(category, satellite, biome, data_type, keyword, limit)`

Lists collections with combined filters.

| Parameter | Values |
|---|---|
| `category` | `raw_image`, `data_cube`, `mosaic`, `land_cover`, `modis`, `ocean`, `weather` |
| `satellite` | `CBERS-4`, `CBERS-4A`, `Amazonia-1`, `Sentinel-2`, `Landsat`, `MODIS`, `GOES-19` |
| `biome` | `cerrado`, `amazonia`, `mata_atlantica`, `pantanal`, `caatinga`, `pampa` |
| `data_type` | `SR` (surface reflectance), `DN` (digital numbers), `LCC` (land cover) |
| `keyword` | Free text |

**Prompts:**

```
List all available data cubes in BDC.

Which Sentinel-2 collections exist in BDC?

List the raw image collections from CBERS-4A.

Which land use classification (LCC) collections are available?

Search for collections that mention "mosaic" in the title.

List the available mosaics for the Amazon.

Which weather data collections exist in BDC?
```

---

### `get_collection_detail(collection_id)`

Complete metadata: bands, temporal/spatial extent, STAC extensions.

**Prompts:**

```
Show the complete details of the LANDSAT-16D-1 collection.

What is the temporal and spatial extent of the CBERS4-WFI-16D-2 data cube?

Detail the S2_L2A-1 collection — resolution, bands, coverage, and available period.

What metadata is available for the mosaic-landsat-amazon-3m-1 collection?
```

---

### `get_collection_bands(collection_id)`

Band information: wavelength, resolution, data type.

**Prompts:**

```
What spectral bands does the LANDSAT-16D-1 collection have?

List the Sentinel-2 L2A (S2_L2A-1) bands with wavelength and resolution.

What bands are available in the CBERS4-WFI-16D-2 data cube?

Does LANDSAT-16D-1 have pre-computed NDVI? What bands does it offer?
```

---

### `compare_collections(collection_ids)`

Compares multiple collections: common bands, resolution, coverage.

**Prompts:**

```
Compare the LANDSAT-16D-1 and CBERS4-WFI-16D-2 collections for vegetation monitoring.

What is the difference between S2_L2A-1 and LANDSAT-16D-1 in terms of bands and resolution?

Compare the CBERS-WFI-8D-1 and CBERS4-WFI-16D-2 data cubes — which has better temporal resolution?

Compare LANDSAT-16D-1, CBERS4-WFI-16D-2, and S2_L2A-1 for multitemporal analysis.
```

---

## 3. Item Search

### `search_items(collections, bbox, datetime_range, cloud_cover_max, limit, sortby)`

Advanced cross-collection search with multiple filters.

**Prompts:**

```
Search for Sentinel-2 images of the Cerrado in 2023 with less than 10% cloud cover.

Find LANDSAT-16D-1 items for the bbox [-50, -15, -49, -14] between 2020 and 2023.

Search for the 20 most recent CBERS4-WFI-16D-2 images for Goias.

Search for simultaneous Landsat and CBERS images for Mato Grosso in the second half of 2022.

Find LANDSAT-16D-1 composites for the Amazon between June and August 2021.
```

---

### `search_by_point(lon, lat, collections, datetime_range, cloud_cover_max)`

Searches for items containing a specific coordinate.

**Prompts:**

```
Search for all available images at point -49.5, -15.7 (Goiania) in 2023.

Find Sentinel-2 images covering coordinate -60.0, -3.1 (Manaus) with less than 20% cloud cover.

Which LANDSAT-16D-1 composites cover point -46.63, -23.55 (Sao Paulo) in 2022?

Search for CBERS-4A data covering -55.0, -12.5 between 2020 and 2023.
```

---

### `search_by_polygon(geojson_geometry, collections, datetime_range, cloud_cover_max)`

Searches for items intersecting a GeoJSON geometry.

**Prompts:**

```
Search for Landsat images intersecting this GeoJSON polygon: {"type": "Polygon", "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]]}

Find LANDSAT-16D-1 composites in 2022 covering this study area: [insert GeoJSON]

Search for Sentinel-2 images with less than 15% cloud cover for this farm geometry: [insert GeoJSON]
```

---

### `search_by_tile(collection_id, tile_id, datetime_range)`

Searches by specific BDC tile (6-digit format).

**Prompts:**

```
Search for all composites of tile 007004 in CBERS4-WFI-16D-2 in 2022.

Find items for tile 021019 in the LANDSAT-16D-1 collection between January and June 2023.

List all available items for BDC tile 013011 of LANDSAT-16D-1.
```

---

### `search_latest_items(collection_id, bbox, n, cloud_cover_max)`

The N most recent items from a collection.

**Prompts:**

```
Show the 5 most recent LANDSAT-16D-1 items for the Cerrado.

What are the 10 most recent CBERS4-WFI-16D-2 composites for Goias?

Find the most recent Sentinel-2 image for the Amazon with less than 10% cloud cover.

Last 3 LANDSAT-16D-1 composites for Mato Grosso do Sul.
```

---

### `search_cloud_free(collections, bbox, datetime_range, max_cloud)`

Images with lowest cloud cover, sorted from cleanest.

**Prompts:**

```
Find the cleanest Sentinel-2 images (least clouds) for the Pantanal in 2023.

Search for LANDSAT-16D-1 composites with maximum 5% cloud cover for the Amazon in the dry season of 2022 (June-October).

Which CBERS-4A images have the lowest cloud cover in the Cerrado of Goias in 2023?

Find the 20 cleanest Landsat images for Mato Grosso between 2020 and 2023.
```

---

### `get_all_pages(collections, bbox, datetime_range, cloud_cover_max, max_items)`

Iterates through all result pages (up to 5000 items).

**Prompts:**

```
Search for ALL LANDSAT-16D-1 items for the Cerrado from 2018 to 2023 (all pages).

How many CBERS4-WFI-16D-2 items exist for the Amazon? Search up to 5000 items.

Collect the complete catalog of Landsat composites for Goias between 2015 and 2023.
```

---

## 4. Items and Assets

### `get_item(collection_id, item_id)`

Complete item details: geometry, properties, assets.

**Prompts:**

```
Show the complete details of item LANDSAT-16D-1-item-001.

What properties does item CBERS4-WFI-16D-2_007004_2023-06-15 have?

Detail item [item ID] from collection S2_L2A-1 — cloud cover, geometry, date.
```

---

### `list_item_assets(collection_id, item_id)`

Lists assets with URLs, MIME type, bands, and whether it is COG.

**Prompts:**

```
List all available assets for item [item_id] of LANDSAT-16D-1.

Which bands can I download from item [item_id] of collection CBERS4-WFI-16D-2?

Does item [item_id] of S2_L2A-1 have data in COG format? List the assets.
```

---

### `get_asset_download_info(collection_id, item_id, asset_key)`

Generates download snippets (curl, wget, Python, R).

**Prompts:**

```
Generate the commands to download the NDVI band of item [item_id] from LANDSAT-16D-1.

How do I download the RED asset of item [item_id] via Python and via curl?

Give me the R code to access the NIR band of item [item_id] from CBERS4-WFI-16D-2.

Generate a download snippet for the thumbnail of item [item_id].
```

---

### `get_thumbnail_url(collection_id, item_id)`

Thumbnail URL for quick visualization.

**Prompts:**

```
What is the thumbnail URL for item [item_id] of LANDSAT-16D-1?

Show the preview link for item [item_id] of collection S2_L2A-1.
```

---

### `get_quicklook_bands(collection_id)`

Bands used in the quicklook/thumbnail.

**Prompts:**

```
Which bands are used to generate the quicklook for the LANDSAT-16D-1 collection?

How is the CBERS4-WFI-16D-2 thumbnail composed? Which RGB bands?
```

---

### `get_stac_item_as_geojson(collection_id, item_id)`

Item as pure GeoJSON Feature for GIS.

**Prompts:**

```
Export item [item_id] of LANDSAT-16D-1 as GeoJSON for use in QGIS.

Convert item [item_id] to GeoJSON Feature.
```

---

## 5. Data Cubes

### `list_data_cubes(satellite, temporal_period, biome)`

Lists BDC data cubes with filters.

**Prompts:**

```
What data cubes are available in BDC?

List the Landsat data cubes with 16-day temporal resolution.

Which CBERS data cubes exist for the Amazon?

Are there monthly composition data cubes? Which ones?

List the available 8-day data cubes.
```

---

### `get_bdc_grid_info(collection_id)`

BDC grid: projection, tile size, overlap.

**Prompts:**

```
What grid does LANDSAT-16D-1 use? Projection, tile size, and overlap.

Explain the BDC grid system for CBERS4-WFI-16D-2.

What is the projection and resolution of the grid used by the S2_L2A-1 collection?
```

---

### `get_cube_quality_info(collection_id)`

Quality bands (CLEAROB, CMASK, TOTALOB).

**Prompts:**

```
What quality bands does LANDSAT-16D-1 have and how to interpret them?

How to use the CMASK band of CBERS4-WFI-16D-2 to mask clouds?

Explain the values of the CLEAROB quality band of the Landsat data cube.

What do the CMASK values mean? How to use them to filter contaminated pixels?
```

---

### `find_cube_for_analysis(region, start_year, end_year, min_resolution_m, required_indices)`

Recommends the best data cube for an analysis.

**Prompts:**

```
Which data cube should I use to analyze NDVI time series in Goias from 2019 to 2023?

Recommend a data cube with up to 30m resolution for the Cerrado that has NDVI and EVI.

What is the best data cube to monitor vegetation in Mato Grosso between 2020 and 2024 with minimum 64m resolution?

I need a data cube with NDVI for the Amazon from 2015 to 2023. Which one to use?

Which data cube has the best temporal resolution for monitoring crops in Goias?
```

---

## 6. Satellites

### `get_cbers_collections(version)`

CBERS collections with sensors (PAN5M, PAN10M, MUX, WFI, HRC).

**Prompts:**

```
What CBERS collections are available in BDC?

List only the CBERS-4A collections with their sensors and resolutions.

Which CBERS-4 sensors can I use? PAN5M, MUX, WFI — what is the difference?

Does CBERS-2B still have data available in BDC?
```

---

### `get_sentinel2_collections()`

Available Sentinel-2 collections.

**Prompts:**

```
Which Sentinel-2 collections are in BDC? Does it have L1C and L2A?

List the Sentinel-2 collections — raw images, cubes, and mosaics.

Is there a Sentinel-2 data cube in BDC?
```

---

### `get_landsat_collections()`

Available Landsat collections.

**Prompts:**

```
Which Landsat collections exist in BDC?

List all Landsat products — raw, data cubes, and mosaics.

Does BDC have 16-day Landsat composites? And bimonthly?
```

---

### `get_goes19_info()`

GOES-19 CMI data.

**Prompts:**

```
What GOES-19 data is available in BDC?

Does BDC have weather data? What GOES-19 bands?

What is the acquisition frequency of GOES-19 CMI?
```

---

### `get_amazonia1_collections()`

Amazonia-1 satellite — 100% Brazilian.

**Prompts:**

```
What data from the Amazonia-1 satellite is available?

Tell me about Amazonia-1 — sensor, resolution, coverage.

Does Amazonia-1 have data in BDC? What spatial resolution?
```

---

### `get_sentinel3_info()`

Sentinel-3 OLCI — ocean/coastal data.

**Prompts:**

```
Does BDC have Sentinel-3 data? Which products?

Are there ocean color data available? Sentinel-3 OLCI?

What coastal/ocean data can I access via BDC?
```

---

## 7. Biomes and Regions

### `get_biome_bbox(biome)`

WGS84 bounding box for biomes, states, and regions.

| Type | Accepted values |
|---|---|
| Biomes | `amazonia`, `cerrado`, `mata_atlantica`, `caatinga`, `pantanal`, `pampa` |
| States | `goias`, `mato_grosso`, `para`, `minas_gerais`, `bahia`, etc. |
| Regions | `matopiba`, `arco_desmatamento`, `norte`, `nordeste`, `sudeste`, `sul`, `centro_oeste` |

**Prompts:**

```
What is the bounding box of the Cerrado?

Give me the Pantanal coordinates in WGS84.

What is the bbox of MATOPIBA?

Geographic coordinates of the deforestation arc.

What is the geographic extent of the state of Goias?

Give me the bbox of the North region of Brazil.
```

---

### `find_collections_for_biome(biome, category, satellite)`

Collections with coverage of a biome.

**Prompts:**

```
Which collections cover the Cerrado?

Find data cubes available for the Amazon.

Which Landsat collections cover the Pantanal?

List the raw image collections available for the Caatinga.

What Sentinel-2 data covers the Atlantic Forest?
```

---

### `get_cerrado_monitoring_collections()`

Cerrado monitoring package.

**Prompts:**

```
Which collections are recommended for monitoring the Cerrado?

Build a data kit for land use monitoring in the Cerrado.

What data to use for tracking deforestation in the Cerrado?
```

---

### `get_amazon_monitoring_collections()`

Amazon monitoring package.

**Prompts:**

```
Which collections to use for monitoring deforestation in the Amazon?

Build a data kit for Amazon monitoring.

What data does INPE recommend for Amazon forest degradation analysis?
```

---

### `get_deforestation_analysis_collections()`

Complete deforestation analysis package.

**Prompts:**

```
Which collections to use for a complete deforestation analysis?

Build a data package to detect and quantify deforestation.

I need data to compare deforestation across biomes. Which collections?
```

---

## 8. Analysis and Code Generation

### `discover_collections_for_topic(topic)`

Suggests collections by topic in natural language.

**Prompts:**

```
Which collections to use for studying deforestation in the Cerrado?

Suggest data for coastal water quality monitoring.

I need data to analyze soybean expansion in Mato Grosso. What to use?

Which collections are suitable for studying NDVI time series in the Amazon?

Data for monitoring degraded pastures in Goias.

Suggest collections for urban heat island analysis.
```

---

### `build_python_search_snippet(collections, bbox_or_biome, datetime_range, cloud_max, asset_keys)`

Generates complete Python code with pystac-client.

**Prompts:**

```
Generate Python code to search LANDSAT-16D-1 images in the Cerrado from 2020 to 2023.

Give me the Python snippet to access NDVI and EVI from CBERS4-WFI-16D-2 in Mato Grosso.

Python code to search Sentinel-2 with less than 10% cloud cover in bbox [-50, -15, -49, -14].

Generate complete Python code to download LANDSAT-16D-1 images for the Amazon in 2022.
```

---

### `build_r_snippet(collections, bbox_or_biome, datetime_range, cloud_max)`

Generates R code with rstac.

**Prompts:**

```
Generate R code using rstac to search LANDSAT-16D-1 data in the Cerrado.

Give me the R snippet to access CBERS composites in the Pantanal in 2023.

R code to search Sentinel-2 images in the Amazon with cloud filter.
```

---

### `get_time_series_plan(collection_id, bbox_or_biome, start_year, end_year, band)`

Time series plan: expected items, volume, Python snippet.

**Prompts:**

```
Build a NDVI time series plan for the Cerrado using LANDSAT-16D-1 from 2018 to 2024.

How many composites to expect from CBERS4-WFI-16D-2 for Goias between 2020 and 2023?

Plan EVI time series extraction for the deforestation arc, 2019 to 2023.

What is the expected data volume for an NDVI time series in the Amazon?
```

---

## 9. Spectral Indices

### `list_spectral_indices(category)`

Lists 20 indices with category filter.

| Category | Indices |
|---|---|
| `vegetation` | NDVI, EVI, EVI2, SAVI, MSAVI2, GNDVI, ARVI, SIPI, CRI1, NDMI |
| `water` | NDWI, MNDWI |
| `burn` | NBR, NBR2, BAI, MIRBI |
| `soil` | BSI, CMRI |
| `urban` | NDBI |
| `snow` | NDSI |

**Prompts:**

```
List all available spectral indices.

Which vegetation indices are available?

List the indices for fire detection.

Which indices exist for water monitoring?

Show the available soil indices.
```

---

### `get_spectral_index_info(index_name)`

Index details: formula, bands, applications, reference.

**Prompts:**

```
Explain the NDVI index — formula, required bands, and applications.

What is the difference between EVI and EVI2? When to use each?

Detail the NBR index — what it is used for, formula, and value range.

Explain SAVI and when it is better than NDVI.

What is MIRBI? What is it used for in the Cerrado?

What is the BAI formula and how to interpret its values?
```

---

### `get_collection_index_availability(collection_id)`

Checks which indices are computable with a collection's bands.

**Prompts:**

```
Which spectral indices can I compute with the LANDSAT-16D-1 collection?

Does CBERS4-WFI-16D-2 have enough bands to compute NBR?

Which indices are pre-computed in the LANDSAT-16D-1 collection?

Can I compute MNDWI from Sentinel-2 L2A?

Which indices can I NOT compute with CBERS-4 WFI bands?
```

---

### `generate_index_code(index_name, collection_id, language)`

Generates Python, R, or sits code to compute an index.

**Prompts:**

```
Generate the Python code to compute NDVI from LANDSAT-16D-1.

Give me the R snippet to compute NBR using Sentinel-2 data.

Generate sits code to compute EVI on the CBERS4-WFI-16D-2 collection.

How to compute SAVI in Python using the LANDSAT-16D-1 collection?

Generate code to compute MNDWI from LANDSAT-16D-1 in Python.

Give me the R code to compute BAI using LANDSAT-16D-1.
```

---

### `suggest_indices_for_application(application)`

Suggests indices for a specific application.

| Application | Suggested indices |
|---|---|
| `vegetation` | NDVI, EVI, EVI2, SAVI, GNDVI, NDMI |
| `fire` / `burn` | NBR, NBR2, BAI, MIRBI |
| `water` | NDWI, MNDWI |
| `deforestation` | NDVI, EVI, NBR, NDMI |
| `agriculture` | NDVI, EVI, EVI2, GNDVI, SAVI |
| `pasture` | NDVI, EVI2, SAVI, MSAVI2 |
| `drought` | NDMI, NDVI, SAVI |
| `cerrado` | NDVI, EVI2, SAVI, MIRBI, NBR |
| `amazonia` | NDVI, EVI, NDMI, NBR |

**Prompts:**

```
Which indices to use for monitoring fires in the Cerrado?

Suggest spectral indices for mapping degraded pastures.

Which indices are most suitable for detecting deforestation?

Indices for drought and water stress monitoring?

Which indices to use for mapping water in urban areas?

Suggest indices for precision agriculture.
```

---

## 10. Preprocessing

### `get_preprocessing_guide(collection_id)`

Correction level already applied, what is missing, and recommendations.

**Prompts:**

```
What is the preprocessing level of the LANDSAT-16D-1 collection? What is already corrected?

Does the CBERS4-WFI-16D-2 data need atmospheric correction?

I need surface reflectance data. Does the CB4-MUX-L2-DN-1 collection work or do I need to correct it?

What is the preprocessing guide for raw CBERS-4 images?

Is the LANDSAT-16D-1 data cube ARD (Analysis Ready Data)? What is missing?
```

---

### `get_cloud_mask_strategy(collection_id)`

Cloud masking strategy: CMASK, SCL, Fmask.

**Prompts:**

```
How to mask clouds in LANDSAT-16D-1? Which band to use and what values?

Give me the Python code to apply cloud mask on CBERS4-WFI-16D-2 using CMASK.

What is the cloud masking strategy for Sentinel-2 L2A in BDC?

Generate R code to filter cloud and shadow pixels in the LANDSAT-16D-1 collection.

What do the CMASK band values mean? How to interpret them?
```

---

### `get_atmospheric_correction_info(collection_id)`

Atmospheric correction algorithm applied.

**Prompts:**

```
What atmospheric correction algorithm was applied to LANDSAT-16D-1?

Does the CB4-WFI-L4-SR-1 collection already have atmospheric correction? Which one?

Do the BDC Sentinel-2 L2A images use Sen2Cor?

Do I need to atmospherically correct the CB4-MUX-L2-DN-1 images?
```

---

### `get_pan_sharpening_guide(collection_id)`

Pan-sharpening guide for CBERS panchromatic.

**Prompts:**

```
How to do pan-sharpening of CBERS-4 PAN5M with MUX?

Generate a guide for fusing PAN10M with WFI on CBERS-4A.

Is it possible to combine PAN5M and MUX from CBERS-4 to get 5m multispectral? How?

What is the best pan-sharpening technique for CBERS data?
```

---

## 11. CRS Projection and Geometries

### `reproject_bbox(bbox, from_crs, to_crs)`

Reprojection between CRS: WGS84, BDC Albers, UTM, SIRGAS2000.

| CRS Alias | Description |
|---|---|
| `EPSG:4326` / `wgs84` | WGS84 (degrees) |
| `bdc_albers` / `EPSG:100001` | BDC Albers Equal-Area (meters) |
| `EPSG:4674` / `sirgas2000` | SIRGAS 2000 |
| `EPSG:327xx` | UTM South zone |

**Prompts:**

```
Convert the bbox [-50, -15, -49, -14] from WGS84 to BDC Albers.

Reproject the Cerrado bbox from geographic coordinates to UTM zone 22S.

Convert bbox from BDC Albers back to WGS84.

Transform coordinates [-60, -12, -55, -8] to SIRGAS 2000.

What is the extent in meters of bbox [-50, -15, -49, -14] in BDC Albers?
```

---

### `calculate_area(bbox, geojson, crs)`

Calculates area in m², hectares, and km².

**Prompts:**

```
What is the area in hectares of bbox [-50, -15, -49, -14]?

Calculate the area of this region: [-53.2, -19.5, -45.9, -12.4] (Goias).

What is the area in km² of this GeoJSON polygon? {"type": "Polygon", "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]]}

Calculate the area of my farm defined by this GeoJSON: [insert geometry]

How many hectares is the Pantanal bbox?
```

---

### `get_utm_zone(lon, lat)`

Returns UTM zone and EPSG for a coordinate.

**Prompts:**

```
What is the UTM zone for Goiania (-49.25, -16.68)?

Which UTM zone is Manaus (-60.02, -3.12) in?

What is the EPSG code for the UTM zone covering Sao Paulo (-46.63, -23.55)?

Identify the UTM zone for coordinate -55.0, -12.5 in Mato Grosso.
```

---

### `convert_geometry_format(geometry, to_format)`

Converts between GeoJSON and WKT.

**Prompts:**

```
Convert this GeoJSON to WKT: {"type": "Polygon", "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]]}

Convert this WKT to GeoJSON: POLYGON ((-50 -15, -49 -15, -49 -14, -50 -14, -50 -15))

Transform my GeoJSON polygon to WKT format for use in PostGIS.

Convert this WKT study area to GeoJSON for use in STAC: [insert WKT]
```

---

## 12. Time Series

### `plan_time_series_extraction(collection_id, bbox_or_biome, start_year, end_year, bands, output_format)`

Advanced plan with complete sits and Python code.

**Prompts:**

```
Build a complete plan to extract NDVI and EVI time series from LANDSAT-16D-1 for the Cerrado, 2018 to 2023.

Plan the extraction of RED and NIR time series from the Amazon using CBERS4-WFI-16D-2, 2020-2023.

I want to extract an NDVI time series for bbox [-50, -15, -49, -14] from LANDSAT-16D-1. Generate the plan with Python and sits code.

Build a multiband time series extraction plan (NDVI, EVI, SWIR16) for Mato Grosso, 2019-2024, with CSV output.

Plan an NDVI time series for the Pantanal using bimonthly Landsat composites.
```

---

### `get_filtering_guide(method)`

Filtering methods guide with snippets.

| Method | Description |
|---|---|
| `savitzky_golay` | Local polynomial filter, preserves phenological peaks |
| `whittaker` | Smoother with penalty, robust to gaps |
| `cloud_filter` | Cloud mask + interpolation |

**Prompts:**

```
What is the best filtering method for NDVI time series?

Compare Savitzky-Golay and Whittaker for time series smoothing.

Give me the complete Whittaker filter guide with Python, R, and sits code.

How to use Savitzky-Golay filter on satellite time series? What parameters?

Which filtering method works best with series that have many gaps (clouds)?

List all available filtering methods with pros and cons.
```

---

### `plan_phenology_extraction(collection_id, bbox_or_biome, band)`

Phenological metrics: SOS, EOS, Peak, Amplitude, LOS.

**Prompts:**

```
Build a plan to extract phenological metrics from NDVI in the Cerrado using LANDSAT-16D-1.

How to extract SOS (Start of Season) and EOS (End of Season) from NDVI time series in the Amazon?

Plan phenological analysis for crop monitoring in Goias using EVI.

Generate Python and sits code to calculate phenological amplitude and length of season in Mato Grosso.

I want to identify planting and harvesting dates via NDVI phenology. Build the plan.
```

---

### `analyze_temporal_gaps(collection_id, bbox_or_biome, datetime_range)`

Temporal gap analysis via real STAC search.

**Prompts:**

```
Analyze the temporal gaps of LANDSAT-16D-1 for Mato Grosso in 2022.

Is the CBERS4-WFI-16D-2 time series in the Cerrado complete from 2020 to 2023? Are there gaps?

Verify the temporal completeness of the LANDSAT-16D-1 collection for the Amazon between 2018 and 2023.

How many observations are missing in the LANDSAT-16D-1 series for Goias in 2021?

Analyze gaps of LANDSAT-16D-1 in bbox [-50, -15, -49, -14] from 2020 to 2023.
```

---

### `generate_sits_cube_code(collection_id, bbox_or_biome, start_year, end_year, bands)`

Complete R sits code: sits_cube to sits_get_data.

**Prompts:**

```
Generate complete sits code to create a LANDSAT-16D-1 cube of the Cerrado with NDVI and EVI, 2020 to 2023.

R sits code to access CBERS4-WFI-16D-2 data in the Amazon from 2019 to 2022.

Generate the sits workflow to create a cube, regularize, and extract time series from LANDSAT-16D-1 in Mato Grosso.

Sits code to create a cube with RED, NIR, SWIR16 bands from LANDSAT-16D-1 for the Pantanal.

Generate sits code for a bimonthly Landsat data cube in the Amazon.
```

---

## 13. LULC Classification

### `plan_classification_workflow(region, start_year, end_year, classes, algorithm)`

Complete classification plan in 9 steps with sits and Python code.

| Algorithm | Key |
|---|---|
| Random Forest | `random_forest` |
| SVM | `svm` |
| XGBoost | `xgboost` |
| LightGBM | `lightgbm` |
| TempCNN / ResNet | `deep_learning` |

**Prompts:**

```
Build a complete land use classification workflow for the Cerrado from 2020 to 2023 with Random Forest.

Plan a LULC classification of the Amazon with XGBoost, classes: Forest, Pasture, Agriculture, Water, Urban.

Create a classification plan with SVM for the Pantanal, 2021-2023, with 4 cover classes.

Build a classification workflow with Deep Learning (TempCNN) for Mato Grosso, 2019-2023.

Plan a land use classification for MATOPIBA with classes: Soybean, Corn, Cerrado, Pasture, Water.

I want to classify land use in Goias. Build the complete plan with sits and Python code.
```

---

### `get_sample_design_guide(region, classes, total_samples)`

Stratified sample design.

**Prompts:**

```
How to plan sampling for classification with 6 classes in the Cerrado?

How many samples do I need per class for a reliable classification?

Build a sample plan for Forest/Pasture/Agriculture classification in the Amazon with 500 samples.

What is the ideal sampling strategy for 8 LULC classes in Mato Grosso?

How to distribute 1000 samples across 5 land use classes?

Generate sits and Python code to load and validate training samples.
```

---

### `get_ml_algorithm_guide(use_case)`

Algorithm comparison with recommendations per use case.

| Use case | Key |
|---|---|
| Few samples | `few_samples` |
| Maximum accuracy | `high_accuracy` |
| Speed | `fast` |
| Large area | `large_area` |
| Time series | `temporal` |

**Prompts:**

```
Which ML algorithm should I use for classification with few samples (<200 per class)?

Compare Random Forest, SVM, and XGBoost for time series classification.

What is the best algorithm for large area classification (entire state)?

I need fast training. LightGBM or XGBoost?

When is it worth using Deep Learning (TempCNN) instead of Random Forest?

Give me a complete guide of all algorithms with pros, cons, and hyperparameters.
```

---

### `get_accuracy_assessment_guide(n_classes)`

Assessment guide: OA, Kappa, F1, confusion matrix.

**Prompts:**

```
How to evaluate the accuracy of my classification with 6 classes?

Generate Python code to compute confusion matrix, Kappa, and F1-score.

What is the minimum number of validation samples for 8 classes?

Give me the complete accuracy assessment guide with sits and Python code.

How to interpret Overall Accuracy vs Kappa? What value is good?

Generate Python and R code to produce a per-class accuracy report.
```

---

### `generate_sits_classification_code(collection_id, region, algorithm, classes, start_year, end_year)`

Complete R sits code for classification (10 steps).

**Prompts:**

```
Generate complete sits code to classify the Cerrado with Random Forest using LANDSAT-16D-1, 2020-2023.

Sits code for Amazon classification with XGBoost, classes Forest/Pasture/Agriculture/Water.

Generate the complete sits script for classification with TempCNN in Mato Grosso.

R sits code for land use classification in the Pantanal with LightGBM, 2021-2023.

Generate sits code to classify Goias with SVM using LANDSAT-16D-1, classes: Soybean, Corn, Cerrado, Pasture, Water, 2020-2022.
```

---

## 14. Change Detection

### `list_change_detection_methods()`

Lists available methods: BFAST, LandTrendr, dNBR, NDVI Anomaly.

**Prompts:**

```
Which change detection methods are available?

List the algorithms for detecting land cover changes.

What techniques exist for identifying deforestation in time series?
```

---

### `plan_change_detection(method, region, start_year, end_year)`

Complete plan with Python and R code.

**Prompts:**

```
Build a change detection plan with BFAST for the Amazon, 2018-2023.

Plan NDVI anomaly analysis for the Cerrado between 2020 and 2023.

Create a change detection plan using LandTrendr in Mato Grosso, 2010-2023.

Build a change analysis with dNBR in Chapada dos Veadeiros, 2019-2023.

Plan change detection via NDVI anomaly for monitoring drought in the northeastern semi-arid region.
```

---

### `plan_fire_scar_detection(region, event_date)`

Fire scar detection with dNBR and USGS severity classification.

**Prompts:**

```
Detect fire scars in the Cerrado near the date 2023-08-15.

Plan a burn severity analysis in the Amazon for the September 2022 event.

Build a plan for burned area detection in Chapada dos Veadeiros in October 2023.

Analyze fires in the Pantanal near August 2020. Generate code with severity classification.

Detect fire in bbox [-48, -16, -47, -15] near July 2023.

Build a fire analysis for Serra da Canastra in September 2022.
```

---

### `plan_deforestation_detection(region, start_year, end_year, method)`

Deforestation detection with BFAST or LandTrendr.

**Prompts:**

```
Plan deforestation detection in the Amazon with BFAST, 2018 to 2023.

Build a deforestation analysis for the Cerrado with LandTrendr from 2010 to 2023.

Detect deforestation in the deforestation arc using BFAST, 2019-2024.

Plan deforestation monitoring in Para with BFAST, 2020-2023.

Compare BFAST and LandTrendr for detecting deforestation in Mato Grosso from 2015 to 2023.
```

---

## 15. Administration

### `get_api_metrics()`

API usage metrics: calls, latency, cache hits.

**Prompts:**

```
Show the BDC API usage metrics for this session.

How many API calls have been made? What is the average latency?

What is the cache hit rate?
```

---

### `invalidate_cache(namespace)`

Invalidate cache by namespace or entirely.

| Namespace | Description |
|---|---|
| `collection` | Individual collections cache |
| `collections_list` | Collections list cache |
| `item` | Items cache |
| (empty) | Clear all cache |

**Prompts:**

```
Clear all MCP server cache.

Invalidate the collections cache to force refresh.

Clear the items cache.
```

---

## 16. Combined Workflows

Prompts that combine multiple tools for complete workflows.

### Workflow: Degraded Pasture Monitoring

```
I need to monitor degraded pastures in Goias from 2019 to 2024. Build the complete workflow:
1. Which data cube to use?
2. Which spectral indices are ideal for pasture?
3. Generate sits code to extract NDVI and SAVI time series.
4. Plan the classification with classes: Good Pasture, Degraded Pasture, Agriculture, Cerrado, Water.
5. How to evaluate accuracy?
```

### Workflow: Complete Fire Analysis

```
There were fires in the Cerrado of Goias in August 2023. Build a complete analysis:
1. Detect fire scars using dNBR.
2. Which indices to use for complementary fire analysis?
3. Check if there are temporal gaps in LANDSAT-16D-1 for this period.
4. Generate complete Python and R code.
5. Calculate the burned area in hectares.
```

### Workflow: Amazon LULC Classification

```
Classify land use in southern Para, 2020-2023:
1. Recommend the best data cube.
2. Build the classification plan with XGBoost.
3. Which classes to use (Forest, Pasture, Agriculture, Water, Urban)?
4. Sample design for 1000 samples.
5. Generate complete sits code.
6. Accuracy assessment guide.
```

### Workflow: Time Series for Agricultural Phenology

```
I want to analyze soybean crop phenology in Mato Grosso:
1. Which data cube and bands to use?
2. Build an NDVI and EVI time series extraction plan, 2018-2024.
3. Which filter to use for smoothing the series?
4. Extract phenological metrics (SOS as planting date, EOS as harvest).
5. Generate sits and Python code.
```

### Workflow: Amazon Deforestation Monitoring

```
Build a complete deforestation monitoring system for the Amazon:
1. Which collections to use (BDC data + PRODES/DETER reference)?
2. Analyze temporal gaps of LANDSAT-16D-1 for the Amazon.
3. Plan detection with BFAST, 2018-2024.
4. Generate Python and R code.
5. How to validate against INPE PRODES data?
```

### Workflow: Multi-Sensor Comparison

```
Compare Landsat, CBERS, and Sentinel-2 data for Cerrado monitoring:
1. Compare the LANDSAT-16D-1, CBERS4-WFI-16D-2, and S2_L2A-1 collections.
2. Which bands and indices does each one offer?
3. Which has the best temporal and spatial resolution?
4. Generate code to search data from all three sources simultaneously.
```

### Workflow: Drought Impact Analysis

```
Analyze the impact of drought in the northeastern semi-arid region:
1. Which indices to use for monitoring drought (NDMI, NDVI, SAVI)?
2. Build an NDVI anomaly detection plan for the Caatinga, 2019-2023.
3. Generate NDMI and NDVI time series.
4. Identify periods of severe anomaly.
5. Calculate the affected area.
```

---

## Usage Tips

### Accepted Region Names

The server recognizes biomes, states, and special regions as bbox:

- **Biomes**: `amazonia`, `cerrado`, `mata_atlantica`, `caatinga`, `pantanal`, `pampa`
- **States**: `goias`, `mato_grosso`, `para`, `minas_gerais`, `bahia`, `sao_paulo`, `rio_de_janeiro`, `tocantins`, `maranhao`, `piaui`, `mato_grosso_do_sul`, etc.
- **Regions**: `matopiba`, `arco_desmatamento`, `norte`, `nordeste`, `sudeste`, `sul`, `centro_oeste`

### Date Format

Always use ISO 8601: `"2020-01-01/2023-12-31"`

### Bbox Format

Array with 4 values: `[min_lon, min_lat, max_lon, max_lat]` (WGS84)

Example: `[-50.0, -15.0, -49.0, -14.0]`

### Most Used Collection IDs

| Use | Collection |
|---|---|
| Landsat 30m time series | `LANDSAT-16D-1` |
| CBERS 64m time series | `CBERS4-WFI-16D-2` |
| High resolution 10m | `S2_L2A-1` |
| Quick 8-day coverage | `CBERS-WFI-8D-1` |
| Bimonthly composite | `landsat-tsirf-bimonthly-1` |
| Amazon mosaic | `mosaic-landsat-amazon-3m-1` |
| MODIS NDVI 250m | `mod13q1-6.1` |
