from __future__ import annotations

import os
from pathlib import Path


def app_root() -> Path:
    return Path(__file__).resolve().parents[2]


def logs_dir() -> Path:
    return app_root() / "logs"


