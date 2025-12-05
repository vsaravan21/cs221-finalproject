"""
Centralized paths and constants for the TripCompass project.
"""

from __future__ import annotations

import pathlib
from typing import Final


PACKAGE_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parent
REPO_ROOT: Final[pathlib.Path] = PACKAGE_ROOT.parent
DATA_DIR: Final[pathlib.Path] = PACKAGE_ROOT / "data"
PROCESSED_DATA_DIR: Final[pathlib.Path] = DATA_DIR / "processed"
REPORTS_DIR: Final[pathlib.Path] = REPO_ROOT / "reports"
DATA_REPORTS_DIR: Final[pathlib.Path] = REPORTS_DIR / "data_reports"


def ensure_directories() -> None:
    """Create commonly used directories if they do not already exist."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


RAW_DATA_MANIFEST: Final[pathlib.Path] = DATA_DIR / "data_sources.json"
POI_OUTPUT_PATH: Final[pathlib.Path] = DATA_DIR / "pois_sf_enriched.csv"
DATA_QUALITY_REPORT: Final[pathlib.Path] = DATA_REPORTS_DIR / "data_quality.json"

