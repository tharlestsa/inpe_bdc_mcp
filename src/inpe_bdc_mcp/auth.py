"""Gerenciamento de autenticação para a STAC API do INPE/BDC."""

from __future__ import annotations

import os


class BDCAuth:
    """Gerencia a API key do Brazil Data Cube.

    A autenticação é opcional para coleções públicas e obrigatória
    para coleções restritas. O header ``x-api-key`` é injetado
    automaticamente em todas as requisições quando disponível.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key: str | None = api_key or os.getenv("BDC_API_KEY") or None

    @property
    def headers(self) -> dict[str, str]:
        if self.api_key:
            return {"x-api-key": self.api_key}
        return {}

    def is_authenticated(self) -> bool:
        return bool(self.api_key)
