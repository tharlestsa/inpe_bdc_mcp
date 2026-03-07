"""Testes unitários para o módulo tools/spectral.py."""

from __future__ import annotations

from inpe_bdc_mcp.tools.spectral import (
    generate_index_code,
    get_spectral_index_info,
    list_spectral_indices,
    suggest_indices_for_application,
)


class TestListSpectralIndices:
    def test_list_all_returns_20(self):
        result = list_spectral_indices()
        assert len(result) == 20

    def test_list_all_have_required_fields(self):
        for idx in list_spectral_indices():
            assert "name" in idx
            assert "formula" in idx
            assert "required_bands" in idx
            assert "category" in idx

    def test_filter_by_vegetation(self):
        result = list_spectral_indices(category="vegetation")
        assert len(result) > 0
        assert all(r["category"] == "vegetation" for r in result)

    def test_filter_by_water(self):
        result = list_spectral_indices(category="water")
        assert len(result) == 2  # NDWI, MNDWI

    def test_filter_by_burn(self):
        result = list_spectral_indices(category="burn")
        assert len(result) == 4  # NBR, NBR2, BAI, MIRBI

    def test_filter_invalid_category_returns_empty(self):
        result = list_spectral_indices(category="nonexistent")
        assert result == []


class TestGetSpectralIndexInfo:
    def test_ndvi(self):
        result = get_spectral_index_info("NDVI")
        assert result["name"] == "NDVI"
        assert "NIR" in result["formula"]
        assert "RED" in result["formula"]
        assert result["category"] == "vegetation"

    def test_case_insensitive(self):
        result = get_spectral_index_info("ndvi")
        assert result["name"] == "NDVI"

    def test_unknown_index(self):
        result = get_spectral_index_info("FAKE_INDEX")
        assert "error" in result
        assert "available_indices" in result

    def test_bai_non_standard_range(self):
        result = get_spectral_index_info("BAI")
        assert result["value_range"] == [0.0, 500.0]


class TestSuggestIndicesForApplication:
    def test_vegetacao(self):
        result = suggest_indices_for_application("vegetacao")
        names = [r["name"] for r in result]
        assert "NDVI" in names
        assert "EVI" in names

    def test_fogo(self):
        result = suggest_indices_for_application("fogo")
        names = [r["name"] for r in result]
        assert "NBR" in names
        assert "BAI" in names

    def test_agua(self):
        result = suggest_indices_for_application("agua")
        names = [r["name"] for r in result]
        assert "NDWI" in names

    def test_desmatamento(self):
        result = suggest_indices_for_application("desmatamento")
        names = [r["name"] for r in result]
        assert "NDVI" in names
        assert "NBR" in names

    def test_unknown_application(self):
        result = suggest_indices_for_application("xyz_invalid")
        assert "error" in result[0]


class TestGenerateIndexCode:
    def test_ndvi_python_for_landsat(self):
        result = generate_index_code("NDVI", "LANDSAT-16D-1", language="python")
        assert result["index_name"] == "NDVI"
        assert result["is_precomputed"] is True
        assert "python_snippet" in result

    def test_nbr_computable_for_landsat(self):
        result = generate_index_code("NBR", "LANDSAT-16D-1", language="python")
        assert result["index_name"] == "NBR"
        assert result["is_precomputed"] is False
        assert "r_snippet" in result

    def test_unknown_index_code(self):
        result = generate_index_code("FAKE", "LANDSAT-16D-1")
        assert "error" in result

    def test_sits_snippet_generated_for_computable(self):
        result = generate_index_code("NBR", "LANDSAT-16D-1", language="sits")
        assert result["sits_snippet"] is not None
        assert "sits_apply" in result["sits_snippet"]
