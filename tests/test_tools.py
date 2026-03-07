"""Testes das ferramentas (tools) com API mockada."""

from __future__ import annotations

from inpe_bdc_mcp.tools.biomes import _infer_category, get_biome_bbox
from inpe_bdc_mcp.utils.brazil import BRAZIL_REGIONS


class TestBiomeBbox:
    def test_known_biome(self):
        result = get_biome_bbox("cerrado")
        assert "bbox" in result
        assert len(result["bbox"]) == 4
        assert result["crs"] == "EPSG:4326 (WGS84)"

    def test_unknown_biome(self):
        result = get_biome_bbox("atlantida")
        assert "error" in result
        assert "available_regions" in result

    def test_all_biomes_resolve(self):
        for name in BRAZIL_REGIONS:
            result = get_biome_bbox(name)
            assert "bbox" in result, f"Falha para '{name}'"


class TestInferCategory:
    def test_land_cover(self):
        assert _infer_category("LCC_L8_30_16D_STK_Cerrado-1", {}) == "land_cover"

    def test_mosaic_from_id(self):
        assert _infer_category("mosaic-landsat-brazil-6m-1", {}) == "mosaic"

    def test_mosaic_from_title(self):
        assert _infer_category("xyz-1", {"title": "Landsat Mosaic"}) == "mosaic"

    def test_data_cube(self):
        assert _infer_category("LANDSAT-16D-1", {"title": "Cube"}) == "data_cube"

    def test_data_cube_from_period(self):
        assert _infer_category("CBERS-WFI-8D-1", {}) == "data_cube"

    def test_modis(self):
        assert _infer_category("mod13q1-6.1", {}) == "modis"

    def test_weather(self):
        assert _infer_category("GOES19-L2-CMI-1", {}) == "weather"

    def test_raw_image(self):
        assert _infer_category("CB4-WFI-L4-SR-1", {}) == "raw_image"

    def test_sentinel_l2a(self):
        assert _infer_category("S2_L2A-1", {}) == "raw_image"

    def test_unknown_returns_none(self):
        assert _infer_category("xyz-unknown-1", {"title": "Something"}) is None
