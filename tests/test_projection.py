"""Testes unitários para o módulo tools/projection.py."""

from __future__ import annotations

import pytest

from inpe_bdc_mcp.tools.projection import (
    calculate_area,
    convert_geometry_format,
    get_utm_zone,
    reproject_bbox,
)


class TestReprojectBbox:
    def test_wgs84_to_bdc_albers(self):
        bbox = [-50.0, -15.0, -49.0, -14.0]
        result = reproject_bbox(bbox, from_crs="EPSG:4326", to_crs="EPSG:100001")
        assert "reprojected_bbox" in result
        rbox = result["reprojected_bbox"]
        assert len(rbox) == 4
        # BDC Albers usa metros, valores na ordem de milhões
        assert rbox[0] > 100_000
        assert rbox[2] > rbox[0]
        assert rbox[3] > rbox[1]

    def test_identity_transform(self):
        bbox = [-50.0, -15.0, -49.0, -14.0]
        result = reproject_bbox(bbox, from_crs="EPSG:4326", to_crs="EPSG:4326")
        rbox = result["reprojected_bbox"]
        for orig, rep in zip(bbox, rbox):
            assert abs(orig - rep) < 0.001

    def test_invalid_bbox_length(self):
        with pytest.raises(ValueError, match="4 elementos"):
            reproject_bbox([1, 2, 3])

    def test_alias_wgs84(self):
        bbox = [-50.0, -15.0, -49.0, -14.0]
        result = reproject_bbox(bbox, from_crs="wgs84", to_crs="bdc_albers")
        assert "reprojected_bbox" in result


class TestCalculateArea:
    def test_bbox_area(self):
        result = calculate_area(bbox=[-50.0, -15.0, -49.0, -14.0])
        assert result["area_ha"] > 0
        assert result["area_km2"] > 0
        assert result["area_m2"] > 0
        # 1 grau x 1 grau perto do equador ~ 12000 km²
        assert 10_000 < result["area_km2"] < 15_000

    def test_geojson_area(self):
        geojson = {
            "type": "Polygon",
            "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]],
        }
        result = calculate_area(geojson=geojson)
        assert result["area_km2"] > 0

    def test_no_input_raises(self):
        with pytest.raises(ValueError, match="bbox.*geojson"):
            calculate_area()


class TestGetUtmZone:
    def test_sao_paulo(self):
        result = get_utm_zone(lon=-46.63, lat=-23.55)
        assert result["utm_zone"] == "23S"
        assert result["epsg_code"] == "EPSG:32723"
        assert result["hemisphere"] == "S"

    def test_northern_hemisphere(self):
        result = get_utm_zone(lon=-43.0, lat=5.0)
        assert result["hemisphere"] == "N"
        assert "327" not in result["epsg_code"]  # deve ser 326xx

    def test_manaus(self):
        result = get_utm_zone(lon=-60.02, lat=-3.12)
        assert result["utm_zone"] == "20S"


class TestConvertGeometryFormat:
    def test_geojson_to_wkt(self):
        geojson = {
            "type": "Polygon",
            "coordinates": [[[-50, -15], [-49, -15], [-49, -14], [-50, -14], [-50, -15]]],
        }
        result = convert_geometry_format(geojson, to_format="wkt")
        assert result["input_format"] == "geojson"
        assert result["output_format"] == "wkt"
        assert "POLYGON" in result["result"]
        assert result["geometry_type"] == "Polygon"
        assert result["is_valid"] is True

    def test_wkt_to_geojson(self):
        wkt = "POLYGON ((-50 -15, -49 -15, -49 -14, -50 -14, -50 -15))"
        result = convert_geometry_format(wkt, to_format="geojson")
        assert result["input_format"] == "wkt"
        assert result["output_format"] == "geojson"
        assert result["result"]["type"] == "Polygon"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="não suportado"):
            convert_geometry_format({"type": "Point", "coordinates": [0, 0]}, to_format="kml")

    def test_invalid_geometry_type_raises(self):
        with pytest.raises(ValueError, match="dict.*string"):
            convert_geometry_format(42)  # type: ignore[arg-type]
