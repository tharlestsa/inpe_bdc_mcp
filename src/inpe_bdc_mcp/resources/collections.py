"""MCP Resources para coleções individuais do BDC."""

from __future__ import annotations

import json
from typing import Any

from ..tools.collections import get_collection_detail
from ..tools.items import get_item


def collection_resource(collection_id: str) -> str:
    """Metadados completos de uma coleção."""
    detail = get_collection_detail(collection_id)
    return json.dumps(detail, indent=2, ensure_ascii=False)


def item_resource(collection_id: str, item_id: str) -> str:
    """Detalhes completos de um item STAC."""
    detail = get_item(collection_id, item_id)
    return json.dumps(detail, indent=2, ensure_ascii=False)
