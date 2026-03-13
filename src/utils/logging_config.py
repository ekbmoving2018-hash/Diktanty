"""Настройка логирования для приложения и Railway."""

import logging
import sys
from typing import Optional

from src.config import get_settings


def setup_logging(level: Optional[str] = None) -> None:
    """Настраивает корневой логгер: формат, уровень, вывод в stdout."""
    settings = get_settings()
    log_level = (level or settings.LOG_LEVEL).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(numeric_level)
    if not root.handlers:
        root.addHandler(handler)
