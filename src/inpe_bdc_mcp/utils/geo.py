"""Helpers geoespaciais para construção de geometrias GeoJSON."""

from __future__ import annotations

from typing import Any


def make_point(lon: float, lat: float) -> dict[str, Any]:
    return {"type": "Point", "coordinates": [lon, lat]}


def make_bbox_polygon(bbox: list[float]) -> dict[str, Any]:
    min_lon, min_lat, max_lon, max_lat = bbox
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat],
        ]],
    }


def validate_bbox(bbox: list[float]) -> bool:
    if len(bbox) != 4:
        return False
    min_lon, min_lat, max_lon, max_lat = bbox
    return (
        -180 <= min_lon <= 180
        and -90 <= min_lat <= 90
        and -180 <= max_lon <= 180
        and -90 <= max_lat <= 90
        and min_lon < max_lon
        and min_lat < max_lat
    )


def bbox_intersects(a: list[float], b: list[float]) -> bool:
    return not (
        a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]
    )
