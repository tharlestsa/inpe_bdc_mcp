"""Ferramentas MCP para detecção de mudanças e monitoramento ambiental."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS, COLLECTION_BAND_MAPPING
from ..models.change_detection import ChangeDetectionPlan
from ..models.classification import WorkflowStep
from ..utils.brazil import resolve_bbox


# ------------------------------------------------------------------ #
# Métodos de detecção de mudanças
# ------------------------------------------------------------------ #

_CHANGE_METHODS: dict[str, dict[str, Any]] = {
    "bfast": {
        "name": "BFAST (Breaks For Additive Season and Trend)",
        "description": (
            "Decompõe série temporal em tendência, sazonalidade e resíduo. "
            "Detecta rupturas (breakpoints) na componente de tendência. "
            "Amplamente usado para detecção de desmatamento e degradação florestal."
        ),
        "applicable_scenarios": [
            "Desmatamento gradual e abrupto",
            "Degradação florestal",
            "Mudanças de uso do solo de longo prazo",
            "Recuperação de vegetação pós-distúrbio",
        ],
        "required_data": "Série temporal longa (>= 2 anos) de NDVI ou EVI com resolução mínima de 16 dias.",
        "recommended_collections": ["LANDSAT-16D-1", "CBERS4-WFI-16D-2", "mod13q1-6.1"],
        "limitations": [
            "Necessita séries longas (mínimo ~2 ciclos sazonais completos)",
            "Sensível à qualidade da filtragem de nuvens",
            "Computacionalmente intensivo para grandes áreas",
        ],
    },
    "landtrendr": {
        "name": "LandTrendr (Landsat-based Detection of Trends in Disturbance and Recovery)",
        "description": (
            "Segmentação temporal que simplifica a série temporal em segmentos lineares. "
            "Identifica distúrbios como mudanças abruptas nos segmentos. "
            "Desenvolvido para Landsat, aplicável a qualquer série temporal de médio prazo."
        ),
        "applicable_scenarios": [
            "Desmatamento abrupto",
            "Distúrbios florestais (fogo, vento, insetos)",
            "Regeneração florestal",
            "Análise histórica de 30+ anos",
        ],
        "required_data": "Série temporal anual ou sazonal de NBR, NDVI ou band5 (SWIR). Mínimo 10 anos.",
        "recommended_collections": ["LANDSAT-16D-1", "landsat-tsirf-bimonthly-1"],
        "limitations": [
            "Projetado para resolução temporal anual/sazonal",
            "Requer calibração dos parâmetros de segmentação",
            "Melhor desempenho com Landsat (séries longas)",
        ],
    },
    "dnbr": {
        "name": "dNBR (Differenced Normalized Burn Ratio)",
        "description": (
            "Diferença entre NBR pré e pós-evento (queimada). "
            "Quantifica a severidade de queimadas em 4 classes (USGS). "
            "Método padrão para avaliação de áreas queimadas."
        ),
        "applicable_scenarios": [
            "Detecção de cicatrizes de fogo",
            "Severidade de queimadas",
            "Monitoramento de recuperação pós-fogo",
        ],
        "required_data": "Par de imagens (pré e pós-fogo) com bandas NIR e SWIR22.",
        "recommended_collections": ["LANDSAT-16D-1", "S2_L2A-1", "CB4-WFI-L4-SR-1"],
        "limitations": [
            "Requer imagem pré-fogo sem nuvens",
            "Melhor para eventos discretos (não contínuos)",
        ],
    },
    "ndvi_anomaly": {
        "name": "Anomalia NDVI",
        "description": (
            "Compara NDVI observado com a média histórica (climatologia). "
            "Anomalias negativas indicam estresse, seca ou desmatamento. "
            "Método simples e eficaz para monitoramento contínuo."
        ),
        "applicable_scenarios": [
            "Monitoramento de seca",
            "Alertas de desmatamento",
            "Estresse hídrico em agricultura",
            "Impacto de eventos extremos",
        ],
        "required_data": "Série temporal de NDVI com mínimo 3 anos para climatologia.",
        "recommended_collections": ["LANDSAT-16D-1", "CBERS4-WFI-16D-2", "mod13q1-6.1"],
        "limitations": [
            "Sensível à qualidade da climatologia de referência",
            "Pode confundir sazonalidade anômala com mudança real",
        ],
    },
}


def list_change_detection_methods() -> list[dict[str, Any]]:
    """Lista métodos de detecção de mudanças disponíveis: BFAST, LandTrendr, dNBR, NDVI Anomaly."""
    return [
        {
            "method": k,
            "name": v["name"],
            "description": v["description"],
            "applicable_scenarios": v["applicable_scenarios"],
            "recommended_collections": v.get("recommended_collections", []),
        }
        for k, v in _CHANGE_METHODS.items()
    ]


def plan_change_detection(
    method: str,
    region: str | list[float],
    start_year: int = 2018,
    end_year: int = 2023,
) -> dict[str, Any]:
    """Plano completo de detecção de mudanças com código Python e R.

    Args:
        method: Método — "bfast", "landtrendr", "dnbr" ou "ndvi_anomaly".
        region: Nome da região/bioma ou bbox [min_lon, min_lat, max_lon, max_lat].
        start_year: Ano inicial da análise.
        end_year: Ano final da análise.
    """
    key = method.lower().replace(" ", "_")
    info = _CHANGE_METHODS.get(key)
    if info is None:
        return {
            "error": f"Método '{method}' não encontrado.",
            "available": list(_CHANGE_METHODS.keys()),
        }

    if isinstance(region, str):
        bbox = resolve_bbox(region) or [-53.2, -19.5, -45.9, -12.4]
        region_name = region
    else:
        bbox = region
        region_name = "custom"

    recommended_coll = info.get("recommended_collections", ["LANDSAT-16D-1"])[0]

    steps = _build_steps(key, recommended_coll)
    python_snippet = _build_python_snippet(key, recommended_coll, bbox, start_year, end_year)
    r_snippet = _build_r_snippet(key, recommended_coll, bbox, start_year, end_year)

    return ChangeDetectionPlan(
        method=info["name"],
        description=info["description"],
        applicable_scenarios=info["applicable_scenarios"],
        required_data=info["required_data"],
        recommended_collection=recommended_coll,
        steps=steps,
        python_snippet=python_snippet,
        r_snippet=r_snippet,
        interpretation_guide=_INTERPRETATION_GUIDES.get(key, ""),
        limitations=info["limitations"],
    ).model_dump()


def plan_fire_scar_detection(
    region: str | list[float],
    event_date: str,
) -> dict[str, Any]:
    """Plano para detecção de cicatrizes de fogo usando dNBR/NBR.

    Args:
        region: Nome da região/bioma ou bbox.
        event_date: Data aproximada do evento de fogo (ISO 8601, ex: "2023-08-15").
    """
    if isinstance(region, str):
        bbox = resolve_bbox(region) or [-53.2, -19.5, -45.9, -12.4]
        region_name = region
    else:
        bbox = region
        region_name = "custom"

    # Janelas pré/pós fogo com tratamento de fronteira de ano
    year = int(event_date[:4])
    month = int(event_date[5:7])

    # Pré-fogo: 3 meses antes até 1 mês antes
    pre_start_month = month - 3
    pre_start_year = year
    if pre_start_month < 1:
        pre_start_month += 12
        pre_start_year -= 1

    pre_end_month = month - 1
    pre_end_year = year
    if pre_end_month < 1:
        pre_end_month += 12
        pre_end_year -= 1

    pre_start = f"{pre_start_year}-{pre_start_month:02d}-01"
    pre_end = f"{pre_end_year}-{pre_end_month:02d}-28"

    # Pós-fogo: data do evento até 2 meses depois
    post_start = event_date
    post_end_month = month + 2
    post_end_year = year
    if post_end_month > 12:
        post_end_month -= 12
        post_end_year += 1

    post_end = f"{post_end_year}-{post_end_month:02d}-28"

    band_map = COLLECTION_BAND_MAPPING.get("LANDSAT-16D-1", {})
    nir_key = band_map.get("nir", "NIR")
    swir22_key = band_map.get("swir22", "SWIR22")

    return ChangeDetectionPlan(
        method="dNBR — Detecção de Cicatrizes de Fogo",
        description=(
            f"Análise de severidade de queimada na região '{region_name}' "
            f"próximo à data {event_date}. Usa a diferença de NBR (dNBR) "
            f"entre imagens pré e pós-fogo."
        ),
        applicable_scenarios=["Cicatrizes de fogo", "Severidade de queimadas", "Recuperação pós-fogo"],
        required_data=f"Imagens com NIR ({nir_key}) e SWIR22 ({swir22_key}) pré e pós {event_date}.",
        recommended_collection="LANDSAT-16D-1",
        steps=[
            WorkflowStep(step_number=1, name="Buscar imagem pré-fogo",
                         description=f"Buscar imagem limpa (sem nuvens) no período {pre_start} a {pre_end}."),
            WorkflowStep(step_number=2, name="Buscar imagem pós-fogo",
                         description=f"Buscar imagem limpa no período {post_start} a {post_end}."),
            WorkflowStep(step_number=3, name="Calcular NBR pré e pós",
                         description="NBR = (NIR - SWIR22) / (NIR + SWIR22)"),
            WorkflowStep(step_number=4, name="Calcular dNBR",
                         description="dNBR = NBR_pre - NBR_post"),
            WorkflowStep(step_number=5, name="Classificar severidade",
                         description="Aplicar limiares USGS: baixa (<0.1), moderada-baixa (0.1-0.27), moderada-alta (0.27-0.66), alta (>0.66)"),
            WorkflowStep(step_number=6, name="Calcular área queimada",
                         description="Contar pixels por classe de severidade e multiplicar pela área do pixel."),
        ],
        python_snippet=f'''import rasterio
import numpy as np
from pystac_client import Client
import os

client = Client.open(
    "https://data.inpe.br/bdc/stac/v1/",
    headers={{"x-api-key": os.getenv("BDC_API_KEY", "")}}
)

bbox = {bbox}

# 1. Buscar imagem PRÉ-FOGO
search_pre = client.search(
    collections=["LANDSAT-16D-1"],
    bbox=bbox,
    datetime="{pre_start}/{pre_end}",
    limit=5
)
items_pre = sorted(search_pre.items(), key=lambda i: i.datetime, reverse=True)

# 2. Buscar imagem PÓS-FOGO
search_post = client.search(
    collections=["LANDSAT-16D-1"],
    bbox=bbox,
    datetime="{post_start}/{post_end}",
    limit=5
)
items_post = sorted(search_post.items(), key=lambda i: i.datetime)

# 3. Calcular NBR
def calc_nbr(item):
    with rasterio.open(item.assets["{nir_key}"].href) as src:
        nir = src.read(1).astype("float32")
    with rasterio.open(item.assets["{swir22_key}"].href) as src:
        swir22 = src.read(1).astype("float32")
    return (nir - swir22) / (nir + swir22 + 1e-10)

nbr_pre = calc_nbr(items_pre[0])
nbr_post = calc_nbr(items_post[0])

# 4. dNBR
dnbr = nbr_pre - nbr_post

# 5. Classificação de severidade (USGS)
severity = np.zeros_like(dnbr, dtype="uint8")
severity[dnbr < 0.1] = 1   # Não queimado / rebrota
severity[(dnbr >= 0.1) & (dnbr < 0.27)] = 2  # Severidade baixa
severity[(dnbr >= 0.27) & (dnbr < 0.66)] = 3  # Severidade moderada-alta
severity[dnbr >= 0.66] = 4  # Severidade alta

# 6. Área por classe (pixel 30m = 900 m²)
pixel_area_ha = 900 / 10000  # 0.09 ha
for cls, label in [(2, "Baixa"), (3, "Moderada-alta"), (4, "Alta")]:
    area = np.sum(severity == cls) * pixel_area_ha
    print(f"Severidade {{label}}: {{area:.1f}} ha")
''',
        r_snippet=f'''library(rstac)
library(terra)

# Buscar imagens pré e pós fogo
s_obj <- stac("https://data.inpe.br/bdc/stac/v1/")

pre <- s_obj |>
  stac_search(collections = "LANDSAT-16D-1",
              bbox = c({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}),
              datetime = "{pre_start}/{pre_end}") |>
  post_request()

post <- s_obj |>
  stac_search(collections = "LANDSAT-16D-1",
              bbox = c({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}),
              datetime = "{post_start}/{post_end}") |>
  post_request()

# Calcular NBR e dNBR
nir_pre  <- rast(pre$features[[1]]$assets${nir_key}$href)
swir_pre <- rast(pre$features[[1]]$assets${swir22_key}$href)
nbr_pre  <- (nir_pre - swir_pre) / (nir_pre + swir_pre)

nir_post  <- rast(post$features[[1]]$assets${nir_key}$href)
swir_post <- rast(post$features[[1]]$assets${swir22_key}$href)
nbr_post  <- (nir_post - swir_post) / (nir_post + swir_post)

dnbr <- nbr_pre - nbr_post
plot(dnbr, main = "dNBR — Severidade de Queimada")
''',
        interpretation_guide=(
            "Classificação de severidade dNBR (USGS):\n"
            "  dNBR < -0.25  → Rebrota alta (pós-fogo)\n"
            "  -0.25 a -0.1  → Rebrota baixa\n"
            "  -0.1 a 0.1    → Não queimado\n"
            "  0.1 a 0.27    → Severidade baixa\n"
            "  0.27 a 0.44   → Severidade moderada-baixa\n"
            "  0.44 a 0.66   → Severidade moderada-alta\n"
            "  > 0.66        → Severidade alta"
        ),
        limitations=[
            "Requer imagens sem nuvens próximas ao evento.",
            "Melhor para eventos discretos (queimadas localizadas).",
            "Em áreas de Cerrado, a sazonalidade pode confundir com queimadas antigas.",
        ],
    ).model_dump()


def plan_deforestation_detection(
    region: str | list[float],
    start_year: int = 2018,
    end_year: int = 2023,
    method: str = "bfast",
) -> dict[str, Any]:
    """Plano completo para detecção de desmatamento com BFAST ou LandTrendr.

    Args:
        region: Nome da região/bioma ou bbox.
        start_year: Ano inicial.
        end_year: Ano final.
        method: Método — "bfast" ou "landtrendr".
    """
    if isinstance(region, str):
        bbox = resolve_bbox(region) or [-60.0, -12.0, -55.0, -8.0]
        region_name = region
    else:
        bbox = region
        region_name = "custom"

    key = method.lower()
    if key not in ("bfast", "landtrendr"):
        key = "bfast"

    band_map = COLLECTION_BAND_MAPPING.get("LANDSAT-16D-1", {})
    ndvi_key = band_map.get("ndvi", "NDVI")

    steps = [
        WorkflowStep(step_number=1, name="Preparar série temporal",
                     description=f"Extrair série NDVI de LANDSAT-16D-1 para {region_name}, {start_year}-{end_year}."),
        WorkflowStep(step_number=2, name="Filtrar nuvens e ruídos",
                     description="Aplicar máscara CMASK e filtragem Whittaker/Savitzky-Golay."),
        WorkflowStep(step_number=3, name="Aplicar algoritmo de detecção",
                     description=f"Executar {key.upper()} na série temporal filtrada."),
        WorkflowStep(step_number=4, name="Validar breakpoints",
                     description="Verificar breakpoints detectados contra dados de referência (PRODES/DETER)."),
        WorkflowStep(step_number=5, name="Mapear e quantificar",
                     description="Gerar mapa de desmatamento e calcular área por ano."),
    ]

    if key == "bfast":
        python_snippet = f'''import numpy as np
from pystac_client import Client
import rasterio
import os

# 1. Extrair série temporal NDVI
client = Client.open(
    "https://data.inpe.br/bdc/stac/v1/",
    headers={{"x-api-key": os.getenv("BDC_API_KEY", "")}}
)

search = client.search(
    collections=["LANDSAT-16D-1"],
    bbox={bbox},
    datetime="{start_year}-01-01/{end_year}-12-31",
    limit=500
)
items = sorted(search.items(), key=lambda i: i.datetime)

# 2. BFAST via bfast (pacote Python)
# pip install bfast
from bfast import BFASTMonitor

# Preparar cubo de dados (n_dates, height, width)
ndvi_cube = []
dates = []
for item in items:
    if "{ndvi_key}" in item.assets:
        with rasterio.open(item.assets["{ndvi_key}"].href) as src:
            ndvi_cube.append(src.read(1).astype("float32"))
            dates.append(item.datetime)

ndvi_cube = np.stack(ndvi_cube)

# 3. Aplicar BFAST Monitor
# Usar metade inicial como histórico, metade final como monitoramento
n_history = len(dates) // 2
model = BFASTMonitor(
    start_monitor=n_history,
    freq=23,  # ~23 composições de 16 dias por ano
    k=3,      # harmônicos
    hfrac=0.25,
    trend=True,
    level=0.05
)

# Para um pixel específico:
# result = model.fit(ndvi_cube[:, row, col])
# breakpoint = result.breakpoint  # Índice temporal da ruptura

# 4. Para área completa, iterar por pixels ou usar versão vetorizada
'''
        r_snippet = f'''library(sits)
library(bfast)

# 1. Criar cubo e extrair série temporal via sits
cube <- sits_cube(
  source     = "BDC",
  collection = "LANDSAT-16D-1",
  bands      = c("{ndvi_key}"),
  roi        = c(lon_min = {bbox[0]}, lat_min = {bbox[1]},
                 lon_max = {bbox[2]}, lat_max = {bbox[3]}),
  start_date = "{start_year}-01-01",
  end_date   = "{end_year}-12-31"
)

# 2. Extrair série para um ponto
point <- data.frame(longitude = {(bbox[0]+bbox[2])/2:.4f},
                    latitude = {(bbox[1]+bbox[3])/2:.4f},
                    label = "test")
ts <- sits_get_data(cube, point)

# 3. Converter para ts e aplicar BFAST
ndvi_ts <- ts(ts$time_series[[1]]${ndvi_key},
              frequency = 23, start = c({start_year}, 1))

# BFAST Monitor
bf <- bfastmonitor(ndvi_ts, start = c({(start_year + end_year)//2}, 1),
                   formula = response ~ trend + harmon,
                   order = 3, history = "all")

plot(bf)
cat("Breakpoint:", bf$breakpoint, "\\n")
cat("Magnitude:", bf$magnitude, "\\n")
'''
    else:  # landtrendr
        python_snippet = f'''# LandTrendr — implementação via série temporal anual
import numpy as np

# LandTrendr trabalha com composições anuais
# Para cada ano, selecionar a melhor observação (menor nuvem) ou mediana
# Usar NBR ou NDVI anual

# Implementação simplificada de segmentação temporal
def landtrendr_segment(y, max_segments=6, spike_threshold=0.75):
    """Segmentação temporal simplificada estilo LandTrendr."""
    n = len(y)
    # Passo 1: Remover spikes
    for i in range(1, n - 1):
        if abs(y[i] - y[i-1]) > spike_threshold and abs(y[i] - y[i+1]) > spike_threshold:
            y[i] = (y[i-1] + y[i+1]) / 2

    # Passo 2: Segmentação por ajuste linear mínimo (simplificado)
    # Para implementação completa, usar o pacote lt-gee ou similar
    from numpy.polynomial import polynomial as P
    segments = []
    # ... segmentação iterativa
    return segments

# Para implementação completa, recomenda-se usar Google Earth Engine:
# https://emapr.github.io/LT-GEE/
'''
        r_snippet = f'''# LandTrendr via pacote lidR ou implementação custom
# Recomenda-se usar Google Earth Engine para LandTrendr em escala

library(sits)

# Criar composições anuais via sits
cube <- sits_cube(
  source     = "BDC",
  collection = "LANDSAT-16D-1",
  bands      = c("NDVI", "NBR"),
  roi        = c(lon_min = {bbox[0]}, lat_min = {bbox[1]},
                 lon_max = {bbox[2]}, lat_max = {bbox[3]}),
  start_date = "{start_year}-01-01",
  end_date   = "{end_year}-12-31"
)

# Alternativa: usar sits_classify com modelo treinado para detectar mudanças
# sits implementa detecção de mudanças via classificação temporal
'''

    return ChangeDetectionPlan(
        method=f"Detecção de Desmatamento — {key.upper()}",
        description=f"Plano para detectar desmatamento na região '{region_name}' ({start_year}-{end_year}) usando {key.upper()}.",
        applicable_scenarios=["Desmatamento", "Degradação florestal", "Mudança de uso do solo"],
        required_data=f"Série temporal NDVI/NBR de LANDSAT-16D-1, {start_year}-{end_year}.",
        recommended_collection="LANDSAT-16D-1",
        steps=steps,
        python_snippet=python_snippet,
        r_snippet=r_snippet,
        interpretation_guide=(
            "Interpretação de resultados de desmatamento:\n"
            "- Breakpoint com magnitude negativa grande (< -0.15 NDVI) indica desmatamento.\n"
            "- Breakpoints sazonais com magnitude baixa podem ser falsos positivos.\n"
            "- Validar contra PRODES (desmatamento anual) e DETER (alertas) do INPE.\n"
            "- Sites de referência: http://terrabrasilis.dpi.inpe.br/ (PRODES/DETER)"
        ),
        limitations=[
            "BFAST: mínimo 2 anos de histórico para modelo sazonal robusto.",
            "LandTrendr: melhor com composições anuais (10+ anos).",
            f"Validar resultados com dados PRODES/DETER do INPE para {region_name}.",
        ],
    ).model_dump()


# ------------------------------------------------------------------ #
# Helpers internos
# ------------------------------------------------------------------ #

def _build_steps(method: str, collection: str) -> list[WorkflowStep]:
    """Gera passos do workflow de detecção de mudanças."""
    base_steps = [
        WorkflowStep(step_number=1, name="Preparar dados",
                     description=f"Buscar e organizar série temporal de {collection}."),
        WorkflowStep(step_number=2, name="Filtragem de qualidade",
                     description="Aplicar máscara de nuvens e filtragem temporal."),
    ]

    if method == "bfast":
        base_steps.extend([
            WorkflowStep(step_number=3, name="Definir período de monitoramento",
                         description="Separar série em período histórico e de monitoramento."),
            WorkflowStep(step_number=4, name="Ajustar modelo BFAST",
                         description="Ajustar modelo sazonal+tendência no período histórico."),
            WorkflowStep(step_number=5, name="Detectar breakpoints",
                         description="Identificar rupturas no período de monitoramento."),
        ])
    elif method == "landtrendr":
        base_steps.extend([
            WorkflowStep(step_number=3, name="Gerar composições anuais",
                         description="Criar composição anual (mediana ou melhor pixel) para cada ano."),
            WorkflowStep(step_number=4, name="Segmentação temporal",
                         description="Simplificar série em segmentos lineares (max 6-8 segmentos)."),
            WorkflowStep(step_number=5, name="Identificar distúrbios",
                         description="Detectar segmentos com declínio acentuado (distúrbios)."),
        ])
    elif method == "dnbr":
        base_steps.extend([
            WorkflowStep(step_number=3, name="Selecionar imagens pré/pós",
                         description="Identificar imagem pré-evento e pós-evento sem nuvens."),
            WorkflowStep(step_number=4, name="Calcular dNBR",
                         description="dNBR = NBR_pre - NBR_post"),
            WorkflowStep(step_number=5, name="Classificar severidade",
                         description="Aplicar limiares USGS para classes de severidade."),
        ])
    else:  # ndvi_anomaly
        base_steps.extend([
            WorkflowStep(step_number=3, name="Calcular climatologia",
                         description="Média e desvio padrão por período do ano (baseline)."),
            WorkflowStep(step_number=4, name="Calcular anomalias",
                         description="Z-score = (NDVI_obs - média_histórica) / desvio_padrão"),
            WorkflowStep(step_number=5, name="Detectar mudanças",
                         description="Anomalias < -2σ por ≥2 composições consecutivas = mudança."),
        ])

    base_steps.append(
        WorkflowStep(step_number=6, name="Validar e quantificar",
                     description="Validar detecções com dados de referência e calcular áreas.")
    )
    return base_steps


def _build_python_snippet(method: str, collection: str, bbox: list[float], start: int, end: int) -> str:
    """Gera snippet Python para o método de detecção de mudanças."""
    base = f'''from pystac_client import Client
import rasterio
import numpy as np
import os

client = Client.open(
    "https://data.inpe.br/bdc/stac/v1/",
    headers={{"x-api-key": os.getenv("BDC_API_KEY", "")}}
)

search = client.search(
    collections=["{collection}"],
    bbox={bbox},
    datetime="{start}-01-01/{end}-12-31",
    limit=500
)
items = sorted(search.items(), key=lambda i: i.datetime)
print(f"Itens: {{len(items)}}")
'''

    if method == "ndvi_anomaly":
        base += '''
# Calcular climatologia (média por período do ano)
import pandas as pd

ndvi_data = []
for item in items:
    if "NDVI" in item.assets:
        with rasterio.open(item.assets["NDVI"].href) as src:
            val = src.read(1).astype("float32")
            ndvi_data.append({"date": item.datetime, "ndvi_mean": np.nanmean(val)})

df = pd.DataFrame(ndvi_data)
df["doy"] = df["date"].dt.dayofyear
climatology = df.groupby("doy")["ndvi_mean"].agg(["mean", "std"])

# Calcular anomalia
df["zscore"] = df.apply(
    lambda r: (r["ndvi_mean"] - climatology.loc[r["doy"], "mean"]) /
              max(climatology.loc[r["doy"], "std"], 0.01),
    axis=1
)

# Detecções: z-score < -2 por 2+ composições consecutivas
alerts = df[df["zscore"] < -2]
print(f"Alertas de anomalia: {len(alerts)}")
'''
    return base


def _build_r_snippet(method: str, collection: str, bbox: list[float], start: int, end: int) -> str:
    """Gera snippet R para o método de detecção de mudanças."""
    return f'''library(sits)
library(rstac)

# Criar cubo BDC
cube <- sits_cube(
  source     = "BDC",
  collection = "{collection}",
  bands      = c("NDVI"),
  roi        = c(lon_min = {bbox[0]}, lat_min = {bbox[1]},
                 lon_max = {bbox[2]}, lat_max = {bbox[3]}),
  start_date = "{start}-01-01",
  end_date   = "{end}-12-31"
)

cat("Timeline:", length(sits_timeline(cube)), "datas\\n")

# Para detecção de mudanças com sits, usar classificação temporal
# O sits detecta mudanças comparando classificações de diferentes períodos
'''


_INTERPRETATION_GUIDES: dict[str, str] = {
    "bfast": (
        "Interpretação BFAST:\n"
        "- Breakpoint: data da ruptura na tendência. Magnitude negativa = perda de vegetação.\n"
        "- Magnitude < -0.1 NDVI: possível desmatamento/degradação.\n"
        "- Magnitude < -0.2 NDVI: desmatamento provável.\n"
        "- Verificar se breakpoint coincide com período seco (falso positivo sazonal)."
    ),
    "landtrendr": (
        "Interpretação LandTrendr:\n"
        "- Segmento com declínio > 0.15 NDVI em < 2 anos: distúrbio abrupto.\n"
        "- Declínio gradual ao longo de 5+ anos: degradação.\n"
        "- Segmento ascendente após distúrbio: recuperação/regeneração.\n"
        "- Magnitude e duração do segmento classificam o tipo de mudança."
    ),
    "dnbr": (
        "Classificação dNBR (USGS):\n"
        "  dNBR < -0.25  → Rebrota alta\n"
        "  -0.1 a 0.1    → Não queimado\n"
        "  0.1 a 0.27    → Severidade baixa\n"
        "  0.27 a 0.66   → Severidade moderada-alta\n"
        "  > 0.66        → Severidade alta"
    ),
    "ndvi_anomaly": (
        "Interpretação de anomalias NDVI:\n"
        "- Z-score < -1: anomalia moderada (estresse)\n"
        "- Z-score < -2: anomalia severa (possível desmatamento/seca extrema)\n"
        "- Z-score < -3: anomalia extrema (desmatamento provável)\n"
        "- Anomalias persistentes (>2 composições): mudança real vs. ruído"
    ),
}
