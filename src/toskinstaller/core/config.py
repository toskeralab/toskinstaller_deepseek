"""Modelos de configuração do TOSKINSTALLER.

Todos os modelos são dataclasses serializáveis em JSON. O objetivo é que
qualquer escolha feita pelo usuário durante o uso do TOSKINSTALLER seja
representável neste schema — nada deve ser fixo em código.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

# ---------------------------------------------------------------- constantes

Language = Literal["python", "node", "unknown"]
Toolchain = Literal[
    "pyinstaller", "nuitka", "cx_freeze",
    "pkg", "electron_builder",
    "none",
]
PackageFormat = Literal["exe", "msi", "portable", "both"]
Theme = Literal["dark", "light", "toskera"]
ProgressAnimation = Literal["bar", "ring", "dots"]
Locale = Literal["pt_BR", "en_US"]
PartnerAppMode = Literal["url", "embedded", "local_path"]


# --------------------------------------------------------------- ProjectInfo


@dataclass(slots=True)
class ProjectInfo:
    """Resultado da detecção de um projeto do usuário."""

    root: str
    language: Language = "unknown"
    toolchain: Toolchain = "none"
    confidence: float = 0.0
    entry_point: str | None = None
    signals: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectInfo":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# --------------------------------------------------------------- BuildConfig


@dataclass(slots=True)
class BuildConfig:
    """Parâmetros de build da Etapa 1 (projeto → executável)."""

    onefile: bool = True
    windowed: bool = True
    name: str | None = None
    icon: str | None = None
    add_data: list[str] = field(default_factory=list)
    extra_args: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BuildConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ----------------------------------------------------------- PartnerAppConfig


@dataclass(slots=True)
class PartnerAppConfig:
    """Configuração de um app parceiro instalado à parte do app principal."""

    name: str
    mode: PartnerAppMode = "url"
    source: str = ""          # URL, caminho local, ou nome do recurso embutido
    silent: bool = False       # instalação silenciosa (/S, /quiet, /silent)
    args: list[str] = field(default_factory=list)
    optional: bool = True      # usuário final pode pular

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PartnerAppConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------- ThemeConfig


@dataclass(slots=True)
class ThemeConfig:
    """Aparência do pacote final."""

    theme: Theme = "dark"
    progress_animation: ProgressAnimation = "bar"
    logo_path: str | None = None
    banner_path: str | None = None
    license_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThemeConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ------------------------------------------------------------- PackageConfig


@dataclass(slots=True)
class PackageConfig:
    """Configuração completa do pacote final (Etapa 2)."""

    project: ProjectInfo | None = None
    build: BuildConfig = field(default_factory=BuildConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    partner_apps: list[PartnerAppConfig] = field(default_factory=list)

    format: PackageFormat = "exe"
    locale: Locale = "pt_BR"

    shortcut_start_menu: bool = True
    shortcut_desktop: bool = False
    install_dir: str | None = None

    signature_pfx: str | None = None       # caminho do certificado
    signature_password: str | None = None  # senha do certificado
    signature_timestamp: str = "http://timestamp.digicert.com"

    # -------------------------------------------------------------- json io

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project.to_dict() if self.project else None,
            "build": self.build.to_dict(),
            "theme": self.theme.to_dict(),
            "partner_apps": [p.to_dict() for p in self.partner_apps],
            "format": self.format,
            "locale": self.locale,
            "shortcut_start_menu": self.shortcut_start_menu,
            "shortcut_desktop": self.shortcut_desktop,
            "install_dir": self.install_dir,
            "signature_pfx": self.signature_pfx,
            "signature_password": "***" if self.signature_password else None,
            "signature_timestamp": self.signature_timestamp,
        }

    def to_json(self, path: str | Path, *, indent: int = 2) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=indent, ensure_ascii=False)
        return target

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PackageConfig":
        project_data = data.get("project")
        build_data = data.get("build") or {}
        theme_data = data.get("theme") or {}
        partners_data = data.get("partner_apps") or []

        return cls(
            project=ProjectInfo.from_dict(project_data) if project_data else None,
            build=BuildConfig.from_dict(build_data),
            theme=ThemeConfig.from_dict(theme_data),
            partner_apps=[PartnerAppConfig.from_dict(p) for p in partners_data],
            format=data.get("format", "exe"),
            locale=data.get("locale", "pt_BR"),
            shortcut_start_menu=data.get("shortcut_start_menu", True),
            shortcut_desktop=data.get("shortcut_desktop", False),
            install_dir=data.get("install_dir"),
            signature_pfx=data.get("signature_pfx"),
            signature_password=data.get("signature_password"),
            signature_timestamp=data.get(
                "signature_timestamp", "http://timestamp.digicert.com"
            ),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "PackageConfig":
        source = Path(path)
        with source.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)
