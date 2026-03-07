"""MCP Resources para informações do catálogo STAC do BDC."""

from __future__ import annotations

import json
from typing import Any

from ..catalogs import ALL_COLLECTIONS, BRAZILIAN_SATELLITES, DATA_CUBES, LCC_COLLECTIONS, MODIS_AND_SPECIAL, MOSAICS
from ..tools.catalog import catalog_info, get_api_capabilities
from ..utils.brazil import BRAZIL_REGIONS


def catalog_resource() -> str:
    """Catálogo INPE/BDC — landing page completa."""
    info = catalog_info()
    return json.dumps(info, indent=2, ensure_ascii=False)


def collections_index_resource() -> str:
    """Índice de todas as coleções conhecidas com categorização."""
    index = {
        "total_known_collections": len(ALL_COLLECTIONS),
        "categories": {
            "raw_images": {
                "description": "Imagens brutas de satélites brasileiros (CBERS, Amazonia-1)",
                "collections": list(BRAZILIAN_SATELLITES.keys()),
            },
            "data_cubes": {
                "description": "Composições temporais (data cubes) do Brazil Data Cube",
                "collections": list(DATA_CUBES.keys()),
            },
            "land_cover": {
                "description": "Classificações de uso e cobertura do solo",
                "collections": list(LCC_COLLECTIONS.keys()),
            },
            "mosaics": {
                "description": "Mosaicos regionais compostos",
                "collections": list(MOSAICS.keys()),
            },
            "modis_and_special": {
                "description": "MODIS, Sentinel-3, GOES-19 e outros sensores",
                "collections": list(MODIS_AND_SPECIAL.keys()),
            },
        },
    }
    return json.dumps(index, indent=2, ensure_ascii=False)


def satellites_resource() -> str:
    """Catálogo dos satélites disponíveis."""
    satellites = {
        "CBERS-4": {
            "status": "Operacional",
            "sensors": ["PAN5M (5m)", "PAN10M (10m)", "MUX (20m)", "WFI (64m)"],
            "partnership": "INPE/CAST (China-Brasil)",
        },
        "CBERS-4A": {
            "status": "Operacional",
            "sensors": ["MUX (20m)", "WFI (55m)"],
            "partnership": "INPE/CAST",
        },
        "CBERS-2B": {
            "status": "Encerrado",
            "sensors": ["HRC (2.5m)"],
        },
        "Amazonia-1": {
            "status": "Operacional (desde 2021)",
            "sensors": ["WFI (60m)"],
            "origin": "100% brasileiro",
        },
        "Sentinel-2": {
            "status": "Operacional (ESA)",
            "data_available": ["L1C (TOA)", "L2A (SR)", "Data cubes", "Mosaicos"],
            "resolution": "10-60m",
        },
        "Landsat": {
            "status": "Operacional (USGS/NASA)",
            "data_available": ["Data cubes 16D", "Mosaicos"],
            "resolution": "30m",
        },
        "MODIS": {
            "products": ["MOD13Q1 (NDVI Terra)", "MYD13Q1 (NDVI Aqua)", "Ocean Color"],
            "resolution": "250m-1km",
        },
        "GOES-19": {
            "status": "Operacional (NOAA)",
            "product": "CMI (Cloud & Moisture Imagery)",
            "domain": "Meteorologia",
        },
        "Sentinel-3": {
            "sensor": "OLCI",
            "domain": "Oceânico/costeiro",
            "resolution": "300m",
        },
    }
    return json.dumps(satellites, indent=2, ensure_ascii=False)


def biomes_resource() -> str:
    """Guia de biomas brasileiros com bboxes e coleções disponíveis."""
    biomes = {
        name: {
            "bbox": bbox,
            "format": "[min_lon, min_lat, max_lon, max_lat]",
        }
        for name, bbox in BRAZIL_REGIONS.items()
    }
    return json.dumps(biomes, indent=2, ensure_ascii=False)


def guide_resource() -> str:
    """Guia completo de uso do INPE BDC MCP Server."""
    guide = {
        "title": "Guia de Uso — INPE BDC MCP Server",
        "authentication": {
            "method": "Header x-api-key",
            "env_var": "BDC_API_KEY",
            "public_access": "Coleções públicas não requerem autenticação",
            "restricted_access": "Algumas coleções requerem API key do portal BDC",
            "portal": "https://brazildatacube.dpi.inpe.br/",
        },
        "search_tips": [
            "Use bbox como lista [min_lon, min_lat, max_lon, max_lat] ou nome de região ('cerrado', 'goias')",
            "datetime_range segue ISO 8601: '2020-01-01/2023-12-31', '2022-06-01/..', '../2021-01-01'",
            "cloud_cover_max filtra por eo:cloud_cover (0-100)",
            "Para séries temporais, prefira data cubes (*-16D-*, *-8D-*) em vez de imagens brutas",
            "sortby aceita '-properties.datetime' para ordenar do mais recente ao mais antigo",
        ],
        "collection_categories": {
            "raw_image": "Imagens brutas (DN/SR) de satélites — análise cena a cena",
            "data_cube": "Composições temporais regulares — séries temporais",
            "mosaic": "Mosaicos regionais — visualização e base cartográfica",
            "land_cover": "Classificação de uso e cobertura do solo — mapas temáticos",
            "modis": "Produtos MODIS — longa série histórica, baixa resolução",
            "ocean": "Dados oceânicos — clorofila, cor do oceano",
            "weather": "Dados meteorológicos — GOES-19 alta frequência",
        },
        "common_workflows": [
            "Buscar imagens: search_items() com filtros de coleção, região e data",
            "Série temporal: find_cube_for_analysis() → search_items() → get_asset_download_info()",
            "Explorar coleções: list_collections() → get_collection_detail() → get_collection_bands()",
            "Gerar código: build_python_search_snippet() ou build_r_snippet()",
        ],
    }
    return json.dumps(guide, indent=2, ensure_ascii=False)
