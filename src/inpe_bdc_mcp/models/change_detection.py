"""Modelos Pydantic para detecção de mudanças e fenologia."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .classification import WorkflowStep


class ChangeDetectionPlan(BaseModel):
    method: str = ""
    description: str = ""
    applicable_scenarios: list[str] = Field(default_factory=list)
    required_data: str = ""
    recommended_collection: str = ""
    steps: list[WorkflowStep] = Field(default_factory=list)
    python_snippet: str = ""
    r_snippet: str = ""
    interpretation_guide: str = ""
    limitations: list[str] = Field(default_factory=list)


class PhenologyPlan(BaseModel):
    collection_id: str
    region: str = ""
    metrics: list[str] = Field(default_factory=list)
    temporal_resolution_days: int = 0
    filtering_method: str = ""
    python_snippet: str = ""
    r_snippet: str = ""
    sits_snippet: str = ""
    interpretation_guide: str = ""
