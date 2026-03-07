# INPE BDC MCP Server

MCP Server for the **INPE/Brazil Data Cube STAC API** — access to satellite imagery, composite data cubes, mosaics, land use classifications, spectral indices, time series, and LULC classification workflows for AI agents.

## Overview

The [Brazil Data Cube (BDC)](https://brazildatacube.dpi.inpe.br/) is an INPE project that produces and provides Analysis-Ready Data (ARD) for Earth observation. The catalog includes:

- **Brazilian satellites**: CBERS-4, CBERS-4A, Amazonia-1
- **International satellites**: Sentinel-2, Sentinel-3, Landsat, MODIS, GOES-19
- **Temporal data cubes**: 8-day, 16-day, or monthly composites with NDVI/EVI
- **Regional mosaics**: Amazon, São Paulo, Paraíba, entire Brazil
- **Land use classifications**: Cerrado, Atlantic Forest, Pantanal
- **Ocean data**: chlorophyll-a, ocean color (MODIS-Aqua)
- **Weather data**: GOES-19 CMI

**STAC API base:** `https://data.inpe.br/bdc/stac/v1/`

The server exposes **68 tools**, **7 prompts**, and **7 resources** organized into 12 thematic modules, covering everything from data discovery to complete land use classification workflows inspired by the R package [sits](https://e-sensing.github.io/sitsbook/).

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended)

## Installation

```bash
# With uv (recommended)
cd inpe-bdc-mcp
uv sync

# Or with pip
pip install -e .
```

## Authentication

Authentication is **optional** for public collections. For restricted collections, obtain an API key from the [BDC portal](https://brazildatacube.dpi.inpe.br/).

```bash
export BDC_API_KEY="your-key-here"
```

## Claude Code Registration

### Via CLI (recommended)

```bash
claude mcp add -s user -t stdio inpe-bdc -e BDC_API_KEY="your-key-here" -- uv run --directory /path/to/inpe-bdc-mcp python -m inpe_bdc_mcp
```

### Via settings.json

Add to your `~/.claude/settings.json` or project `.claude/settings.json`:

```json
{
  "mcpServers": {
    "inpe-bdc": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/inpe-bdc-mcp", "python", "-m", "inpe_bdc_mcp"],
      "env": {
        "BDC_API_KEY": ""
      }
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "inpe-bdc": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/inpe-bdc-mcp", "python", "-m", "inpe_bdc_mcp"],
      "env": {
        "BDC_API_KEY": ""
      }
    }
  }
}
```

## Architecture

```
src/inpe_bdc_mcp/
├── server.py               # FastMCP entrypoint — registers 68 tools + 7 prompts + 7 resources
├── client.py               # Singleton HTTP client for STAC API (httpx)
├── auth.py                 # Authentication (API key)
├── catalogs.py             # Static catalog of collections, bands, and constants
├── models/                 # Pydantic models
│   ├── collection.py       #   STAC collections
│   ├── item.py             #   STAC items
│   ├── search.py           #   Search and time series
│   ├── spectral.py         #   Spectral indices
│   ├── preprocessing.py    #   Preprocessing
│   ├── classification.py   #   LULC classification
│   └── change_detection.py #   Change detection and phenology
├── tools/                  # Tool modules (business logic)
│   ├── catalog.py          #   Catalog and conformance
│   ├── collections.py      #   Collections and bands
│   ├── search.py           #   Item search
│   ├── items.py            #   Items and assets
│   ├── datacube.py         #   Data cubes
│   ├── satellites.py       #   Satellites
│   ├── biomes.py           #   Biomes and regions
│   ├── analysis.py         #   Analysis and code generation
│   ├── spectral.py         #   Spectral indices (20 indices)
│   ├── preprocessing.py    #   Image preprocessing
│   ├── projection.py       #   CRS projection and geometries
│   ├── timeseries.py       #   Time series (sits)
│   ├── classification.py   #   LULC classification (sits)
│   └── change_detection.py #   Change detection
├── resources/              # MCP Resources
│   ├── catalog.py
│   └── collections.py
└── utils/                  # Utilities
    ├── brazil.py           #   Biomes, states, and regions of Brazil
    ├── bdc_grid.py         #   BDC grid
    ├── cache.py            #   In-memory TTL cache
    ├── geo.py              #   Geospatial utilities
    └── metrics.py          #   API usage metrics
```

## Tools (68 Tools)

### Catalog (3)

| Tool | Description |
|---|---|
| `catalog_info()` | General catalog information: STAC version, total collections, endpoints |
| `list_conformance_classes()` | Implemented OGC conformance classes |
| `get_api_capabilities()` | API capabilities: CQL2, fields, sortby, authentication |

### Collections (4)

| Tool | Description |
|---|---|
| `list_collections(category, satellite, biome, data_type, keyword, limit)` | List collections with multiple filters |
| `get_collection_detail(collection_id)` | Complete metadata for a collection |
| `get_collection_bands(collection_id)` | Detailed spectral bands |
| `compare_collections(collection_ids)` | Compare multiple collections |

### Item Search (7)

| Tool | Description |
|---|---|
| `search_items(collections, bbox, datetime_range, cloud_cover_max, limit, sortby)` | Advanced search with filters |
| `search_by_point(lon, lat, collections, datetime_range, cloud_cover_max)` | Search by coordinate |
| `search_by_polygon(geojson_geometry, collections, datetime_range)` | Search by GeoJSON geometry |
| `search_by_tile(collection_id, tile_id, datetime_range)` | Search by BDC tile |
| `search_latest_items(collection_id, bbox, n)` | N most recent items |
| `search_cloud_free(collections, bbox, datetime_range, max_cloud)` | Images with lowest cloud cover |
| `get_all_pages(collections, bbox, datetime_range, max_items)` | All result pages |

### Items and Assets (6)

| Tool | Description |
|---|---|
| `get_item(collection_id, item_id)` | Complete item details |
| `list_item_assets(collection_id, item_id)` | Assets with URLs and metadata |
| `get_asset_download_info(collection_id, item_id, asset_key)` | Download snippets (curl, Python, R) |
| `get_thumbnail_url(collection_id, item_id)` | Thumbnail URL |
| `get_quicklook_bands(collection_id)` | Bands used in quicklook |
| `get_stac_item_as_geojson(collection_id, item_id)` | Item as GeoJSON Feature |

### Data Cubes (4)

| Tool | Description |
|---|---|
| `list_data_cubes(satellite, temporal_period, biome)` | List composite data cubes |
| `get_bdc_grid_info(collection_id)` | BDC grid info (projection, tile size) |
| `get_cube_quality_info(collection_id)` | Quality bands (CLEAROB, CMASK) |
| `find_cube_for_analysis(region, start_year, end_year, min_resolution_m, required_indices)` | Recommend data cube |

### Satellites (6)

| Tool | Description |
|---|---|
| `get_cbers_collections(version)` | CBERS collections with sensor descriptions |
| `get_sentinel2_collections()` | Sentinel-2 collections (L1C, L2A, cubes) |
| `get_landsat_collections()` | Landsat collections |
| `get_goes19_info()` | GOES-19 CMI weather data |
| `get_amazonia1_collections()` | Amazonia-1 satellite (100% Brazilian) |
| `get_sentinel3_info()` | Sentinel-3 OLCI ocean data |

### Biomes and Regions (5)

| Tool | Description |
|---|---|
| `get_biome_bbox(biome)` | WGS84 bbox for biome/state/region |
| `find_collections_for_biome(biome, category, satellite)` | Collections for a biome |
| `get_cerrado_monitoring_collections()` | Cerrado monitoring package |
| `get_amazon_monitoring_collections()` | Amazon monitoring package |
| `get_deforestation_analysis_collections()` | Deforestation analysis package |

### Analysis and Code (4)

| Tool | Description |
|---|---|
| `discover_collections_for_topic(topic)` | Suggest collections by topic in natural language |
| `build_python_search_snippet(collections, bbox_or_biome, datetime_range)` | Generate Python code (pystac-client) |
| `build_r_snippet(collections, bbox_or_biome, datetime_range)` | Generate R code (rstac) |
| `get_time_series_plan(collection_id, bbox_or_biome, start_year, end_year, band)` | Time series plan |

### Spectral Indices (5)

| Tool | Description |
|---|---|
| `list_spectral_indices(category)` | List 20 indices (vegetation, water, soil, burn, snow, urban) |
| `get_spectral_index_info(index_name)` | Formula, bands, applications, value range, reference |
| `get_collection_index_availability(collection_id)` | Pre-computed vs computable vs unavailable indices |
| `generate_index_code(index_name, collection_id, language)` | Python/R/sits snippet to compute the index |
| `suggest_indices_for_application(application)` | Suggest indices for "vegetation", "water", "fire", etc. |

**Included indices:** NDVI, EVI, EVI2, SAVI, MSAVI2, NDWI, MNDWI, NDBI, NBR, NBR2, NDMI, NDSI, BSI, GNDVI, BAI, MIRBI, CMRI, ARVI, SIPI, CRI1.

### Preprocessing (4)

| Tool | Description |
|---|---|
| `get_preprocessing_guide(collection_id)` | What is already corrected, what is missing, recommendations |
| `get_cloud_mask_strategy(collection_id)` | Mask band (CMASK/SCL/Fmask), values, snippets |
| `get_atmospheric_correction_info(collection_id)` | Algorithm used (LaSRC, Sen2Cor, etc.) |
| `get_pan_sharpening_guide(collection_id)` | Guide for CBERS PAN5M/PAN10M + MUX/WFI |

### CRS Projection and Geometries (4)

| Tool | Description |
|---|---|
| `reproject_bbox(bbox, from_crs, to_crs)` | Reprojection WGS84 ↔ BDC Albers ↔ UTM |
| `calculate_area(bbox, geojson, crs)` | Area in m², hectares, and km² |
| `get_utm_zone(lon, lat)` | UTM zone and EPSG code for a coordinate |
| `convert_geometry_format(geometry, to_format)` | Conversion GeoJSON ↔ WKT |

### Time Series (5)

Inspired by the [sits](https://e-sensing.github.io/sitsbook/) workflow: `sits_cube` → `sits_regularize` → `sits_get_data` → `sits_filter`.

| Tool | Description |
|---|---|
| `plan_time_series_extraction(collection_id, bbox_or_biome, start_year, end_year, bands, output_format)` | Advanced plan with sits and Python code |
| `get_filtering_guide(method)` | Savitzky-Golay, Whittaker, Cloud Filter — parameters and snippets |
| `plan_phenology_extraction(collection_id, bbox_or_biome, band)` | Phenological metrics (SOS, EOS, Peak, Amplitude, LOS) |
| `analyze_temporal_gaps(collection_id, bbox_or_biome, datetime_range)` | Temporal gap analysis via real STAC search |
| `generate_sits_cube_code(collection_id, bbox_or_biome, start_year, end_year, bands)` | Complete R sits code |

### LULC Classification (5)

Maps the complete sits workflow: `sits_train` → `sits_classify` → `sits_smooth` → `sits_label_classification`.

| Tool | Description |
|---|---|
| `plan_classification_workflow(region, start_year, end_year, classes, algorithm)` | Complete LULC plan in 9 steps |
| `get_sample_design_guide(region, classes, total_samples)` | Stratified sample design |
| `get_ml_algorithm_guide(use_case)` | Comparison RF vs SVM vs XGBoost vs LightGBM vs DL |
| `get_accuracy_assessment_guide(n_classes)` | Confusion matrix, OA, Kappa, F1 |
| `generate_sits_classification_code(collection_id, region, algorithm, classes, start_year, end_year)` | Complete R sits code |

**Supported algorithms:** Random Forest, SVM, XGBoost, LightGBM, Deep Learning (TempCNN/ResNet).

### Change Detection (4)

| Tool | Description |
|---|---|
| `list_change_detection_methods()` | BFAST, LandTrendr, dNBR, NDVI Anomaly |
| `plan_change_detection(method, region, start_year, end_year)` | Complete plan with Python and R code |
| `plan_fire_scar_detection(region, event_date)` | dNBR with USGS severity classification |
| `plan_deforestation_detection(region, start_year, end_year, method)` | BFAST/LandTrendr for deforestation |

### Administration (2)

| Tool | Description |
|---|---|
| `get_api_metrics()` | API usage metrics (requests, cache hits, latency) |
| `invalidate_cache(namespace)` | Invalidate cache by namespace or entirely |

## MCP Resources (7)

| URI | Description |
|---|---|
| `stac://inpe-bdc/catalog` | Catalog landing page |
| `stac://inpe-bdc/collections` | Categorized collection index |
| `stac://inpe-bdc/satellites` | Satellite catalog |
| `stac://inpe-bdc/biomes` | Biomes with bboxes |
| `stac://inpe-bdc/guide` | Complete usage guide |
| `stac://inpe-bdc/collection/{collection_id}` | Collection metadata |
| `stac://inpe-bdc/item/{collection_id}/{item_id}` | Item details |

## MCP Prompts (7)

| Prompt | Description |
|---|---|
| `search_images(satellite, region, period)` | Guided satellite image search |
| `deforestation_analysis(biome, start_year, end_year)` | Deforestation analysis |
| `time_series_workflow(collection_id, region, band)` | Time series workflow |
| `mosaic_exploration(region, satellite)` | Mosaic exploration |
| `sits_classification_workflow(region, start_year, end_year, algorithm)` | LULC classification with sits |
| `change_detection_workflow(method, region, start_year, end_year)` | Change detection |
| `spectral_analysis(application, collection_id)` | Spectral analysis |

## Collection Catalog

### Brazilian Satellites (Raw Images)

| ID | Satellite | Sensor | Resolution |
|---|---|---|---|
| CB4-PAN5M-L2-DN-1 | CBERS-4 | PAN5M | 5m |
| CB4-PAN10M-L2-DN-1 | CBERS-4 | PAN10M | 10m |
| CB4-MUX-L2-DN-1 | CBERS-4 | MUX | 20m |
| CB4-WFI-L4-SR-1 | CBERS-4 | WFI | 64m |
| CB4A-MUX-L4-DN-1 | CBERS-4A | MUX | 20m |
| CB4A-WFI-L4-DN-1 | CBERS-4A | WFI | 55m |
| CB2B-HRC-L2-DN-1 | CBERS-2B | HRC | 2.5m |
| AMZ1-WFI-L2-DN-1 | Amazonia-1 | WFI | 60m |

### Data Cubes

| ID | Satellite | Period | Resolution |
|---|---|---|---|
| CBERS4-WFI-16D-2 | CBERS-4 | 16 days | 64m |
| CBERS-WFI-8D-1 | CBERS/WFI | 8 days | 64m |
| LANDSAT-16D-1 | Landsat | 16 days | 30m |
| landsat-tsirf-bimonthly-1 | Landsat | 2 months | 30m |
| S2_L2A-1 | Sentinel-2 | — | 10m |

### Mosaics

| ID | Region | Satellite |
|---|---|---|
| mosaic-landsat-amazon-3m-1 | Amazon | Landsat |
| mosaic-s2-amazon-3m-1 | Amazon | Sentinel-2 |
| mosaic-landsat-brazil-6m-1 | Brazil | Landsat |

### Classification (LCC)

| ID | Biome |
|---|---|
| LCC_L8_30_16D_STK_Cerrado-1 | Cerrado |
| LCC_L8_30_16D_STK_MataAtlantica-1 | Atlantic Forest |
| LCC_L8_30_16D_STK_Pantanal-1 | Pantanal |

### MODIS / Special

| ID | Product | Domain |
|---|---|---|
| mod13q1-6.1 | NDVI Terra 250m | Vegetation |
| myd13q1-6.1 | NDVI Aqua 250m | Vegetation |
| MODISA-OCSMART-CHL-MONTHLY-1 | Chlorophyll-a | Ocean |
| GOES19-L2-CMI-1 | CMI | Weather |

## Supported Spectral Indices

| Index | Full Name | Category | Bands |
|---|---|---|---|
| NDVI | Normalized Difference Vegetation Index | vegetation | NIR, RED |
| EVI | Enhanced Vegetation Index | vegetation | NIR, RED, BLUE |
| EVI2 | Enhanced Vegetation Index 2 | vegetation | NIR, RED |
| SAVI | Soil Adjusted Vegetation Index | vegetation | NIR, RED |
| MSAVI2 | Modified SAVI 2 | vegetation | NIR, RED |
| GNDVI | Green NDVI | vegetation | NIR, GREEN |
| ARVI | Atmospherically Resistant VI | vegetation | NIR, RED, BLUE |
| SIPI | Structure Insensitive Pigment Index | vegetation | NIR, BLUE, RED |
| CRI1 | Carotenoid Reflectance Index 1 | vegetation | BLUE, GREEN |
| NDMI | Normalized Difference Moisture Index | vegetation | NIR, SWIR16 |
| NDWI | Normalized Difference Water Index | water | GREEN, NIR |
| MNDWI | Modified NDWI | water | GREEN, SWIR16 |
| NDBI | Normalized Difference Built-up Index | urban | SWIR16, NIR |
| NBR | Normalized Burn Ratio | burn | NIR, SWIR22 |
| NBR2 | Normalized Burn Ratio 2 | burn | SWIR16, SWIR22 |
| BAI | Burned Area Index | burn | RED, NIR |
| MIRBI | Mid-Infrared Burn Index | burn | SWIR22, SWIR16 |
| BSI | Bare Soil Index | soil | SWIR16, RED, NIR, BLUE |
| CMRI | Clay Minerals Ratio Index | soil | SWIR16, SWIR22 |
| NDSI | Normalized Difference Snow Index | snow | GREEN, SWIR16 |

## Usage Examples

### Discovery and Search

```
"Search for Sentinel-2 images with less than 10% cloud cover for the Cerrado in 2023"

"Which data cube should I use to analyze NDVI time series in Goias from 2019 to 2023?"

"List the available mosaics for the Amazon"

"Give me the Python snippet to download a CBERS-4A scene from the Pantanal"

"Compare CBERS-4 WFI and Sentinel-2 L2A collections for deforestation monitoring"
```

### Spectral Indices

```
"Which indices can I compute with the LANDSAT-16D-1 collection?"

"Suggest spectral indices for fire monitoring in the Cerrado"

"Generate the Python code to compute NBR from Landsat"
```

### Time Series

```
"Build a plan for EVI time series across the deforestation arc from 2018 to 2024"

"Generate sits code to create a LANDSAT-16D-1 cube for the Amazon"

"Which filtering method should I use to smooth an NDVI time series?"

"Analyze the temporal gaps of LANDSAT-16D-1 for Mato Grosso in 2022"
```

### LULC Classification

```
"Build a complete land use classification workflow for the Cerrado with XGBoost"

"Which ML algorithm should I use for classification with few samples?"

"Generate the complete sits code for classification with Random Forest"

"How do I evaluate the accuracy of my classification with 8 classes?"
```

### Change Detection

```
"Plan deforestation detection in the Amazon with BFAST from 2018 to 2023"

"Detect fire scars in the Cerrado around August 2023"

"Which change detection methods are available?"
```

### Projection and Geometries

```
"Convert this bbox from WGS84 to BDC Albers"

"What is the area in hectares of this region?"

"What is the UTM zone for the coordinates of Manaus?"
```

## Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Tests by module
uv run pytest tests/test_spectral.py -v
uv run pytest tests/test_projection.py -v
uv run pytest tests/test_timeseries.py -v
uv run pytest tests/test_classification.py -v
uv run pytest tests/test_change_detection.py -v
```

Tests use [respx](https://lundberg.github.io/respx/) for HTTP call mocking to the STAC API, ensuring offline and deterministic execution.

## Dependencies

| Package | Usage |
|---|---|
| `mcp[cli]` | MCP framework (FastMCP) |
| `httpx` | Async HTTP client |
| `pystac-client` | STAC client |
| `pystac` | STAC models |
| `shapely` | Geometric operations |
| `pyproj` | Cartographic projections (CRS) |
| `pydantic` | Data validation |

## Technical Notes

### BDC Albers CRS (EPSG:100001)

The Brazil Data Cube uses a custom Albers Equal-Area coordinate system (EPSG:100001), not recognized by pyproj. The server resolves it internally via Proj4 string:

```
+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22
+x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs
```

The aliases `bdc_albers`, `epsg:100001`, and `wgs84` are automatically resolved by the projection tools.

### sits Workflow (R)

The classification and time series tools generate code for the R package [sits](https://e-sensing.github.io/sitsbook/), which implements the complete pipeline:

1. `sits_cube()` — Create STAC cube
2. `sits_regularize()` — Regularize temporal resolution
3. `sits_get_data()` — Extract time series
4. `sits_filter()` — Filter noise (Whittaker/Savitzky-Golay)
5. `sits_som()` — Evaluate sample quality
6. `sits_train()` — Train model (RF/SVM/XGBoost/TempCNN)
7. `sits_classify()` — Classify cube
8. `sits_smooth()` — Bayesian post-processing
9. `sits_label_classification()` — Generate final map

### Nature of the Tools

The geospatial analysis tools (spectral indices, classification, change detection) generate **information, guidance, and code snippets** — the MCP server **does not process rasters directly**. Data processing occurs in the user's environment via the generated Python or R snippets.

## Known Limitations

- Some restricted collections require an API key — configure `BDC_API_KEY`
- The BDC API may have variable latency depending on server load
- Pagination limited to 1000 items per page
- Advanced CQL2 filters depend on the server's conformance classes
- Sortby may not work for all fields across all collections
- The server does not process rasters — it generates code and guidance for processing in the user's environment

## Citation

If you use Brazil Data Cube data in publications, please cite:

> Ferreira, K.R.; Queiroz, G.R.; Vinhas, L.; Marujo, R.F.B.; Simoes, R.E.O.; Picoli, M.C.A.; Camara, G.; Cartaxo, R.; Gomes, V.C.F.; Santos, L.A.; Sanchez, A.H.; Arcanjo, J.S.; Fronza, J.G.; Noronha, C.A.; Costa, R.W.; Zaglia, M.C.; Zioti, F.; Korting, T.S.; Soares, A.R.; Chaves, M.E.D.; Fonseca, L.M.G. Earth Observation Data Cubes for Brazil: Requirements, Methodology and Products. Remote Sensing, 12, 4033, 2020. DOI: 10.3390/rs12244033

## Credits

### Data and Infrastructure

- **[INPE — National Institute for Space Research](https://www.gov.br/inpe/)** — Production and provision of Earth observation data
- **[Brazil Data Cube (BDC)](https://brazildatacube.dpi.inpe.br/)** — ARD data cube platform and STAC API
- **[STAC — SpatioTemporal Asset Catalog](https://stacspec.org/)** — Geospatial data catalog specification

### Scientific References

- **sits (Satellite Image Time Series)** — Simoes, R.; Camara, G.; Queiroz, G.; Souza, F.; Andrade, P.R.; Santos, L.; Carvalho, A.; Ferreira, K. *Satellite Image Time Series Analysis on Earth Observation Data Cubes*. [sits R package](https://e-sensing.github.io/sitsbook/)
- **BFAST** — Verbesselt, J.; Hyndman, R.; Newnham, G.; Culvenor, D. *Detecting Trend and Seasonal Changes in Satellite Image Time Series*. Remote Sensing of Environment, 2010.
- **LandTrendr** — Kennedy, R.E.; Yang, Z.; Cohen, W.B. *Detecting Trends in Forest Disturbance and Recovery*. Remote Sensing of Environment, 2010.

### Technologies

- **[MCP — Model Context Protocol](https://modelcontextprotocol.io/)** — Communication protocol between AI agents and tools
- **[FastMCP](https://github.com/jlowin/fastmcp)** — Python framework for MCP servers
- **[pyproj](https://pyproj4.github.io/pyproj/)** — Cartographic transformations
- **[Shapely](https://shapely.readthedocs.io/)** — Geometric operations
- **[pystac-client](https://pystac-client.readthedocs.io/)** — STAC client for Python

## License

MIT
