"""Testes unitários para o módulo tools/timeseries.py."""

from __future__ import annotations

from typing import Any

import pytest
import respx
from httpx import Response

from inpe_bdc_mcp.client import BASE_URL, BDCClient
from inpe_bdc_mcp.tools.timeseries import (
    analyze_temporal_gaps,
    generate_sits_cube_code,
    get_filtering_guide,
    plan_phenology_extraction,
    plan_time_series_extraction,
)

_BASE = BASE_URL.rstrip("/")


class TestPlanTimeSeriesExtraction:
    def test_basic_plan(self):
        result = plan_time_series_extraction(
            collection_id="LANDSAT-16D-1",
            bbox_or_biome="Cerrado",
            start_year=2020,
            end_year=2022,
        )
        assert result["collection_id"] == "LANDSAT-16D-1"
        assert result["is_data_cube"] is True
        assert "sits_code" in result
        assert "python_code" in result
        assert result["expected_items"] > 0

    def test_custom_bbox(self):
        result = plan_time_series_extraction(
            collection_id="LANDSAT-16D-1",
            bbox_or_biome=[-50.0, -15.0, -49.0, -14.0],
            start_year=2021,
            end_year=2021,
            bands=["NDVI", "EVI"],
        )
        assert result["region"] == "custom"
        assert result["bbox"] == [-50.0, -15.0, -49.0, -14.0]
        assert "NDVI" in result["bands"]

    def test_default_region(self):
        result = plan_time_series_extraction(
            collection_id="LANDSAT-16D-1",
        )
        assert result["region"] == "Goiás (padrão)"

    def test_sits_code_contains_collection(self):
        result = plan_time_series_extraction(
            collection_id="LANDSAT-16D-1",
            bbox_or_biome="Amazônia",
        )
        assert "LANDSAT-16D-1" in result["sits_code"]
        assert "sits_cube" in result["sits_code"]


class TestGetFilteringGuide:
    def test_list_all(self):
        result = get_filtering_guide()
        assert isinstance(result, list)
        assert len(result) == 3
        methods = [r["method"] for r in result]
        assert "savitzky_golay" in methods
        assert "whittaker" in methods

    def test_specific_method(self):
        result = get_filtering_guide("savitzky_golay")
        assert result["method"] == "savitzky_golay"
        assert "python" in result
        assert "r" in result
        assert "sits" in result

    def test_whittaker(self):
        result = get_filtering_guide("whittaker")
        assert result["method"] == "whittaker"
        assert "lambda" in result["parameters"]

    def test_unknown_method(self):
        result = get_filtering_guide("unknown_filter")
        assert "error" in result
        assert "available" in result


class TestPlanPhenologyExtraction:
    def test_basic_plan(self):
        result = plan_phenology_extraction(
            collection_id="LANDSAT-16D-1",
            bbox_or_biome="Cerrado",
        )
        assert result["collection_id"] == "LANDSAT-16D-1"
        assert "SOS" in result["metrics"][0]
        assert result["temporal_resolution_days"] == 16
        assert "python_snippet" in result
        assert "sits_snippet" in result

    def test_bimonthly_collection(self):
        result = plan_phenology_extraction(
            collection_id="landsat-tsirf-bimonthly-1",
        )
        assert result["temporal_resolution_days"] == 60

    def test_custom_band(self):
        result = plan_phenology_extraction(
            collection_id="LANDSAT-16D-1",
            band="EVI",
        )
        assert "EVI" in result["python_snippet"]


class TestAnalyzeTemporalGaps:
    @respx.mock(assert_all_called=False)
    def test_with_features(self, respx_mock):
        """Testa analyze_temporal_gaps com mock de API retornando features."""
        features = [
            {
                "type": "Feature",
                "id": f"item-{i:03d}",
                "properties": {"datetime": f"2021-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T00:00:00Z"},
                "geometry": None,
                "assets": {},
            }
            for i in range(24)
        ]
        respx_mock.post(f"{_BASE}/search").mock(
            return_value=Response(200, json={
                "type": "FeatureCollection",
                "features": features,
                "links": [],
                "numberMatched": 24,
                "numberReturned": 24,
            })
        )

        result = analyze_temporal_gaps(
            collection_id="LANDSAT-16D-1",
            bbox_or_biome=[-50.0, -15.0, -49.0, -14.0],
            datetime_range="2021-01-01/2021-12-31",
        )
        assert result["collection_id"] == "LANDSAT-16D-1"
        assert result["total_items"] == 24
        assert "gap_statistics" in result
        assert "completeness_pct" in result

    @respx.mock(assert_all_called=False)
    def test_empty_result(self, respx_mock):
        """Testa analyze_temporal_gaps sem itens encontrados."""
        respx_mock.post(f"{_BASE}/search").mock(
            return_value=Response(200, json={
                "type": "FeatureCollection",
                "features": [],
                "links": [],
                "numberMatched": 0,
                "numberReturned": 0,
            })
        )

        result = analyze_temporal_gaps(
            collection_id="LANDSAT-16D-1",
            bbox_or_biome="Cerrado",
        )
        assert result["total_items"] == 0
        assert "note" in result


class TestGenerateSitsCubeCode:
    def test_basic_code(self):
        code = generate_sits_cube_code(
            collection_id="LANDSAT-16D-1",
            bbox_or_biome="Cerrado",
            start_year=2020,
            end_year=2023,
        )
        assert "sits_cube" in code
        assert "LANDSAT-16D-1" in code
        assert "2020-01-01" in code
        assert "2023-12-31" in code

    def test_custom_bands(self):
        code = generate_sits_cube_code(
            collection_id="LANDSAT-16D-1",
            bands=["NDVI", "RED", "NIR"],
        )
        assert "NDVI" in code

    def test_non_cube_collection_includes_regularize(self):
        code = generate_sits_cube_code(
            collection_id="S2_L2A-1",
        )
        assert "sits_regularize" in code or "regular" in code.lower()
