"""Modelos Pydantic para resultados de busca STAC."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .item import ItemSummary


class SearchResult(BaseModel):
    total_matched: int | None = None
    returned: int = 0
    items: list[ItemSummary] = Field(default_factory=list)
    next_page_token: str | None = None
    request_time_ms: float = 0.0


class DataCubeInfo(BaseModel):
    collection_id: str
    title: str = ""
    satellite: str = ""
    temporal_composition: str = ""
    composition_method: str = ""
    spatial_resolution_m: float = 0.0
    bdc_grid_version: str = ""
    available_bands: list[str] = Field(default_factory=list)
    derived_indices: list[str] = Field(default_factory=list)
    quality_bands: list[str] = Field(default_factory=list)
    temporal_extent_start: str | None = None
    temporal_extent_end: str | None = None
    tile_count: int | None = None


class QualityInfo(BaseModel):
    collection_id: str
    quality_bands: dict[str, str] = Field(default_factory=dict)
    interpretation_guide: str = ""


class DeforestationDataPack(BaseModel):
    land_cover_collections: list[str] = Field(default_factory=list)
    raw_image_collections: list[str] = Field(default_factory=list)
    data_cube_collections: list[str] = Field(default_factory=list)
    recommended_period: str = ""
    recommended_bands: list[str] = Field(default_factory=list)
    analysis_notes: str = ""


class TopicDiscovery(BaseModel):
    topic: str
    suggested_collections: list[dict] = Field(default_factory=list)
    recommended_workflow: str = ""
    notes: str = ""


class TimeSeriesPlan(BaseModel):
    collection_id: str
    band: str
    temporal_resolution_days: int = 0
    expected_item_count: int = 0
    recommended_chunk_size: int = 100
    estimated_data_volume_gb: float | None = None
    python_snippet: str = ""
    notes: str = ""
