"""Modelos Pydantic para itens e assets STAC."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssetInfo(BaseModel):
    key: str
    href: str
    title: str | None = None
    type: str = ""
    roles: list[str] = Field(default_factory=list)
    is_cog: bool = False
    is_thumbnail: bool = False
    description: str | None = None
    eo_bands: list[dict] = Field(default_factory=list)
    raster_bands: list[dict] = Field(default_factory=list)


class ItemSummary(BaseModel):
    id: str
    collection_id: str = ""
    datetime: str | None = None
    bbox: list[float] = Field(default_factory=list)
    cloud_cover: float | None = None
    platform: str | None = None
    bdc_tile: str | None = None
    asset_keys: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None


class ItemDetail(BaseModel):
    id: str
    collection_id: str = ""
    datetime: str | None = None
    geometry: dict = Field(default_factory=dict)
    bbox: list[float] = Field(default_factory=list)
    cloud_cover: float | None = None
    platform: str | None = None
    instrument: str | None = None
    gsd: float | None = None
    bdc_tile: str | None = None
    assets: dict[str, AssetInfo] = Field(default_factory=dict)
    links: list[dict] = Field(default_factory=list)
    all_properties: dict = Field(default_factory=dict)


class DownloadInfo(BaseModel):
    url: str
    mime_type: str = ""
    curl_command: str = ""
    wget_command: str = ""
    python_rasterio_snippet: str = ""
    python_download_snippet: str = ""
    r_terra_snippet: str = ""
    requires_auth: bool = False
    auth_header: str | None = None
