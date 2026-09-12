"""Testes do detector de linguagem e toolchain."""

from __future__ import annotations

from pathlib import Path

import pytest

from toskinstaller.core.detector import Detector


def test_detect_python_project(python_project: Path) -> None:
    info = Detector().detect(python_project)

    assert info.language == "python"
    assert info.toolchain == "pyinstaller"
    assert info.confidence > 0.5
    assert info.entry_point is not None
    assert Path(info.entry_point).name == "main.py"
    assert any("requirements.txt" in s for s in info.signals)


def test_detect_node_project(node_project: Path) -> None:
    info = Detector().detect(node_project)

    assert info.language == "node"
    # package.json contém "bin" → pkg
    assert info.toolchain == "pkg"
    assert info.confidence > 0.5
    assert info.entry_point is not None
    assert Path(info.entry_point).name == "index.js"


def test_detect_empty_project(empty_project: Path) -> None:
    info = Detector().detect(empty_project)

    assert info.language == "unknown"
    assert info.toolchain == "none"
    assert info.confidence == 0.0


def test_detect_nonexistent_path(tmp_path: Path) -> None:
    info = Detector().detect(tmp_path / "does-not-exist")
    assert info.language == "unknown"
    assert info.confidence == 0.0


def test_detect_file_instead_of_dir(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("oi", encoding="utf-8")

    info = Detector().detect(target)
    assert info.language == "unknown"
    assert info.confidence == 0.0


def test_detect_ignores_node_modules(tmp_path: Path) -> None:
    # cria package.json + muitos .js em node_modules (deve ignorar node_modules)
    (tmp_path / "package.json").write_text('{"name": "x"}', encoding="utf-8")
    (tmp_path / "index.js").write_text("console.log('x')", encoding="utf-8")

    nm = tmp_path / "node_modules" / "lib"
    nm.mkdir(parents=True)
    for i in range(50):
        (nm / f"f{i}.js").write_text("", encoding="utf-8")

    info = Detector().detect(tmp_path)
    assert info.language == "node"
    # apesar de 50 .js em node_modules, o signal de sources deve contar poucos
    source_counts = info.metadata.get("source_counts", {})
    assert source_counts.get("node", 0) < 10


def test_detect_python_beats_node_when_heavier(tmp_path: Path) -> None:
    # projeto claramente Python: markers fortes + vários .py
    (tmp_path / "requirements.txt").write_text("", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    for i in range(5):
        (tmp_path / f"mod{i}.py").write_text("x = 1", encoding="utf-8")

    info = Detector().detect(tmp_path)
    assert info.language == "python"
    assert info.toolchain == "pyinstaller"
