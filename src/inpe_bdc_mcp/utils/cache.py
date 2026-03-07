"""Cache em memória com TTL para reduzir chamadas à STAC API."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

CACHE_TTL = {
    "catalog_info": 7200,
    "conformance": 7200,
    "collection": 1800,
    "collections_list": 900,
    "item": 300,
    "search_results": 60,
}


_MISSING = object()


class TTLCache:
    """Cache simples em memória com expiração por chave."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def _make_key(self, namespace: str, params: dict[str, Any] | None = None) -> str:
        base = namespace
        if params:
            raw = json.dumps(params, sort_keys=True, default=str)
            base += ":" + hashlib.sha256(raw.encode()).hexdigest()[:16]
        return base

    def get(self, namespace: str, params: dict[str, Any] | None = None) -> Any:
        """Retorna valor do cache ou _MISSING sentinel se não encontrado."""
        key = self._make_key(namespace, params)
        entry = self._store.get(key)
        if entry is None:
            return _MISSING
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return _MISSING
        return value

    def set(
        self,
        namespace: str,
        value: Any,
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> None:
        key = self._make_key(namespace, params)
        if ttl is None:
            ttl = CACHE_TTL.get(namespace, 300)
        self._store[key] = (time.monotonic() + ttl, value)

    def invalidate(self, namespace: str, params: dict[str, Any] | None = None) -> None:
        """Remove uma entrada específica do cache."""
        key = self._make_key(namespace, params)
        self._store.pop(key, None)

    def invalidate_namespace(self, namespace: str) -> int:
        """Remove todas as entradas de um namespace (ex: todas as coleções cacheadas).

        Returns:
            Número de entradas removidas.
        """
        prefix = namespace + ":"
        keys_to_remove = [
            k for k in self._store
            if k == namespace or k.startswith(prefix)
        ]
        for k in keys_to_remove:
            del self._store[k]
        return len(keys_to_remove)

    def clear(self) -> None:
        """Remove todas as entradas do cache."""
        self._store.clear()


cache = TTLCache()
