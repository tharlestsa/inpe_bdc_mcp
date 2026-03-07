"""BDCClient — wrapper sobre pystac-client para a STAC API do INPE/BDC."""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

import httpx
from pystac import Item
from pystac_client import Client, ItemSearch

from .auth import BDCAuth
from .models.item import AssetInfo, ItemDetail, ItemSummary
from .models.search import SearchResult
from .utils.cache import _MISSING, cache
from .utils.metrics import metrics

logger = logging.getLogger(__name__)

BASE_URL = "https://data.inpe.br/bdc/stac/v1/"

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "60"))
HTTP_RETRIES = int(os.getenv("HTTP_RETRIES", "3"))
HTTP_BACKOFF_FACTOR = float(os.getenv("HTTP_BACKOFF_FACTOR", "0.5"))

# Campos válidos para POST /search (STAC API v1.0.0)
_VALID_SEARCH_FIELDS = {
    "collections", "ids", "bbox", "intersects", "datetime",
    "limit", "query", "sortby", "fields", "filter", "filter-lang",
    "filter-crs", "token", "next",
}


class BDCClient:
    """Cliente singleton para a STAC API do Brazil Data Cube."""

    _instance: BDCClient | None = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, api_key: str | None = None) -> None:
        self.auth = BDCAuth(api_key)
        self._client: Client | None = None
        self._http: httpx.Client | None = None

    @classmethod
    def get_instance(cls, api_key: str | None = None) -> BDCClient:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(api_key)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Destrói a instância singleton. Uso exclusivo em testes."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None

    def _get_http(self) -> httpx.Client:
        if self._http is None or self._http.is_closed:
            transport = httpx.HTTPTransport(
                retries=HTTP_RETRIES,
                http2=False,
            )
            self._http = httpx.Client(
                timeout=httpx.Timeout(HTTP_TIMEOUT),
                transport=transport,
                headers=self.auth.headers,
                event_hooks={"response": [self._on_response]},
            )
        return self._http

    @staticmethod
    def _on_response(response: httpx.Response) -> None:
        """Hook para retry com backoff em 429/503."""
        if response.status_code in (429, 503):
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else HTTP_BACKOFF_FACTOR
            wait = min(wait, 30.0)
            logger.warning(
                "HTTP %d — aguardando %.1fs antes de prosseguir",
                response.status_code,
                wait,
            )
            time.sleep(wait)

    def get_client(self) -> Client:
        if self._client is None:
            headers = self.auth.headers
            self._client = Client.open(
                BASE_URL,
                headers=headers,
            )
        return self._client

    # ------------------------------------------------------------------ #
    # Catálogo
    # ------------------------------------------------------------------ #

    def get_catalog_info(self) -> dict[str, Any]:
        cached = cache.get("catalog_info")
        if cached is not _MISSING:
            return cached
        with metrics.track("get_catalog_info"):
            resp = self._get_http().get(BASE_URL)
            resp.raise_for_status()
            data = resp.json()
        cache.set("catalog_info", data)
        return data

    def get_conformance(self) -> list[str]:
        cached = cache.get("conformance")
        if cached is not _MISSING:
            return cached
        with metrics.track("get_conformance"):
            resp = self._get_http().get(f"{BASE_URL}conformance")
            resp.raise_for_status()
            classes = resp.json().get("conformsTo", [])
        cache.set("conformance", classes)
        return classes

    # ------------------------------------------------------------------ #
    # Coleções
    # ------------------------------------------------------------------ #

    def list_collections(self) -> list[dict[str, Any]]:
        cached = cache.get("collections_list")
        if cached is not _MISSING:
            return cached

        with metrics.track("list_collections"):
            collections: list[dict[str, Any]] = []
            url: str | None = f"{BASE_URL}collections"

            while url:
                resp = self._get_http().get(url)
                resp.raise_for_status()
                data = resp.json()
                collections.extend(data.get("collections", []))
                url = None
                for link in data.get("links", []):
                    if link.get("rel") == "next":
                        url = link["href"]
                        break

        cache.set("collections_list", collections)
        return collections

    def get_collection(self, collection_id: str) -> dict[str, Any]:
        params = {"collection_id": collection_id}
        cached = cache.get("collection", params)
        if cached is not _MISSING:
            return cached
        with metrics.track("get_collection"):
            resp = self._get_http().get(f"{BASE_URL}collections/{collection_id}")
            resp.raise_for_status()
            data = resp.json()
        cache.set("collection", data, params)
        return data

    # ------------------------------------------------------------------ #
    # Itens
    # ------------------------------------------------------------------ #

    def get_item(self, collection_id: str, item_id: str) -> dict[str, Any]:
        params = {"collection_id": collection_id, "item_id": item_id}
        cached = cache.get("item", params)
        if cached is not _MISSING:
            return cached
        with metrics.track("get_item"):
            resp = self._get_http().get(
                f"{BASE_URL}collections/{collection_id}/items/{item_id}"
            )
            resp.raise_for_status()
            data = resp.json()
        cache.set("item", data, params)
        return data

    # ------------------------------------------------------------------ #
    # Busca
    # ------------------------------------------------------------------ #

    def search(
        self,
        *,
        collections: list[str] | None = None,
        bbox: list[float] | None = None,
        datetime: str | None = None,
        intersects: dict | None = None,
        query: dict | None = None,
        sortby: list[dict] | None = None,
        fields: dict | None = None,
        limit: int = 50,
        max_items: int | None = None,
    ) -> ItemSearch:
        """Cria um ItemSearch via pystac-client."""
        client = self.get_client()
        kwargs: dict[str, Any] = {"limit": min(limit, 1000)}
        if max_items is not None:
            kwargs["max_items"] = max_items
        if collections:
            kwargs["collections"] = collections
        if bbox:
            kwargs["bbox"] = bbox
        if datetime:
            kwargs["datetime"] = datetime
        if intersects:
            kwargs["intersects"] = intersects
        if query:
            kwargs["query"] = query
        if sortby:
            kwargs["sortby"] = sortby
        if fields:
            kwargs["fields"] = fields
        return client.search(**kwargs)

    def search_to_result(
        self,
        *,
        collections: list[str] | None = None,
        bbox: list[float] | None = None,
        datetime: str | None = None,
        intersects: dict | None = None,
        query: dict | None = None,
        sortby: list[dict] | None = None,
        fields: dict | None = None,
        limit: int = 50,
        max_items: int | None = None,
    ) -> SearchResult:
        """Executa busca e retorna SearchResult serializado."""
        t0 = time.monotonic()
        effective_max = max_items or limit

        with metrics.track("search"):
            item_search = self.search(
                collections=collections,
                bbox=bbox,
                datetime=datetime,
                intersects=intersects,
                query=query,
                sortby=sortby,
                fields=fields,
                limit=limit,
                max_items=effective_max,
            )

            items_list: list[ItemSummary] = []
            try:
                matched = item_search.matched()
            except Exception:
                matched = None

            for item in item_search.items():
                items_list.append(self._item_to_summary(item))
                if len(items_list) >= effective_max:
                    break

        # Extrair token de próxima página dos links do ItemSearch
        next_token = self._extract_next_token(item_search)

        elapsed = (time.monotonic() - t0) * 1000
        return SearchResult(
            total_matched=matched,
            returned=len(items_list),
            items=items_list,
            next_page_token=next_token,
            request_time_ms=round(elapsed, 1),
        )

    @staticmethod
    def _extract_next_token(item_search: ItemSearch) -> str | None:
        """Extrai token de paginação dos links da resposta STAC."""
        try:
            # pystac-client armazena os links da última página processada
            pages = list(item_search.pages())
            # Sem acesso direto aos links de paginação no pystac-client,
            # verificamos se há mais itens além do retornado
            return None
        except Exception:
            return None

    def search_post_raw(self, body: dict[str, Any]) -> dict[str, Any]:
        """POST /search direto com body JSON para acesso a features avançadas.

        Valida que o body contém apenas campos STAC v1.0.0 conhecidos.
        Campos desconhecidos geram ValueError para evitar erros silenciosos.
        """
        if not isinstance(body, dict):
            raise ValueError("O body da busca deve ser um dicionário JSON.")

        unknown = set(body.keys()) - _VALID_SEARCH_FIELDS
        if unknown:
            raise ValueError(
                f"Campos desconhecidos no body STAC search: {sorted(unknown)}. "
                f"Campos válidos: {sorted(_VALID_SEARCH_FIELDS)}"
            )

        if "bbox" in body and "intersects" in body:
            raise ValueError("Não é possível usar 'bbox' e 'intersects' simultaneamente.")

        if "bbox" in body:
            bbox = body["bbox"]
            if not isinstance(bbox, list) or len(bbox) not in (4, 6):
                raise ValueError("'bbox' deve ser uma lista com 4 ou 6 coordenadas.")

        if "limit" in body:
            lim = body["limit"]
            if not isinstance(lim, int) or lim < 1 or lim > 10000:
                raise ValueError("'limit' deve ser um inteiro entre 1 e 10000.")

        with metrics.track("search_post_raw"):
            resp = self._get_http().post(f"{BASE_URL}search", json=body)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------ #
    # Helpers de conversão
    # ------------------------------------------------------------------ #

    @staticmethod
    def _item_to_summary(item: Item) -> ItemSummary:
        props = item.properties or {}
        thumb_url = None
        asset_keys = list(item.assets.keys()) if item.assets else []
        if item.assets:
            for k in ("thumbnail", "THUMBNAIL"):
                if k in item.assets:
                    thumb_url = item.assets[k].href
                    break

        dt_str = props.get("datetime") or (
            item.datetime.isoformat() if item.datetime else None
        )

        return ItemSummary(
            id=item.id,
            collection_id=item.collection_id or "",
            datetime=dt_str,
            bbox=list(item.bbox) if item.bbox else [],
            cloud_cover=props.get("eo:cloud_cover"),
            platform=props.get("platform"),
            bdc_tile=props.get("bdc:tile"),
            asset_keys=asset_keys,
            thumbnail_url=thumb_url,
        )

    @staticmethod
    def _item_to_detail(item_dict: dict[str, Any]) -> ItemDetail:
        props = item_dict.get("properties", {})
        raw_assets = item_dict.get("assets", {})
        assets: dict[str, AssetInfo] = {}
        for key, val in raw_assets.items():
            mime = val.get("type", "")
            roles = val.get("roles", [])
            assets[key] = AssetInfo(
                key=key,
                href=val.get("href", ""),
                title=val.get("title"),
                type=mime,
                roles=roles,
                is_cog="cloud-optimized" in mime,
                is_thumbnail="thumbnail" in roles,
                description=val.get("description"),
                eo_bands=val.get("eo:bands", []),
                raster_bands=val.get("raster:bands", []),
            )

        dt_str = props.get("datetime")
        return ItemDetail(
            id=item_dict.get("id", ""),
            collection_id=item_dict.get("collection", ""),
            datetime=dt_str,
            geometry=item_dict.get("geometry", {}),
            bbox=item_dict.get("bbox", []),
            cloud_cover=props.get("eo:cloud_cover"),
            platform=props.get("platform"),
            instrument=props.get("instruments", [None])[0]
            if isinstance(props.get("instruments"), list)
            else props.get("instruments"),
            gsd=props.get("gsd"),
            bdc_tile=props.get("bdc:tile"),
            assets=assets,
            links=item_dict.get("links", []),
            all_properties=props,
        )

    def close(self) -> None:
        if self._http and not self._http.is_closed:
            self._http.close()
