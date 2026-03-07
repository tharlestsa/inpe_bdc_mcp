"""Fixtures compartilhadas para testes do inpe-bdc-mcp."""

from __future__ import annotations

from typing import Any

import pytest
import respx
from httpx import Response

from inpe_bdc_mcp.client import BASE_URL, BDCClient
from inpe_bdc_mcp.utils.cache import cache
from inpe_bdc_mcp.utils.metrics import metrics


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reseta singleton e cache antes/depois de cada teste."""
    BDCClient.reset_instance()
    cache.clear()
    metrics.reset()
    yield
    BDCClient.reset_instance()
    cache.clear()
    metrics.reset()


@pytest.fixture
def client() -> BDCClient:
    """Retorna instância limpa do BDCClient."""
    return BDCClient.get_instance()


# ------------------------------------------------------------------ #
# Dados fake de resposta da API
# ------------------------------------------------------------------ #

_BASE = BASE_URL.rstrip("/")


def _url(path: str) -> str:
    """Constrói URL completa para matching do respx."""
    if path:
        return f"{_BASE}/{path}"
    return f"{_BASE}/"


FAKE_CATALOG = {
    "id": "INPE",
    "title": "INPE STAC Server",
    "description": "Catálogo de teste",
    "stac_version": "1.0.0",
    "type": "Catalog",
    "links": [
        {"rel": "self", "href": _url("")},
        {"rel": "conformance", "href": _url("conformance")},
        {"rel": "data", "href": _url("collections")},
        {"rel": "search", "href": _url("search")},
    ],
}

FAKE_CONFORMANCE = {
    "conformsTo": [
        "https://api.stacspec.org/v1.0.0/core",
        "https://api.stacspec.org/v1.0.0/item-search",
        "https://api.stacspec.org/v1.0.0/item-search#fields",
        "https://api.stacspec.org/v1.0.0/item-search#sort",
        "https://api.stacspec.org/v1.0.0/item-search#filter",
    ],
}


def make_fake_collection(cid: str, title: str = "", **extra: Any) -> dict[str, Any]:
    """Cria uma coleção STAC fake para testes."""
    return {
        "id": cid,
        "title": title or f"Test Collection {cid}",
        "description": f"Descrição de teste para {cid}",
        "license": "CC-BY-4.0",
        "stac_version": "1.0.0",
        "extent": {
            "spatial": {"bbox": [[-73.9, -33.8, -34.8, 5.3]]},
            "temporal": {"interval": [["2020-01-01T00:00:00Z", None]]},
        },
        "links": [],
        **extra,
    }


def make_fake_item(item_id: str, collection_id: str) -> dict[str, Any]:
    """Cria um item STAC fake para testes."""
    return {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": item_id,
        "collection": collection_id,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]],
        },
        "bbox": [-50, -15, -49, -14],
        "properties": {
            "datetime": "2023-06-15T10:00:00Z",
            "eo:cloud_cover": 12.5,
            "platform": "CBERS-4",
            "bdc:tile": "007004",
        },
        "assets": {
            "thumbnail": {
                "href": f"https://example.com/{item_id}/thumb.png",
                "type": "image/png",
                "roles": ["thumbnail"],
            },
            "NDVI": {
                "href": f"https://example.com/{item_id}/NDVI.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "roles": ["data"],
                "title": "NDVI",
            },
        },
        "links": [],
    }


FAKE_COLLECTIONS = [
    make_fake_collection("S2_L2A-1", "Sentinel-2 - Level-2A"),
    make_fake_collection("LANDSAT-16D-1", "Landsat - 16 Day Cube"),
    make_fake_collection("CBERS4-WFI-16D-2", "CBERS-4 WFI 16 Day Cube"),
]

FAKE_COLLECTIONS_RESPONSE = {
    "collections": FAKE_COLLECTIONS,
    "links": [],
}


@pytest.fixture
def mock_stac_api():
    """Mocka todas as rotas da STAC API com respx."""
    with respx.mock(assert_all_called=False) as router:
        router.get(url=_url("")).mock(return_value=Response(200, json=FAKE_CATALOG))
        router.get(url=_url("conformance")).mock(
            return_value=Response(200, json=FAKE_CONFORMANCE)
        )
        router.get(url=_url("collections")).mock(
            return_value=Response(200, json=FAKE_COLLECTIONS_RESPONSE)
        )

        for coll in FAKE_COLLECTIONS:
            cid = coll["id"]
            router.get(url=_url(f"collections/{cid}")).mock(
                return_value=Response(200, json=coll)
            )
            fake_item = make_fake_item(f"{cid}-item-001", cid)
            router.get(url=_url(f"collections/{cid}/items/{cid}-item-001")).mock(
                return_value=Response(200, json=fake_item)
            )

        router.post(url=_url("search")).mock(
            return_value=Response(200, json={
                "type": "FeatureCollection",
                "features": [make_fake_item("search-001", "S2_L2A-1")],
                "links": [],
                "numberMatched": 1,
                "numberReturned": 1,
            })
        )

        yield router
