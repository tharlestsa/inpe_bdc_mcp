"""Modelos Pydantic para orientação de pré-processamento de imagens."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CloudMaskStrategy(BaseModel):
    collection_id: str
    mask_band: str | None = None
    mask_values: dict[str, list[int]] = Field(default_factory=dict)
    python_snippet: str = ""
    r_snippet: str = ""
    quality_assessment: str = ""
    recommendations: list[str] = Field(default_factory=list)


class PreprocessingGuide(BaseModel):
    collection_id: str
    processing_level: str = ""
    atmospheric_correction: str = ""
    geometric_correction: str = ""
    cloud_mask: CloudMaskStrategy | None = None
    radiometric_info: str = ""
    pan_sharpening_applicable: bool = False
    pan_sharpening_guide: str | None = None
    recommendations: list[str] = Field(default_factory=list)
