"""Ferramentas MCP por satélite/sensor disponíveis no BDC."""

from __future__ import annotations

from typing import Any

from .collections import get_collection_detail, list_collections


def get_cbers_collections(version: str | None = None) -> dict[str, Any]:
    """Lista coleções CBERS (China-Brazil Earth Resources Satellite).

    Args:
        version: "CBERS-2B", "CBERS-4" ou "CBERS-4A". None para todos.
    """
    satellite = version or "CBERS"
    results = list_collections(satellite=satellite)

    sensor_info = {
        "PAN5M": "Câmera pancromática 5m — alta resolução para mapeamento urbano e infraestrutura.",
        "PAN10M": "Câmera pancromática 10m — resolução intermediária, boa para mapeamento regional.",
        "MUX": "Câmera multiespectral 20m — 4 bandas (B/G/R/NIR), ideal para vegetação e uso do solo.",
        "WFI": "Wide Field Imager — ampla cobertura (866km), revisita de 5 dias, monitoramento ambiental.",
        "HRC": "High Resolution Camera 2.5m (CBERS-2B) — a mais alta resolução do programa CBERS.",
    }

    return {
        "collections": results,
        "sensor_descriptions": sensor_info,
        "program_info": (
            "CBERS (China-Brazil Earth Resources Satellite) é uma parceria entre INPE e CAST "
            "(Chinese Academy of Space Technology). Atualmente CBERS-4 e CBERS-4A estão em operação."
        ),
    }


def get_sentinel2_collections() -> dict[str, Any]:
    """Lista coleções Sentinel-2 disponíveis no BDC."""
    results = list_collections(satellite="Sentinel-2")

    return {
        "collections": results,
        "level_descriptions": {
            "L1C": "Top of Atmosphere (TOA) — reflectância no topo da atmosfera, sem correção atmosférica.",
            "L2A": "Surface Reflectance (SR) — reflectância de superfície, corrigida atmosfericamente. Recomendada para análises quantitativas.",
        },
        "note": (
            "O BDC disponibiliza tanto imagens brutas quanto data cubes compostos "
            "e mosaicos regionais baseados em Sentinel-2."
        ),
    }


def get_landsat_collections() -> dict[str, Any]:
    """Lista coleções Landsat disponíveis no BDC."""
    results = list_collections(satellite="Landsat")

    return {
        "collections": results,
        "note": (
            "Inclui imagens brutas, data cubes compostos (LANDSAT-16D) e mosaicos regionais. "
            "O data cube LANDSAT-16D-1 combina Landsat-8/9 OLI com composição de 16 dias (LCF)."
        ),
    }


def get_goes19_info() -> dict[str, Any]:
    """Informações sobre dados GOES-19 CMI disponíveis no BDC."""
    detail = get_collection_detail("GOES19-L2-CMI-1")
    return {
        "collection": detail,
        "product_info": {
            "name": "Cloud & Moisture Imagery (CMI)",
            "satellite": "GOES-19 (GOES-T)",
            "domain": "Meteorologia e monitoramento atmosférico",
            "coverage": "América do Sul e Oceano Atlântico",
            "frequency": "Alta frequência (5-15 minutos)",
            "instrument": "ABI (Advanced Baseline Imager)",
            "bands": "16 bandas espectrais (visível, infravermelho próximo e termal)",
        },
    }


def get_amazonia1_collections() -> dict[str, Any]:
    """Lista coleções do satélite Amazonia-1."""
    results = list_collections(satellite="AMAZONIA")

    return {
        "collections": results,
        "satellite_info": {
            "name": "Amazonia-1",
            "launch_date": "2021-02-28",
            "origin": "100% brasileiro, desenvolvido pelo INPE",
            "sensor": "WFI (Wide Field Imager)",
            "resolution_m": 60,
            "swath_km": 866,
            "revisit_days": 5,
            "purpose": (
                "Monitoramento da Amazônia e de desmatamento. "
                "Complementa os dados CBERS para vigilância ambiental contínua."
            ),
        },
    }


def get_sentinel3_info() -> dict[str, Any]:
    """Informações sobre dados Sentinel-3 OLCI disponíveis no BDC."""
    detail = get_collection_detail("sentinel-3-olci-l1-bundle-1")
    return {
        "collection": detail,
        "sensor_info": {
            "name": "OLCI (Ocean and Land Colour Instrument)",
            "level": "L1B Full Resolution",
            "domain": "Monitoramento oceânico e costeiro",
            "bands": "21 bandas espectrais (400-1020 nm)",
            "resolution_m": 300,
            "applications": [
                "Qualidade da água",
                "Clorofila e produtividade primária oceânica",
                "Monitoramento de florações de algas",
                "Cor do oceano",
                "Vegetação terrestre (complementar)",
            ],
        },
    }
