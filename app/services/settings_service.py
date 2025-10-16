from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AppSettings:
    theme: Optional[str] = None
    plugins_path: Optional[str] = None


def load_settings() -> AppSettings:
    # Placeholder for future expansion; keep behavior unchanged for now.
    return AppSettings()


