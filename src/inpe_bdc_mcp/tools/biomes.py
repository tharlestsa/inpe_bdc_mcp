"""Ferramentas MCP orientadas a biomas e regiões brasileiras."""

from __future__ import annotations

import logging
from typing import Any

from ..catalogs import ALL_COLLECTIONS
from ..client import BDCClient
from ..models.search import DeforestationDataPack
from ..utils.brazil import BRAZIL_REGIONS, resolve_bbox
from ..utils.geo import bbox_intersects
from .collections import _collection_to_summary

logger = logging.getLogger(__name__)


def _infer_category(cid: str, coll: dict[str, Any]) -> str | None:
    """Infere a categoria de uma coleção a partir de seus metadados.

    Utilizado quando a coleção não está no catálogo estático ALL_COLLECTIONS.
    """
    cid_lower = cid.lower()
    title = (coll.get("title") or "").lower()
    desc = (coll.get("description") or "").lower()
    text = f"{cid_lower} {title} {desc}"

    if cid_lower.startswith("lcc"):
        return "land_cover"
    if "mosaic" in cid_lower or "mosaic" in title:
        return "mosaic"
    if "cube" in text or any(p in cid_lower for p in ("-16d-", "-8d-", "-1m-", "-2m-", "-3m-")):
        return "data_cube"
    if "mod" in cid_lower[:4] or "modis" in text:
        return "modis"
    if "goes" in cid_lower:
        return "weather"
    if "ocean" in text or "chl" in cid_lower or "rrs" in cid_lower:
        return "ocean"
    # Coleções com sensor/satélite e nível de processamento → raw_image
    if any(p in cid_lower for p in ("-l2-", "-l4-", "-l1-", "_l2a")):
        return "raw_image"
    return None


def get_biome_bbox(biome: str) -> dict[str, Any]:
    """Retorna bbox WGS84 aproximado para um bioma ou região brasileira.

    Args:
        biome: Nome do bioma/estado/região (ex: "cerrado", "goias", "amazonia_legal").
    """
    bbox = resolve_bbox(biome)
    if bbox is None:
        return {
            "error": f"Região '{biome}' não reconhecida.",
            "available_regions": sorted(BRAZIL_REGIONS.keys()),
        }
    return {
        "region": biome,
        "bbox": bbox,
        "format": "[min_lon, min_lat, max_lon, max_lat]",
        "crs": "EPSG:4326 (WGS84)",
    }


def find_collections_for_biome(
    biome: str,
    category: str | None = None,
    satellite: str | None = None,
) -> list[dict[str, Any]]:
    """Encontra coleções com cobertura espacial do bioma especificado.

    Args:
        biome: Nome do bioma (ex: "cerrado", "amazonia").
        category: Filtro opcional por categoria (ex: "data_cube", "raw_image").
        satellite: Filtro opcional por satélite.
    """
    biome_bbox = resolve_bbox(biome)
    if biome_bbox is None:
        return [{"error": f"Bioma '{biome}' não reconhecido.", "available": sorted(BRAZIL_REGIONS.keys())}]

    client = BDCClient.get_instance()
    all_colls = client.list_collections()

    results: list[dict[str, Any]] = []
    for coll in all_colls:
        cid = coll.get("id", "")
        known = ALL_COLLECTIONS.get(cid, {})

        if category:
            known_cat = known.get("category")
            if known_cat:
                if known_cat != category:
                    continue
            else:
                # Inferir categoria a partir dos metadados da coleção
                inferred = _infer_category(cid, coll)
                if inferred != category:
                    continue

        if satellite and satellite.lower() not in (known.get("satellite", "") or "").lower():
            continue

        extent = coll.get("extent", {})
        spatial = extent.get("spatial", {}).get("bbox", [[]])[0]
        if spatial and len(spatial) == 4:
            if not bbox_intersects(spatial, biome_bbox):
                continue

        summary = _collection_to_summary(cid, coll)
        results.append(summary.model_dump())

    return results


def get_cerrado_monitoring_collections() -> dict[str, Any]:
    """Retorna coleções recomendadas para monitoramento do Cerrado."""
    recommended_ids = [
        "LCC_L8_30_16D_STK_Cerrado-1",
        "LCC_L8_30_1M_STK_Cerrado-1",
        "LANDSAT-16D-1",
        "CBERS4-WFI-16D-2",
        "S2_L2A-1",
    ]

    client = BDCClient.get_instance()
    results: list[dict[str, Any]] = []
    for cid in recommended_ids:
        try:
            data = client.get_collection(cid)
            summary = _collection_to_summary(cid, data)
            results.append(summary.model_dump())
        except Exception as exc:
            logger.warning("Coleção %s indisponível: %s", cid, exc)
            results.append({"id": cid, "status": "indisponível"})

    return {
        "biome": "Cerrado",
        "bbox": resolve_bbox("cerrado"),
        "collections": results,
        "analysis_tips": (
            "Para monitoramento do Cerrado, recomenda-se usar os data cubes LANDSAT-16D-1 "
            "ou CBERS4-WFI-16D-2 para séries temporais de NDVI/EVI. "
            "As coleções LCC fornecem classificação de uso e cobertura do solo já processada."
        ),
    }


def get_amazon_monitoring_collections() -> dict[str, Any]:
    """Retorna coleções recomendadas para monitoramento da Amazônia."""
    recommended_ids = [
        "LANDSAT-16D-1",
        "CBERS4-WFI-16D-2",
        "AMZ1-WFI-L2-DN-1",
        "mosaic-landsat-amazon-3m-1",
        "mosaic-s2-amazon-3m-1",
        "S2_L2A-1",
    ]

    client = BDCClient.get_instance()
    results: list[dict[str, Any]] = []
    for cid in recommended_ids:
        try:
            data = client.get_collection(cid)
            summary = _collection_to_summary(cid, data)
            results.append(summary.model_dump())
        except Exception as exc:
            logger.warning("Coleção %s indisponível: %s", cid, exc)
            results.append({"id": cid, "status": "indisponível"})

    return {
        "biome": "Amazônia",
        "bbox": resolve_bbox("amazonia"),
        "collections": results,
        "analysis_tips": (
            "Para monitoramento de desmatamento na Amazônia, use data cubes para análise "
            "temporal e mosaicos para visualização de base. O satélite Amazonia-1 (AMZ1) "
            "foi especificamente projetado para vigilância da região amazônica."
        ),
    }


def get_deforestation_analysis_collections() -> dict[str, Any]:
    """Retorna conjunto de coleções recomendadas para análise de desmatamento."""
    pack = DeforestationDataPack(
        land_cover_collections=[
            "LCC_L8_30_16D_STK_Cerrado-1",
            "LCC_L8_30_16D_STK_MataAtlantica-1",
            "LCC_L8_30_16D_STK_Pantanal-1",
        ],
        raw_image_collections=[
            "CB4-WFI-L4-SR-1",
            "CB4A-WFI-L4-DN-1",
            "AMZ1-WFI-L2-DN-1",
        ],
        data_cube_collections=[
            "LANDSAT-16D-1",
            "CBERS4-WFI-16D-2",
            "CBERS-WFI-8D-1",
        ],
        recommended_period="2017-01-01/presente",
        recommended_bands=["NDVI", "EVI", "NIR", "SWIR16", "RED", "GREEN", "CMASK", "CLEAROB"],
        analysis_notes=(
            "Para detecção de desmatamento, recomenda-se:\n"
            "1. Usar data cubes (LANDSAT-16D ou CBERS4-WFI-16D) para construir séries temporais de NDVI/EVI\n"
            "2. Aplicar algoritmos de detecção de mudança (BFAST, LandTrendr) nas séries\n"
            "3. Validar com imagens de alta resolução (Sentinel-2 L2A)\n"
            "4. Usar coleções LCC como referência de classificação\n"
            "5. Filtrar pixels com CLEAROB >= 3 e CMASK == 1 para garantir qualidade"
        ),
    )
    return pack.model_dump()
