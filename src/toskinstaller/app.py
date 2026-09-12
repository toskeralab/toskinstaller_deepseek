"""Ponto de entrada principal do TOSKINSTALLER.

F0+F1: modo CLI mínimo para validação do detector.
F4: substituirá o fluxo CLI por uma QApplication com wizard PySide6.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from toskinstaller import __version__
from toskinstaller.core.detector import Detector
from toskinstaller.core.i18n import I18n, I18nError
from toskinstaller.core.logger import get_logger, setup_logging


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toskinstaller",
        description="TOSKINSTALLER — ToskeraLAB ART/TECH House",
    )
    parser.add_argument(
        "--detect",
        metavar="PASTA",
        type=Path,
        help="Detecta linguagem e toolchain de um projeto e imprime JSON.",
    )
    parser.add_argument(
        "--locale",
        default="pt_BR",
        choices=("pt_BR", "en_US"),
        help="Idioma da saída (padrão: pt_BR).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"TOSKINSTALLER {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    setup_logging()
    logger = get_logger("app")
    logger.info("TOSKINSTALLER %s iniciado (locale=%s)", __version__, args.locale)

    try:
        i18n = I18n(args.locale)
    except I18nError as exc:
        print(f"[toskinstaller] erro de i18n: {exc}", file=sys.stderr)
        return 2

    if args.detect is not None:
        return _run_detect(args.detect, i18n)

    # F4 substituirá este ramo por uma QApplication.
    print(i18n.t("app.cli_help"))
    return 0


def _run_detect(path: Path, i18n: I18n) -> int:
    detector = Detector()
    info = detector.detect(path)

    payload = info.to_dict()
    payload["language_label"] = i18n.t(f"detector.language.{info.language}")
    payload["toolchain_label"] = i18n.t(f"toolchain.{info.toolchain}")

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if info.language != "unknown" else 1


if __name__ == "__main__":
    raise SystemExit(main())
