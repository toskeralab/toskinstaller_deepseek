"""Internacionalização simples baseada em arquivos JSON.

Uso:
    i18n = I18n("pt_BR")
    i18n.t("detector.python_found", count=3)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
_DEFAULT_LOCALE = "pt_BR"
_SUPPORTED = ("pt_BR", "en_US")


class I18nError(RuntimeError):
    """Erro ao carregar locale."""


class I18n:
    """Carregador de traduções com fallback para chave e para locale padrão."""

    def __init__(self, locale: str = _DEFAULT_LOCALE, locales_dir: Path | None = None) -> None:
        self.locales_dir = Path(locales_dir) if locales_dir else _LOCALES_DIR
        self.locale = locale if locale in _SUPPORTED else _DEFAULT_LOCALE
        self._strings: dict[str, str] = {}
        self._fallback: dict[str, str] = {}
        self._load()

    # ------------------------------------------------------------------ load

    def _load(self) -> None:
        self._strings = self._read(self.locale)
        if self.locale != _DEFAULT_LOCALE:
            self._fallback = self._read(_DEFAULT_LOCALE)

    def _read(self, locale: str) -> dict[str, str]:
        path = self.locales_dir / f"{locale}.json"
        if not path.exists():
            raise I18nError(f"Arquivo de locale não encontrado: {path}")
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise I18nError(f"JSON inválido em {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise I18nError(f"Locale {path} deve ser um objeto JSON.")
        return {str(k): str(v) for k, v in data.items()}

    # ------------------------------------------------------------------- api

    @property
    def available_locales(self) -> tuple[str, ...]:
        return _SUPPORTED

    def t(self, key: str, **kwargs: Any) -> str:
        """Traduz `key`. Faz fallback para o locale padrão e para a própria chave."""
        template = self._strings.get(key) or self._fallback.get(key) or key
        if not kwargs:
            return template
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            # Interpolação malformada — devolve template puro em vez de estourar
            return template

    def __call__(self, key: str, **kwargs: Any) -> str:
        return self.t(key, **kwargs)
