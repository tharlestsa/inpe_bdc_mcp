"""Testes unitários para o módulo tools/classification.py."""

from __future__ import annotations

from inpe_bdc_mcp.tools.classification import (
    generate_sits_classification_code,
    get_accuracy_assessment_guide,
    get_ml_algorithm_guide,
    get_sample_design_guide,
    plan_classification_workflow,
)


class TestPlanClassificationWorkflow:
    def test_basic_workflow(self):
        result = plan_classification_workflow(
            region="Cerrado",
            start_year=2020,
            end_year=2022,
        )
        assert "workflow_name" in result
        assert result["target_region"] == "Cerrado"
        assert result["target_period"] == "2020-2022"
        assert len(result["steps"]) == 9
        assert "sits_r_code" in result
        assert "python_code" in result

    def test_custom_bbox(self):
        result = plan_classification_workflow(
            region=[-50.0, -15.0, -49.0, -14.0],
        )
        assert result["target_region"] == "custom"

    def test_custom_classes(self):
        classes = ["Forest", "Water"]
        result = plan_classification_workflow(
            region="Amazônia",
            classes=classes,
        )
        assert "Forest" in result["notes"]
        assert "Water" in result["notes"]
        assert result["estimated_complexity"] == "medium"

    def test_many_classes_high_complexity(self):
        classes = ["A", "B", "C", "D", "E", "F"]
        result = plan_classification_workflow(region="Cerrado", classes=classes)
        assert result["estimated_complexity"] == "high"

    def test_xgboost_algorithm(self):
        result = plan_classification_workflow(
            region="Cerrado",
            algorithm="xgboost",
        )
        assert "XGBoost" in result["notes"]
        assert "sits_xgboost" in result["sits_r_code"]


class TestGetSampleDesignGuide:
    def test_basic_guide(self):
        result = get_sample_design_guide(
            region="Cerrado",
            classes=["Forest", "Pasture", "Agriculture"],
        )
        assert result["strategy"] == "stratified"
        assert result["minimum_samples_per_class"] >= 50
        assert "sits_snippet" in result
        assert "python_snippet" in result

    def test_custom_total_samples(self):
        result = get_sample_design_guide(
            region="Amazônia",
            classes=["Forest", "Water"],
            total_samples=200,
        )
        assert result["minimum_samples_per_class"] >= 50

    def test_default_total(self):
        result = get_sample_design_guide(
            region="Cerrado",
            classes=["A", "B", "C", "D", "E", "F"],
        )
        assert result["minimum_samples_per_class"] == 50


class TestGetMLAlgorithmGuide:
    def test_all_algorithms(self):
        result = get_ml_algorithm_guide()
        assert len(result["algorithms"]) == 5
        names = [a["name"] for a in result["algorithms"]]
        assert "Random Forest" in names
        assert any("XGBoost" in n for n in names)

    def test_few_samples_recommendation(self):
        result = get_ml_algorithm_guide(use_case="few_samples")
        assert "SVM" in result["recommendation"]

    def test_high_accuracy_recommendation(self):
        result = get_ml_algorithm_guide(use_case="high_accuracy")
        assert "XGBoost" in result["recommendation"] or "TempCNN" in result["recommendation"]

    def test_fast_recommendation(self):
        result = get_ml_algorithm_guide(use_case="fast")
        assert "LightGBM" in result["recommendation"]


class TestGetAccuracyAssessmentGuide:
    def test_default(self):
        result = get_accuracy_assessment_guide()
        assert len(result["metrics"]) > 0
        assert "Overall Accuracy" in result["metrics"][0]
        assert "python_snippet" in result
        assert "sits_snippet" in result

    def test_custom_n_classes(self):
        result = get_accuracy_assessment_guide(n_classes=10)
        assert "500" in result["validation_strategy"]  # 50 * 10


class TestGenerateSitsClassificationCode:
    def test_basic_code(self):
        code = generate_sits_classification_code(
            collection_id="LANDSAT-16D-1",
            region="Cerrado",
        )
        assert "sits_cube" in code
        assert "LANDSAT-16D-1" in code
        assert "sits_classify" in code
        assert "sits_smooth" in code

    def test_custom_algorithm(self):
        code = generate_sits_classification_code(
            collection_id="LANDSAT-16D-1",
            region="Amazônia",
            algorithm="xgboost",
        )
        assert "sits_xgboost" in code

    def test_deep_learning_uses_tempcnn(self):
        code = generate_sits_classification_code(
            collection_id="LANDSAT-16D-1",
            region="Cerrado",
            algorithm="deep_learning",
        )
        assert "sits_tempcnn" in code

    def test_custom_years(self):
        code = generate_sits_classification_code(
            collection_id="LANDSAT-16D-1",
            region="Cerrado",
            start_year=2018,
            end_year=2020,
        )
        assert "2018-01-01" in code
        assert "2020-12-31" in code
