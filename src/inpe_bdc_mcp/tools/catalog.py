"""Ferramentas MCP para informações do catálogo STAC do INPE/BDC."""

from __future__ import annotations

import json
from typing import Any

from ..client import BDCClient


def catalog_info() -> dict[str, Any]:
    """Retorna informações gerais do catálogo INPE/BDC STAC."""
    client = BDCClient.get_instance()
    data = client.get_catalog_info()

    links = data.get("links", [])
    endpoints = {
        link["rel"]: link.get("href", "")
        for link in links
        if link.get("rel") in ("self", "root", "service-doc", "conformance", "data", "search")
    }

    collections = client.list_collections()

    return {
        "id": data.get("id", ""),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "stac_version": data.get("stac_version", ""),
        "type": data.get("type", ""),
        "total_collections": len(collections),
        "endpoints": endpoints,
        "is_authenticated": client.auth.is_authenticated(),
        "conformance_classes_count": len(client.get_conformance()),
    }


def list_conformance_classes() -> list[str]:
    """Lista todas as conformance classes OGC implementadas pela API."""
    client = BDCClient.get_instance()
    return client.get_conformance()


def get_api_capabilities() -> dict[str, Any]:
    """Resume as capacidades da STAC API do BDC."""
    client = BDCClient.get_instance()
    conformance = client.get_conformance()

    conformance_str = " ".join(conformance).lower()

    return {
        "base_url": "https://data.inpe.br/bdc/stac/v1/",
        "stac_version": "1.0.0",
        "supports_get_search": True,
        "supports_post_search": True,
        "supports_cql2": "cql2" in conformance_str or "filter" in conformance_str,
        "supports_fields": "fields" in conformance_str,
        "supports_sortby": "sort" in conformance_str,
        "supports_query": True,
        "supports_cross_collection_search": True,
        "authentication": {
            "method": "x-api-key header",
            "required_for_public": False,
            "required_for_restricted": True,
            "is_configured": client.auth.is_authenticated(),
        },
        "pagination": "cursor-based (next link token)",
        "max_limit_per_page": 1000,
        "conformance_classes": conformance,
    }
