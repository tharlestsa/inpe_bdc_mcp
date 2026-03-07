"""Métricas de observabilidade para chamadas à STAC API."""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)


class APIMetrics:
    """Contadores de chamadas e latência por operação."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._calls: dict[str, int] = {}
        self._total_ms: dict[str, float] = {}
        self._errors: dict[str, int] = {}

    @contextmanager
    def track(self, operation: str) -> Generator[None, None, None]:
        """Context manager que registra contagem e latência de uma operação."""
        t0 = time.monotonic()
        try:
            yield
        except Exception:
            with self._lock:
                self._errors[operation] = self._errors.get(operation, 0) + 1
            raise
        finally:
            elapsed_ms = (time.monotonic() - t0) * 1000
            with self._lock:
                self._calls[operation] = self._calls.get(operation, 0) + 1
                self._total_ms[operation] = self._total_ms.get(operation, 0.0) + elapsed_ms

    def snapshot(self) -> dict[str, Any]:
        """Retorna snapshot das métricas acumuladas."""
        with self._lock:
            result: dict[str, Any] = {}
            for op in sorted(set(self._calls) | set(self._errors)):
                calls = self._calls.get(op, 0)
                total = self._total_ms.get(op, 0.0)
                result[op] = {
                    "calls": calls,
                    "errors": self._errors.get(op, 0),
                    "total_ms": round(total, 1),
                    "avg_ms": round(total / calls, 1) if calls > 0 else 0.0,
                }
            return result

    def reset(self) -> None:
        """Reseta todas as métricas. Uso em testes."""
        with self._lock:
            self._calls.clear()
            self._total_ms.clear()
            self._errors.clear()


metrics = APIMetrics()
