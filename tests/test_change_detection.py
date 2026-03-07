"""Testes unitários para o módulo tools/change_detection.py."""

from __future__ import annotations

from inpe_bdc_mcp.tools.change_detection import (
    list_change_detection_methods,
    plan_change_detection,
    plan_deforestation_detection,
    plan_fire_scar_detection,
)


class TestListChangeDetectionMethods:
    def test_returns_4_methods(self):
        result = list_change_detection_methods()
        assert len(result) == 4

    def test_methods_have_required_fields(self):
        for m in list_change_detection_methods():
            assert "method" in m
            assert "name" in m
            assert "description" in m
            assert "applicable_scenarios" in m

    def test_bfast_present(self):
        methods = {m["method"] for m in list_change_detection_methods()}
        assert "bfast" in methods
        assert "dnbr" in methods
        assert "ndvi_anomaly" in methods
        assert "landtrendr" in methods


class TestPlanChangeDetection:
    def test_bfast(self):
        result = plan_change_detection(
            method="bfast",
            region="Amazônia",
            start_year=2018,
            end_year=2023,
        )
        assert "BFAST" in result["method"]
        assert len(result["steps"]) > 0
        assert result["python_snippet"] != ""
        assert result["r_snippet"] != ""

    def test_ndvi_anomaly(self):
        result = plan_change_detection(
            method="ndvi_anomaly",
            region="Cerrado",
        )
        assert "Anomalia" in result["method"]
        assert "climatologia" in result["python_snippet"].lower() or "zscore" in result["python_snippet"]

    def test_unknown_method_returns_error(self):
        result = plan_change_detection(
            method="unknown_method",
            region="Cerrado",
        )
        assert "error" in result

    def test_custom_bbox(self):
        result = plan_change_detection(
            method="dnbr",
            region=[-50.0, -15.0, -49.0, -14.0],
        )
        assert "dNBR" in result["method"]


class TestPlanFireScarDetection:
    def test_basic_fire(self):
        result = plan_fire_scar_detection(
            region="Cerrado",
            event_date="2023-08-15",
        )
        assert "dNBR" in result["method"]
        assert "Severidade" in result["interpretation_guide"] or "severidade" in result["interpretation_guide"]
        assert len(result["steps"]) == 6
        assert "python_snippet" in result
        assert "r_snippet" in result

    def test_january_event_year_boundary(self):
        """Evento em janeiro: janela pré-fogo deve cruzar fronteira de ano."""
        result = plan_fire_scar_detection(
            region="Amazônia",
            event_date="2023-01-15",
        )
        # Pré-fogo deve começar em 2022 (outubro)
        assert "2022" in result["steps"][0]["description"]

    def test_december_event_post_window(self):
        """Evento em dezembro: janela pós-fogo deve avançar ao ano seguinte."""
        result = plan_fire_scar_detection(
            region="Cerrado",
            event_date="2023-12-10",
        )
        # Pós-fogo deve ir até 2024
        assert "2024" in result["steps"][1]["description"]

    def test_custom_bbox_region(self):
        result = plan_fire_scar_detection(
            region=[-48.0, -16.0, -47.0, -15.0],
            event_date="2023-07-01",
        )
        assert result["recommended_collection"] == "LANDSAT-16D-1"


class TestPlanDeforestationDetection:
    def test_bfast_deforestation(self):
        result = plan_deforestation_detection(
            region="Amazônia",
            start_year=2018,
            end_year=2023,
            method="bfast",
        )
        assert "BFAST" in result["method"]
        assert "python_snippet" in result
        assert "bfast" in result["python_snippet"].lower() or "BFASTMonitor" in result["python_snippet"]

    def test_landtrendr_deforestation(self):
        result = plan_deforestation_detection(
            region="Cerrado",
            method="landtrendr",
        )
        assert "LANDTRENDR" in result["method"]

    def test_invalid_method_defaults_to_bfast(self):
        result = plan_deforestation_detection(
            region="Cerrado",
            method="invalid",
        )
        assert "BFAST" in result["method"]

    def test_steps_count(self):
        result = plan_deforestation_detection(region="Amazônia")
        assert len(result["steps"]) == 5
