"""Modelos Pydantic para índices espectrais e álgebra de bandas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SpectralIndex(BaseModel):
    name: str
    full_name: str
    formula: str
    formula_python: str
    required_bands: list[str]
    value_range: list[float] = Field(default_factory=lambda: [-1.0, 1.0])
    category: str = ""
    description: str = ""
    reference: str | None = None
    applications: list[str] = Field(default_factory=list)


class IndexAvailability(BaseModel):
    collection_id: str
    collection_title: str = ""
    precomputed_indices: list[str] = Field(default_factory=list)
    computable_indices: list[str] = Field(default_factory=list)
    missing_bands_for: dict[str, list[str]] = Field(default_factory=dict)
    band_mapping: dict[str, str] = Field(default_factory=dict)


class IndexComputeGuide(BaseModel):
    index_name: str
    collection_id: str
    is_precomputed: bool = False
    precomputed_band_key: str | None = None
    formula: str = ""
    band_mapping: dict[str, str] = Field(default_factory=dict)
    python_snippet: str = ""
    r_snippet: str = ""
    sits_snippet: str | None = None
    notes: str = ""
