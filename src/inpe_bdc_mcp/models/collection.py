"""Modelos Pydantic para coleções STAC do BDC."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BandInfo(BaseModel):
    name: str
    common_name: str | None = None
    description: str | None = None
    wavelength_nm: float | None = None
    gsd_m: float | None = None
    data_type: str = "unknown"
    nodata: float | None = None
    scale: float | None = None
    offset: float | None = None
    role: str = "data"


class CollectionSummary(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    satellite: str = ""
    sensor: str | None = None
    spatial_resolution_m: float | None = None
    temporal_composition: str | None = None
    composition_method: str | None = None
    level: str | None = None
    temporal_extent_start: str | None = None
    temporal_extent_end: str | None = None
    spatial_extent_bbox: list[float] = Field(default_factory=list)
    bands: list[str] = Field(default_factory=list)
    bdc_grid: str | None = None
    is_data_cube: bool = False
    is_mosaic: bool = False
    is_public: bool = True
    license: str = "proprietary"
    version: str | None = None


class CollectionDetail(CollectionSummary):
    stac_extensions: list[str] = Field(default_factory=list)
    summaries: dict = Field(default_factory=dict)
    item_assets: dict = Field(default_factory=dict)
    links: list[dict] = Field(default_factory=list)
    bdc_bands_quicklook: list[str] = Field(default_factory=list)
    bdc_metadata: dict = Field(default_factory=dict)
    bdc_grs: str | None = None
    bdc_tiles: list[str] = Field(default_factory=list)
    extra_properties: dict = Field(default_factory=dict)


class CollectionComparison(BaseModel):
    collections: list[CollectionSummary]
    common_bands: list[str] = Field(default_factory=list)
    temporal_overlap_start: str | None = None
    temporal_overlap_end: str | None = None
    resolution_comparison: list[dict] = Field(default_factory=list)
    processing_differences: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
