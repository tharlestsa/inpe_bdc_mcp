"""Catálogo estático de coleções conhecidas do INPE/BDC para filtragem local."""

from __future__ import annotations

from typing import Any

# Mapeamento de sufixos temporais (período de composição) para dias.
# Utilizado por analysis.py, timeseries.py e outros módulos.
PERIOD_DAYS: dict[str, int] = {
    "8D": 8,
    "16D": 16,
    "1M": 30,
    "2M": 60,
    "3M": 90,
    "6M": 180,
}

BRAZILIAN_SATELLITES: dict[str, dict[str, Any]] = {
    "CB4-PAN5M-L2-DN-1": {"sensor": "PAN5M", "satellite": "CBERS-4", "level": "L2", "res_m": 5, "category": "raw_image"},
    "CB4-PAN5M-L4-DN-1": {"sensor": "PAN5M", "satellite": "CBERS-4", "level": "L4", "res_m": 5, "category": "raw_image"},
    "CB4-PAN10M-L2-DN-1": {"sensor": "PAN10M", "satellite": "CBERS-4", "level": "L2", "res_m": 10, "category": "raw_image"},
    "CB4-PAN10M-L4-DN-1": {"sensor": "PAN10M", "satellite": "CBERS-4", "level": "L4", "res_m": 10, "category": "raw_image"},
    "CB4-MUX-L2-DN-1": {"sensor": "MUX", "satellite": "CBERS-4", "level": "L2", "res_m": 20, "category": "raw_image"},
    "CB4-MUX-L4-DN-1": {"sensor": "MUX", "satellite": "CBERS-4", "level": "L4", "res_m": 20, "category": "raw_image"},
    "CB4-WFI-L2-DN-1": {"sensor": "WFI", "satellite": "CBERS-4", "level": "L2", "res_m": 64, "category": "raw_image"},
    "CB4-WFI-L4-DN-1": {"sensor": "WFI", "satellite": "CBERS-4", "level": "L4", "res_m": 64, "category": "raw_image"},
    "CB4-WFI-L4-SR-1": {"sensor": "WFI", "satellite": "CBERS-4", "level": "L4-SR", "res_m": 64, "category": "raw_image"},
    "CB4A-MUX-L2-DN-1": {"sensor": "MUX", "satellite": "CBERS-4A", "level": "L2", "res_m": 20, "category": "raw_image"},
    "CB4A-MUX-L4-DN-1": {"sensor": "MUX", "satellite": "CBERS-4A", "level": "L4", "res_m": 20, "category": "raw_image"},
    "CB4A-WFI-L2-DN-1": {"sensor": "WFI", "satellite": "CBERS-4A", "level": "L2", "res_m": 55, "category": "raw_image"},
    "CB4A-WFI-L4-DN-1": {"sensor": "WFI", "satellite": "CBERS-4A", "level": "L4", "res_m": 55, "category": "raw_image"},
    "CB2B-HRC-L2-DN-1": {"sensor": "HRC", "satellite": "CBERS-2B", "level": "L2", "res_m": 2.5, "category": "raw_image"},
    "AMZ1-WFI-L2-DN-1": {"sensor": "WFI", "satellite": "AMAZONIA-1", "level": "L2", "res_m": 60, "category": "raw_image"},
}

DATA_CUBES: dict[str, dict[str, Any]] = {
    "CBERS4-WFI-16D-2": {"satellite": "CBERS-4", "period": "16D", "method": "LCF", "res_m": 64, "category": "data_cube"},
    "CBERS-WFI-8D-1": {"satellite": "CBERS/WFI", "period": "8D", "method": "LCF", "res_m": 64, "category": "data_cube"},
    "LANDSAT-16D-1": {"satellite": "Landsat", "period": "16D", "method": "LCF", "res_m": 30, "category": "data_cube"},
    "landsat-tsirf-bimonthly-1": {"satellite": "Landsat", "period": "2M", "method": "TSIRF", "res_m": 30, "category": "data_cube"},
    "S2_L1C_BUNDLE-1": {"satellite": "Sentinel-2", "level": "L1C", "type": "bundle", "category": "data_cube"},
    "S2_L2A-1": {"satellite": "Sentinel-2", "level": "L2A", "res_m": 10, "category": "data_cube"},
}

LCC_COLLECTIONS: dict[str, dict[str, Any]] = {
    "LCC_L8_30_16D_STK_Cerrado-1": {"biome": "Cerrado", "sensor": "Landsat-8", "category": "land_cover"},
    "LCC_L8_30_16D_STK_MataAtlantica-1": {"biome": "Mata Atlântica", "sensor": "Landsat-8", "category": "land_cover"},
    "LCC_L8_30_16D_STK_Pantanal-1": {"biome": "Pantanal", "sensor": "Landsat-8", "category": "land_cover"},
    "LCC_L8_30_1M_STK_Cerrado-1": {"biome": "Cerrado", "sensor": "Landsat-8", "period": "1M", "category": "land_cover"},
    "LCC_C4_64_1M_STK_GO_PA-SPC-AC-NA-1": {"region": "Goiás/Pará", "sensor": "CBERS-4", "category": "land_cover"},
}

MOSAICS: dict[str, dict[str, Any]] = {
    "mosaic-cbers4a-paraiba-3m-1": {"region": "Paraíba", "satellite": "CBERS-4A", "period": "3M", "category": "mosaic"},
    "mosaic-s2-paraiba-3m-1": {"region": "Paraíba", "satellite": "Sentinel-2", "period": "3M", "category": "mosaic"},
    "mosaic-s2-yanomami_territory-6m-1": {"region": "TI Yanomami", "satellite": "Sentinel-2", "period": "6M", "category": "mosaic"},
    "mosaic-landsat-sp-6m-1": {"region": "São Paulo", "satellite": "Landsat", "period": "6M", "category": "mosaic"},
    "mosaic-landsat-amazon-3m-1": {"region": "Amazônia", "satellite": "Landsat", "period": "3M", "category": "mosaic"},
    "mosaic-s2-amazon-3m-1": {"region": "Amazônia", "satellite": "Sentinel-2", "period": "3M", "category": "mosaic"},
    "mosaic-landsat-brazil-6m-1": {"region": "Brasil", "satellite": "Landsat", "period": "6M", "category": "mosaic"},
}

MODIS_AND_SPECIAL: dict[str, dict[str, Any]] = {
    "mod13q1-6.1": {"product": "MOD13Q1", "sensor": "MODIS-Terra", "res_m": 250, "category": "modis"},
    "myd13q1-6.1": {"product": "MYD13Q1", "sensor": "MODIS-Aqua", "res_m": 250, "category": "modis"},
    "MODISA-OCSMART-RRS-MONTHLY-1": {"product": "Rrs", "sensor": "MODIS-Aqua", "domain": "ocean", "category": "ocean"},
    "MODISA-OCSMART-CHL-MONTHLY-1": {"product": "Chlorophyll-a", "sensor": "MODIS-Aqua", "domain": "ocean", "category": "ocean"},
    "sentinel-3-olci-l1-bundle-1": {"satellite": "Sentinel-3", "sensor": "OLCI", "level": "L1B", "category": "ocean"},
    "GOES19-L2-CMI-1": {"satellite": "GOES-19", "product": "CMI", "domain": "weather", "category": "weather"},
}

# Mapeamento common_name → band_key por coleção BDC conhecida
COLLECTION_BAND_MAPPING: dict[str, dict[str, str]] = {
    "LANDSAT-16D-1": {
        "blue": "BLUE", "green": "GREEN", "red": "RED",
        "nir": "NIR", "swir16": "SWIR16", "swir22": "SWIR22",
        "ndvi": "NDVI", "evi": "EVI",
    },
    "CBERS4-WFI-16D-2": {
        "blue": "BLUE", "green": "GREEN", "red": "RED", "nir": "NIR",
        "ndvi": "NDVI", "evi": "EVI",
    },
    "CBERS-WFI-8D-1": {
        "blue": "BLUE", "green": "GREEN", "red": "RED", "nir": "NIR",
        "ndvi": "NDVI", "evi": "EVI",
    },
    "S2_L2A-1": {
        "coastal": "B01", "blue": "B02", "green": "B03", "red": "B04",
        "rededge1": "B05", "rededge2": "B06", "rededge3": "B07",
        "nir": "B08", "nir08a": "B8A", "watervapour": "B09",
        "swir16": "B11", "swir22": "B12",
    },
    "S2_L1C_BUNDLE-1": {
        "coastal": "B01", "blue": "B02", "green": "B03", "red": "B04",
        "rededge1": "B05", "rededge2": "B06", "rededge3": "B07",
        "nir": "B08", "nir08a": "B8A", "watervapour": "B09",
        "cirrus": "B10", "swir16": "B11", "swir22": "B12",
    },
    "CB4-WFI-L4-SR-1": {
        "blue": "BAND13", "green": "BAND14", "red": "BAND15", "nir": "BAND16",
    },
    "CB4-MUX-L4-DN-1": {
        "blue": "BAND5", "green": "BAND6", "red": "BAND7", "nir": "BAND8",
    },
    "CB4A-WFI-L4-DN-1": {
        "blue": "BAND13", "green": "BAND14", "red": "BAND15", "nir": "BAND16",
    },
    "AMZ1-WFI-L2-DN-1": {
        "blue": "BAND13", "green": "BAND14", "red": "BAND15", "nir": "BAND16",
    },
    "mod13q1-6.1": {
        "ndvi": "NDVI", "evi": "EVI",
        "red": "sur_refl_b01", "nir": "sur_refl_b02",
        "blue": "sur_refl_b03", "swir16": "sur_refl_b07",
    },
    "myd13q1-6.1": {
        "ndvi": "NDVI", "evi": "EVI",
        "red": "sur_refl_b01", "nir": "sur_refl_b02",
        "blue": "sur_refl_b03", "swir16": "sur_refl_b07",
    },
    "landsat-tsirf-bimonthly-1": {
        "blue": "BLUE", "green": "GREEN", "red": "RED",
        "nir": "NIR", "swir16": "SWIR16", "swir22": "SWIR22",
    },
}


# Catálogo unificado
ALL_COLLECTIONS: dict[str, dict[str, Any]] = {
    **BRAZILIAN_SATELLITES,
    **DATA_CUBES,
    **LCC_COLLECTIONS,
    **MOSAICS,
    **MODIS_AND_SPECIAL,
}


def get_known_info(collection_id: str) -> dict[str, Any] | None:
    return ALL_COLLECTIONS.get(collection_id)


def filter_by_category(category: str) -> list[str]:
    return [k for k, v in ALL_COLLECTIONS.items() if v.get("category") == category]


def filter_by_satellite(satellite: str) -> list[str]:
    sat_lower = satellite.lower()
    return [
        k for k, v in ALL_COLLECTIONS.items()
        if sat_lower in (v.get("satellite", "") or "").lower()
        or sat_lower in (v.get("sensor", "") or "").lower()
    ]


def filter_by_biome(biome: str) -> list[str]:
    biome_lower = biome.lower()
    return [
        k for k, v in ALL_COLLECTIONS.items()
        if biome_lower in (v.get("biome", "") or "").lower()
        or biome_lower in (v.get("region", "") or "").lower()
    ]
