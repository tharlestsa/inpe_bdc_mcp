"""Ferramentas MCP para análise de séries temporais de imagens de satélite."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS, COLLECTION_BAND_MAPPING, PERIOD_DAYS
from ..models.change_detection import PhenologyPlan
from ..utils.brazil import resolve_bbox


# ------------------------------------------------------------------ #
# Métodos de filtragem de séries temporais
# ------------------------------------------------------------------ #

_FILTERING_METHODS: dict[str, dict[str, Any]] = {
    "savitzky_golay": {
        "name": "Savitzky-Golay",
        "description": (
            "Filtro polinomial de suavização local. Preserva picos e vales da série temporal. "
            "Amplamente usado em séries NDVI/EVI para remover ruídos de nuvens residuais."
        ),
        "parameters": {
            "window_length": "Tamanho da janela (ímpar). Típico: 5-9 para composições 16D.",
            "polyorder": "Grau do polinômio. Típico: 2-3.",
        },
        "pros": [
            "Preserva picos fenológicos",
            "Implementação simples",
            "Bom para séries com poucos gaps",
        ],
        "cons": [
            "Sensível a outliers extremos",
            "Não interpola gaps",
        ],
        "python": '''from scipy.signal import savgol_filter
import numpy as np

# Série temporal NDVI (ex: 23 datas por ano, composição 16D)
ndvi_series = np.array([...])  # shape: (n_dates,)

# Suavização
ndvi_smooth = savgol_filter(ndvi_series, window_length=7, polyorder=2)
''',
        "r": '''library(signal)

ndvi_series <- c(...)  # Série temporal NDVI
ndvi_smooth <- sgolayfilt(ndvi_series, p = 2, n = 7)
''',
        "sits": '''library(sits)

# Filtragem via sits
cube_filtered <- sits_filter(
  data = cube,
  filter = sits_sgolay(order = 2, length = 7)
)
''',
    },
    "whittaker": {
        "name": "Whittaker",
        "description": (
            "Suavizador baseado em penalização. Excelente para séries com gaps e ruídos. "
            "Balanço entre fidelidade aos dados e suavidade controlado pelo parâmetro lambda."
        ),
        "parameters": {
            "lambda": "Parâmetro de suavização. Valores maiores = mais suave. Típico: 0.5-10.",
            "d": "Ordem da diferença. Típico: 2 (segunda diferença).",
        },
        "pros": [
            "Robusto a gaps e dados faltantes",
            "Controle fino da suavização via lambda",
            "Bom para séries MODIS/CBERS com muitos gaps",
        ],
        "cons": [
            "Pode suavizar excessivamente picos fenológicos com lambda alto",
        ],
        "python": '''import numpy as np
from scipy import sparse

def whittaker_smooth(y, lmbda=2.0, d=2):
    """Suavizador Whittaker-Henderson."""
    m = len(y)
    E = sparse.eye(m)
    D = sparse.diff(E, n=d)
    W = sparse.diags(np.isfinite(y).astype(float))
    y_clean = np.where(np.isfinite(y), y, 0)
    z = sparse.linalg.spsolve(W + lmbda * D.T @ D, W @ y_clean)
    return z

ndvi_smooth = whittaker_smooth(ndvi_series, lmbda=2.0)
''',
        "r": '''# Whittaker via ptw
library(ptw)

ndvi_smooth <- whit2(ndvi_series, lambda = 2.0)
''',
        "sits": '''library(sits)

cube_filtered <- sits_filter(
  data = cube,
  filter = sits_whittaker(lambda = 2.0)
)
''',
    },
    "cloud_filter": {
        "name": "Filtragem por máscara de nuvem + interpolação",
        "description": (
            "Remove observações contaminadas por nuvem/sombra usando banda de qualidade "
            "(CMASK, SCL, Fmask) e interpola os gaps via interpolação linear ou spline."
        ),
        "parameters": {
            "quality_band": "Banda de qualidade (CMASK, SCL, Fmask).",
            "interp_method": "Método de interpolação: 'linear', 'spline', 'nearest'.",
        },
        "pros": [
            "Abordagem fisicamente motivada",
            "Remove ruídos na fonte",
        ],
        "cons": [
            "Depende da qualidade da máscara de nuvem",
            "Interpolação pode gerar artefatos em gaps longos",
        ],
        "python": '''import numpy as np
from scipy.interpolate import interp1d

# ndvi_series: (n_dates,), quality: (n_dates,)
# Mascarar pixels com nuvem (quality != 1 para CMASK)
valid = quality == 1
ndvi_clean = np.where(valid, ndvi_series, np.nan)

# Interpolação linear dos gaps
dates_num = np.arange(len(ndvi_clean))
valid_idx = np.where(valid)[0]
if len(valid_idx) >= 2:
    f = interp1d(valid_idx, ndvi_clean[valid_idx],
                 kind="linear", fill_value="extrapolate")
    ndvi_interp = f(dates_num)
''',
        "r": '''library(zoo)

# Mascarar e interpolar
ndvi_clean <- ifelse(quality == 1, ndvi_series, NA)
ndvi_interp <- na.approx(ndvi_clean, rule = 2)
''',
        "sits": '''library(sits)

# sits usa CMASK automaticamente em cubos BDC
# A filtragem de nuvens é feita durante sits_get_data()
ts <- sits_get_data(
  cube = cube,
  samples = samples
)
''',
    },
}


def plan_time_series_extraction(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
    bands: list[str] | None = None,
    output_format: str = "dataframe",
) -> dict[str, Any]:
    """Plano avançado para extração de séries temporais com código sits e Python.

    Args:
        collection_id: ID da coleção (preferencialmente data cube).
        bbox_or_biome: Bbox [min_lon, min_lat, max_lon, max_lat] ou nome de região/bioma.
        start_year: Ano inicial da série.
        end_year: Ano final da série.
        bands: Lista de bandas/índices (ex: ["NDVI", "EVI"]). Padrão: ["NDVI"].
        output_format: Formato de saída — "dataframe", "array", "csv".
    """
    if bands is None:
        bands = ["NDVI"]

    known = ALL_COLLECTIONS.get(collection_id, {})
    period = known.get("period", "16D")
    res_m = known.get("res_m")
    category = known.get("category", "")

    period_days = PERIOD_DAYS.get(period, 16)
    total_days = (end_year - start_year + 1) * 365
    expected_items = total_days // period_days

    if isinstance(bbox_or_biome, str):
        bbox = resolve_bbox(bbox_or_biome) or [-53.2, -19.5, -45.9, -12.4]
        region_name = bbox_or_biome
    elif isinstance(bbox_or_biome, list):
        bbox = bbox_or_biome
        region_name = "custom"
    else:
        bbox = [-53.2, -19.5, -45.9, -12.4]
        region_name = "Goiás (padrão)"

    # Mapear bandas para coleção
    band_map = COLLECTION_BAND_MAPPING.get(collection_id, {})
    mapped_bands: dict[str, str] = {}
    for b in bands:
        bl = b.lower()
        if bl in band_map:
            mapped_bands[b] = band_map[bl]
        else:
            mapped_bands[b] = b

    bands_r = ", ".join(f'"{v}"' for v in mapped_bands.values())
    bands_py = str(list(mapped_bands.values()))

    is_cube = category == "data_cube" or bool(known.get("period"))

    sits_code = f'''library(sits)

# 1. Criar cubo STAC
cube <- sits_cube(
  source     = "BDC",
  collection = "{collection_id}",
  bands      = c({bands_r}),
  roi        = c(lon_min = {bbox[0]}, lat_min = {bbox[1]},
                 lon_max = {bbox[2]}, lat_max = {bbox[3]}),
  start_date = "{start_year}-01-01",
  end_date   = "{end_year}-12-31"
)

# 2. Regularizar (se não for data cube BDC)
{"# Cubo BDC já é regular — pular sits_regularize()" if is_cube else f'''reg_cube <- sits_regularize(
  cube   = cube,
  period = "{period}",
  res    = {res_m or 30}
)'''}

# 3. Extrair séries temporais em pontos de amostra
ts <- sits_get_data(
  cube    = {"cube" if is_cube else "reg_cube"},
  samples = samples_csv  # data.frame com longitude, latitude, label
)

# 4. Filtrar ruídos
ts_filtered <- sits_filter(ts, filter = sits_whittaker(lambda = 2.0))

# 5. Plotar
plot(ts_filtered)
'''

    python_code = f'''from pystac_client import Client
import rasterio
import numpy as np
import pandas as pd
import os

# 1. Conectar ao STAC BDC
client = Client.open(
    "https://data.inpe.br/bdc/stac/v1/",
    headers={{"x-api-key": os.getenv("BDC_API_KEY", "")}}
)

# 2. Buscar itens
search = client.search(
    collections=["{collection_id}"],
    bbox={bbox},
    datetime="{start_year}-01-01/{end_year}-12-31",
    limit=500
)
items = sorted(search.items(), key=lambda i: i.datetime)
print(f"Itens encontrados: {{len(items)}}")

# 3. Extrair série temporal para um ponto
lon, lat = {(bbox[0]+bbox[2])/2:.4f}, {(bbox[1]+bbox[3])/2:.4f}
bands = {bands_py}

records = []
for item in items:
    row = {{"datetime": item.datetime}}
    for band in bands:
        if band in item.assets:
            with rasterio.open(item.assets[band].href) as src:
                val = list(src.sample([(lon, lat)]))[0]
                row[band] = float(val[0]) if val[0] != src.nodata else np.nan
    records.append(row)

df = pd.DataFrame(records)
df.set_index("datetime", inplace=True)
print(df.head(10))

# 4. Suavização
from scipy.signal import savgol_filter
for band in bands:
    if band in df.columns:
        valid = df[band].notna()
        if valid.sum() > 7:
            df[f"{{band}}_smooth"] = savgol_filter(
                df[band].interpolate(), window_length=7, polyorder=2
            )
'''

    return {
        "collection_id": collection_id,
        "region": region_name,
        "bbox": bbox,
        "period": f"{start_year}-{end_year}",
        "temporal_resolution": f"{period} ({period_days} dias)",
        "expected_items": expected_items,
        "bands": mapped_bands,
        "is_data_cube": is_cube,
        "spatial_resolution_m": res_m,
        "output_format": output_format,
        "sits_code": sits_code,
        "python_code": python_code,
        "recommendations": [
            f"Coleção {collection_id}: ~{expected_items} itens no período solicitado.",
            "Para data cubes BDC, os dados já são ARD (Analysis Ready Data).",
            "Use sits_whittaker ou savgol_filter para suavizar ruídos residuais.",
            "Para grandes áreas, processe tile a tile para evitar sobrecarga de memória.",
            "Verifique a banda CLEAROB para avaliar a qualidade de cada pixel.",
        ],
    }


def get_filtering_guide(method: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
    """Retorna guia de métodos de filtragem para séries temporais de satélite.

    Args:
        method: Nome do método — "savitzky_golay", "whittaker", "cloud_filter". Se None, lista todos.
    """
    if method is None:
        return [
            {"method": k, **{mk: mv for mk, mv in v.items() if mk != "python" and mk != "r" and mk != "sits"}}
            for k, v in _FILTERING_METHODS.items()
        ]

    key = method.lower().replace("-", "_").replace(" ", "_")
    data = _FILTERING_METHODS.get(key)
    if data is None:
        return {
            "error": f"Método '{method}' não encontrado.",
            "available": list(_FILTERING_METHODS.keys()),
        }

    return {"method": key, **data}


def plan_phenology_extraction(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    band: str = "NDVI",
) -> dict[str, Any]:
    """Plano para extração de métricas fenológicas (SOS, EOS, Peak, Amplitude).

    Args:
        collection_id: ID da coleção (data cube recomendado).
        bbox_or_biome: Bbox ou nome de região/bioma.
        band: Banda/índice para fenologia (padrão: "NDVI").
    """
    known = ALL_COLLECTIONS.get(collection_id, {})
    period = known.get("period", "16D")
    period_days = PERIOD_DAYS.get(period, 16)

    if isinstance(bbox_or_biome, str):
        region_name = bbox_or_biome
    elif isinstance(bbox_or_biome, list):
        region_name = "custom"
    else:
        region_name = ""

    band_map = COLLECTION_BAND_MAPPING.get(collection_id, {})
    band_key = band_map.get(band.lower(), band)

    return PhenologyPlan(
        collection_id=collection_id,
        region=region_name,
        metrics=["SOS (Start of Season)", "EOS (End of Season)", "POS (Peak of Season)",
                 "Amplitude", "Base Value", "Length of Season (LOS)",
                 "Small Integral", "Large Integral"],
        temporal_resolution_days=period_days,
        filtering_method="whittaker (lambda=2.0) ou savitzky_golay (window=7, order=2)",
        python_snippet=f'''import numpy as np
from scipy.signal import savgol_filter, argrelextrema

# Série temporal {band} suavizada
ndvi_smooth = savgol_filter(ndvi_series, window_length=7, polyorder=2)

# Métricas fenológicas simples
threshold = 0.2  # Limiar para início/fim de estação

# SOS (Start of Season): primeiro cruzamento ascendente do threshold
sos_idx = np.where((ndvi_smooth[:-1] < threshold) & (ndvi_smooth[1:] >= threshold))[0]

# EOS (End of Season): primeiro cruzamento descendente
eos_idx = np.where((ndvi_smooth[:-1] >= threshold) & (ndvi_smooth[1:] < threshold))[0]

# POS (Peak of Season): máximo entre SOS e EOS
if len(sos_idx) > 0 and len(eos_idx) > 0:
    peak_idx = sos_idx[0] + np.argmax(ndvi_smooth[sos_idx[0]:eos_idx[0]+1])
    amplitude = ndvi_smooth[peak_idx] - ndvi_smooth[sos_idx[0]]
    los = eos_idx[0] - sos_idx[0]  # Length of Season (em composições)
    print(f"SOS: {{dates[sos_idx[0]]}}, EOS: {{dates[eos_idx[0]]}}")
    print(f"Peak: {{dates[peak_idx]}}, Amplitude: {{amplitude:.3f}}")
    print(f"Length of Season: {{los * {period_days}}} dias")
''',
        r_snippet=f'''library(terra)
library(phenofit)

# Extrair métricas fenológicas
pheno <- extract_pheno(ndvi_ts, method = "zhang")

# Ou via sits
library(sits)
# Extrair com sits_apply e funções personalizadas
''',
        sits_snippet=f'''library(sits)

# Cubo BDC
cube <- sits_cube(
  source     = "BDC",
  collection = "{collection_id}",
  bands      = c("{band_key}"),
  # ... roi e datas
)

# Extrair séries
ts <- sits_get_data(cube, samples)

# Fenologia via sits_apply (custom)
# O sits não tem função dedicada de fenologia,
# mas permite aplicar funções personalizadas:
cube_pheno <- sits_apply(
  data = cube,
  PEAK = max({band_key}),
  BASE = min({band_key}),
  AMP  = max({band_key}) - min({band_key}),
  output_dir = "./phenology/"
)
''',
        interpretation_guide=(
            "Métricas fenológicas:\n"
            "- SOS (Start of Season): Início do crescimento vegetativo. No Cerrado, geralmente outubro-novembro.\n"
            "- EOS (End of Season): Fim do ciclo vegetativo. Tipicamente abril-maio.\n"
            "- POS (Peak of Season): Máximo vigor vegetativo. Janeiro-fevereiro no Cerrado.\n"
            "- Amplitude: Diferença entre pico e base. Maior em áreas agrícolas.\n"
            "- LOS (Length of Season): Duração do ciclo em dias.\n"
            "- Small Integral: Área sob a curva acima da base — proporcional à produtividade.\n"
            "- Large Integral: Área total sob a curva — biomassa total acumulada.\n\n"
            "Para agricultura: SOS identifica data de plantio, EOS a colheita.\n"
            "Para desmatamento: perda abrupta de amplitude indica conversão."
        ),
    ).model_dump()


def analyze_temporal_gaps(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    datetime_range: str = "2020-01-01/2023-12-31",
) -> dict[str, Any]:
    """Analisa gaps temporais em uma coleção para uma região, via busca STAC.

    Args:
        collection_id: ID da coleção STAC.
        bbox_or_biome: Bbox ou nome de região/bioma.
        datetime_range: Intervalo temporal ISO 8601.
    """
    from ..client import BDCClient

    # Resolver bbox
    if isinstance(bbox_or_biome, str):
        bbox = resolve_bbox(bbox_or_biome)
        region_name = bbox_or_biome
    elif isinstance(bbox_or_biome, list):
        bbox = bbox_or_biome
        region_name = "custom"
    else:
        bbox = None
        region_name = "global"

    # Buscar itens
    client = BDCClient.get_instance()
    params: dict[str, Any] = {
        "collections": [collection_id],
        "datetime": datetime_range,
        "limit": 500,
    }
    if bbox:
        params["bbox"] = bbox

    result = client.search_post_raw(params)
    features = result.get("features", [])

    if not features:
        return {
            "collection_id": collection_id,
            "region": region_name,
            "datetime_range": datetime_range,
            "total_items": 0,
            "note": "Nenhum item encontrado para os parâmetros informados.",
        }

    # Extrair datas
    from datetime import datetime
    dates: list[datetime] = []
    for f in features:
        dt_str = f.get("properties", {}).get("datetime")
        if dt_str:
            try:
                dates.append(datetime.fromisoformat(dt_str.replace("Z", "+00:00")))
            except (ValueError, TypeError):
                pass

    dates.sort()

    if len(dates) < 2:
        return {
            "collection_id": collection_id,
            "region": region_name,
            "total_items": len(dates),
            "note": "Poucos itens para análise de gaps.",
        }

    # Calcular gaps
    gaps_days = [(dates[i+1] - dates[i]).days for i in range(len(dates) - 1)]
    known = ALL_COLLECTIONS.get(collection_id, {})
    expected_period = PERIOD_DAYS.get(known.get("period", ""), 16)

    significant_gaps = [
        {
            "from": dates[i].isoformat(),
            "to": dates[i+1].isoformat(),
            "days": gaps_days[i],
            "expected_days": expected_period,
            "missing_observations": max(0, gaps_days[i] // expected_period - 1),
        }
        for i in range(len(gaps_days))
        if gaps_days[i] > expected_period * 1.5
    ]

    import statistics
    return {
        "collection_id": collection_id,
        "region": region_name,
        "datetime_range": datetime_range,
        "total_items": len(features),
        "unique_dates": len(dates),
        "first_date": dates[0].isoformat(),
        "last_date": dates[-1].isoformat(),
        "expected_period_days": expected_period,
        "gap_statistics": {
            "min_gap_days": min(gaps_days),
            "max_gap_days": max(gaps_days),
            "mean_gap_days": round(statistics.mean(gaps_days), 1),
            "median_gap_days": round(statistics.median(gaps_days), 1),
        },
        "significant_gaps": significant_gaps[:20],
        "total_significant_gaps": len(significant_gaps),
        "completeness_pct": round(
            (len(dates) / max(1, (dates[-1] - dates[0]).days // expected_period + 1)) * 100, 1
        ),
        "recommendation": (
            "Série temporal completa e regular."
            if not significant_gaps
            else f"{len(significant_gaps)} gaps significativos detectados. "
                 "Recomenda-se filtragem Whittaker com interpolação para preencher os gaps."
        ),
    }


def generate_sits_cube_code(
    collection_id: str,
    bbox_or_biome: str | list[float] | None = None,
    start_year: int = 2020,
    end_year: int = 2023,
    bands: list[str] | None = None,
) -> str:
    """Gera código R sits completo (sits_cube até sits_get_data).

    Args:
        collection_id: ID da coleção BDC.
        bbox_or_biome: Bbox ou nome de região/bioma.
        start_year: Ano inicial.
        end_year: Ano final.
        bands: Lista de bandas (ex: ["NDVI", "EVI", "RED", "NIR"]). Padrão: ["NDVI", "EVI"].
    """
    if bands is None:
        bands = ["NDVI", "EVI"]

    band_map = COLLECTION_BAND_MAPPING.get(collection_id, {})
    mapped = [band_map.get(b.lower(), b) for b in bands]
    bands_r = ", ".join(f'"{b}"' for b in mapped)

    if isinstance(bbox_or_biome, str):
        bbox = resolve_bbox(bbox_or_biome) or [-53.2, -19.5, -45.9, -12.4]
        region_comment = f"  # Região: {bbox_or_biome}"
    elif isinstance(bbox_or_biome, list):
        bbox = bbox_or_biome
        region_comment = ""
    else:
        bbox = [-53.2, -19.5, -45.9, -12.4]
        region_comment = "  # Goiás (padrão)"

    known = ALL_COLLECTIONS.get(collection_id, {})
    is_cube = known.get("category") == "data_cube" or bool(known.get("period"))
    period = known.get("period", "16D")
    res = known.get("res_m", 30)

    return f'''library(sits)

# ==============================================================
# Workflow sits completo para coleção {collection_id}
# ==============================================================

# 1. Definir variáveis de ambiente
Sys.setenv("BDC_ACCESS_KEY" = Sys.getenv("BDC_API_KEY"))

# 2. Criar cubo STAC
cube <- sits_cube(
  source     = "BDC",
  collection = "{collection_id}",
  bands      = c({bands_r}),
  roi        = c(
    lon_min = {bbox[0]}, lat_min = {bbox[1]},
    lon_max = {bbox[2]}, lat_max = {bbox[3]}
  ),{region_comment}
  start_date = "{start_year}-01-01",
  end_date   = "{end_year}-12-31"
)

cat("Cubo criado:", sits_timeline(cube) |> length(), "datas\\n")

# 3. Regularizar{"  (já regular — opcional)" if is_cube else ""}
{"# Cubo BDC já é regular" if is_cube else f'''reg_cube <- sits_regularize(
  cube   = cube,
  period = "{period}",
  res    = {res},
  output_dir = "./regularized/"
)'''}

# 4. Extrair séries temporais em pontos
# Preparar amostras: CSV com colunas longitude, latitude, start_date, end_date, label
# samples <- read.csv("samples.csv")
# ts <- sits_get_data(cube = {"cube" if is_cube else "reg_cube"}, samples = samples)

# 5. Filtrar ruídos
# ts_filtered <- sits_filter(ts, filter = sits_whittaker(lambda = 2.0))

# 6. Plotar séries
# plot(ts_filtered)

# 7. Aplicar índice espectral personalizado (se necessário)
# cube_ndvi <- sits_apply(
#   data = {"cube" if is_cube else "reg_cube"},
#   NDVI_CUSTOM = (NIR - RED) / (NIR + RED),
#   output_dir = "./indices/"
# )
'''
