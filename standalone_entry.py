"""
PyInstaller-friendly entrypoint for standalone GUI builds.

Uses ``from app.app import run`` so PyInstaller can trace the import graph
statically. ``run.py`` uses ``from GUI.app.app import run``, which relies on
runtime sys.modules patching; PyInstaller does not execute that shim during
analysis, so ``GUI.app`` imports are not discovered.

This entry creates the virtual GUI package for runtime (e.g. install_import_aliases)
but imports via ``app.app``, which resolves when the script directory (GUI root)
is in sys.path.

Example:
    cd GUI
    python standalone_entry.py --dev
"""

from __future__ import annotations

import os
import sys
import types


def _ensure_gui_virtual_package() -> None:
    """Ensure ``import GUI...`` works (needed by install_import_aliases)."""
    if "GUI" in sys.modules:
        return
    repo_root = os.path.dirname(os.path.abspath(__file__))
    os.environ.setdefault("GUI_STANDALONE_MODE", "1")
    module = types.ModuleType("GUI")
    module.__path__ = [repo_root]
    sys.modules["GUI"] = module


if __name__ == "__main__":
    _ensure_gui_virtual_package()
    # Use app.app (traceable by PyInstaller) rather than GUI.app.app
    from app.app import run

    raise SystemExit(run(sys.argv))
