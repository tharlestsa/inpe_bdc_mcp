"""Ferramentas MCP para índices espectrais e álgebra de bandas."""

from __future__ import annotations

from typing import Any

from ..catalogs import ALL_COLLECTIONS, COLLECTION_BAND_MAPPING
from ..client import BDCClient
from ..models.spectral import IndexAvailability, IndexComputeGuide, SpectralIndex

# ------------------------------------------------------------------ #
# Base de dados de índices espectrais
# ------------------------------------------------------------------ #

_SPECTRAL_INDICES: dict[str, dict[str, Any]] = {
    "NDVI": {
        "full_name": "Normalized Difference Vegetation Index",
        "formula": "(NIR - RED) / (NIR + RED)",
        "formula_python": "(nir - red) / (nir + red + 1e-10)",
        "required_bands": ["nir", "red"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Índice mais utilizado para monitoramento de vegetação. Valores entre 0.3-0.8 indicam vegetação saudável.",
        "reference": "Rouse et al. (1974)",
        "applications": ["monitoramento de vegetação", "detecção de estresse hídrico", "estimativa de biomassa", "séries temporais fenológicas"],
    },
    "EVI": {
        "full_name": "Enhanced Vegetation Index",
        "formula": "2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))",
        "formula_python": "2.5 * ((nir - red) / (nir + 6*red - 7.5*blue + 1))",
        "required_bands": ["nir", "red", "blue"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Versão melhorada do NDVI que corrige efeitos atmosféricos e saturação em vegetação densa.",
        "reference": "Huete et al. (2002)",
        "applications": ["vegetação densa (florestas tropicais)", "monitoramento de Cerrado/Amazônia", "correção de efeitos atmosféricos"],
    },
    "EVI2": {
        "full_name": "Enhanced Vegetation Index 2 (two-band)",
        "formula": "2.5 * ((NIR - RED) / (NIR + 2.4*RED + 1))",
        "formula_python": "2.5 * ((nir - red) / (nir + 2.4*red + 1))",
        "required_bands": ["nir", "red"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Versão simplificada do EVI que não requer banda azul. Útil para sensores com 4 bandas (CBERS WFI).",
        "reference": "Jiang et al. (2008)",
        "applications": ["alternativa ao EVI quando banda azul indisponível", "CBERS WFI", "séries temporais"],
    },
    "SAVI": {
        "full_name": "Soil Adjusted Vegetation Index",
        "formula": "((NIR - RED) / (NIR + RED + L)) * (1 + L), L=0.5",
        "formula_python": "((nir - red) / (nir + red + 0.5)) * 1.5",
        "required_bands": ["nir", "red"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Minimiza a influência do brilho do solo. Ideal para áreas com vegetação esparsa (Caatinga, Cerrado aberto).",
        "reference": "Huete (1988)",
        "applications": ["vegetação esparsa", "regiões semiáridas", "Caatinga", "pastagens degradadas"],
    },
    "MSAVI2": {
        "full_name": "Modified Soil Adjusted Vegetation Index 2",
        "formula": "(2*NIR + 1 - sqrt((2*NIR+1)² - 8*(NIR-RED))) / 2",
        "formula_python": "(2*nir + 1 - np.sqrt((2*nir + 1)**2 - 8*(nir - red))) / 2",
        "required_bands": ["nir", "red"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Ajuste automático do fator L do SAVI. Melhor em solos muito expostos.",
        "reference": "Qi et al. (1994)",
        "applications": ["solo exposto", "vegetação esparsa", "regiões áridas"],
    },
    "NDWI": {
        "full_name": "Normalized Difference Water Index",
        "formula": "(GREEN - NIR) / (GREEN + NIR)",
        "formula_python": "(green - nir) / (green + nir + 1e-10)",
        "required_bands": ["green", "nir"],
        "value_range": [-1.0, 1.0],
        "category": "water",
        "description": "Detecta presença de água superficial. Valores positivos indicam corpos d'água.",
        "reference": "McFeeters (1996)",
        "applications": ["mapeamento de corpos d'água", "detecção de inundações", "monitoramento de reservatórios"],
    },
    "MNDWI": {
        "full_name": "Modified Normalized Difference Water Index",
        "formula": "(GREEN - SWIR16) / (GREEN + SWIR16)",
        "formula_python": "(green - swir16) / (green + swir16 + 1e-10)",
        "required_bands": ["green", "swir16"],
        "value_range": [-1.0, 1.0],
        "category": "water",
        "description": "Versão melhorada do NDWI usando SWIR. Melhor discriminação entre água e superfícies construídas.",
        "reference": "Xu (2006)",
        "applications": ["áreas urbanas com corpos d'água", "discriminação água/asfalto", "mapeamento costeiro"],
    },
    "NDBI": {
        "full_name": "Normalized Difference Built-up Index",
        "formula": "(SWIR16 - NIR) / (SWIR16 + NIR)",
        "formula_python": "(swir16 - nir) / (swir16 + nir + 1e-10)",
        "required_bands": ["swir16", "nir"],
        "value_range": [-1.0, 1.0],
        "category": "urban",
        "description": "Realça áreas construídas/urbanas. Valores positivos indicam superfícies impermeáveis.",
        "reference": "Zha et al. (2003)",
        "applications": ["expansão urbana", "mapeamento de áreas impermeáveis", "ilhas de calor"],
    },
    "NBR": {
        "full_name": "Normalized Burn Ratio",
        "formula": "(NIR - SWIR22) / (NIR + SWIR22)",
        "formula_python": "(nir - swir22) / (nir + swir22 + 1e-10)",
        "required_bands": ["nir", "swir22"],
        "value_range": [-1.0, 1.0],
        "category": "burn",
        "description": "Detecta áreas queimadas e cicatrizes de fogo. A diferença pré/pós-fogo (dNBR) quantifica a severidade.",
        "reference": "Key & Benson (2006)",
        "applications": ["detecção de cicatrizes de fogo", "severidade de queimadas", "monitoramento de recuperação pós-fogo"],
    },
    "NBR2": {
        "full_name": "Normalized Burn Ratio 2",
        "formula": "(SWIR16 - SWIR22) / (SWIR16 + SWIR22)",
        "formula_python": "(swir16 - swir22) / (swir16 + swir22 + 1e-10)",
        "required_bands": ["swir16", "swir22"],
        "value_range": [-1.0, 1.0],
        "category": "burn",
        "description": "Sensível a variações de umidade pós-fogo. Complementar ao NBR para análise de severidade.",
        "reference": "Key & Benson (2006)",
        "applications": ["severidade de queimadas", "recuperação de vegetação pós-fogo"],
    },
    "NDMI": {
        "full_name": "Normalized Difference Moisture Index",
        "formula": "(NIR - SWIR16) / (NIR + SWIR16)",
        "formula_python": "(nir - swir16) / (nir + swir16 + 1e-10)",
        "required_bands": ["nir", "swir16"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Indicador de conteúdo de umidade na vegetação. Útil para detecção de estresse hídrico.",
        "reference": "Wilson & Sader (2002)",
        "applications": ["estresse hídrico", "seca", "monitoramento de irrigação"],
    },
    "NDSI": {
        "full_name": "Normalized Difference Snow Index",
        "formula": "(GREEN - SWIR16) / (GREEN + SWIR16)",
        "formula_python": "(green - swir16) / (green + swir16 + 1e-10)",
        "required_bands": ["green", "swir16"],
        "value_range": [-1.0, 1.0],
        "category": "snow",
        "description": "Detecta cobertura de neve/gelo. Mesma fórmula do MNDWI, interpretação diferente.",
        "reference": "Hall et al. (1995)",
        "applications": ["mapeamento de neve", "geleiras", "mudanças climáticas em altitude"],
    },
    "BSI": {
        "full_name": "Bare Soil Index",
        "formula": "((SWIR16 + RED) - (NIR + BLUE)) / ((SWIR16 + RED) + (NIR + BLUE))",
        "formula_python": "((swir16 + red) - (nir + blue)) / ((swir16 + red) + (nir + blue) + 1e-10)",
        "required_bands": ["swir16", "red", "nir", "blue"],
        "value_range": [-1.0, 1.0],
        "category": "soil",
        "description": "Realça solo exposto. Útil para mapeamento de áreas degradadas e preparo do solo agrícola.",
        "reference": "Rikimaru et al. (2002)",
        "applications": ["solo exposto", "degradação", "preparo agrícola", "mineração"],
    },
    "GNDVI": {
        "full_name": "Green Normalized Difference Vegetation Index",
        "formula": "(NIR - GREEN) / (NIR + GREEN)",
        "formula_python": "(nir - green) / (nir + green + 1e-10)",
        "required_bands": ["nir", "green"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Mais sensível à variação de clorofila que o NDVI. Útil para estimar concentração de clorofila.",
        "reference": "Gitelson et al. (1996)",
        "applications": ["concentração de clorofila", "vigor vegetativo", "agricultura de precisão"],
    },
    "BAI": {
        "full_name": "Burned Area Index",
        "formula": "1 / ((0.1 - RED)² + (0.06 - NIR)²)",
        "formula_python": "1.0 / ((0.1 - red)**2 + (0.06 - nir)**2 + 1e-10)",
        "required_bands": ["red", "nir"],
        "value_range": [0.0, 500.0],
        "category": "burn",
        "description": "Índice espectral para detecção de áreas queimadas recentes. Valores altos indicam superfícies queimadas.",
        "reference": "Chuvieco et al. (2002)",
        "applications": ["detecção de queimadas recentes", "mapeamento de área queimada"],
    },
    "MIRBI": {
        "full_name": "Mid-Infrared Burn Index",
        "formula": "10*SWIR22 - 9.8*SWIR16 + 2",
        "formula_python": "10*swir22 - 9.8*swir16 + 2",
        "required_bands": ["swir22", "swir16"],
        "value_range": [-2.0, 10.0],
        "category": "burn",
        "description": "Índice para áreas queimadas no Cerrado brasileiro. Desenvolvido especificamente para savanas tropicais.",
        "reference": "Trigg & Flasse (2001)",
        "applications": ["queimadas em Cerrado", "savanas tropicais", "monitoramento de fogo"],
    },
    "CMRI": {
        "full_name": "Clay Minerals Ratio Index",
        "formula": "SWIR16 / SWIR22",
        "formula_python": "swir16 / (swir22 + 1e-10)",
        "required_bands": ["swir16", "swir22"],
        "value_range": [0.0, 5.0],
        "category": "soil",
        "description": "Detecta presença de minerais argilosos na superfície. Útil para mapeamento geológico.",
        "reference": "Drury (1987)",
        "applications": ["mapeamento geológico", "minerais argilosos", "lateritas"],
    },
    "ARVI": {
        "full_name": "Atmospherically Resistant Vegetation Index",
        "formula": "(NIR - (2*RED - BLUE)) / (NIR + (2*RED - BLUE))",
        "formula_python": "(nir - (2*red - blue)) / (nir + (2*red - blue) + 1e-10)",
        "required_bands": ["nir", "red", "blue"],
        "value_range": [-1.0, 1.0],
        "category": "vegetation",
        "description": "Resistente a efeitos atmosféricos. Alternativa ao NDVI em regiões com alta carga de aerossóis.",
        "reference": "Kaufman & Tanré (1992)",
        "applications": ["atmosfera com alta turbidez", "monitoramento em condições de queimada"],
    },
    "SIPI": {
        "full_name": "Structure Insensitive Pigment Index",
        "formula": "(NIR - BLUE) / (NIR - RED)",
        "formula_python": "(nir - blue) / (nir - red + 1e-10)",
        "required_bands": ["nir", "blue", "red"],
        "value_range": [0.0, 3.0],
        "category": "vegetation",
        "description": "Sensível à razão entre carotenóides e clorofila. Indica estresse e senescência da vegetação.",
        "reference": "Peñuelas et al. (1995)",
        "applications": ["estresse vegetativo", "senescência", "saúde da vegetação"],
    },
    "CRI1": {
        "full_name": "Carotenoid Reflectance Index 1",
        "formula": "(1/BLUE) - (1/GREEN)",
        "formula_python": "(1.0/(blue + 1e-10)) - (1.0/(green + 1e-10))",
        "required_bands": ["blue", "green"],
        "value_range": [-10.0, 10.0],
        "category": "vegetation",
        "description": "Estima concentração de carotenóides. Indicador de estado fisiológico e estresse.",
        "reference": "Gitelson et al. (2002)",
        "applications": ["concentração de carotenóides", "maturação foliar", "estresse ambiental"],
    },
}

# Mapeamento de aplicações para índices recomendados
_APPLICATION_MAP: dict[str, list[str]] = {
    "vegetacao": ["NDVI", "EVI", "EVI2", "SAVI", "GNDVI", "NDMI"],
    "vegetation": ["NDVI", "EVI", "EVI2", "SAVI", "GNDVI", "NDMI"],
    "agua": ["NDWI", "MNDWI"],
    "water": ["NDWI", "MNDWI"],
    "fogo": ["NBR", "NBR2", "BAI", "MIRBI"],
    "fire": ["NBR", "NBR2", "BAI", "MIRBI"],
    "queimada": ["NBR", "NBR2", "BAI", "MIRBI"],
    "burn": ["NBR", "NBR2", "BAI", "MIRBI"],
    "solo": ["BSI", "SAVI", "MSAVI2", "CMRI"],
    "soil": ["BSI", "SAVI", "MSAVI2", "CMRI"],
    "urbano": ["NDBI", "BSI"],
    "urban": ["NDBI", "BSI"],
    "neve": ["NDSI"],
    "snow": ["NDSI"],
    "desmatamento": ["NDVI", "EVI", "NBR", "NDMI"],
    "deforestation": ["NDVI", "EVI", "NBR", "NDMI"],
    "seca": ["NDMI", "NDVI", "SAVI"],
    "drought": ["NDMI", "NDVI", "SAVI"],
    "agricultura": ["NDVI", "EVI", "EVI2", "GNDVI", "SAVI"],
    "agriculture": ["NDVI", "EVI", "EVI2", "GNDVI", "SAVI"],
    "cerrado": ["NDVI", "EVI2", "SAVI", "MIRBI", "NBR"],
    "amazonia": ["NDVI", "EVI", "NDMI", "NBR"],
    "pastagem": ["NDVI", "EVI2", "SAVI", "MSAVI2"],
    "pasture": ["NDVI", "EVI2", "SAVI", "MSAVI2"],
}

# Bandas que quando presentes indicam índice pré-calculado
_PRECOMPUTED_INDICES = {"NDVI", "EVI", "EVI2", "SAVI", "NBRT"}


def list_spectral_indices(category: str | None = None) -> list[dict[str, Any]]:
    """Lista todos os índices espectrais disponíveis.

    Args:
        category: Filtro por categoria — "vegetation", "water", "soil", "burn", "snow", "urban".
    """
    results: list[dict[str, Any]] = []
    for name, data in _SPECTRAL_INDICES.items():
        if category and data["category"] != category.lower():
            continue
        idx = SpectralIndex(name=name, **data)
        results.append(idx.model_dump())
    return results


def get_spectral_index_info(index_name: str) -> dict[str, Any]:
    """Retorna detalhes completos de um índice espectral.

    Args:
        index_name: Nome do índice (ex: "NDVI", "EVI", "NBR").
    """
    key = index_name.upper()
    data = _SPECTRAL_INDICES.get(key)
    if data is None:
        return {
            "error": f"Índice '{index_name}' não encontrado.",
            "available_indices": sorted(_SPECTRAL_INDICES.keys()),
        }
    return SpectralIndex(name=key, **data).model_dump()


def get_collection_index_availability(collection_id: str) -> dict[str, Any]:
    """Verifica quais índices espectrais podem ser calculados a partir de uma coleção.

    Args:
        collection_id: ID da coleção STAC.
    """
    # Obter mapeamento de bandas
    band_map = COLLECTION_BAND_MAPPING.get(collection_id, {})

    # Se não temos mapeamento estático, tentar extrair dinamicamente
    if not band_map:
        try:
            client = BDCClient.get_instance()
            data = client.get_collection(collection_id)
            from .collections import _extract_bands
            bands = _extract_bands(data)
            # Criar mapeamento inferido a partir dos nomes das bandas
            for b in bands:
                bl = b.lower()
                if bl in ("red", "green", "blue", "nir", "swir16", "swir22"):
                    band_map[bl] = b
                elif bl in ("ndvi", "evi", "evi2", "savi"):
                    band_map[bl] = b
        except Exception:
            pass

    available_common = set(band_map.keys())

    precomputed: list[str] = []
    computable: list[str] = []
    missing_for: dict[str, list[str]] = {}

    for name, data in _SPECTRAL_INDICES.items():
        # Verificar se é pré-calculado
        if name.lower() in available_common and name in _PRECOMPUTED_INDICES:
            precomputed.append(name)
            continue

        required = set(data["required_bands"])
        missing = required - available_common
        if not missing:
            computable.append(name)
        else:
            missing_for[name] = sorted(missing)

    # Obter título
    known = ALL_COLLECTIONS.get(collection_id, {})
    title = ""
    try:
        client = BDCClient.get_instance()
        coll = client.get_collection(collection_id)
        title = coll.get("title", "")
    except Exception:
        pass

    return IndexAvailability(
        collection_id=collection_id,
        collection_title=title,
        precomputed_indices=sorted(precomputed),
        computable_indices=sorted(computable),
        missing_bands_for=missing_for,
        band_mapping=band_map,
    ).model_dump()


def generate_index_code(
    index_name: str,
    collection_id: str,
    language: str = "python",
) -> dict[str, Any]:
    """Gera código para calcular um índice espectral a partir de uma coleção BDC.

    Args:
        index_name: Nome do índice (ex: "NDVI", "EVI").
        collection_id: ID da coleção STAC.
        language: Linguagem — "python", "r" ou "sits".
    """
    key = index_name.upper()
    data = _SPECTRAL_INDICES.get(key)
    if data is None:
        return {"error": f"Índice '{index_name}' não encontrado.", "available": sorted(_SPECTRAL_INDICES.keys())}

    band_map = COLLECTION_BAND_MAPPING.get(collection_id, {})

    # Verificar se é pré-calculado
    is_precomputed = key.lower() in band_map and key in _PRECOMPUTED_INDICES
    precomputed_key = band_map.get(key.lower()) if is_precomputed else None

    # Mapear bandas requeridas para a coleção
    mapped: dict[str, str] = {}
    for req in data["required_bands"]:
        if req in band_map:
            mapped[req] = band_map[req]

    python_snippet = _generate_python_index(key, data, collection_id, mapped, is_precomputed, precomputed_key)
    r_snippet = _generate_r_index(key, data, collection_id, mapped, is_precomputed, precomputed_key)
    sits_snippet = _generate_sits_index(key, data, collection_id, mapped) if not is_precomputed else None

    notes = ""
    if is_precomputed:
        notes = f"O índice {key} já está pré-calculado na coleção {collection_id} como banda '{precomputed_key}'. Basta acessar diretamente."
    elif len(mapped) < len(data["required_bands"]):
        missing = set(data["required_bands"]) - set(mapped.keys())
        notes = f"Atenção: bandas {sorted(missing)} não mapeadas para {collection_id}. Verifique os nomes das bandas com get_collection_bands()."

    return IndexComputeGuide(
        index_name=key,
        collection_id=collection_id,
        is_precomputed=is_precomputed,
        precomputed_band_key=precomputed_key,
        formula=data["formula"],
        band_mapping=mapped,
        python_snippet=python_snippet,
        r_snippet=r_snippet,
        sits_snippet=sits_snippet,
        notes=notes,
    ).model_dump()


def suggest_indices_for_application(application: str) -> list[dict[str, Any]]:
    """Sugere índices espectrais para uma aplicação de sensoriamento remoto.

    Args:
        application: Tipo de aplicação (ex: "vegetacao", "fogo", "agua", "desmatamento", "agricultura").
    """
    app_lower = application.lower()

    # Buscar correspondência direta ou por substring
    matched_names: list[str] = []
    for key, indices in _APPLICATION_MAP.items():
        if key in app_lower or app_lower in key:
            for idx in indices:
                if idx not in matched_names:
                    matched_names.append(idx)

    if not matched_names:
        return [{
            "error": f"Aplicação '{application}' não reconhecida.",
            "available_applications": sorted(set(_APPLICATION_MAP.keys())),
        }]

    results: list[dict[str, Any]] = []
    for name in matched_names:
        data = _SPECTRAL_INDICES.get(name)
        if data:
            idx = SpectralIndex(name=name, **data)
            results.append(idx.model_dump())

    return results


# ------------------------------------------------------------------ #
# Helpers de geração de código
# ------------------------------------------------------------------ #

def _generate_python_index(
    name: str, data: dict, collection_id: str,
    mapped: dict[str, str], is_precomputed: bool, precomputed_key: str | None,
) -> str:
    if is_precomputed:
        return f'''import rasterio

# {name} já pré-calculado na coleção {collection_id}
# Acesse diretamente o asset "{precomputed_key}"
url = item.assets["{precomputed_key}"].href
with rasterio.open(url) as src:
    {name.lower()} = src.read(1).astype("float32")
    print(f"{name} shape: {{{name.lower()}.shape}}, range: [{{{name.lower()}.min():.3f}}, {{{name.lower()}.max():.3f}}]")
'''

    reads = []
    for req, band_key in mapped.items():
        reads.append(f'    {req} = src_{req}.read(1).astype("float32")')

    opens = "\n".join(
        f'with rasterio.open(item.assets["{bk}"].href) as src_{req}:'
        for req, bk in mapped.items()
    )

    return f'''import rasterio
import numpy as np

# Calcular {name} para coleção {collection_id}
# Fórmula: {data["formula"]}

{opens}
{chr(10).join(reads)}

# Aplicar fórmula
{name.lower()} = {data["formula_python"]}
{name.lower()} = np.clip({name.lower()}, {data["value_range"][0]}, {data["value_range"][1]})
print(f"{name} calculado: shape={{{name.lower()}.shape}}")
'''


def _generate_r_index(
    name: str, data: dict, collection_id: str,
    mapped: dict[str, str], is_precomputed: bool, precomputed_key: str | None,
) -> str:
    if is_precomputed:
        return f'''library(terra)

# {name} já pré-calculado — acessar asset "{precomputed_key}"
{name.lower()} <- rast(item_assets[["{precomputed_key}"]]$href)
plot({name.lower()}, main = "{name} - {collection_id}")
'''

    reads = "\n".join(
        f'{req} <- rast(item_assets[["{bk}"]]$href)'
        for req, bk in mapped.items()
    )

    formula_r = data["formula"].replace("*", " * ").replace("/", " / ")

    return f'''library(terra)

# Calcular {name} para coleção {collection_id}
{reads}

{name.lower()} <- {formula_r}
plot({name.lower()}, main = "{name} - {collection_id}")
'''


def _generate_sits_index(
    name: str, data: dict, collection_id: str, mapped: dict[str, str],
) -> str:
    band_refs = ", ".join(f'"{bk}"' for bk in mapped.values())
    formula_sits = data["formula_python"].replace("np.", "")

    return f'''library(sits)

# Calcular {name} via sits_apply
cube <- sits_cube(
  source = "BDC",
  collection = "{collection_id}",
  bands = c({band_refs}),
  # ... parâmetros de região e período
)

cube_{name.lower()} <- sits_apply(
  data = cube,
  {name} = {formula_sits},
  output_dir = "./output/"
)
'''
