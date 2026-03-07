"""Ferramentas MCP para análise, descoberta temática e geração de código."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS, PERIOD_DAYS
from ..models.search import TimeSeriesPlan, TopicDiscovery
from ..utils.brazil import resolve_bbox

# Mapeamento de tópicos para coleções recomendadas
_TOPIC_MAP: dict[str, list[dict[str, Any]]] = {
    "desmatamento": [
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat 16 dias — série temporal NDVI/EVI"},
        {"id": "CBERS4-WFI-16D-2", "reason": "Data cube CBERS-4 WFI 16 dias — boa cobertura temporal"},
        {"id": "LCC_L8_30_16D_STK_Cerrado-1", "reason": "Classificação de uso e cobertura do solo — Cerrado"},
        {"id": "AMZ1-WFI-L2-DN-1", "reason": "Amazonia-1 — satélite brasileiro para vigilância"},
    ],
    "deforestation": [
        {"id": "LANDSAT-16D-1", "reason": "Landsat 16-day data cube — NDVI/EVI time series"},
        {"id": "CBERS4-WFI-16D-2", "reason": "CBERS-4 WFI 16-day cube — good temporal coverage"},
    ],
    "cerrado": [
        {"id": "LCC_L8_30_16D_STK_Cerrado-1", "reason": "Classificação de uso/cobertura do Cerrado"},
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat para série temporal"},
        {"id": "CBERS4-WFI-16D-2", "reason": "Data cube CBERS-4 para monitoramento"},
    ],
    "amazonia": [
        {"id": "mosaic-landsat-amazon-3m-1", "reason": "Mosaico Landsat trimestral da Amazônia"},
        {"id": "mosaic-s2-amazon-3m-1", "reason": "Mosaico Sentinel-2 trimestral da Amazônia"},
        {"id": "AMZ1-WFI-L2-DN-1", "reason": "Amazonia-1 WFI — monitoramento contínuo"},
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat para séries temporais"},
    ],
    "ndvi": [
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat 16D com banda NDVI pré-calculada"},
        {"id": "CBERS4-WFI-16D-2", "reason": "Data cube CBERS WFI 16D com NDVI"},
        {"id": "mod13q1-6.1", "reason": "MODIS MOD13Q1 — NDVI 250m a cada 16 dias, longa série histórica"},
    ],
    "evi": [
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat com EVI pré-calculado"},
        {"id": "CBERS4-WFI-16D-2", "reason": "Data cube CBERS com EVI"},
        {"id": "mod13q1-6.1", "reason": "MODIS MOD13Q1 — EVI 250m"},
    ],
    "serie temporal": [
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat 16D — melhor resolução (30m)"},
        {"id": "CBERS4-WFI-16D-2", "reason": "Data cube CBERS 16D — complementar ao Landsat"},
        {"id": "CBERS-WFI-8D-1", "reason": "Data cube CBERS 8D — maior frequência temporal"},
    ],
    "time series": [
        {"id": "LANDSAT-16D-1", "reason": "Landsat 16-day data cube — best resolution (30m)"},
        {"id": "CBERS-WFI-8D-1", "reason": "CBERS 8-day cube — higher temporal frequency"},
    ],
    "agua": [
        {"id": "MODISA-OCSMART-CHL-MONTHLY-1", "reason": "Clorofila-a MODIS — qualidade da água costeira"},
        {"id": "MODISA-OCSMART-RRS-MONTHLY-1", "reason": "Reflectância remota MODIS — cor do oceano"},
        {"id": "sentinel-3-olci-l1-bundle-1", "reason": "Sentinel-3 OLCI — monitoramento costeiro"},
    ],
    "water": [
        {"id": "MODISA-OCSMART-CHL-MONTHLY-1", "reason": "MODIS Chlorophyll-a — coastal water quality"},
        {"id": "sentinel-3-olci-l1-bundle-1", "reason": "Sentinel-3 OLCI — coastal monitoring"},
    ],
    "oceano": [
        {"id": "MODISA-OCSMART-CHL-MONTHLY-1", "reason": "Clorofila-a mensal MODIS-Aqua"},
        {"id": "MODISA-OCSMART-RRS-MONTHLY-1", "reason": "Reflectância remota mensal MODIS-Aqua"},
        {"id": "sentinel-3-olci-l1-bundle-1", "reason": "Sentinel-3 OLCI L1B"},
    ],
    "clima": [
        {"id": "GOES19-L2-CMI-1", "reason": "GOES-19 CMI — dados meteorológicos de alta frequência"},
    ],
    "weather": [
        {"id": "GOES19-L2-CMI-1", "reason": "GOES-19 CMI — high-frequency meteorological data"},
    ],
    "agricultura": [
        {"id": "S2_L2A-1", "reason": "Sentinel-2 L2A 10m — alta resolução para parcelas agrícolas"},
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat 16D para safra/entressafra"},
        {"id": "mod13q1-6.1", "reason": "MODIS NDVI 250m — monitoramento de safra em larga escala"},
    ],
    "soja": [
        {"id": "S2_L2A-1", "reason": "Sentinel-2 L2A — monitoramento de parcelas de soja"},
        {"id": "LANDSAT-16D-1", "reason": "Landsat 16D — série temporal para ciclo da soja"},
    ],
    "queimada": [
        {"id": "CB4-WFI-L4-SR-1", "reason": "CBERS-4 WFI SR — detecção de cicatrizes de fogo"},
        {"id": "LANDSAT-16D-1", "reason": "Data cube Landsat — índice NBR para áreas queimadas"},
        {"id": "CBERS4-WFI-16D-2", "reason": "Data cube CBERS 16D"},
    ],
    "fire": [
        {"id": "LANDSAT-16D-1", "reason": "Landsat 16D cube — NBR index for burn scars"},
        {"id": "CB4-WFI-L4-SR-1", "reason": "CBERS-4 WFI SR — fire scar detection"},
    ],
    "urbano": [
        {"id": "S2_L2A-1", "reason": "Sentinel-2 L2A 10m — melhor resolução para áreas urbanas"},
        {"id": "CB4-PAN5M-L4-DN-1", "reason": "CBERS-4 PAN 5m — alta resolução pancromática"},
        {"id": "CB4-PAN10M-L4-DN-1", "reason": "CBERS-4 PAN 10m"},
    ],
    "mosaico": [
        {"id": "mosaic-landsat-brazil-6m-1", "reason": "Mosaico Landsat semestral do Brasil inteiro"},
        {"id": "mosaic-landsat-amazon-3m-1", "reason": "Mosaico Landsat trimestral da Amazônia"},
        {"id": "mosaic-s2-amazon-3m-1", "reason": "Mosaico Sentinel-2 trimestral da Amazônia"},
    ],
}


def discover_collections_for_topic(topic: str) -> dict[str, Any]:
    """Sugere coleções BDC relevantes para um tema de análise.

    Args:
        topic: Tema em linguagem natural, português ou inglês
               (ex: "desmatamento no Cerrado", "NDVI time series", "qualidade da água").
    """
    topic_lower = topic.lower()
    matched_collections: list[dict[str, Any]] = []
    matched_keys: set[str] = set()

    for key, colls in _TOPIC_MAP.items():
        if key in topic_lower:
            for c in colls:
                if c["id"] not in matched_keys:
                    matched_collections.append(c)
                    matched_keys.add(c["id"])

    # Se nenhum match direto, buscar por palavras-chave nos nomes das coleções
    if not matched_collections:
        words = topic_lower.split()
        for cid, info in ALL_COLLECTIONS.items():
            cid_lower = cid.lower()
            sat_lower = (info.get("satellite", "") or "").lower()
            for w in words:
                if len(w) > 2 and (w in cid_lower or w in sat_lower):
                    if cid not in matched_keys:
                        matched_collections.append({
                            "id": cid,
                            "reason": f"Match por palavra-chave '{w}' no ID da coleção",
                        })
                        matched_keys.add(cid)

    workflow = ""
    if any(k in topic_lower for k in ("ndvi", "evi", "serie", "series", "temporal")):
        workflow = (
            "1. Selecione um data cube (ex: LANDSAT-16D-1)\n"
            "2. Defina bbox da região e período temporal\n"
            "3. Busque itens com search_items()\n"
            "4. Extraia a banda desejada (NDVI/EVI) de cada item\n"
            "5. Construa a série temporal pixel a pixel usando rasterio"
        )
    elif any(k in topic_lower for k in ("desmatamento", "deforestation")):
        workflow = (
            "1. Busque imagens do data cube para o período de análise\n"
            "2. Extraia séries temporais de NDVI/EVI\n"
            "3. Aplique algoritmo de detecção de mudança\n"
            "4. Valide com classificação LCC existente"
        )

    discovery = TopicDiscovery(
        topic=topic,
        suggested_collections=matched_collections,
        recommended_workflow=workflow,
        notes=f"Encontradas {len(matched_collections)} coleções relevantes para '{topic}'.",
    )
    return discovery.model_dump()


def build_python_search_snippet(
    collections: list[str],
    bbox_or_biome: str | list[float] | None = None,
    datetime_range: str = "2020-01-01/2023-12-31",
    cloud_max: float | None = None,
    asset_keys: list[str] | None = None,
) -> str:
    """Gera snippet Python completo para busca e acesso a dados usando pystac-client.

    Args:
        collections: Lista de IDs de coleções.
        bbox_or_biome: Bbox [min_lon, min_lat, max_lon, max_lat] ou nome de região.
        datetime_range: Intervalo temporal ISO 8601.
        cloud_max: Percentual máximo de nuvens.
        asset_keys: Chaves dos assets para acessar (ex: ["NDVI", "EVI"]).
    """
    # Resolver bbox
    if isinstance(bbox_or_biome, str):
        bbox = resolve_bbox(bbox_or_biome)
        bbox_comment = f"  # Região: {bbox_or_biome}"
    elif isinstance(bbox_or_biome, list):
        bbox = bbox_or_biome
        bbox_comment = ""
    else:
        bbox = None
        bbox_comment = ""

    colls_str = str(collections)
    bbox_str = str(bbox) if bbox else "None"

    query_part = ""
    if cloud_max is not None:
        query_part = f'\n    query={{"eo:cloud_cover": {{"lte": {cloud_max}}}}},'

    asset_part = ""
    if asset_keys:
        first_key = asset_keys[0]
        asset_part = f'''

    # Acessar asset '{first_key}' via rasterio (COG — streaming):
    for item in items:
        if "{first_key}" in item.assets:
            url = item.assets["{first_key}"].href
            import rasterio
            with rasterio.open(url) as src:
                data = src.read(1)
                print(f"{{item.id}}: shape={{data.shape}}, dtype={{data.dtype}}")'''

    snippet = f'''from pystac_client import Client
import os

client = Client.open(
    "https://data.inpe.br/bdc/stac/v1/",
    headers={{"x-api-key": os.getenv("BDC_API_KEY", "")}}
)

search = client.search(
    collections={colls_str},
    bbox={bbox_str},{bbox_comment}{query_part}
    datetime="{datetime_range}",
    limit=100
)

items = list(search.items())
print(f"Total de itens encontrados: {{len(items)}}")

for item in items[:5]:
    print(f"  {{item.id}} | {{item.datetime}} | assets: {{list(item.assets.keys())}}")
{asset_part}
'''
    return snippet


def build_r_snippet(
    collections: list[str],
    bbox_or_biome: str | list[float] | None = None,
    datetime_range: str = "2020-01-01/2023-12-31",
    cloud_max: float | None = None,
) -> str:
    """Gera snippet R usando rstac para busca no BDC.

    Args:
        collections: Lista de IDs de coleções.
        bbox_or_biome: Bbox ou nome de região.
        datetime_range: Intervalo temporal ISO 8601.
        cloud_max: Percentual máximo de nuvens.
    """
    if isinstance(bbox_or_biome, str):
        bbox = resolve_bbox(bbox_or_biome)
        bbox_comment = f"  # Região: {bbox_or_biome}"
    elif isinstance(bbox_or_biome, list):
        bbox = bbox_or_biome
        bbox_comment = ""
    else:
        bbox = [-73.9, -33.8, -34.8, 5.3]
        bbox_comment = "  # Brasil inteiro"

    colls_r = ", ".join(f'"{c}"' for c in collections)
    bbox_r = f"c({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]})" if bbox else "NULL"

    ext_query = ""
    if cloud_max is not None:
        ext_query = f'\n  ext_query("eo:cloud_cover" <= {cloud_max}) |>'

    snippet = f'''library(rstac)

s_obj <- stac("https://data.inpe.br/bdc/stac/v1/")

it_obj <- s_obj |>
  stac_search(
    collections = c({colls_r}),
    bbox        = {bbox_r},{bbox_comment}
    datetime    = "{datetime_range}",
    limit       = 100
  ) |>{ext_query}
  post_request()

# Total de itens encontrados:
cat("Matched:", items_matched(it_obj), "\\n")

# Listar primeiros itens:
items_datetime(it_obj)

# Selecionar e obter URLs dos assets:
# it_obj |>
#   assets_select(asset_names = "NDVI") |>
#   assets_url()
'''
    return snippet


def get_time_series_plan(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
    band: str = "NDVI",
) -> dict[str, Any]:
    """Plano para extração de série temporal de um data cube.

    Args:
        collection_id: ID da coleção (preferencialmente data cube).
        bbox_or_biome: Bbox ou nome de região.
        start_year: Ano inicial.
        end_year: Ano final.
        band: Banda espectral ou índice (ex: "NDVI", "EVI", "RED").
    """
    known = ALL_COLLECTIONS.get(collection_id, {})
    period = known.get("period", "16D")

    # Estimar número de itens
    period_days = PERIOD_DAYS.get(period, 16)
    total_days = (end_year - start_year + 1) * 365
    expected_items = total_days // period_days

    # Resolver bbox para snippet
    if isinstance(bbox_or_biome, str):
        bbox = resolve_bbox(bbox_or_biome) or [-53.2, -19.5, -45.9, -12.4]
        region_name = bbox_or_biome
    elif isinstance(bbox_or_biome, list):
        bbox = bbox_or_biome
        region_name = "custom"
    else:
        bbox = [-53.2, -19.5, -45.9, -12.4]
        region_name = "Goiás (padrão)"

    snippet = build_python_search_snippet(
        collections=[collection_id],
        bbox_or_biome=bbox,
        datetime_range=f"{start_year}-01-01/{end_year}-12-31",
        asset_keys=[band],
    )

    plan = TimeSeriesPlan(
        collection_id=collection_id,
        band=band,
        temporal_resolution_days=period_days,
        expected_item_count=expected_items,
        recommended_chunk_size=min(100, expected_items),
        estimated_data_volume_gb=None,
        python_snippet=snippet,
        notes=(
            f"Série temporal de {band} para a região '{region_name}' "
            f"de {start_year} a {end_year} usando {collection_id}. "
            f"Período de composição: {period} ({period_days} dias). "
            f"Estimativa: ~{expected_items} itens. "
            f"Recomenda-se processar em lotes de {min(100, expected_items)} itens."
        ),
    )
    return plan.model_dump()
