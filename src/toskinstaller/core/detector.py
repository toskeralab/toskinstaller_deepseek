"""Detecção automática de linguagem e toolchain de um projeto.

Estratégia:
  1. Arquivos-marcadores (`requirements.txt`, `package.json`, etc.) com pesos.
  2. Arquivos-fonte por extensão (`.py`, `.js`, `.ts`, ...) contados em profundidade
     limitada e ignorando pastas ruidosas (node_modules, .venv, dist, ...).
  3. Escolha do ponto de entrada por heurística.
  4. Escolha da toolchain a partir de metadados (ex.: electron em package.json).

A confiança (0.0–1.0) cresce com o peso total do vencedor e com a diferença
para o segundo colocado. Quando empate, a decisão fica ambígua e a linguagem
retornada é "unknown" com confidence baixa.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from toskinstaller.core.config import ProjectInfo
from toskinstaller.core.logger import get_logger

logger = get_logger("detector")

# --------------------------------------------------------------- constantes

_IGNORED_DIRS: frozenset[str] = frozenset({
    ".git", ".hg", ".svn",
    "node_modules", "bower_components",
    ".venv", "venv", "env", "ENV", ".env",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "dist", "build", "target", "out", "bin", "obj",
    ".idea", ".vscode", ".vs",
    ".tox", ".eggs", "*.egg-info",
})

_PY_MARKERS: dict[str, int] = {
    "requirements.txt": 4,
    "pyproject.toml": 4,
    "setup.py": 4,
    "setup.cfg": 2,
    "Pipfile": 3,
    "Pipfile.lock": 2,
    "poetry.lock": 3,
    "tox.ini": 1,
    "MANIFEST.in": 1,
}

_NODE_MARKERS: dict[str, int] = {
    "package.json": 5,
    "package-lock.json": 3,
    "yarn.lock": 3,
    "pnpm-lock.yaml": 3,
    "tsconfig.json": 2,
    ".nvmrc": 1,
}

_PY_ENTRY_CANDIDATES: tuple[str, ...] = (
    "main.py", "app.py", "__main__.py",
    "src/main.py", "src/app.py", "src/__main__.py",
    "run.py", "start.py",
)

_NODE_ENTRY_CANDIDATES: tuple[str, ...] = (
    "index.js", "main.js", "app.js", "server.js", "cli.js",
    "index.ts", "main.ts", "app.ts",
    "src/index.js", "src/main.js", "src/index.ts",
)

_SOURCE_EXTS: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".js": "node",
    ".mjs": "node",
    ".cjs": "node",
    ".ts": "node",
    ".tsx": "node",
    ".jsx": "node",
}

_MAX_DEPTH = 4
_MAX_SOURCE_FILES = 5000  # evita varrer monorepos enormes


# --------------------------------------------------------------- detector


class Detector:
    """Detecta linguagem, toolchain e ponto de entrada de um projeto."""

    def __init__(self, max_depth: int = _MAX_DEPTH) -> None:
        self.max_depth = max_depth

    # --------------------------------------------------------------- público

    def detect(self, root: str | Path) -> ProjectInfo:
        root_path = Path(root).expanduser().resolve()

        if not root_path.exists():
            logger.warning("Caminho inexistente: %s", root_path)
            return ProjectInfo(root=str(root_path), language="unknown", confidence=0.0)

        if not root_path.is_dir():
            logger.warning("Não é uma pasta: %s", root_path)
            return ProjectInfo(root=str(root_path), language="unknown", confidence=0.0)

        scores: dict[str, float] = defaultdict(float)
        signals: list[str] = []
        metadata: dict[str, object] = {}

        # 1) arquivos-marcadores no nível raiz
        self._score_markers(root_path, scores, signals, metadata)

        # 2) contagem de arquivos-fonte por extensão
        self._score_sources(root_path, scores, signals, metadata)

        if not signals:
            logger.info("Nenhum sinal em %s", root_path)
            return ProjectInfo(root=str(root_path), language="unknown", confidence=0.0)

        language, confidence = self._pick_language(scores)

        if language == "unknown":
            return ProjectInfo(
                root=str(root_path),
                language="unknown",
                confidence=confidence,
                signals=signals,
                metadata=metadata,
            )

        entry = self._detect_entry_point(root_path, language)
        toolchain = self._pick_toolchain(language, root_path, metadata)

        info = ProjectInfo(
            root=str(root_path),
            language=language,
            toolchain=toolchain,
            confidence=confidence,
            entry_point=str(entry) if entry else None,
            signals=signals,
            metadata=metadata,
        )
        logger.info("Detecção: %s", info.to_dict())
        return info

    # ------------------------------------------------------------- privados

    def _score_markers(
        self,
        root: Path,
        scores: dict[str, float],
        signals: list[str],
        metadata: dict[str, object],
    ) -> None:
        for filename, weight in _PY_MARKERS.items():
            candidate = root / filename
            if candidate.exists():
                scores["python"] += weight
                signals.append(f"file:{filename}")

        for filename, weight in _NODE_MARKERS.items():
            candidate = root / filename
            if candidate.exists():
                scores["node"] += weight
                signals.append(f"file:{filename}")

        # enriquecer metadata a partir do package.json, se existir
        pkg = root / "package.json"
        if pkg.exists():
            try:
                with pkg.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                metadata["node_dependencies"] = sorted(deps.keys())
                metadata["node_has_bin"] = bool(data.get("bin"))
                metadata["node_main"] = data.get("main")
                metadata["node_is_electron"] = "electron" in deps
            except (json.JSONDecodeError, OSError) as exc:
                logger.debug("Falha ao ler package.json: %s", exc)

    def _score_sources(
        self,
        root: Path,
        scores: dict[str, float],
        signals: list[str],
        metadata: dict[str, object],
    ) -> None:
        counts: dict[str, int] = defaultdict(int)
        scanned = 0

        for path in self._iter_files(root):
            scanned += 1
            if scanned > _MAX_SOURCE_FILES:
                logger.warning("Limite de %d arquivos atingido em %s", _MAX_SOURCE_FILES, root)
                break
            lang = _SOURCE_EXTS.get(path.suffix.lower())
            if lang:
                counts[lang] += 1

        metadata["source_counts"] = dict(counts)

        # cada arquivo-fonte vale 0.1 (teto: 5.0 por linguagem)
        for lang, count in counts.items():
            weight = min(5.0, count * 0.1)
            if weight > 0:
                scores[lang] += weight
                signals.append(f"sources:{lang}={count}")

    def _iter_files(self, root: Path) -> Iterable[Path]:
        stack: list[tuple[Path, int]] = [(root, 0)]
        while stack:
            current, depth = stack.pop()
            if depth > self.max_depth:
                continue
            try:
                for child in current.iterdir():
                    if child.is_dir():
                        if child.name in _IGNORED_DIRS or child.name.startswith("."):
                            continue
                        stack.append((child, depth + 1))
                    elif child.is_file():
                        yield child
            except (PermissionError, OSError) as exc:
                logger.debug("Ignorado (sem permissão?): %s — %s", current, exc)

    def _pick_language(self, scores: dict[str, float]) -> tuple[str, float]:
        if not scores:
            return "unknown", 0.0

        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top_lang, top_score = ordered[0]
        second_score = ordered[1][1] if len(ordered) > 1 else 0.0

        if top_score <= 0:
            return "unknown", 0.0

        # ambiguidade: se o 2º está a menos de 15% do 1º, não decidimos
        if second_score > 0 and (top_score - second_score) / top_score < 0.15:
            return "unknown", round(min(1.0, top_score / 12.0) * 0.4, 2)

        base = min(1.0, top_score / 12.0)
        margin = (top_score - second_score) / top_score
        confidence = round(base * (0.6 + 0.4 * margin), 2)
        return top_lang, min(1.0, confidence)

    def _detect_entry_point(self, root: Path, language: str) -> Path | None:
        candidates = (
            _PY_ENTRY_CANDIDATES if language == "python" else _NODE_ENTRY_CANDIDATES
        )
        for rel in candidates:
            candidate = root / rel
            if candidate.is_file():
                return candidate
        return None

    def _pick_toolchain(
        self,
        language: str,
        root: Path,
        metadata: dict[str, object],
    ) -> str:
        if language == "python":
            # F1: PyInstaller é o padrão. Nuitka e cx_Freeze serão oferecidos na UI (F4).
            return "pyinstaller"

        if language == "node":
            if metadata.get("node_is_electron"):
                return "electron_builder"
            if metadata.get("node_has_bin"):
                return "pkg"
            return "pkg"

        return "none"
