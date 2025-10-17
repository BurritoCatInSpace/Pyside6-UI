from __future__ import annotations

import platform
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QMessageBox,
    QMenuBar,
    QMenu,
    QPushButton,
    QApplication,
)
from PySide6.QtGui import QAction

import logging

from ...plugins import plugin_registry
from ...plugins.plugin_management import PluginManagementDialog
from ...themes.theme_manager import ThemeManager
from ...themes.theme_dialog import ThemeDialog
# Try to import from platforms first, fallback to ui app constants
try:
    from platforms.constants import VERSION, VERSION_NAME, SUPPORTED_PLATFORMS, VERSION_INFO, REQUIRE_ADMIN_BY_DEFAULT
except ImportError:
    try:
        # If running from ui directory, try parent directory
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from platforms.constants import VERSION, VERSION_NAME, SUPPORTED_PLATFORMS, VERSION_INFO, REQUIRE_ADMIN_BY_DEFAULT
    except ImportError:
        from ..constants import VERSION, VERSION_NAME, SUPPORTED_PLATFORMS, VERSION_INFO, REQUIRE_ADMIN_BY_DEFAULT
from ..ui.widgets.loading_placeholder import LoadingPlaceholder
from ..ui.widgets.admin_required_placeholder import AdminRequiredPlaceholder
from ..ui.widgets.error_placeholder import ErrorPlaceholder
from ..services.plugin_service import discover_and_register_all_plugins
from ..utils.window_title import build_title
from ..utils.version import build_version_details
from ..utils.admin import needs_admin_for_plugin
from ..ui.widgets.loading_placeholder import LoadingPlaceholder
from ..ui.widgets.admin_required_placeholder import AdminRequiredPlaceholder
from ..ui.widgets.error_placeholder import ErrorPlaceholder

CURRENT_PLATFORM = platform.system().lower()

try:
    if CURRENT_PLATFORM == "windows":
        from ..utils.elevation_windows import is_admin, run_as_admin
    elif CURRENT_PLATFORM == "linux":
        from ..utils.elevation_linux import is_admin, get_sudo_status
    else:  # pragma: no cover - unsupported platforms
        raise RuntimeError(f"Unsupported platform: {CURRENT_PLATFORM}")
except Exception as e:  # pragma: no cover - import-time platform errors
    raise


logger = logging.getLogger(__name__)


class TabLoaderThreadSignals:  # lightweight signal holder for typing clarity only
    def __init__(self):
        self.finished = None
        self.error = None
        self.add_tab = None


from PySide6.QtCore import QThread, Signal  # placed here to keep import order tidy


class TabLoaderThread(QThread):
    finished = Signal()
    error = Signal(str)
    add_tab = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TabLoaderThread")
        self.tab_widget: Optional[QTabWidget] = None

    def set_tab_widget(self, tab_widget: QTabWidget) -> None:
        self.tab_widget = tab_widget

    def run(self) -> None:
        try:
            self.discover_and_register_plugins()
            enabled_plugins = plugin_registry.get_enabled_plugins()
            for tab_name, plugin_class in enabled_plugins.items():
                self.add_tab.emit(tab_name, plugin_class)
            self.finished.emit()
        except Exception as e:  # pragma: no cover - runtime error path
            logger.error(f"Error in TabLoaderThread: {e}")
            self.error.emit(str(e))

    def discover_and_register_plugins(self) -> None:
        discover_and_register_all_plugins()



class MainWindow(QMainWindow):
    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        logger.info(f"Initializing MainWindow for {VERSION_NAME} v{VERSION} on {CURRENT_PLATFORM}")

        if CURRENT_PLATFORM == "windows":
            self.is_admin = is_admin()
            if self.is_admin:
                logger.info("Application running with admin privileges")
            else:
                if REQUIRE_ADMIN_BY_DEFAULT:
                    try:
                        logger.warning("Attempting to restart with elevated rights...")
                        run_as_admin()
                    except Exception as e:
                        logger.warning(f"Elevation denied or failed ({e}); continuing without admin.")
                    self.is_admin = is_admin()
                    if not self.is_admin:
                        logger.info(
                            "Continuing without admin privileges. Some operations will be disabled until elevated."
                        )
                else:
                    logger.info(
                        "Running without admin privileges by default. Some operations will be disabled until elevated."
                    )
        elif CURRENT_PLATFORM == "linux":
            self.sudo_status = get_sudo_status()
            self.is_admin = self.sudo_status["is_admin"]
            if self.is_admin:
                logger.info("Application running with admin/root privileges")
            else:
                logger.info(f"Application running as user '{self.sudo_status['current_user']}'")
                if self.sudo_status["sudo_available"]:
                    logger.info("Sudo is available - operations requiring root will prompt for password")
                else:
                    logger.warning("Sudo not available - some operations may not work")

        self.setWindowTitle(f"{VERSION_NAME} v{VERSION} ({CURRENT_PLATFORM.capitalize()})")
        self.setGeometry(100, 100, 800, 600)

        self.theme_manager = theme_manager if theme_manager is not None else ThemeManager()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.loading_widget = QWidget()
        self.loading_widget.setObjectName("loadingWidget")
        layout.addWidget(self.loading_widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.hide()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_widget)

        self.loaded_tabs: Dict[str, Dict[str, Any]] = {}
        self.is_loading_tab = False

        QApplication.processEvents()

        self.tab_loader = TabLoaderThread()
        self.tab_loader.set_tab_widget(self.tab_widget)
        self.tab_loader.finished.connect(self.on_tabs_loaded)
        self.tab_loader.error.connect(self.on_tab_load_error)
        self.tab_loader.add_tab.connect(self.add_tab)
        self.tab_loader.start()

        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        self.plugins_menu = QMenu("Plugins", self)
        self.menu_bar.addMenu(self.plugins_menu)
        self.manage_plugins_action = QAction("Manage Plugins...", self)
        self.plugins_menu.addAction(self.manage_plugins_action)
        self.manage_plugins_action.triggered.connect(self.open_plugin_management_dialog)

        self.theme_menu = QMenu("Theme", self)
        self.menu_bar.addMenu(self.theme_menu)
        self.select_theme_action = QAction("Select Theme...", self)
        self.theme_menu.addAction(self.select_theme_action)
        self.select_theme_action.triggered.connect(self.open_theme_dialog)

        if CURRENT_PLATFORM == "windows":
            # Only show the admin menu/action when not already elevated
            if not getattr(self, "is_admin", False):
                self.admin_menu = QMenu("Admin", self)
                self.menu_bar.addMenu(self.admin_menu)
                self.restart_admin_action = QAction("Restart as Administrator", self)
                self.restart_admin_action.triggered.connect(self.restart_as_admin)
                self.admin_menu.addAction(self.restart_admin_action)

        self.update_window_title()

    @Slot(str, object)
    def add_tab(self, tab_name: str, plugin_class: object) -> None:
        placeholder = LoadingPlaceholder(tab_name)
        self.loaded_tabs[tab_name] = {
            "plugin_class": plugin_class,
            "instance": None,
            "placeholder": placeholder,
        }
        self.tab_widget.addTab(placeholder, tab_name)
        self.update_window_title()

    def on_tab_changed(self, index: int) -> None:
        if self.is_loading_tab or index < 0:
            return
        try:
            self.is_loading_tab = True
            tab_name = self.tab_widget.tabText(index)
            tab_info = self.loaded_tabs.get(tab_name)
            if tab_info and not tab_info["instance"]:
                plugin_class = tab_info["plugin_class"]
                requires_admin = bool(getattr(plugin_class, "requires_admin", False))
                if needs_admin_for_plugin(CURRENT_PLATFORM == "windows", requires_admin, getattr(self, "is_admin", False)):
                    admin_widget = AdminRequiredPlaceholder(tab_name)
                    admin_widget.restartRequested.connect(self.restart_as_admin)
                    tab_info["instance"] = admin_widget
                else:
                    tab_info["instance"] = plugin_class.create_widget(self.tab_widget)
                self.tab_widget.removeTab(index)
                self.tab_widget.insertTab(index, tab_info["instance"], tab_name)
                self.tab_widget.setCurrentIndex(index)
                logger.info(f"Lazy loaded plugin tab: {tab_name}")
        except Exception as e:
            logger.error(f"Error loading tab {tab_name}: {e}")
            # Replace current tab content with an error placeholder
            error_widget = ErrorPlaceholder(tab_name, str(e))
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(index, error_widget, tab_name)
            self.tab_widget.setCurrentIndex(index)
        finally:
            self.is_loading_tab = False
            self.update_window_title()

    def update_window_title(self) -> None:
        base_title = f"{VERSION_NAME} v{VERSION} ({CURRENT_PLATFORM.capitalize()})"
        try:
            current_index = self.tab_widget.currentIndex()
            if current_index is None or current_index < 0:
                self.setWindowTitle(build_title(VERSION_NAME, VERSION, CURRENT_PLATFORM))
                return
            tab_name = self.tab_widget.tabText(current_index)
            plugin_version = None
            tab_info = self.loaded_tabs.get(tab_name)
            if tab_info:
                plugin_class = tab_info.get("plugin_class")
                if plugin_class is not None:
                    plugin_version = getattr(plugin_class, "plugin_version", None)
            self.setWindowTitle(
                build_title(VERSION_NAME, VERSION, CURRENT_PLATFORM, tab_name, plugin_version)
            )
        except Exception:
            self.setWindowTitle(build_title(VERSION_NAME, VERSION, CURRENT_PLATFORM))

    def on_tabs_loaded(self) -> None:
        self.loading_widget.hide()
        self.tab_widget.show()
        logger.info("All tabs loaded successfully")
        self.update_window_title()

    def on_tab_load_error(self, error_msg: str) -> None:
        self.loading_widget.hide()
        self.tab_widget.show()
        logger.error(f"Error loading tabs: {error_msg}")
        QMessageBox.critical(self, "Error", f"Failed to load tabs: {error_msg}")

    def get_version_details(self) -> Dict[str, str]:
        return build_version_details(VERSION_INFO, CURRENT_PLATFORM)

    def prompt_for_admin_operation(self, operation_description: str) -> bool:
        if CURRENT_PLATFORM == "windows":
            if self.is_admin:
                return True
            QMessageBox.warning(
                self,
                "Admin Privileges Required",
                f"{operation_description} requires administrator privileges.\n"
                "Please restart the application as administrator.",
            )
            return False
        elif CURRENT_PLATFORM == "linux":
            if self.is_admin:
                return True
            if not self.sudo_status["sudo_available"]:
                QMessageBox.warning(
                    self,
                    "Admin Privileges Required",
                    f"{operation_description} requires root privileges, but sudo is not available.\n"
                    "Please run the application as root or install sudo.",
                )
                return False
            reply = QMessageBox.question(
                self,
                "Admin Privileges Required",
                f"{operation_description} requires root privileges.\n"
                "The application will prompt for your password when needed.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            return reply == QMessageBox.StandardButton.Yes
        return False

    def open_plugin_management_dialog(self) -> None:
        dlg = PluginManagementDialog(self)
        dlg.pluginToggled.connect(self.on_plugin_toggled)
        dlg.resize(900, 560)
        dlg.exec()

    def on_plugin_toggled(self, plugin_name: str, enabled: bool) -> None:
        if enabled:
            if plugin_name not in self.loaded_tabs:
                plugin_class = plugin_registry.get_plugin(plugin_name)
                if plugin_class:
                    self.add_tab(plugin_name, plugin_class)
        else:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == plugin_name:
                    self.tab_widget.removeTab(i)
                    break
            if plugin_name in self.loaded_tabs:
                del self.loaded_tabs[plugin_name]
        self.update_window_title()

    def open_theme_dialog(self) -> None:
        dialog = ThemeDialog(self.theme_manager, self)
        dialog.themeSelected.connect(self.on_theme_selected)
        dialog.exec()

    def on_theme_selected(self, theme_name: str) -> None:
        logger.info(f"Theme selected: {theme_name}")

    def restart_as_admin(self) -> None:
        if CURRENT_PLATFORM == "windows":
            try:
                run_as_admin()
            except Exception as e:
                logger.error(f"Failed to restart as administrator: {e}")
                QMessageBox.critical(self, "Error", f"Failed to restart as administrator:\n{e}")


