"""Modelos Pydantic para workflows de classificação LULC inspirados no SITS."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    step_number: int
    name: str
    description: str = ""
    sits_function: str | None = None
    python_equivalent: str | None = None


class MLAlgorithmInfo(BaseModel):
    name: str
    sits_function: str = ""
    sklearn_class: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    best_for: str = ""
    hyperparameters: dict[str, str] = Field(default_factory=dict)


class MLAlgorithmGuide(BaseModel):
    algorithms: list[MLAlgorithmInfo] = Field(default_factory=list)
    recommendation: str = ""
    comparison_notes: str = ""


class SampleDesignGuide(BaseModel):
    strategy: str = "stratified"
    minimum_samples_per_class: int = 50
    recommended_classes: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    sits_snippet: str = ""
    python_snippet: str = ""


class AccuracyAssessmentGuide(BaseModel):
    metrics: list[str] = Field(default_factory=list)
    validation_strategy: str = ""
    python_snippet: str = ""
    sits_snippet: str = ""


class PostProcessingGuide(BaseModel):
    methods: list[str] = Field(default_factory=list)
    sits_snippet: str = ""
    python_snippet: str = ""
    description: str = ""


class ClassificationPlan(BaseModel):
    workflow_name: str = ""
    target_region: str = ""
    target_period: str = ""
    recommended_collection: str = ""
    steps: list[WorkflowStep] = Field(default_factory=list)
    sits_r_code: str = ""
    python_code: str = ""
    sample_design: SampleDesignGuide | None = None
    ml_algorithm_guide: MLAlgorithmGuide | None = None
    accuracy_assessment: AccuracyAssessmentGuide | None = None
    post_processing: PostProcessingGuide | None = None
    estimated_complexity: str = "medium"
    notes: str = ""
