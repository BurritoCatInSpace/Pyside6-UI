from __future__ import annotations

import sys
from typing import List
import platform

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.services.logging_service import setup_logging
from themes.theme_manager import ThemeManager
from app.ui.main_window import MainWindow
# Try to import from platforms first, fallback to ui app constants
try:
    from platforms.constants import VERSION, VERSION_NAME
except ImportError:
    try:
        # If running from ui directory, try parent directory
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from platforms.constants import VERSION, VERSION_NAME
    except ImportError:
        from app.constants import VERSION, VERSION_NAME

# Linux-specific checks
if platform.system().lower() == "linux":
    from app.utils.qt_dependencies_linux import ensure_qt_xcb_dependencies_installed
    from app.utils.elevation_linux import is_admin, ensure_root_privileges


def run(argv: List[str]) -> int:
    """Application bootstrap. Mirrors previous behavior from main.py without changes."""
    logger = setup_logging()
    logger.info(f"Starting {VERSION_NAME} v{VERSION} on {platform.system().lower()}")

    # On Linux, before creating QApplication, ensure Qt xcb system dependencies are present
    if platform.system().lower() == "linux":
        try:
            if not ensure_qt_xcb_dependencies_installed():
                logger.error(
                    "Required Qt xcb dependencies are missing and could not be installed automatically."
                )
                print(
                    "Missing Qt dependencies. Please install: "
                    "libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 "
                    "libxcb-keysyms1 libxcb-render-util0 libxkbcommon-x11-0 qtwayland5",
                    file=sys.stderr,
                )
                return 1
        except Exception as e:
            logger.error(f"Error while ensuring Qt dependencies: {e}")

    app = QApplication(argv)

    # Global style and font retained
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    # On Linux, prompt for root if required (preserves previous behavior)
    if platform.system().lower() == "linux":
        if not is_admin():
            logger.info("Application not running as root, requesting admin privileges...")
            if not ensure_root_privileges():
                logger.error("Admin privileges not granted. Application cannot continue.")
                return 1
            logger.info("Admin privileges obtained successfully.")

    # Apply theme using ThemeManager auto-detection
    theme_manager = ThemeManager()
    theme_manager.apply_auto_theme()

    window = MainWindow(theme_manager)
    window.show()

    exit_code = app.exec()
    logger.info(f"Application closed with code {exit_code}")
    return exit_code


