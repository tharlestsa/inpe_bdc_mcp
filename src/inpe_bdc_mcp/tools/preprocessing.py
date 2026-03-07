"""Ferramentas MCP para orientação de pré-processamento de imagens de satélite."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS
from ..models.preprocessing import CloudMaskStrategy, PreprocessingGuide

# ------------------------------------------------------------------ #
# Níveis de processamento por padrão de ID de coleção
# ------------------------------------------------------------------ #

_PROCESSING_INFO: dict[str, dict[str, Any]] = {
    "L4-SR": {
        "level": "L4 — Reflectância de Superfície (SR)",
        "atmospheric": "Correção atmosférica aplicada (algoritmo LaSRC para Landsat, MS3 para CBERS).",
        "geometric": "Ortorretificado com modelo digital de elevação (DEM).",
        "radiometric": "Calibração radiométrica e conversão para reflectância de superfície.",
    },
    "L4-DN": {
        "level": "L4 — Números Digitais (DN)",
        "atmospheric": "NÃO aplicada. Os dados são números digitais brutos. Recomenda-se correção atmosférica antes de calcular índices espectrais.",
        "geometric": "Ortorretificado com DEM.",
        "radiometric": "Calibração radiométrica básica. Para análises quantitativas, converter DN para radiância/reflectância.",
    },
    "L2-DN": {
        "level": "L2 — Números Digitais (DN)",
        "atmospheric": "NÃO aplicada.",
        "geometric": "Georreferenciado com modelo de órbita (sem ortorretificação). Pode haver distorções em terreno acidentado.",
        "radiometric": "Calibração radiométrica básica.",
    },
    "L2A": {
        "level": "L2A — Reflectância de Superfície (BOA)",
        "atmospheric": "Correção atmosférica aplicada pelo algoritmo Sen2Cor (Sentinel-2). Reflectância Bottom-of-Atmosphere (BOA).",
        "geometric": "Ortorretificado com DEM Copernicus (Sentinel-2).",
        "radiometric": "Calibração radiométrica completa. Dados prontos para análise quantitativa.",
    },
    "L1C": {
        "level": "L1C — Reflectância no Topo da Atmosfera (TOA)",
        "atmospheric": "NÃO aplicada. Dados são reflectância Top-of-Atmosphere (TOA). Aplicar Sen2Cor ou ACOLITE para obter BOA.",
        "geometric": "Ortorretificado com DEM.",
        "radiometric": "Calibração radiométrica completa.",
    },
    "L1B": {
        "level": "L1B — Radiância no Topo da Atmosfera",
        "atmospheric": "NÃO aplicada. Dados são radiância TOA.",
        "geometric": "Georreferenciado.",
        "radiometric": "Calibração radiométrica básica.",
    },
    "DATA_CUBE": {
        "level": "Data Cube BDC — Analysis Ready Data (ARD)",
        "atmospheric": "Correção atmosférica já aplicada nas imagens fonte. O data cube é composto de imagens ARD.",
        "geometric": "Ortorretificado e reprojetado para grade BDC (Albers Equal-Area).",
        "radiometric": "Reflectância de superfície normalizada. Composição temporal com Best Pixel (LCF) ou TSIRF.",
    },
}

# ------------------------------------------------------------------ #
# Estratégias de máscara de nuvem
# ------------------------------------------------------------------ #

_CLOUD_STRATEGIES: dict[str, dict[str, Any]] = {
    "CMASK": {
        "band": "CMASK",
        "values": {"sem_dados": [0], "limpo": [1], "nuvem": [127], "sombra": [255]},
        "quality_assessment": "Máscara binária do BDC. Alta confiabilidade para data cubes compostos.",
        "recommendations": [
            "Filtrar pixels com CMASK == 1 (limpo) para análises quantitativas.",
            "Combinar com CLEAROB >= 3 para garantir robustez da composição.",
            "Para séries temporais, verificar TOTALOB para entender a frequência de observações úteis.",
        ],
        "python": '''import rasterio
import numpy as np

# Máscara de nuvem BDC (CMASK)
with rasterio.open(item.assets["CMASK"].href) as src:
    cmask = src.read(1)

clear_mask = cmask == 1  # Pixels limpos
cloud_mask = cmask == 127  # Pixels com nuvem
shadow_mask = cmask == 255  # Pixels com sombra

# Aplicar máscara aos dados
with rasterio.open(item.assets["NDVI"].href) as src:
    ndvi = src.read(1).astype("float32")
    ndvi[~clear_mask] = np.nan  # Mascarar pixels não-limpos
''',
        "r": '''library(terra)

cmask <- rast(item_assets[["CMASK"]]$href)
ndvi <- rast(item_assets[["NDVI"]]$href)

# Aplicar máscara: manter apenas pixels limpos (valor 1)
ndvi_clean <- mask(ndvi, cmask, maskvalues = c(0, 127, 255))
plot(ndvi_clean, main = "NDVI (sem nuvens)")
''',
    },
    "SCL": {
        "band": "SCL",
        "values": {
            "sem_dados": [0], "saturado": [1], "sombra_escura": [2], "sombra_nuvem": [3],
            "vegetacao": [4], "solo_exposto": [5], "agua": [6], "nao_classificado": [7],
            "nuvem_media": [8], "nuvem_alta": [9], "cirrus": [10], "neve": [11],
        },
        "quality_assessment": "Scene Classification Layer do Sentinel-2 (Sen2Cor). Classificação detalhada com 12 classes.",
        "recommendations": [
            "Para análise de vegetação: manter classes 4 (vegetação) e 5 (solo).",
            "Para máscara simples: excluir classes 0, 1, 2, 3, 8, 9, 10.",
            "Classe 6 (água) útil para análise hidrológica.",
        ],
        "python": '''import rasterio
import numpy as np

# Scene Classification Layer (Sentinel-2)
with rasterio.open(item.assets["SCL"].href) as src:
    scl = src.read(1)

# Classes válidas para análise terrestre: vegetação (4) + solo (5)
valid_mask = np.isin(scl, [4, 5])

# Excluir nuvens, sombras e dados inválidos
cloud_free = ~np.isin(scl, [0, 1, 2, 3, 8, 9, 10])
''',
        "r": '''library(terra)

scl <- rast(item_assets[["SCL"]]$href)

# Manter apenas vegetação (4) e solo (5)
valid <- scl %in% c(4, 5)
data_clean <- mask(data, valid, maskvalues = FALSE)
''',
    },
    "FMASK": {
        "band": "Fmask",
        "values": {"limpo": [0], "agua": [1], "sombra_nuvem": [2], "neve": [3], "nuvem": [4]},
        "quality_assessment": "Algoritmo Fmask (Function of Mask). Usado em coleções Landsat não processadas pelo BDC.",
        "recommendations": [
            "Filtrar com Fmask == 0 para pixels limpos.",
            "Para hidrologia, incluir Fmask == 1 (água).",
        ],
        "python": '''import rasterio
import numpy as np

with rasterio.open(item.assets["Fmask"].href) as src:
    fmask = src.read(1)

clear = fmask == 0  # Pixels limpos
''',
        "r": '''library(terra)
fmask <- rast(item_assets[["Fmask"]]$href)
clear <- fmask == 0
''',
    },
}


def _detect_processing_level(collection_id: str) -> str:
    """Detecta o nível de processamento a partir do ID da coleção."""
    cid = collection_id.upper()
    known = ALL_COLLECTIONS.get(collection_id, {})

    # Data cubes BDC
    if known.get("category") == "data_cube" or known.get("period"):
        return "DATA_CUBE"

    level = known.get("level", "")
    if level:
        level_upper = level.upper()
        for key in ("L4-SR", "L4-DN", "L2-DN", "L2A", "L1C", "L1B"):
            if key in level_upper:
                return key

    # Inferir do ID
    if "-SR-" in cid or "L4-SR" in cid:
        return "L4-SR"
    if "L2A" in cid or "_L2A" in cid:
        return "L2A"
    if "L1C" in cid:
        return "L1C"
    if "L4-DN" in cid or "-L4-DN" in cid:
        return "L4-DN"
    if "L2-DN" in cid or "-L2-DN" in cid:
        return "L2-DN"
    if "L1B" in cid:
        return "L1B"
    if any(p in cid for p in ("-16D-", "-8D-", "-1M-", "-2M-", "-3M-")):
        return "DATA_CUBE"

    return "L2-DN"


def _detect_cloud_strategy(collection_id: str) -> str:
    """Detecta a estratégia de máscara de nuvem para a coleção."""
    known = ALL_COLLECTIONS.get(collection_id, {})

    if known.get("category") == "data_cube" or known.get("period"):
        return "CMASK"

    level = known.get("level", "")
    if "L2A" in level or "Sentinel-2" in known.get("satellite", ""):
        return "SCL"

    return "FMASK"


def get_preprocessing_guide(collection_id: str) -> dict[str, Any]:
    """Retorna guia completo de pré-processamento para uma coleção.

    Args:
        collection_id: ID da coleção STAC.
    """
    level_key = _detect_processing_level(collection_id)
    info = _PROCESSING_INFO.get(level_key, _PROCESSING_INFO["L2-DN"])

    cloud_key = _detect_cloud_strategy(collection_id)
    cloud_data = _CLOUD_STRATEGIES.get(cloud_key, _CLOUD_STRATEGIES["FMASK"])

    cloud_mask = CloudMaskStrategy(
        collection_id=collection_id,
        mask_band=cloud_data["band"],
        mask_values=cloud_data["values"],
        python_snippet=cloud_data["python"],
        r_snippet=cloud_data["r"],
        quality_assessment=cloud_data["quality_assessment"],
        recommendations=cloud_data["recommendations"],
    )

    # Pan-sharpening
    known = ALL_COLLECTIONS.get(collection_id, {})
    sensor = known.get("sensor", "")
    is_pan = "PAN" in sensor.upper()

    recs: list[str] = []
    if level_key in ("L2-DN", "L4-DN"):
        recs.append("Converter DN para reflectância antes de calcular índices espectrais.")
    if level_key == "L1C":
        recs.append("Aplicar correção atmosférica (Sen2Cor ou ACOLITE) para obter reflectância de superfície.")
    if level_key == "DATA_CUBE":
        recs.append("Dados já prontos para análise (ARD). Filtrar com CMASK e CLEAROB para qualidade máxima.")
    if level_key in ("L2A", "L4-SR"):
        recs.append("Dados com reflectância de superfície. Prontos para cálculo de índices espectrais.")

    return PreprocessingGuide(
        collection_id=collection_id,
        processing_level=info["level"],
        atmospheric_correction=info["atmospheric"],
        geometric_correction=info["geometric"],
        cloud_mask=cloud_mask,
        radiometric_info=info["radiometric"],
        pan_sharpening_applicable=is_pan,
        pan_sharpening_guide=_PAN_SHARPENING_GUIDE if is_pan else None,
        recommendations=recs,
    ).model_dump()


def get_cloud_mask_strategy(collection_id: str) -> dict[str, Any]:
    """Retorna estratégia de mascaramento de nuvens com código Python/R.

    Args:
        collection_id: ID da coleção STAC.
    """
    cloud_key = _detect_cloud_strategy(collection_id)
    cloud_data = _CLOUD_STRATEGIES.get(cloud_key, _CLOUD_STRATEGIES["FMASK"])

    return CloudMaskStrategy(
        collection_id=collection_id,
        mask_band=cloud_data["band"],
        mask_values=cloud_data["values"],
        python_snippet=cloud_data["python"],
        r_snippet=cloud_data["r"],
        quality_assessment=cloud_data["quality_assessment"],
        recommendations=cloud_data["recommendations"],
    ).model_dump()


def get_atmospheric_correction_info(collection_id: str) -> dict[str, Any]:
    """Retorna informações sobre correção atmosférica de uma coleção.

    Args:
        collection_id: ID da coleção STAC.
    """
    level_key = _detect_processing_level(collection_id)
    info = _PROCESSING_INFO.get(level_key, _PROCESSING_INFO["L2-DN"])

    needs_correction = level_key in ("L2-DN", "L4-DN", "L1C", "L1B")

    result: dict[str, Any] = {
        "collection_id": collection_id,
        "processing_level": info["level"],
        "atmospheric_correction_status": info["atmospheric"],
        "needs_correction": needs_correction,
    }

    if needs_correction:
        result["correction_options"] = [
            {
                "algorithm": "Sen2Cor",
                "applicable_to": "Sentinel-2 L1C",
                "description": "Processador padrão ESA. Gera produtos L2A.",
                "tool": "sen2cor (standalone) ou snap (ESA SNAP Toolbox)",
            },
            {
                "algorithm": "ACOLITE",
                "applicable_to": "Sentinel-2, Landsat, Sentinel-3",
                "description": "Excelente para superfícies aquáticas. Dark spectrum fitting.",
                "tool": "acolite (Python package)",
            },
            {
                "algorithm": "LaSRC",
                "applicable_to": "Landsat 4-9",
                "description": "Algoritmo do USGS para Landsat. Produz reflectância de superfície.",
                "tool": "ESPA (USGS) ou processamento BDC",
            },
            {
                "algorithm": "6S / Py6S",
                "applicable_to": "Qualquer sensor óptico",
                "description": "Modelo de transferência radiativa. Mais preciso, porém mais complexo.",
                "tool": "Py6S (Python package)",
            },
        ]
        result["recommendation"] = (
            "Para a maioria das análises, prefira usar coleções BDC já corrigidas (SR ou L2A) "
            "ou data cubes (ARD). Aplique correção atmosférica apenas se necessário usar dados brutos."
        )

    return result


def get_pan_sharpening_guide(collection_id: str) -> dict[str, Any]:
    """Retorna guia de pan-sharpening para coleções pancromáticas (CBERS PAN).

    Args:
        collection_id: ID da coleção STAC.
    """
    known = ALL_COLLECTIONS.get(collection_id, {})
    sensor = known.get("sensor", "")

    if "PAN" not in sensor.upper():
        return {
            "collection_id": collection_id,
            "applicable": False,
            "note": f"Pan-sharpening não aplicável à coleção {collection_id} (sensor: {sensor or 'desconhecido'}).",
            "pan_collections": ["CB4-PAN5M-L4-DN-1", "CB4-PAN10M-L4-DN-1"],
        }

    return {
        "collection_id": collection_id,
        "applicable": True,
        "pan_resolution_m": known.get("res_m"),
        "guide": _PAN_SHARPENING_GUIDE,
        "compatible_multispectral": _get_compatible_ms(collection_id),
        "methods": [
            {"name": "Brovey Transform", "best_for": "Visualização RGB", "preserves_spectral": False},
            {"name": "Gram-Schmidt", "best_for": "Análise espectral", "preserves_spectral": True},
            {"name": "IHS (Intensity-Hue-Saturation)", "best_for": "Uso geral", "preserves_spectral": False},
        ],
        "python_snippet": '''import rasterio
from rasterio.merge import merge
import numpy as np

# Pan-sharpening simples (Brovey Transform)
with rasterio.open("pan.tif") as src_pan:
    pan = src_pan.read(1).astype("float32")

with rasterio.open("multispectral.tif") as src_ms:
    ms = src_ms.read().astype("float32")  # shape: (bands, h, w)

# Brovey: band_sharp = band_ms * (pan / sum(ms_bands))
intensity = ms.sum(axis=0)
sharpened = ms * (pan / (intensity + 1e-10))
''',
    }


def _get_compatible_ms(pan_collection_id: str) -> list[str]:
    """Retorna coleções multiespectrais compatíveis para pan-sharpening."""
    if "PAN5M" in pan_collection_id or "PAN10M" in pan_collection_id:
        prefix = pan_collection_id.split("-")[0]  # CB4 ou CB4A
        return [
            cid for cid in ALL_COLLECTIONS
            if cid.startswith(prefix) and "MUX" in cid
        ]
    return []


_PAN_SHARPENING_GUIDE = (
    "Pan-sharpening combina a alta resolução espacial da banda pancromática (5m ou 10m) "
    "com a informação espectral das bandas multiespectrais (20m ou 64m). "
    "Procedimento:\n"
    "1. Obter imagem PAN (mesma data e região) da coleção pancromática\n"
    "2. Obter imagem multiespectral (MUX ou WFI) coincidente\n"
    "3. Co-registrar as duas imagens (mesmo grid/extent)\n"
    "4. Aplicar algoritmo de fusão (Gram-Schmidt recomendado para preservar informação espectral)\n"
    "5. Validar resultado comparando estatísticas espectrais"
)
