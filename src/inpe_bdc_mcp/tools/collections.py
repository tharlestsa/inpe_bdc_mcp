"""Ferramentas MCP para operações em coleções STAC do INPE/BDC."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS, filter_by_biome, filter_by_category, filter_by_satellite
from ..client import BDCClient
from ..models.collection import BandInfo, CollectionComparison, CollectionDetail, CollectionSummary


def _extract_bands(collection_data: dict[str, Any]) -> list[str]:
    """Extrai nomes de bandas dos item_assets ou summaries."""
    bands: list[str] = []
    item_assets = collection_data.get("item_assets", {})
    for key, asset in item_assets.items():
        roles = asset.get("roles", [])
        if "data" in roles or "index" in roles:
            bands.append(key)
    if not bands:
        summaries = collection_data.get("summaries", {})
        if "eo:bands" in summaries:
            for b in summaries["eo:bands"]:
                if isinstance(b, dict) and "name" in b:
                    bands.append(b["name"])
    return bands


def _collection_to_summary(cid: str, data: dict[str, Any]) -> CollectionSummary:
    """Converte dados brutos de coleção para CollectionSummary."""
    known = ALL_COLLECTIONS.get(cid, {})
    extent = data.get("extent", {})
    spatial = extent.get("spatial", {}).get("bbox", [[]])[0] if extent else []
    temporal = extent.get("temporal", {}).get("interval", [[None, None]])[0] if extent else [None, None]

    title = data.get("title", "")
    desc = data.get("description", "")
    is_cube = "cube" in title.lower() or "cube" in desc.lower() or known.get("category") == "data_cube"
    is_mosaic = "mosaic" in cid.lower() or known.get("category") == "mosaic"

    props = data.get("properties", {})
    bdc_public = props.get("bdc:public", data.get("bdc:public", True))
    if isinstance(bdc_public, str):
        bdc_public = bdc_public.lower() != "false"

    return CollectionSummary(
        id=cid,
        title=title,
        description=desc[:500] if desc else "",
        satellite=known.get("satellite", ""),
        sensor=known.get("sensor"),
        spatial_resolution_m=known.get("res_m"),
        temporal_composition=known.get("period"),
        composition_method=known.get("method"),
        level=known.get("level"),
        temporal_extent_start=temporal[0] if temporal else None,
        temporal_extent_end=temporal[1] if len(temporal) > 1 else None,
        spatial_extent_bbox=spatial if isinstance(spatial, list) else [],
        bands=_extract_bands(data),
        bdc_grid=data.get("bdc:grs") or props.get("bdc:grs"),
        is_data_cube=is_cube,
        is_mosaic=is_mosaic,
        is_public=bool(bdc_public),
        license=data.get("license", "proprietary"),
        version=str(v) if (v := data.get("version")) is not None else None,
    )


def list_collections(
    category: str | None = None,
    satellite: str | None = None,
    biome: str | None = None,
    data_type: str | None = None,
    keyword: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Lista coleções com filtros por categoria, satélite, bioma, tipo ou palavra-chave."""
    client = BDCClient.get_instance()
    all_colls = client.list_collections()

    # Construir conjunto de IDs aceitos se filtros de catálogo estático
    allowed_ids: set[str] | None = None
    if category:
        allowed_ids = set(filter_by_category(category))
    if satellite:
        sat_ids = set(filter_by_satellite(satellite))
        allowed_ids = sat_ids if allowed_ids is None else allowed_ids & sat_ids
    if biome:
        bio_ids = set(filter_by_biome(biome))
        allowed_ids = bio_ids if allowed_ids is None else allowed_ids & bio_ids

    results: list[dict[str, Any]] = []
    for coll in all_colls:
        cid = coll.get("id", "")

        if allowed_ids is not None and cid not in allowed_ids:
            continue

        if data_type:
            dt_upper = data_type.upper()
            cid_upper = cid.upper()
            if dt_upper == "SR" and "-SR-" not in cid_upper:
                continue
            if dt_upper == "DN" and "-DN-" not in cid_upper:
                continue
            if dt_upper == "LCC" and not cid_upper.startswith("LCC"):
                continue

        if keyword:
            kw = keyword.lower()
            title = (coll.get("title") or "").lower()
            desc = (coll.get("description") or "").lower()
            if kw not in title and kw not in desc and kw not in cid.lower():
                continue

        summary = _collection_to_summary(cid, coll)
        results.append(summary.model_dump())

        if len(results) >= limit:
            break

    return results


def get_collection_detail(collection_id: str) -> dict[str, Any]:
    """Retorna metadados completos de uma coleção."""
    client = BDCClient.get_instance()
    data = client.get_collection(collection_id)
    known = ALL_COLLECTIONS.get(collection_id, {})
    summary = _collection_to_summary(collection_id, data)

    props = data.get("properties", {})

    detail = CollectionDetail(
        **summary.model_dump(),
        stac_extensions=data.get("stac_extensions", []),
        summaries=data.get("summaries", {}),
        item_assets=data.get("item_assets", {}),
        links=data.get("links", []),
        bdc_bands_quicklook=props.get("bdc:bands_quicklook", []),
        bdc_metadata=props.get("bdc:metadata", {}),
        bdc_grs=data.get("bdc:grs") or props.get("bdc:grs"),
        bdc_tiles=props.get("bdc:tiles", []),
        extra_properties=props,
    )

    return detail.model_dump()


def get_collection_bands(collection_id: str) -> list[dict[str, Any]]:
    """Retorna informações detalhadas sobre as bandas espectrais de uma coleção."""
    client = BDCClient.get_instance()
    data = client.get_collection(collection_id)

    bands: list[dict[str, Any]] = []
    item_assets = data.get("item_assets", {})

    for key, asset in item_assets.items():
        roles = asset.get("roles", [])
        eo_bands = asset.get("eo:bands", [])
        raster_bands = asset.get("raster:bands", [])

        if not any(r in roles for r in ("data", "index", "mask")):
            continue

        kwargs: dict[str, Any] = {
            "name": key,
            "role": roles[0] if roles else "data",
            "description": asset.get("title") or asset.get("description"),
            "gsd_m": asset.get("gsd"),
        }

        if eo_bands and isinstance(eo_bands, list) and len(eo_bands) > 0:
            eb = eo_bands[0]
            kwargs["common_name"] = eb.get("common_name")
            wl = eb.get("center_wavelength")
            if wl is not None:
                kwargs["wavelength_nm"] = wl * 1000 if wl < 10 else wl

        if raster_bands and isinstance(raster_bands, list) and len(raster_bands) > 0:
            rb = raster_bands[0]
            kwargs["data_type"] = rb.get("data_type", "unknown")
            kwargs["nodata"] = rb.get("nodata")
            kwargs["scale"] = rb.get("scale")
            kwargs["offset"] = rb.get("offset")

        bands.append(BandInfo(**kwargs).model_dump())

    return bands


def compare_collections(collection_ids: list[str]) -> dict[str, Any]:
    """Compara múltiplas coleções: bandas, cobertura temporal, resolução."""
    client = BDCClient.get_instance()
    summaries: list[CollectionSummary] = []

    for cid in collection_ids:
        data = client.get_collection(cid)
        summaries.append(_collection_to_summary(cid, data))

    # Bandas em comum
    if summaries:
        band_sets = [set(s.bands) for s in summaries if s.bands]
        common = sorted(set.intersection(*band_sets)) if band_sets else []
    else:
        common = []

    # Cobertura temporal sobreposta
    starts = [s.temporal_extent_start for s in summaries if s.temporal_extent_start]
    ends = [s.temporal_extent_end for s in summaries if s.temporal_extent_end]
    overlap_start = max(starts) if starts else None
    overlap_end = min(ends) if ends else None

    # Comparação de resolução
    res_comp = [
        {"collection": s.id, "resolution_m": s.spatial_resolution_m, "composition": s.temporal_composition}
        for s in summaries
    ]

    # Diferenças de processamento
    diffs: list[str] = []
    levels = {s.id: s.level for s in summaries if s.level}
    if len(set(levels.values())) > 1:
        diffs.append(f"Níveis de processamento diferentes: {levels}")
    methods = {s.id: s.composition_method for s in summaries if s.composition_method}
    if len(set(methods.values())) > 1:
        diffs.append(f"Métodos de composição diferentes: {methods}")

    # Recomendações
    recs: list[str] = []
    for s in summaries:
        if s.is_data_cube:
            recs.append(f"{s.id}: ideal para séries temporais (data cube {s.temporal_composition})")
        elif s.is_mosaic:
            recs.append(f"{s.id}: ideal para visualização de mosaico regional")
        elif s.spatial_resolution_m and s.spatial_resolution_m <= 10:
            recs.append(f"{s.id}: alta resolução ({s.spatial_resolution_m}m), ideal para análise detalhada")

    comp = CollectionComparison(
        collections=summaries,
        common_bands=common,
        temporal_overlap_start=overlap_start,
        temporal_overlap_end=overlap_end,
        resolution_comparison=res_comp,
        processing_differences=diffs,
        recommendations=recs,
    )
    return comp.model_dump()
