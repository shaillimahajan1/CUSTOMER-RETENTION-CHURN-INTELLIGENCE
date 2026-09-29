"""Utility and helper functions for logging, configuration, seeds, and directory management."""

from __future__ import annotations

import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict

import numpy as np
import yaml


def setup_logger(name: str = "churn_intelligence", level: int = logging.INFO) -> logging.Logger:
    """Configures a standardized, structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def load_config(config_path: str | Path = "config/config.yaml") -> Dict[str, Any]:
    """Loads YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path.resolve()}")
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def set_seed(seed: int = 42) -> None:
    """Sets deterministic random seed across random, numpy."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def ensure_directories(paths: list[str | Path]) -> None:
    """Ensures that all specified directory paths exist."""
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def save_json(data: Any, filepath: str | Path, indent: int = 2) -> None:
    """Saves serializable object to a formatted JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(filepath: str | Path) -> Any:
    """Loads a JSON file from disk."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"JSON file does not exist at: {path.resolve()}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
