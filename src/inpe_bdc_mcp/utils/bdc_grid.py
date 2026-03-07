"""Helpers para a grade BDC_SM (Brazil Data Cube Spatial Mosaic grid)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BDCGridInfo:
    grid_name: str
    crs_epsg: int
    tile_size_m: float
    overlap_m: float
    description: str


BDC_GRIDS: dict[str, BDCGridInfo] = {
    "BDC_SM_V2": BDCGridInfo(
        grid_name="BDC_SM_V2",
        crs_epsg=100001,
        tile_size_m=264000.0,
        overlap_m=0.0,
        description=(
            "Grade BDC Spatial Mosaic V2 — projeção Aea (Albers Equal-Area) "
            "centrada no Brasil, tiles de 264 km x 264 km."
        ),
    ),
    "BDC_MD_V2": BDCGridInfo(
        grid_name="BDC_MD_V2",
        crs_epsg=100001,
        tile_size_m=4752000.0,
        overlap_m=0.0,
        description="Grade BDC Medium V2 para mosaicos de grande escala.",
    ),
    "BDC_LG_V2": BDCGridInfo(
        grid_name="BDC_LG_V2",
        crs_epsg=100001,
        tile_size_m=9504000.0,
        overlap_m=0.0,
        description="Grade BDC Large V2 para mosaicos continentais.",
    ),
}


def get_grid_info(grid_name: str) -> BDCGridInfo | None:
    return BDC_GRIDS.get(grid_name)


def parse_tile_id(tile_id: str) -> tuple[int, int] | None:
    """Converte tile ID BDC (ex: '007004') em (row, col)."""
    tile_id = tile_id.strip()
    if len(tile_id) == 6 and tile_id.isdigit():
        return int(tile_id[:3]), int(tile_id[3:])
    return None
