"""Testes dos modelos de configuração e serialização JSON."""

from __future__ import annotations

import json
from pathlib import Path

from toskinstaller.core.config import (
    BuildConfig,
    PackageConfig,
    PartnerAppConfig,
    ProjectInfo,
    ThemeConfig,
)


def test_project_info_roundtrip() -> None:
    info = ProjectInfo(
        root="C:/proj",
        language="python",
        toolchain="pyinstaller",
        confidence=0.9,
        entry_point="C:/proj/main.py",
        signals=["file:requirements.txt"],
        metadata={"source_counts": {"python": 3}},
    )
    restored = ProjectInfo.from_dict(info.to_dict())
    assert restored == info


def test_build_config_defaults() -> None:
    build = BuildConfig()
    assert build.onefile is True
    assert build.windowed is True
    assert build.add_data == []
    assert build.extra_args == []


def test_partner_app_config_roundtrip() -> None:
    partner = PartnerAppConfig(
        name="MyPartner",
        mode="url",
        source="https://example.com/setup.exe",
        silent=True,
        args=["/quiet"],
    )
    restored = PartnerAppConfig.from_dict(partner.to_dict())
    assert restored == partner


def test_package_config_json_roundtrip(tmp_path: Path) -> None:
    config = PackageConfig(
        project=ProjectInfo(root="C:/p", language="python", toolchain="pyinstaller",
                            confidence=0.8),
        build=BuildConfig(onefile=False, name="Demo"),
        theme=ThemeConfig(theme="toskera", progress_animation="ring"),
        partner_apps=[PartnerAppConfig(name="P", mode="local_path",
                                       source="C:/setup.exe")],
        format="both",
        locale="en_US",
        shortcut_desktop=True,
        install_dir="C:/Program Files/Demo",
        signature_pfx="C:/cert.pfx",
        signature_password="secret",
    )

    target = tmp_path / "config.json"
    config.to_json(target)

    assert target.exists()
    raw = json.loads(target.read_text(encoding="utf-8"))
    # a senha NUNCA deve aparecer em claro no JSON
    assert raw["signature_password"] == "***"

    restored = PackageConfig.from_json(target)
    assert restored.format == "both"
    assert restored.locale == "en_US"
    assert restored.theme.progress_animation == "ring"
    assert restored.build.name == "Demo"
    assert restored.shortcut_desktop is True
    assert restored.partner_apps[0].name == "P"


def test_package_config_minimal_defaults() -> None:
    config = PackageConfig()
    assert config.project is None
    assert config.format == "exe"
    assert config.locale == "pt_BR"
    assert config.shortcut_start_menu is True
    assert config.shortcut_desktop is False
