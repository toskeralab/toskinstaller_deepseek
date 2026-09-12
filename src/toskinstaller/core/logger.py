"""Logging estruturado com rotação de arquivo e saída em console.

Uso típico:
    from toskinstaller.core.logger import setup_logging
    logger = setup_logging()
    logger.info("mensagem")
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_DEFAULT_LOG_DIR = Path.home() / ".toskinstaller" / "logs"
_DEFAULT_LOG_FILE = "toskinstaller.log"
_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
_BACKUP_COUNT = 5

_ROOT_NAME = "toskinstaller"
_configured = False


def setup_logging(
    log_dir: Path | None = None,
    *,
    level: int = logging.INFO,
    console: bool = True,
    force: bool = False,
) -> logging.Logger:
    """Configura e retorna o logger raiz do TOSKINSTALLER.

    Args:
        log_dir: pasta de logs. Padrão: ~/.toskinstaller/logs.
        level: nível de log (logging.INFO, etc.).
        console: se True, adiciona handler de console (stderr).
        force: reconfigura mesmo se já configurado.

    Returns:
        Logger raiz do pacote ('toskinstaller').
    """
    global _configured

    logger = logging.getLogger(_ROOT_NAME)

    if _configured and not force:
        return logger

    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de arquivo (best-effort; nunca falha a inicialização do app)
    try:
        target_dir = Path(log_dir) if log_dir else _DEFAULT_LOG_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            target_dir / _DEFAULT_LOG_FILE,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError as exc:  # pragma: no cover — depende do FS do usuário
        logger.addHandler(logging.NullHandler())
        print(f"[toskinstaller] aviso: não foi possível criar arquivo de log: {exc}",
              file=sys.stderr)

    if console:
        console_handler = logging.StreamHandler(stream=sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    _configured = True
    logger.debug("Logging configurado (level=%s, console=%s)", level, console)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Retorna um logger filho do TOSKINSTALLER."""
    if name:
        return logging.getLogger(f"{_ROOT_NAME}.{name}")
    return logging.getLogger(_ROOT_NAME)
