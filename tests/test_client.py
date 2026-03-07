"""Testes do BDCClient com API mockada."""

from __future__ import annotations

import pytest

from inpe_bdc_mcp.client import BDCClient
from inpe_bdc_mcp.utils.metrics import metrics


class TestBDCClientSingleton:
    def test_get_instance_returns_same(self):
        a = BDCClient.get_instance()
        b = BDCClient.get_instance()
        assert a is b

    def test_reset_instance_creates_new(self):
        a = BDCClient.get_instance()
        BDCClient.reset_instance()
        b = BDCClient.get_instance()
        assert a is not b

    def test_reset_instance_when_none(self):
        BDCClient.reset_instance()
        BDCClient.reset_instance()  # Não deve falhar


class TestBDCClientAPI:
    def test_get_catalog_info(self, mock_stac_api, client):
        info = client.get_catalog_info()
        assert info["id"] == "INPE"
        assert info["stac_version"] == "1.0.0"

    def test_get_catalog_info_cached(self, mock_stac_api, client):
        client.get_catalog_info()
        client.get_catalog_info()
        # Verifica via métricas: apenas 1 chamada real (segunda usa cache)
        snap = metrics.snapshot()
        assert snap["get_catalog_info"]["calls"] == 1

    def test_get_conformance(self, mock_stac_api, client):
        classes = client.get_conformance()
        assert len(classes) == 5
        assert any("core" in c for c in classes)

    def test_list_collections(self, mock_stac_api, client):
        colls = client.list_collections()
        assert len(colls) == 3
        ids = [c["id"] for c in colls]
        assert "S2_L2A-1" in ids

    def test_get_collection(self, mock_stac_api, client):
        data = client.get_collection("S2_L2A-1")
        assert data["id"] == "S2_L2A-1"

    def test_get_item(self, mock_stac_api, client):
        data = client.get_item("S2_L2A-1", "S2_L2A-1-item-001")
        assert data["id"] == "S2_L2A-1-item-001"
        assert data["collection"] == "S2_L2A-1"

    def test_get_item_not_found(self, mock_stac_api, client):
        from tests.conftest import _url
        from httpx import Response

        mock_stac_api.get(url=_url("collections/S2_L2A-1/items/inexistente")).mock(
            return_value=Response(404, json={"code": "NotFound"})
        )

        import httpx
        with pytest.raises(httpx.HTTPStatusError):
            client.get_item("S2_L2A-1", "inexistente")

    def test_metrics_recorded(self, mock_stac_api, client):
        client.get_catalog_info()
        client.get_conformance()
        snap = metrics.snapshot()
        assert "get_catalog_info" in snap
        assert "get_conformance" in snap
        assert snap["get_catalog_info"]["calls"] == 1


class TestSearchPostRawValidation:
    def test_valid_body(self, mock_stac_api, client):
        result = client.search_post_raw({
            "collections": ["S2_L2A-1"],
            "limit": 10,
        })
        assert "features" in result

    def test_invalid_body_type(self, client):
        with pytest.raises(ValueError, match="dicionário JSON"):
            client.search_post_raw("invalid")  # type: ignore

    def test_unknown_fields(self, client):
        with pytest.raises(ValueError, match="Campos desconhecidos"):
            client.search_post_raw({"collections": [], "foo": "bar"})

    def test_bbox_and_intersects_conflict(self, client):
        with pytest.raises(ValueError, match="simultaneamente"):
            client.search_post_raw({
                "bbox": [-50, -15, -49, -14],
                "intersects": {"type": "Point", "coordinates": [-50, -15]},
            })

    def test_invalid_bbox_format(self, client):
        with pytest.raises(ValueError, match="4 ou 6"):
            client.search_post_raw({"bbox": [-50, -15]})

    def test_invalid_limit(self, client):
        with pytest.raises(ValueError, match="entre 1 e 10000"):
            client.search_post_raw({"limit": -1})
