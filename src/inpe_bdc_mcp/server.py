"""INPE Brazil Data Cube MCP Server — entrypoint FastMCP."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

# Logging para stderr (MCP usa stdout para protocolo)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("inpe-bdc-mcp")

mcp = FastMCP(
    "inpe-bdc-stac",
    instructions=(
        "MCP Server para a STAC API do INPE/Brazil Data Cube. "
        "Acesso a imagens de satélite (CBERS, Amazonia-1, Sentinel, Landsat, MODIS, GOES-19), "
        "data cubes compostos, mosaicos, classificações de uso do solo e dados oceânicos/meteorológicos. "
        "Cobertura: território brasileiro e América do Sul."
    ),
)


# ============================================================ #
#  Error handler decorator
# ============================================================ #

def _handle_errors(func):
    """Decorator para tratamento padronizado de erros nas tools."""
    import functools
    import httpx
    from pystac_client.exceptions import APIError

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            logger.warning("Erro da STAC API: %s", e)
            return json.dumps({
                "error": "Erro na STAC API",
                "code": "STAC_API_ERROR",
                "details": str(e)[:500],
                "suggestion": "Verifique os parâmetros da busca ou tente novamente.",
                "requires_api_key": False,
            }, ensure_ascii=False)
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code in (401, 403):
                return json.dumps({
                    "error": "Autenticação necessária",
                    "code": "UNAUTHORIZED",
                    "details": f"HTTP {code}: {e.response.text[:200]}",
                    "suggestion": "Configure a variável BDC_API_KEY com sua chave do portal BDC.",
                    "requires_api_key": True,
                }, ensure_ascii=False)
            elif code == 404:
                return json.dumps({
                    "error": "Recurso não encontrado",
                    "code": "NOT_FOUND",
                    "details": str(e)[:300],
                    "suggestion": "Verifique o ID da coleção/item com list_collections().",
                    "requires_api_key": False,
                }, ensure_ascii=False)
            elif code == 422:
                return json.dumps({
                    "error": "Parâmetros inválidos",
                    "code": "BAD_REQUEST",
                    "details": e.response.text[:500],
                    "suggestion": "Revise os parâmetros da busca.",
                    "requires_api_key": False,
                }, ensure_ascii=False)
            elif code == 429:
                retry_after = e.response.headers.get("Retry-After", "60")
                return json.dumps({
                    "error": "Rate limit excedido",
                    "code": "RATE_LIMIT",
                    "details": f"Aguarde {retry_after} segundos antes de tentar novamente.",
                    "requires_api_key": False,
                }, ensure_ascii=False)
            return json.dumps({
                "error": f"Erro HTTP {code}",
                "code": "NETWORK_ERROR",
                "details": str(e)[:300],
                "requires_api_key": False,
            }, ensure_ascii=False)
        except httpx.TimeoutException:
            return json.dumps({
                "error": "Timeout na requisição",
                "code": "TIMEOUT",
                "details": "A API do BDC não respondeu dentro do tempo limite.",
                "suggestion": "Tente novamente ou reduza o escopo da busca.",
                "requires_api_key": False,
            }, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({
                "error": "Parâmetro inválido",
                "code": "BAD_REQUEST",
                "details": str(e),
                "requires_api_key": False,
            }, ensure_ascii=False)
        except Exception as e:
            logger.exception("Erro inesperado")
            return json.dumps({
                "error": "Erro interno",
                "code": "INTERNAL_ERROR",
                "details": str(e)[:300],
                "requires_api_key": False,
            }, ensure_ascii=False)

    return wrapper


# ============================================================ #
#  Tools — Catálogo
# ============================================================ #

@mcp.tool()
@_handle_errors
def catalog_info() -> str:
    """Retorna informações gerais do catálogo INPE/BDC STAC: versão, total de coleções, endpoints e status de autenticação."""
    from .tools.catalog import catalog_info as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def list_conformance_classes() -> str:
    """Lista todas as conformance classes OGC implementadas pela STAC API do BDC."""
    from .tools.catalog import list_conformance_classes as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_api_capabilities() -> str:
    """Resume as capacidades da STAC API: suporte a CQL2, fields, sortby, autenticação, paginação."""
    from .tools.catalog import get_api_capabilities as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Coleções
# ============================================================ #

@mcp.tool()
@_handle_errors
def list_collections(
    category: str | None = None,
    satellite: str | None = None,
    biome: str | None = None,
    data_type: str | None = None,
    keyword: str | None = None,
    limit: int = 50,
) -> str:
    """Lista coleções do BDC com filtros.

    Args:
        category: Categoria — "raw_image", "data_cube", "mosaic", "land_cover", "modis", "ocean", "weather".
        satellite: Satélite — "CBERS-4", "CBERS-4A", "Amazonia-1", "Sentinel-2", "Landsat", "MODIS", "GOES-19".
        biome: Bioma — "cerrado", "amazonia", "mata_atlantica", "pantanal", "caatinga", "pampa".
        data_type: Tipo de dado — "SR" (surface reflectance), "DN" (digital numbers), "LCC" (land cover).
        keyword: Busca textual livre no título/descrição.
        limit: Número máximo de resultados (padrão 50).
    """
    from .tools.collections import list_collections as _fn
    return json.dumps(_fn(category, satellite, biome, data_type, keyword, limit), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_collection_detail(collection_id: str) -> str:
    """Retorna metadados completos de uma coleção: bandas, extensão temporal/espacial, extensões STAC, propriedades BDC.

    Args:
        collection_id: ID da coleção (ex: "CBERS4-WFI-16D-2", "S2_L2A-1", "LANDSAT-16D-1").
    """
    from .tools.collections import get_collection_detail as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_collection_bands(collection_id: str) -> str:
    """Retorna informações detalhadas sobre bandas espectrais de uma coleção: nome, comprimento de onda, resolução, tipo de dado.

    Args:
        collection_id: ID da coleção.
    """
    from .tools.collections import get_collection_bands as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def compare_collections(collection_ids: list[str]) -> str:
    """Compara múltiplas coleções: bandas em comum, cobertura temporal, resolução, recomendações.

    Args:
        collection_ids: Lista de IDs de coleções para comparar (ex: ["LANDSAT-16D-1", "CBERS4-WFI-16D-2"]).
    """
    from .tools.collections import compare_collections as _fn
    return json.dumps(_fn(collection_ids), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Busca
# ============================================================ #

@mcp.tool()
@_handle_errors
def search_items(
    collections: list[str] | None = None,
    bbox: list[float] | str | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    limit: int = 50,
    sortby: str | None = None,
) -> str:
    """Busca itens STAC com filtros avançados (cross-collection, bbox, temporal, nuvens).

    Args:
        collections: Lista de IDs de coleções (ex: ["CBERS4-WFI-16D-2", "LANDSAT-16D-1"]).
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat] ou nome de região ("cerrado", "goias", "amazonia").
        datetime_range: Intervalo ISO 8601 (ex: "2020-01-01/2023-12-31").
        cloud_cover_max: Percentual máximo de nuvens (0-100).
        limit: Máximo de itens (1-1000, padrão 50).
        sortby: Ordenação — ex: "-properties.datetime" (mais recente primeiro).
    """
    from .tools.search import search_items as _fn
    return json.dumps(_fn(collections, bbox, datetime_range, cloud_cover_max, limit, sortby), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def search_by_point(
    lon: float,
    lat: float,
    collections: list[str] | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    limit: int = 50,
) -> str:
    """Busca itens que contêm um ponto específico (longitude, latitude).

    Args:
        lon: Longitude (WGS84, ex: -49.5).
        lat: Latitude (WGS84, ex: -15.7).
        collections: Lista de IDs de coleções.
        datetime_range: Intervalo ISO 8601.
        cloud_cover_max: Percentual máximo de nuvens (0-100).
        limit: Máximo de itens.
    """
    from .tools.search import search_by_point as _fn
    return json.dumps(_fn(lon, lat, collections, datetime_range, cloud_cover_max, limit), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def search_by_polygon(
    geojson_geometry: dict[str, Any],
    collections: list[str] | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    limit: int = 50,
) -> str:
    """Busca itens que intersectam uma geometria GeoJSON (Polygon ou MultiPolygon).

    Args:
        geojson_geometry: Geometria GeoJSON (ex: {"type": "Polygon", "coordinates": [[[...]]]]}).
        collections: Lista de IDs de coleções.
        datetime_range: Intervalo ISO 8601.
        cloud_cover_max: Percentual máximo de nuvens (0-100).
        limit: Máximo de itens.
    """
    from .tools.search import search_by_polygon as _fn
    return json.dumps(_fn(geojson_geometry, collections, datetime_range, cloud_cover_max, limit), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def search_by_tile(
    collection_id: str,
    tile_id: str,
    datetime_range: str | None = None,
    limit: int = 50,
) -> str:
    """Busca itens por tile BDC específico.

    Args:
        collection_id: ID da coleção.
        tile_id: Tile BDC (ex: "007004" — formato 6 dígitos row/col).
        datetime_range: Intervalo ISO 8601.
        limit: Máximo de itens.
    """
    from .tools.search import search_by_tile as _fn
    return json.dumps(_fn(collection_id, tile_id, datetime_range, limit), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def search_latest_items(
    collection_id: str,
    bbox: list[float] | str | None = None,
    n: int = 10,
    cloud_cover_max: float | None = None,
) -> str:
    """Retorna os N itens mais recentes de uma coleção.

    Args:
        collection_id: ID da coleção.
        bbox: Bounding box ou nome de região.
        n: Número de itens (padrão 10).
        cloud_cover_max: Percentual máximo de nuvens.
    """
    from .tools.search import search_latest_items as _fn
    return json.dumps(_fn(collection_id, bbox, n, cloud_cover_max), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def search_cloud_free(
    collections: list[str],
    bbox: list[float] | str | None = None,
    datetime_range: str | None = None,
    max_cloud: float = 10.0,
    limit: int = 50,
) -> str:
    """Busca imagens com baixa cobertura de nuvens, ordenadas da mais limpa.

    Args:
        collections: Lista de IDs de coleções.
        bbox: Bounding box ou nome de região.
        datetime_range: Intervalo ISO 8601.
        max_cloud: Percentual máximo de nuvens (padrão 10%).
        limit: Máximo de itens.
    """
    from .tools.search import search_cloud_free as _fn
    return json.dumps(_fn(collections, bbox, datetime_range, max_cloud, limit), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_all_pages(
    collections: list[str] | None = None,
    bbox: list[float] | str | None = None,
    datetime_range: str | None = None,
    cloud_cover_max: float | None = None,
    max_items: int = 5000,
) -> str:
    """Itera por todas as páginas de resultados de busca (até max_items).

    Args:
        collections: Lista de IDs de coleções.
        bbox: Bounding box ou nome de região.
        datetime_range: Intervalo ISO 8601.
        cloud_cover_max: Percentual máximo de nuvens.
        max_items: Máximo de itens total (padrão 5000).
    """
    from .tools.search import get_all_pages as _fn
    return json.dumps(_fn(collections, bbox, datetime_range, cloud_cover_max, max_items), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Itens e Assets
# ============================================================ #

@mcp.tool()
@_handle_errors
def get_item(collection_id: str, item_id: str) -> str:
    """Retorna detalhes completos de um item STAC: geometria, propriedades, assets, metadados BDC.

    Args:
        collection_id: ID da coleção.
        item_id: ID do item.
    """
    from .tools.items import get_item as _fn
    return json.dumps(_fn(collection_id, item_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def list_item_assets(collection_id: str, item_id: str) -> str:
    """Lista todos os assets de um item: URLs, tipo MIME, bandas, se é COG.

    Args:
        collection_id: ID da coleção.
        item_id: ID do item.
    """
    from .tools.items import list_item_assets as _fn
    return json.dumps(_fn(collection_id, item_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_asset_download_info(collection_id: str, item_id: str, asset_key: str) -> str:
    """Gera snippets de download (curl, wget, Python, R) para um asset específico.

    Args:
        collection_id: ID da coleção.
        item_id: ID do item.
        asset_key: Chave do asset (ex: "NDVI", "RED", "thumbnail").
    """
    from .tools.items import get_asset_download_info as _fn
    return json.dumps(_fn(collection_id, item_id, asset_key), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_thumbnail_url(collection_id: str, item_id: str) -> str:
    """Retorna URL do thumbnail de um item para visualização rápida.

    Args:
        collection_id: ID da coleção.
        item_id: ID do item.
    """
    from .tools.items import get_thumbnail_url as _fn
    return json.dumps(_fn(collection_id, item_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_quicklook_bands(collection_id: str) -> str:
    """Retorna as bandas usadas para gerar quicklook/thumbnail em uma coleção.

    Args:
        collection_id: ID da coleção.
    """
    from .tools.items import get_quicklook_bands as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_stac_item_as_geojson(collection_id: str, item_id: str) -> str:
    """Retorna um item STAC como GeoJSON Feature puro (para uso em GIS).

    Args:
        collection_id: ID da coleção.
        item_id: ID do item.
    """
    from .tools.items import get_stac_item_as_geojson as _fn
    return json.dumps(_fn(collection_id, item_id), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Data Cubes
# ============================================================ #

@mcp.tool()
@_handle_errors
def list_data_cubes(
    satellite: str | None = None,
    temporal_period: str | None = None,
    biome: str | None = None,
) -> str:
    """Lista data cubes BDC (composições temporais regulares).

    Args:
        satellite: Filtro por satélite (ex: "CBERS-4", "Landsat", "Sentinel-2").
        temporal_period: Filtro por período (ex: "16D", "8D", "1M").
        biome: Filtro por bioma.
    """
    from .tools.datacube import list_data_cubes as _fn
    return json.dumps(_fn(satellite, temporal_period, biome), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_bdc_grid_info(collection_id: str) -> str:
    """Informações sobre a grade BDC usada por uma coleção: projeção, tamanho de tile, sobreposição.

    Args:
        collection_id: ID da coleção.
    """
    from .tools.datacube import get_bdc_grid_info as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_cube_quality_info(collection_id: str) -> str:
    """Explica as bandas de qualidade de um data cube (CLEAROB, CMASK, TOTALOB) e como interpretá-las.

    Args:
        collection_id: ID do data cube.
    """
    from .tools.datacube import get_cube_quality_info as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def find_cube_for_analysis(
    region: str,
    start_year: int | None = None,
    end_year: int | None = None,
    min_resolution_m: float | None = None,
    required_indices: list[str] | None = None,
) -> str:
    """Recomenda data cubes para uma análise temporal em uma região.

    Args:
        region: Nome da região/bioma (ex: "cerrado", "goias").
        start_year: Ano inicial da análise.
        end_year: Ano final da análise.
        min_resolution_m: Resolução espacial máxima aceita (em metros).
        required_indices: Índices espectrais necessários (ex: ["NDVI", "EVI"]).
    """
    from .tools.datacube import find_cube_for_analysis as _fn
    return json.dumps(_fn(region, start_year, end_year, min_resolution_m, required_indices), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Satélites
# ============================================================ #

@mcp.tool()
@_handle_errors
def get_cbers_collections(version: str | None = None) -> str:
    """Lista coleções CBERS com descrição dos sensores (PAN5M, PAN10M, MUX, WFI, HRC).

    Args:
        version: "CBERS-2B", "CBERS-4" ou "CBERS-4A". None para todos.
    """
    from .tools.satellites import get_cbers_collections as _fn
    return json.dumps(_fn(version), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_sentinel2_collections() -> str:
    """Lista coleções Sentinel-2 disponíveis: L1C, L2A, data cubes e mosaicos."""
    from .tools.satellites import get_sentinel2_collections as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_landsat_collections() -> str:
    """Lista coleções Landsat: imagens brutas, data cubes e mosaicos."""
    from .tools.satellites import get_landsat_collections as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_goes19_info() -> str:
    """Informações sobre dados GOES-19 CMI: bandas ABI, frequência, cobertura."""
    from .tools.satellites import get_goes19_info as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_amazonia1_collections() -> str:
    """Lista coleções do satélite Amazonia-1 — satélite 100% brasileiro."""
    from .tools.satellites import get_amazonia1_collections as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_sentinel3_info() -> str:
    """Informações sobre Sentinel-3 OLCI: dados oceânicos/costeiros, 21 bandas."""
    from .tools.satellites import get_sentinel3_info as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Biomas
# ============================================================ #

@mcp.tool()
@_handle_errors
def get_biome_bbox(biome: str) -> str:
    """Retorna bounding box WGS84 de um bioma ou região brasileira.

    Args:
        biome: Nome — "amazonia", "cerrado", "mata_atlantica", "caatinga", "pantanal", "pampa",
               ou estados ("goias", "mato_grosso"), ou regiões ("matopiba", "arco_desmatamento").
    """
    from .tools.biomes import get_biome_bbox as _fn
    return json.dumps(_fn(biome), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def find_collections_for_biome(
    biome: str,
    category: str | None = None,
    satellite: str | None = None,
) -> str:
    """Encontra coleções com cobertura espacial de um bioma brasileiro.

    Args:
        biome: Nome do bioma/região (ex: "cerrado", "amazonia").
        category: Filtro por categoria (ex: "data_cube", "raw_image").
        satellite: Filtro por satélite.
    """
    from .tools.biomes import find_collections_for_biome as _fn
    return json.dumps(_fn(biome, category, satellite), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_cerrado_monitoring_collections() -> str:
    """Coleções recomendadas para monitoramento do Cerrado com dicas de análise."""
    from .tools.biomes import get_cerrado_monitoring_collections as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_amazon_monitoring_collections() -> str:
    """Coleções recomendadas para monitoramento da Amazônia (desmatamento, degradação)."""
    from .tools.biomes import get_amazon_monitoring_collections as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_deforestation_analysis_collections() -> str:
    """Pacote completo de coleções para análise de desmatamento: LCC, imagens brutas, data cubes, bandas recomendadas."""
    from .tools.biomes import get_deforestation_analysis_collections as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Análise e Geração de Código
# ============================================================ #

@mcp.tool()
@_handle_errors
def discover_collections_for_topic(topic: str) -> str:
    """Sugere coleções BDC para um tema de análise em linguagem natural.

    Args:
        topic: Tema em português ou inglês (ex: "desmatamento no Cerrado", "NDVI time series",
               "qualidade da água costeira", "soja em Mato Grosso").
    """
    from .tools.analysis import discover_collections_for_topic as _fn
    return json.dumps(_fn(topic), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def build_python_search_snippet(
    collections: list[str],
    bbox_or_biome: str | list[float] | None = None,
    datetime_range: str = "2020-01-01/2023-12-31",
    cloud_max: float | None = None,
    asset_keys: list[str] | None = None,
) -> str:
    """Gera snippet Python completo usando pystac-client para buscar e acessar dados BDC.

    Args:
        collections: Lista de IDs de coleções.
        bbox_or_biome: Bbox [min_lon, min_lat, max_lon, max_lat] ou nome de região ("cerrado").
        datetime_range: Intervalo temporal ISO 8601.
        cloud_max: Percentual máximo de nuvens.
        asset_keys: Chaves dos assets para acessar (ex: ["NDVI", "EVI"]).
    """
    from .tools.analysis import build_python_search_snippet as _fn
    return _fn(collections, bbox_or_biome, datetime_range, cloud_max, asset_keys)


@mcp.tool()
@_handle_errors
def build_r_snippet(
    collections: list[str],
    bbox_or_biome: str | list[float] | None = None,
    datetime_range: str = "2020-01-01/2023-12-31",
    cloud_max: float | None = None,
) -> str:
    """Gera snippet R usando rstac para buscar dados BDC.

    Args:
        collections: Lista de IDs de coleções.
        bbox_or_biome: Bbox ou nome de região.
        datetime_range: Intervalo temporal ISO 8601.
        cloud_max: Percentual máximo de nuvens.
    """
    from .tools.analysis import build_r_snippet as _fn
    return _fn(collections, bbox_or_biome, datetime_range, cloud_max)


@mcp.tool()
@_handle_errors
def get_time_series_plan(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
    band: str = "NDVI",
) -> str:
    """Plano completo para extração de série temporal: itens esperados, volume, snippet Python.

    Args:
        collection_id: ID do data cube (ex: "LANDSAT-16D-1").
        bbox_or_biome: Bbox ou nome de região.
        start_year: Ano inicial.
        end_year: Ano final.
        band: Banda ou índice (ex: "NDVI", "EVI", "RED").
    """
    from .tools.analysis import get_time_series_plan as _fn
    return json.dumps(_fn(collection_id, bbox_or_biome, start_year, end_year, band), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Índices Espectrais
# ============================================================ #

@mcp.tool()
@_handle_errors
def list_spectral_indices(category: str | None = None) -> str:
    """Lista índices espectrais disponíveis (NDVI, EVI, NBR, NDWI, etc.).

    Args:
        category: Filtro por categoria — "vegetation", "water", "soil", "burn", "snow", "urban".
    """
    from .tools.spectral import list_spectral_indices as _fn
    return json.dumps(_fn(category), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_spectral_index_info(index_name: str) -> str:
    """Retorna detalhes de um índice espectral: fórmula, bandas, aplicações, referência.

    Args:
        index_name: Nome do índice (ex: "NDVI", "EVI", "NBR", "NDWI", "SAVI").
    """
    from .tools.spectral import get_spectral_index_info as _fn
    return json.dumps(_fn(index_name), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_collection_index_availability(collection_id: str) -> str:
    """Verifica quais índices espectrais podem ser calculados a partir de uma coleção BDC.

    Args:
        collection_id: ID da coleção STAC.
    """
    from .tools.spectral import get_collection_index_availability as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def generate_index_code(
    index_name: str,
    collection_id: str,
    language: str = "python",
) -> str:
    """Gera código Python/R/sits para calcular um índice espectral em uma coleção BDC.

    Args:
        index_name: Nome do índice (ex: "NDVI", "EVI").
        collection_id: ID da coleção STAC.
        language: Linguagem — "python", "r" ou "sits".
    """
    from .tools.spectral import generate_index_code as _fn
    return json.dumps(_fn(index_name, collection_id, language), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def suggest_indices_for_application(application: str) -> str:
    """Sugere índices espectrais para uma aplicação de sensoriamento remoto.

    Args:
        application: Tipo de aplicação (ex: "vegetacao", "fogo", "agua", "desmatamento", "agricultura", "pastagem").
    """
    from .tools.spectral import suggest_indices_for_application as _fn
    return json.dumps(_fn(application), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Pré-processamento
# ============================================================ #

@mcp.tool()
@_handle_errors
def get_preprocessing_guide(collection_id: str) -> str:
    """Guia completo de pré-processamento para uma coleção: nível de correção, o que falta, recomendações.

    Args:
        collection_id: ID da coleção STAC.
    """
    from .tools.preprocessing import get_preprocessing_guide as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_cloud_mask_strategy(collection_id: str) -> str:
    """Retorna estratégia de mascaramento de nuvens com código Python/R (CMASK, SCL, Fmask).

    Args:
        collection_id: ID da coleção STAC.
    """
    from .tools.preprocessing import get_cloud_mask_strategy as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_atmospheric_correction_info(collection_id: str) -> str:
    """Informações sobre correção atmosférica: algoritmo aplicado, necessidade de correção adicional.

    Args:
        collection_id: ID da coleção STAC.
    """
    from .tools.preprocessing import get_atmospheric_correction_info as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_pan_sharpening_guide(collection_id: str) -> str:
    """Guia de pan-sharpening para coleções pancromáticas CBERS (PAN5M/PAN10M + MUX/WFI).

    Args:
        collection_id: ID da coleção STAC (ex: "CB4-PAN5M-L4-DN-1").
    """
    from .tools.preprocessing import get_pan_sharpening_guide as _fn
    return json.dumps(_fn(collection_id), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Projeção e Geometria
# ============================================================ #

@mcp.tool()
@_handle_errors
def reproject_bbox(
    bbox: list[float],
    from_crs: str = "EPSG:4326",
    to_crs: str = "bdc_albers",
) -> str:
    """Reprojeção de bounding box entre sistemas de referência (WGS84, BDC Albers, UTM, SIRGAS2000).

    Args:
        bbox: Bounding box [min_x, min_y, max_x, max_y].
        from_crs: CRS de origem — "EPSG:4326", "bdc_albers", "EPSG:xxxxx".
        to_crs: CRS de destino — "EPSG:4326", "bdc_albers", "EPSG:xxxxx".
    """
    from .tools.projection import reproject_bbox as _fn
    return json.dumps(_fn(bbox, from_crs, to_crs), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def calculate_area(
    bbox: list[float] | None = None,
    geojson: dict[str, Any] | None = None,
    crs: str = "EPSG:4326",
) -> str:
    """Calcula área de um bbox ou geometria GeoJSON em hectares e km².

    Args:
        bbox: Bounding box [min_x, min_y, max_x, max_y].
        geojson: Geometria GeoJSON (Polygon).
        crs: CRS da geometria de entrada (padrão: EPSG:4326).
    """
    from .tools.projection import calculate_area as _fn
    return json.dumps(_fn(bbox, geojson, crs), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_utm_zone(lon: float, lat: float) -> str:
    """Retorna a zona UTM e código EPSG para uma coordenada geográfica.

    Args:
        lon: Longitude (WGS84).
        lat: Latitude (WGS84).
    """
    from .tools.projection import get_utm_zone as _fn
    return json.dumps(_fn(lon, lat), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def convert_geometry_format(
    geometry: dict[str, Any] | str,
    to_format: str = "wkt",
) -> str:
    """Converte geometria entre GeoJSON e WKT.

    Args:
        geometry: Geometria GeoJSON (dict) ou WKT (string).
        to_format: Formato de saída — "wkt" ou "geojson".
    """
    from .tools.projection import convert_geometry_format as _fn
    return json.dumps(_fn(geometry, to_format), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Séries Temporais
# ============================================================ #

@mcp.tool()
@_handle_errors
def plan_time_series_extraction(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
    bands: list[str] | None = None,
    output_format: str = "dataframe",
) -> str:
    """Plano avançado para extração de séries temporais com código sits e Python completos.

    Args:
        collection_id: ID do data cube (ex: "LANDSAT-16D-1").
        bbox_or_biome: Bbox ou nome de região/bioma.
        start_year: Ano inicial.
        end_year: Ano final.
        bands: Lista de bandas/índices (ex: ["NDVI", "EVI"]).
        output_format: Formato — "dataframe", "array", "csv".
    """
    from .tools.timeseries import plan_time_series_extraction as _fn
    return json.dumps(_fn(collection_id, bbox_or_biome, start_year, end_year, bands, output_format), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_filtering_guide(method: str | None = None) -> str:
    """Guia de métodos de filtragem para séries temporais: Savitzky-Golay, Whittaker, máscara de nuvem.

    Args:
        method: Nome do método — "savitzky_golay", "whittaker", "cloud_filter". Se None, lista todos.
    """
    from .tools.timeseries import get_filtering_guide as _fn
    return json.dumps(_fn(method), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def plan_phenology_extraction(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    band: str = "NDVI",
) -> str:
    """Plano para extração de métricas fenológicas (SOS, EOS, Peak, Amplitude, Length of Season).

    Args:
        collection_id: ID do data cube.
        bbox_or_biome: Bbox ou nome de região/bioma.
        band: Banda/índice para fenologia (padrão: "NDVI").
    """
    from .tools.timeseries import plan_phenology_extraction as _fn
    return json.dumps(_fn(collection_id, bbox_or_biome, band), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def analyze_temporal_gaps(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    datetime_range: str = "2020-01-01/2023-12-31",
) -> str:
    """Analisa gaps temporais em uma coleção para uma região via busca STAC.

    Args:
        collection_id: ID da coleção STAC.
        bbox_or_biome: Bbox ou nome de região/bioma.
        datetime_range: Intervalo temporal ISO 8601.
    """
    from .tools.timeseries import analyze_temporal_gaps as _fn
    return json.dumps(_fn(collection_id, bbox_or_biome, datetime_range), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def generate_sits_cube_code(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
    bands: list[str] | None = None,
) -> str:
    """Gera código R sits completo: sits_cube, sits_regularize, sits_get_data, sits_filter.

    Args:
        collection_id: ID da coleção BDC.
        bbox_or_biome: Bbox ou nome de região/bioma.
        start_year: Ano inicial.
        end_year: Ano final.
        bands: Lista de bandas (ex: ["NDVI", "EVI"]). Padrão: ["NDVI", "EVI"].
    """
    from .tools.timeseries import generate_sits_cube_code as _fn
    return _fn(collection_id, bbox_or_biome, start_year, end_year, bands)


# ============================================================ #
#  Tools — Classificação LULC
# ============================================================ #

@mcp.tool()
@_handle_errors
def plan_classification_workflow(
    region: str | list[float],
    start_year: int = 2020,
    end_year: int = 2023,
    classes: list[str] | None = None,
    algorithm: str = "random_forest",
) -> str:
    """Plano completo de classificação LULC inspirado no workflow sits (9 etapas).

    Args:
        region: Nome da região/bioma ou bbox.
        start_year: Ano inicial.
        end_year: Ano final.
        classes: Classes LULC (ex: ["Forest", "Pasture", "Agriculture", "Water"]).
        algorithm: Algoritmo — "random_forest", "svm", "xgboost", "lightgbm", "deep_learning".
    """
    from .tools.classification import plan_classification_workflow as _fn
    return json.dumps(_fn(region, start_year, end_year, classes, algorithm), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_sample_design_guide(
    region: str,
    classes: list[str],
    total_samples: int | None = None,
) -> str:
    """Guia de design amostral estratificado para classificação LULC.

    Args:
        region: Nome da região/bioma.
        classes: Lista de classes LULC esperadas.
        total_samples: Total de amostras desejado.
    """
    from .tools.classification import get_sample_design_guide as _fn
    return json.dumps(_fn(region, classes, total_samples), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_ml_algorithm_guide(use_case: str | None = None) -> str:
    """Comparação de algoritmos de ML para classificação: RF, SVM, XGBoost, LightGBM, Deep Learning.

    Args:
        use_case: Caso de uso — "few_samples", "high_accuracy", "fast", "large_area", "temporal".
    """
    from .tools.classification import get_ml_algorithm_guide as _fn
    return json.dumps(_fn(use_case), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def get_accuracy_assessment_guide(n_classes: int | None = None) -> str:
    """Guia de avaliação de acurácia: OA, Kappa, F1, User's/Producer's Accuracy, matriz de confusão.

    Args:
        n_classes: Número de classes na classificação (padrão: 6).
    """
    from .tools.classification import get_accuracy_assessment_guide as _fn
    return json.dumps(_fn(n_classes), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def generate_sits_classification_code(
    collection_id: str,
    region: str | list[float],
    algorithm: str = "random_forest",
    classes: list[str] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
) -> str:
    """Gera código R sits completo para classificação LULC (10 etapas).

    Args:
        collection_id: ID da coleção BDC.
        region: Nome da região/bioma ou bbox.
        algorithm: Algoritmo — "random_forest", "svm", "xgboost", "lightgbm", "deep_learning".
        classes: Lista de classes LULC.
        start_year: Ano inicial.
        end_year: Ano final.
    """
    from .tools.classification import generate_sits_classification_code as _fn
    return _fn(collection_id, region, algorithm, classes, start_year, end_year)


# ============================================================ #
#  Tools — Detecção de Mudanças
# ============================================================ #

@mcp.tool()
@_handle_errors
def list_change_detection_methods() -> str:
    """Lista métodos de detecção de mudanças: BFAST, LandTrendr, dNBR, NDVI Anomaly."""
    from .tools.change_detection import list_change_detection_methods as _fn
    return json.dumps(_fn(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def plan_change_detection(
    method: str,
    region: str | list[float],
    start_year: int = 2018,
    end_year: int = 2023,
) -> str:
    """Plano completo de detecção de mudanças com código Python e R.

    Args:
        method: Método — "bfast", "landtrendr", "dnbr" ou "ndvi_anomaly".
        region: Nome da região/bioma ou bbox.
        start_year: Ano inicial.
        end_year: Ano final.
    """
    from .tools.change_detection import plan_change_detection as _fn
    return json.dumps(_fn(method, region, start_year, end_year), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def plan_fire_scar_detection(
    region: str | list[float],
    event_date: str,
) -> str:
    """Plano para detecção de cicatrizes de fogo usando dNBR com severidade USGS.

    Args:
        region: Nome da região/bioma ou bbox.
        event_date: Data aproximada do evento de fogo (ISO 8601, ex: "2023-08-15").
    """
    from .tools.change_detection import plan_fire_scar_detection as _fn
    return json.dumps(_fn(region, event_date), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def plan_deforestation_detection(
    region: str | list[float],
    start_year: int = 2018,
    end_year: int = 2023,
    method: str = "bfast",
) -> str:
    """Plano completo para detecção de desmatamento com BFAST ou LandTrendr.

    Args:
        region: Nome da região/bioma ou bbox.
        start_year: Ano inicial.
        end_year: Ano final.
        method: Método — "bfast" ou "landtrendr".
    """
    from .tools.change_detection import plan_deforestation_detection as _fn
    return json.dumps(_fn(region, start_year, end_year, method), indent=2, ensure_ascii=False)


# ============================================================ #
#  Tools — Administração
# ============================================================ #

@mcp.tool()
@_handle_errors
def get_api_metrics() -> str:
    """Retorna métricas de uso da API: contagem de chamadas, latência média e erros por operação."""
    from .utils.metrics import metrics
    return json.dumps(metrics.snapshot(), indent=2, ensure_ascii=False)


@mcp.tool()
@_handle_errors
def invalidate_cache(namespace: str | None = None) -> str:
    """Invalida o cache — todo o cache ou apenas um namespace.

    Args:
        namespace: Namespace do cache (ex: "collection", "collections_list", "item").
                   Se None, limpa todo o cache.
    """
    from .utils.cache import cache
    if namespace:
        removed = cache.invalidate_namespace(namespace)
        return json.dumps({"invalidated": namespace, "entries_removed": removed}, ensure_ascii=False)
    cache.clear()
    return json.dumps({"invalidated": "all"}, ensure_ascii=False)


# ============================================================ #
#  MCP Resources
# ============================================================ #

@mcp.resource("stac://inpe-bdc/catalog")
def resource_catalog() -> str:
    """Catálogo INPE/BDC — landing page completa."""
    from .resources.catalog import catalog_resource
    return catalog_resource()


@mcp.resource("stac://inpe-bdc/collections")
def resource_collections_index() -> str:
    """Índice completo de todas as coleções com categorização."""
    from .resources.catalog import collections_index_resource
    return collections_index_resource()


@mcp.resource("stac://inpe-bdc/satellites")
def resource_satellites() -> str:
    """Catálogo dos satélites disponíveis: CBERS, Amazonia-1, Sentinel, Landsat, MODIS, GOES-19."""
    from .resources.catalog import satellites_resource
    return satellites_resource()


@mcp.resource("stac://inpe-bdc/biomes")
def resource_biomes() -> str:
    """Guia de biomas brasileiros: bboxes por bioma/estado/região."""
    from .resources.catalog import biomes_resource
    return biomes_resource()


@mcp.resource("stac://inpe-bdc/guide")
def resource_guide() -> str:
    """Guia completo de uso: autenticação, filtros, exemplos, dicas para análise."""
    from .resources.catalog import guide_resource
    return guide_resource()


@mcp.resource("stac://inpe-bdc/collection/{collection_id}")
def resource_collection(collection_id: str) -> str:
    """Metadados completos de uma coleção STAC."""
    from .resources.collections import collection_resource
    return collection_resource(collection_id)


@mcp.resource("stac://inpe-bdc/item/{collection_id}/{item_id}")
def resource_item(collection_id: str, item_id: str) -> str:
    """Detalhes completos de um item STAC."""
    from .resources.collections import item_resource
    return item_resource(collection_id, item_id)


# ============================================================ #
#  MCP Prompts
# ============================================================ #

@mcp.prompt()
def search_images(satellite: str = "Sentinel-2", region: str = "cerrado", period: str = "2023-01-01/2023-12-31") -> str:
    """Prompt para busca guiada de imagens de satélite no BDC."""
    return (
        f"Busque imagens do satélite {satellite} para a região '{region}' "
        f"no período {period}. Use as seguintes ferramentas:\n\n"
        f"1. Primeiro, use `list_collections(satellite='{satellite}')` para ver as coleções disponíveis\n"
        f"2. Use `get_biome_bbox('{region}')` para obter o bbox da região\n"
        f"3. Use `search_items()` com os filtros apropriados\n"
        f"4. Para cada item de interesse, use `list_item_assets()` para ver os dados disponíveis\n"
        f"5. Use `get_asset_download_info()` para obter snippets de acesso"
    )


@mcp.prompt()
def deforestation_analysis(biome: str = "amazonia", start_year: str = "2020", end_year: str = "2023") -> str:
    """Prompt para análise de desmatamento com dados BDC."""
    return (
        f"Analise o desmatamento no bioma '{biome}' entre {start_year} e {end_year}. "
        f"Siga estes passos:\n\n"
        f"1. Use `get_deforestation_analysis_collections()` para ver o pacote de dados recomendado\n"
        f"2. Use `find_cube_for_analysis(region='{biome}', start_year={start_year}, end_year={end_year}, "
        f"required_indices=['NDVI', 'EVI'])` para identificar o melhor data cube\n"
        f"3. Use `get_cube_quality_info()` para entender as bandas de qualidade\n"
        f"4. Use `search_items()` para buscar os itens no período\n"
        f"5. Use `build_python_search_snippet()` para gerar código de acesso\n"
        f"6. Sugira uma abordagem de detecção de mudança (BFAST, LandTrendr)"
    )


@mcp.prompt()
def time_series_workflow(collection_id: str = "LANDSAT-16D-1", region: str = "goias", band: str = "NDVI") -> str:
    """Prompt para fluxo completo de extração de série temporal."""
    return (
        f"Extraia série temporal de {band} da coleção '{collection_id}' para a região '{region}'. "
        f"Passos:\n\n"
        f"1. Use `get_collection_detail('{collection_id}')` para verificar bandas disponíveis\n"
        f"2. Use `get_time_series_plan('{collection_id}', '{region}', band='{band}')` para o plano\n"
        f"3. Use `get_biome_bbox('{region}')` para o bbox\n"
        f"4. Use `search_items()` para buscar os itens no período desejado\n"
        f"5. Use `build_python_search_snippet()` para gerar código completo\n"
        f"6. Explique como processar a série temporal com rasterio e numpy"
    )


@mcp.prompt()
def mosaic_exploration(region: str = "amazonia", satellite: str = "Landsat") -> str:
    """Prompt para exploração de mosaicos regionais."""
    return (
        f"Explore mosaicos de {satellite} disponíveis para a região '{region}':\n\n"
        f"1. Use `list_collections(category='mosaic', satellite='{satellite}')` para ver mosaicos\n"
        f"2. Use `get_biome_bbox('{region}')` para o bbox\n"
        f"3. Para cada mosaico, use `get_collection_detail()` para ver detalhes\n"
        f"4. Use `search_latest_items()` para ver os itens mais recentes\n"
        f"5. Use `get_thumbnail_url()` para visualização rápida\n"
        f"6. Descreva a cobertura temporal e espacial de cada mosaico"
    )


@mcp.prompt()
def sits_classification_workflow(
    region: str = "cerrado",
    algorithm: str = "random_forest",
    classes: str = "Forest,Pasture,Agriculture,Water",
) -> str:
    """Prompt para workflow completo de classificação LULC com sits."""
    cls_list = [c.strip() for c in classes.split(",")]
    return (
        f"Execute um workflow completo de classificação de uso e cobertura do solo "
        f"para a região '{region}' usando o algoritmo {algorithm}. "
        f"Classes: {', '.join(cls_list)}. Siga estes passos:\n\n"
        f"1. Use `plan_classification_workflow('{region}', classes={cls_list}, algorithm='{algorithm}')` "
        f"para obter o plano completo\n"
        f"2. Use `get_sample_design_guide('{region}', {cls_list})` para design amostral\n"
        f"3. Use `get_ml_algorithm_guide()` para comparar algoritmos\n"
        f"4. Use `generate_sits_classification_code()` para código sits completo\n"
        f"5. Use `get_accuracy_assessment_guide({len(cls_list)})` para avaliação\n"
        f"6. Use `suggest_indices_for_application('vegetacao')` para índices recomendados"
    )


@mcp.prompt()
def change_detection_workflow(
    region: str = "amazonia",
    method: str = "bfast",
    start_year: str = "2018",
    end_year: str = "2023",
) -> str:
    """Prompt para workflow de detecção de mudanças ambientais."""
    return (
        f"Detecte mudanças ambientais na região '{region}' entre {start_year} e {end_year} "
        f"usando o método {method}. Siga estes passos:\n\n"
        f"1. Use `list_change_detection_methods()` para ver os métodos disponíveis\n"
        f"2. Use `plan_change_detection('{method}', '{region}', {start_year}, {end_year})` "
        f"para o plano completo\n"
        f"3. Use `plan_time_series_extraction()` para preparar os dados\n"
        f"4. Use `analyze_temporal_gaps()` para verificar qualidade temporal\n"
        f"5. Use `get_filtering_guide()` para métodos de filtragem de série temporal\n"
        f"6. Use `get_preprocessing_guide()` para verificar o nível de processamento"
    )


@mcp.prompt()
def spectral_analysis(
    application: str = "vegetacao",
    collection_id: str = "LANDSAT-16D-1",
) -> str:
    """Prompt para análise espectral e cálculo de índices."""
    return (
        f"Realize análise espectral para '{application}' usando a coleção '{collection_id}'. "
        f"Siga estes passos:\n\n"
        f"1. Use `suggest_indices_for_application('{application}')` para índices recomendados\n"
        f"2. Use `get_collection_index_availability('{collection_id}')` para ver quais são calculáveis\n"
        f"3. Use `generate_index_code()` para gerar código de cálculo\n"
        f"4. Use `get_preprocessing_guide('{collection_id}')` para verificar se dados estão prontos\n"
        f"5. Use `get_cloud_mask_strategy('{collection_id}')` para mascaramento de nuvens\n"
        f"6. Use `plan_time_series_extraction()` se quiser série temporal do índice"
    )


# ============================================================ #
#  Entrypoint
# ============================================================ #

def main() -> None:
    logger.info("Iniciando INPE BDC MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
