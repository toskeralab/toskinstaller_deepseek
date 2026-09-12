"""Fixtures compartilhadas para os testes do TOSKINSTALLER."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def python_project(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_python_project"


@pytest.fixture()
def node_project(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_node_project"


@pytest.fixture()
def empty_project(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_empty_project"
