"""Ferramentas MCP para projeção CRS, cálculo de área e conversão de geometrias."""

from __future__ import annotations

from typing import Any

from pyproj import CRS, Transformer
from shapely.geometry import box, shape
from shapely.ops import transform

# CRS BDC Albers Equal-Area (EPSG:100001 — customizado, não reconhecido pelo pyproj)
BDC_ALBERS_PROJ4 = (
    "+proj=aea +lat_0=-12 +lon_0=-54 +lat_1=-2 +lat_2=-22 "
    "+x_0=5000000 +y_0=10000000 +ellps=GRS80 +units=m +no_defs"
)

_CRS_ALIASES: dict[str, str] = {
    "wgs84": "EPSG:4326",
    "bdc_albers": BDC_ALBERS_PROJ4,
    "epsg:100001": BDC_ALBERS_PROJ4,
    "sirgas2000": "EPSG:4674",
}


def _resolve_crs(crs_input: str) -> CRS:
    """Resolve alias ou código CRS para um objeto pyproj.CRS."""
    resolved = _CRS_ALIASES.get(crs_input.lower(), crs_input)
    return CRS(resolved)


def reproject_bbox(
    bbox: list[float],
    from_crs: str = "EPSG:4326",
    to_crs: str = "EPSG:100001",
) -> dict[str, Any]:
    """Reprojeta bounding box entre sistemas de coordenadas.

    Args:
        bbox: Bounding box [min_x, min_y, max_x, max_y].
        from_crs: CRS de origem (ex: "EPSG:4326", "wgs84", "bdc_albers").
        to_crs: CRS de destino (ex: "EPSG:100001", "EPSG:32723").
    """
    if len(bbox) != 4:
        raise ValueError(f"bbox deve ter exatamente 4 elementos, recebeu {len(bbox)}.")

    src = _resolve_crs(from_crs)
    dst = _resolve_crs(to_crs)
    transformer = Transformer.from_crs(src, dst, always_xy=True)

    # Transformar os 4 cantos para projeções curvas (Albers, UTM)
    corners = [
        (bbox[0], bbox[1]),  # min_x, min_y
        (bbox[0], bbox[3]),  # min_x, max_y
        (bbox[2], bbox[1]),  # max_x, min_y
        (bbox[2], bbox[3]),  # max_x, max_y
    ]
    transformed = [transformer.transform(x, y) for x, y in corners]
    xs = [p[0] for p in transformed]
    ys = [p[1] for p in transformed]

    return {
        "original_bbox": bbox,
        "reprojected_bbox": [
            round(min(xs), 6), round(min(ys), 6),
            round(max(xs), 6), round(max(ys), 6),
        ],
        "from_crs": src.to_authority() or from_crs,
        "to_crs": dst.to_authority() or to_crs,
        "to_crs_name": dst.name,
    }


def calculate_area(
    bbox: list[float] | None = None,
    geojson: dict | None = None,
    crs: str = "EPSG:4326",
) -> dict[str, Any]:
    """Calcula a área de um bbox ou geometria GeoJSON em hectares e km².

    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat].
        geojson: Geometria GeoJSON (Polygon ou MultiPolygon).
        crs: CRS da entrada (padrão WGS84).
    """
    if bbox is None and geojson is None:
        raise ValueError("Forneça 'bbox' ou 'geojson'.")

    if bbox is not None:
        geom = box(bbox[0], bbox[1], bbox[2], bbox[3])
    else:
        geom = shape(geojson)

    src = _resolve_crs(crs)

    # Reprojetar para CRS de área igual (BDC Albers para Brasil)
    dst = _resolve_crs("bdc_albers")
    transformer = Transformer.from_crs(src, dst, always_xy=True)
    projected = transform(transformer.transform, geom)

    area_m2 = projected.area
    area_ha = area_m2 / 10_000
    area_km2 = area_m2 / 1_000_000

    return {
        "area_m2": round(area_m2, 2),
        "area_ha": round(area_ha, 2),
        "area_km2": round(area_km2, 4),
        "projection_used": "BDC Albers Equal-Area (custom EPSG:100001)",
        "input_crs": str(src.to_authority() or crs),
    }


def get_utm_zone(lon: float, lat: float) -> dict[str, Any]:
    """Retorna a zona UTM e código EPSG para uma coordenada geográfica.

    Args:
        lon: Longitude (WGS84).
        lat: Latitude (WGS84).
    """
    zone_number = int((lon + 180) / 6) + 1
    hemisphere = "N" if lat >= 0 else "S"
    epsg = 32600 + zone_number if lat >= 0 else 32700 + zone_number

    return {
        "longitude": lon,
        "latitude": lat,
        "utm_zone": f"{zone_number}{hemisphere}",
        "epsg_code": f"EPSG:{epsg}",
        "zone_number": zone_number,
        "hemisphere": hemisphere,
        "crs_name": f"WGS 84 / UTM zone {zone_number}{hemisphere}",
    }


def convert_geometry_format(
    geometry: dict | str,
    to_format: str = "wkt",
) -> dict[str, Any]:
    """Converte geometria entre GeoJSON e WKT.

    Args:
        geometry: Geometria GeoJSON (dict) ou WKT (string).
        to_format: Formato de saída — "wkt" ou "geojson".
    """
    from shapely import wkt as shapely_wkt
    from shapely.geometry import mapping

    if isinstance(geometry, dict):
        geom = shape(geometry)
        input_format = "geojson"
    elif isinstance(geometry, str):
        geom = shapely_wkt.loads(geometry)
        input_format = "wkt"
    else:
        raise ValueError("Geometria deve ser dict (GeoJSON) ou string (WKT).")

    if to_format.lower() == "wkt":
        output = geom.wkt
    elif to_format.lower() == "geojson":
        output = mapping(geom)
    else:
        raise ValueError(f"Formato '{to_format}' não suportado. Use 'wkt' ou 'geojson'.")

    return {
        "input_format": input_format,
        "output_format": to_format.lower(),
        "result": output,
        "geometry_type": geom.geom_type,
        "is_valid": geom.is_valid,
    }
