"""Bounding boxes de biomas, estados e regiões especiais do Brasil."""

from __future__ import annotations

BRAZIL_REGIONS: dict[str, list[float]] = {
    # Biomas
    "amazonia": [-73.9, -18.0, -44.0, 5.3],
    "cerrado": [-60.0, -24.7, -41.0, -2.3],
    "mata_atlantica": [-55.0, -33.8, -34.8, -5.0],
    "caatinga": [-45.0, -17.2, -34.8, -2.8],
    "pantanal": [-58.0, -22.0, -50.0, -15.0],
    "pampa": [-57.6, -33.8, -49.7, -28.1],
    # Estados
    "goias": [-53.2, -19.5, -45.9, -12.4],
    "mato_grosso": [-61.6, -18.0, -50.2, -7.3],
    "para": [-58.9, -10.0, -46.0, 2.6],
    "amazonas": [-73.9, -9.9, -56.1, 2.3],
    "mato_grosso_do_sul": [-58.2, -24.1, -50.9, -17.2],
    "minas_gerais": [-51.0, -22.9, -39.9, -14.2],
    "sao_paulo": [-53.1, -25.3, -44.2, -19.8],
    "bahia": [-46.6, -18.3, -37.3, -8.5],
    "maranhao": [-48.7, -10.3, -41.8, -1.0],
    "tocantins": [-50.7, -13.5, -45.7, -5.2],
    "rondonia": [-66.6, -13.7, -59.8, -7.6],
    "acre": [-73.9, -11.1, -66.6, -7.1],
    "roraima": [-64.8, 0.0, -58.9, 5.3],
    "amapa": [-54.9, -1.2, -49.9, 4.4],
    "paraiba": [-38.8, -8.3, -34.8, -6.0],
    # Regiões especiais
    "amazonia_legal": [-73.9, -18.0, -44.0, 5.3],
    "matopiba": [-47.5, -15.0, -40.0, -2.5],
    "arco_desmatamento": [-64.0, -15.0, -48.0, -5.0],
    "brasil": [-73.9, -33.8, -34.8, 5.3],
}

# Aliases comuns (acentos, variações)
_ALIASES: dict[str, str] = {
    "amazon": "amazonia",
    "amazônia": "amazonia",
    "atlantic_forest": "mata_atlantica",
    "mata atlantica": "mata_atlantica",
    "mata atlântica": "mata_atlantica",
    "goiás": "goias",
    "pará": "para",
    "são paulo": "sao_paulo",
    "sao paulo": "sao_paulo",
    "mato grosso": "mato_grosso",
    "mato grosso do sul": "mato_grosso_do_sul",
    "minas gerais": "minas_gerais",
    "maranhão": "maranhao",
    "rondônia": "rondonia",
    "amapá": "amapa",
    "paraíba": "paraiba",
    "brazil": "brasil",
}


def resolve_bbox(name: str) -> list[float] | None:
    """Resolve nome de região/bioma/estado para bbox WGS84."""
    key = name.strip().lower().replace("-", "_")
    key = _ALIASES.get(key, key)
    return BRAZIL_REGIONS.get(key)


def list_regions() -> dict[str, list[float]]:
    return dict(BRAZIL_REGIONS)
