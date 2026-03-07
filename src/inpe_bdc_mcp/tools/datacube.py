"""Ferramentas MCP para operações específicas de Data Cubes do BDC."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS, DATA_CUBES
from ..client import BDCClient
from ..models.search import DataCubeInfo, QualityInfo
from ..utils.bdc_grid import BDC_GRIDS, get_grid_info
from ..utils.brazil import resolve_bbox
from .collections import _collection_to_summary, _extract_bands


def list_data_cubes(
    satellite: str | None = None,
    temporal_period: str | None = None,
    biome: str | None = None,
) -> list[dict[str, Any]]:
    """Lista coleções que são data cubes compostos temporalmente.

    Args:
        satellite: Filtro por satélite (ex: "CBERS-4", "Landsat", "Sentinel-2").
        temporal_period: Filtro por período de composição (ex: "16D", "8D", "1M").
        biome: Filtro por bioma (usado para verificar cobertura espacial).
    """
    client = BDCClient.get_instance()
    all_colls = client.list_collections()

    biome_bbox = resolve_bbox(biome) if biome else None

    results: list[dict[str, Any]] = []
    for coll in all_colls:
        cid = coll.get("id", "")
        known = DATA_CUBES.get(cid)
        if known is None:
            title = (coll.get("title") or "").lower()
            desc = (coll.get("description") or "").lower()
            if "cube" not in title and "cube" not in desc:
                continue
            known = {}

        if satellite:
            sat = known.get("satellite", "")
            if satellite.lower() not in sat.lower():
                continue

        if temporal_period:
            period = known.get("period", "")
            if temporal_period.upper() != period.upper():
                continue

        if biome_bbox:
            extent = coll.get("extent", {})
            spatial = extent.get("spatial", {}).get("bbox", [[]])[0]
            if spatial and len(spatial) == 4:
                from ..utils.geo import bbox_intersects
                if not bbox_intersects(spatial, biome_bbox):
                    continue

        bands = _extract_bands(coll)
        indices = [b for b in bands if b.upper() in ("NDVI", "EVI", "EVI2", "SAVI", "NBRT")]
        quality = [b for b in bands if b.upper() in ("CLEAROB", "CMASK", "TOTALOB", "SCL", "PROVENANCE")]

        extent = coll.get("extent", {})
        temporal = extent.get("temporal", {}).get("interval", [[None, None]])[0]

        props = coll.get("properties", {})

        info = DataCubeInfo(
            collection_id=cid,
            title=coll.get("title", ""),
            satellite=known.get("satellite", ""),
            temporal_composition=known.get("period", ""),
            composition_method=known.get("method", ""),
            spatial_resolution_m=known.get("res_m", 0.0),
            bdc_grid_version=coll.get("bdc:grs") or props.get("bdc:grs", ""),
            available_bands=bands,
            derived_indices=indices,
            quality_bands=quality,
            temporal_extent_start=temporal[0] if temporal else None,
            temporal_extent_end=temporal[1] if len(temporal) > 1 else None,
        )
        results.append(info.model_dump())

    return results


def get_bdc_grid_info(collection_id: str) -> dict[str, Any]:
    """Retorna informações sobre a grade BDC usada por uma coleção."""
    client = BDCClient.get_instance()
    data = client.get_collection(collection_id)
    props = data.get("properties", {})
    grid_name = data.get("bdc:grs") or props.get("bdc:grs", "")

    grid = get_grid_info(grid_name)
    if grid:
        return {
            "collection_id": collection_id,
            "grid_name": grid.grid_name,
            "crs_epsg": grid.crs_epsg,
            "tile_size_m": grid.tile_size_m,
            "overlap_m": grid.overlap_m,
            "description": grid.description,
        }

    return {
        "collection_id": collection_id,
        "grid_name": grid_name or "Não identificada",
        "note": "Informações detalhadas da grade não disponíveis no catálogo local.",
        "available_grids": list(BDC_GRIDS.keys()),
    }


def get_cube_quality_info(collection_id: str) -> dict[str, Any]:
    """Explica as bandas de qualidade de um data cube BDC."""
    client = BDCClient.get_instance()
    data = client.get_collection(collection_id)
    bands = _extract_bands(data)

    quality_descriptions: dict[str, str] = {
        "CLEAROB": (
            "Número de observações livres de nuvem usadas na composição. "
            "Valores mais altos indicam maior confiabilidade do pixel composto."
        ),
        "CMASK": (
            "Máscara de nuvem do item composto. Valores: "
            "0 = sem dados, 1 = limpo, 127 = nuvem, 255 = sombra de nuvem."
        ),
        "TOTALOB": (
            "Número total de observações disponíveis no período de composição, "
            "incluindo observações com nuvem."
        ),
        "PROVENANCE": (
            "Índice do dia dentro do período de composição de onde o pixel foi selecionado. "
            "Útil para rastrear a data exata de aquisição do pixel composto."
        ),
        "SCL": (
            "Scene Classification Layer (Sentinel-2). Classes: "
            "0=no_data, 1=saturated, 2=dark_area, 3=cloud_shadow, "
            "4=vegetation, 5=bare_soil, 6=water, 7=unclassified, "
            "8=cloud_medium, 9=cloud_high, 10=cirrus, 11=snow."
        ),
    }

    found_quality: dict[str, str] = {}
    for b in bands:
        b_upper = b.upper()
        if b_upper in quality_descriptions:
            found_quality[b] = quality_descriptions[b_upper]

    guide = (
        "Para análises confiáveis, recomenda-se filtrar pixels com CLEAROB >= 3 "
        "e CMASK == 1 (limpo). O TOTALOB permite calcular a fração de observações "
        "úteis: CLEAROB / TOTALOB."
    )

    info = QualityInfo(
        collection_id=collection_id,
        quality_bands=found_quality,
        interpretation_guide=guide,
    )
    return info.model_dump()


def find_cube_for_analysis(
    region: str,
    start_year: int | None = None,
    end_year: int | None = None,
    min_resolution_m: float | None = None,
    required_indices: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Recomenda data cubes para uma análise temporal em uma região.

    Args:
        region: Nome da região/bioma (ex: "cerrado", "goias").
        start_year: Ano inicial da análise.
        end_year: Ano final da análise.
        min_resolution_m: Resolução espacial mínima aceita (em metros).
        required_indices: Índices espectrais necessários (ex: ["NDVI", "EVI"]).
    """
    cubes = list_data_cubes(biome=region)
    filtered: list[dict[str, Any]] = []

    for cube in cubes:
        if min_resolution_m and cube.get("spatial_resolution_m", 0) > min_resolution_m:
            continue

        if required_indices:
            available = [b.upper() for b in cube.get("available_bands", [])]
            available += [b.upper() for b in cube.get("derived_indices", [])]
            if not all(idx.upper() in available for idx in required_indices):
                continue

        if start_year and cube.get("temporal_extent_start"):
            cube_start_year = int(cube["temporal_extent_start"][:4])
            if cube_start_year > start_year:
                continue

        if end_year and cube.get("temporal_extent_end") and cube["temporal_extent_end"] != "null":
            try:
                cube_end_year = int(cube["temporal_extent_end"][:4])
                if cube_end_year < end_year:
                    continue
            except (ValueError, TypeError):
                pass

        filtered.append(cube)

    # Ordenar por resolução (menor = melhor)
    filtered.sort(key=lambda c: c.get("spatial_resolution_m", 9999))

    return filtered
