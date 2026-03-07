"""Ferramentas MCP para busca avançada de itens STAC no INPE/BDC."""

from __future__ import annotations

import time
from typing import Any

from ..client import BDCClient
from ..models.item import ItemSummary
from ..models.search import SearchResult
from ..utils.brazil import resolve_bbox
from ..utils.geo import make_point


def _resolve_bbox_param(bbox: list[float] | str | None) -> list[float] | None:
    """Aceita bbox como lista ou nome de região."""
    if bbox is None:
        return None
    if isinstance(bbox, str):
        resolved = resolve_bbox(bbox)
        if resolved is None:
            raise ValueError(
                f"Região '{bbox}' não reconhecida. Use list_regions() para ver nomes válidos."
            )
        return resolved
    return bbox


def search_items(
    collections: list[str] | None = None,
    bbox: list[float] | str | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    limit: int = 50,
    sortby: str | None = None,
) -> dict[str, Any]:
    """Busca itens STAC com filtros avançados.

    Args:
        collections: Lista de IDs de coleções (ex: ["CBERS4-WFI-16D-2"]).
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat] ou nome de região
              (ex: "cerrado", "goias", "amazonia").
        datetime_range: Intervalo ISO 8601 (ex: "2020-01-01/2023-12-31").
        cloud_cover_max: Percentual máximo de cobertura de nuvens (0-100).
        limit: Número máximo de itens (1-1000, padrão 50).
        sortby: Ordenação (ex: "-properties.datetime" para mais recente primeiro).
    """
    client = BDCClient.get_instance()
    resolved_bbox = _resolve_bbox_param(bbox)

    query: dict[str, Any] | None = None
    if cloud_cover_max is not None:
        query = {"eo:cloud_cover": {"lte": cloud_cover_max}}

    sortby_list: list[dict] | None = None
    if sortby:
        parts = sortby.split(",")
        sortby_list = []
        for p in parts:
            p = p.strip()
            if p.startswith("-"):
                sortby_list.append({"field": p[1:], "direction": "desc"})
            elif p.startswith("+"):
                sortby_list.append({"field": p[1:], "direction": "asc"})
            else:
                sortby_list.append({"field": p, "direction": "asc"})

    result = client.search_to_result(
        collections=collections,
        bbox=resolved_bbox,
        datetime=datetime_range,
        query=query,
        sortby=sortby_list,
        limit=min(limit, 1000),
    )
    return result.model_dump()


def search_by_point(
    lon: float,
    lat: float,
    collections: list[str] | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Busca itens que contêm um ponto específico (lon, lat)."""
    client = BDCClient.get_instance()
    intersects = make_point(lon, lat)

    query: dict[str, Any] | None = None
    if cloud_cover_max is not None:
        query = {"eo:cloud_cover": {"lte": cloud_cover_max}}

    result = client.search_to_result(
        collections=collections,
        intersects=intersects,
        datetime=datetime_range,
        query=query,
        limit=min(limit, 1000),
    )
    return result.model_dump()


def search_by_polygon(
    geojson_geometry: dict[str, Any],
    collections: list[str] | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Busca itens que intersectam uma geometria GeoJSON (Polygon/MultiPolygon)."""
    client = BDCClient.get_instance()

    query: dict[str, Any] | None = None
    if cloud_cover_max is not None:
        query = {"eo:cloud_cover": {"lte": cloud_cover_max}}

    result = client.search_to_result(
        collections=collections,
        intersects=geojson_geometry,
        datetime=datetime_range,
        query=query,
        limit=min(limit, 1000),
    )
    return result.model_dump()


def search_by_tile(
    collection_id: str,
    tile_id: str,
    datetime_range: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Busca itens por tile BDC específico (ex: '007004')."""
    client = BDCClient.get_instance()

    query = {"bdc:tile": {"eq": tile_id}}

    result = client.search_to_result(
        collections=[collection_id],
        datetime=datetime_range,
        query=query,
        limit=min(limit, 1000),
    )
    return result.model_dump()


def search_latest_items(
    collection_id: str,
    bbox: list[float] | str | None = None,
    n: int = 10,
    cloud_cover_max: float | None = None,
) -> dict[str, Any]:
    """Retorna os N itens mais recentes de uma coleção."""
    client = BDCClient.get_instance()
    resolved_bbox = _resolve_bbox_param(bbox)

    query: dict[str, Any] | None = None
    if cloud_cover_max is not None:
        query = {"eo:cloud_cover": {"lte": cloud_cover_max}}

    result = client.search_to_result(
        collections=[collection_id],
        bbox=resolved_bbox,
        query=query,
        sortby=[{"field": "properties.datetime", "direction": "desc"}],
        limit=n,
    )
    return result.model_dump()


def search_cloud_free(
    collections: list[str],
    bbox: list[float] | str | None = None,
    datetime_range: str | None = None,
    max_cloud: float = 10.0,
    limit: int = 50,
) -> dict[str, Any]:
    """Busca imagens com baixa cobertura de nuvens, ordenadas da mais limpa."""
    client = BDCClient.get_instance()
    resolved_bbox = _resolve_bbox_param(bbox)

    result = client.search_to_result(
        collections=collections,
        bbox=resolved_bbox,
        datetime=datetime_range,
        query={"eo:cloud_cover": {"lte": max_cloud}},
        sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
        limit=min(limit, 1000),
    )
    return result.model_dump()


def get_all_pages(
    collections: list[str] | None = None,
    bbox: list[float] | str | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    max_items: int = 5000,
) -> dict[str, Any]:
    """Itera por todas as páginas de resultados (até max_items)."""
    client = BDCClient.get_instance()
    resolved_bbox = _resolve_bbox_param(bbox)

    query: dict[str, Any] | None = None
    if cloud_cover_max is not None:
        query = {"eo:cloud_cover": {"lte": cloud_cover_max}}

    result = client.search_to_result(
        collections=collections,
        bbox=resolved_bbox,
        datetime=datetime_range,
        query=query,
        limit=1000,
        max_items=max_items,
    )
    return result.model_dump()
