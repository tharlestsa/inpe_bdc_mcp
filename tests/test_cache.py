"""Testes do TTLCache — invalidação, TTL, namespace e sentinel."""

from __future__ import annotations

import time

from inpe_bdc_mcp.utils.cache import TTLCache, _MISSING


class TestTTLCache:
    def test_get_miss_returns_sentinel(self):
        c = TTLCache()
        assert c.get("inexistente") is _MISSING

    def test_set_and_get(self):
        c = TTLCache()
        c.set("ns", {"key": "value"})
        assert c.get("ns") == {"key": "value"}

    def test_set_with_params(self):
        c = TTLCache()
        c.set("ns", "v1", params={"id": "a"})
        c.set("ns", "v2", params={"id": "b"})
        assert c.get("ns", params={"id": "a"}) == "v1"
        assert c.get("ns", params={"id": "b"}) == "v2"

    def test_cache_falsy_values(self):
        """Cache deve armazenar corretamente valores falsy ([], {}, 0, '')."""
        c = TTLCache()
        c.set("empty_list", [])
        c.set("empty_dict", {})
        c.set("zero", 0)
        c.set("empty_str", "")

        assert c.get("empty_list") == []
        assert c.get("empty_dict") == {}
        assert c.get("zero") == 0
        assert c.get("empty_str") == ""

    def test_ttl_expiration(self):
        c = TTLCache()
        c.set("short", "value", ttl=0)
        # TTL=0 expira imediatamente pois monotonic() avança
        time.sleep(0.01)
        assert c.get("short") is _MISSING

    def test_invalidate_specific_entry(self):
        c = TTLCache()
        c.set("ns", "v1", params={"id": "a"})
        c.set("ns", "v2", params={"id": "b"})

        c.invalidate("ns", params={"id": "a"})
        assert c.get("ns", params={"id": "a"}) is _MISSING
        assert c.get("ns", params={"id": "b"}) == "v2"

    def test_invalidate_namespace(self):
        c = TTLCache()
        c.set("collection", "v1", params={"id": "a"})
        c.set("collection", "v2", params={"id": "b"})
        c.set("other", "keep")

        removed = c.invalidate_namespace("collection")
        assert removed == 2
        assert c.get("collection", params={"id": "a"}) is _MISSING
        assert c.get("collection", params={"id": "b"}) is _MISSING
        assert c.get("other") == "keep"

    def test_invalidate_namespace_without_params(self):
        c = TTLCache()
        c.set("catalog_info", {"data": True})
        removed = c.invalidate_namespace("catalog_info")
        assert removed == 1
        assert c.get("catalog_info") is _MISSING

    def test_clear(self):
        c = TTLCache()
        c.set("a", 1)
        c.set("b", 2)
        c.clear()
        assert c.get("a") is _MISSING
        assert c.get("b") is _MISSING
