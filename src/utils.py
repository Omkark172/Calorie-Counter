import logging
import os
import sys
from pathlib import Path
from typing import Any


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure and return the calorie_counter logger."""
    logger = logging.getLogger("calorie_counter")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def ensure_directory(path: str) -> Path:
    """Ensure the provided directory path exists and return a Path object."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def format_calories(calories: float) -> str:
    """Format a calorie value as a rounded string with a kcal suffix."""
    rounded = round(calories)
    return f"{rounded} kcal"


def get_calorie_emoji(calories: float) -> str:
    """Return an emoji reflecting the calorie level."""
    if calories < 300:
        return "🟢"
    if calories < 600:
        return "🟡"
    return "🔴"


def get_confidence_label(confidence: float) -> str:
    """Return a confidence label based on the provided score."""
    if confidence >= 0.8:
        return "High"
    if confidence >= 0.5:
        return "Medium"
    return "Low"
