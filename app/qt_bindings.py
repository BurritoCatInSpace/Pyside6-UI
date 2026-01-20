"""
Qt binding shim.

Import Qt classes from here instead of directly from a concrete binding
so swapping bindings later is localized to this module.

Supported bindings (via QT_BINDING env var): pyside6 (default), pyqt6.
"""

from __future__ import annotations

import os
import sys
import types

_binding = os.getenv("QT_BINDING", "pyside6").lower()


def get_binding_name() -> str:
    """Return the active Qt binding name."""
    return _binding

if _binding in {"pyqt6", "pyqt"}:
    from PyQt6 import QtCore, QtGui, QtWidgets
    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
    Property = QtCore.pyqtProperty
    # Provide PySide6-style Signal/Slot/Property on QtCore module.
    if not hasattr(QtCore, "Signal"):
        QtCore.Signal = Signal
    if not hasattr(QtCore, "Slot"):
        QtCore.Slot = Slot
    if not hasattr(QtCore, "Property"):
        QtCore.Property = Property
    # Back-compat aliases for PySide6-style enum access.
    if not hasattr(QtCore.Qt, "Horizontal"):
        QtCore.Qt.Horizontal = QtCore.Qt.Orientation.Horizontal
    if not hasattr(QtCore.Qt, "Vertical"):
        QtCore.Qt.Vertical = QtCore.Qt.Orientation.Vertical
    if not hasattr(QtWidgets.QFrame, "StyledPanel"):
        QtWidgets.QFrame.StyledPanel = QtWidgets.QFrame.Shape.StyledPanel
    if not hasattr(QtGui.QFont, "Bold"):
        QtGui.QFont.Bold = QtGui.QFont.Weight.Bold
    if not hasattr(QtWidgets.QHeaderView, "ResizeToContents"):
        QtWidgets.QHeaderView.ResizeToContents = QtWidgets.QHeaderView.ResizeMode.ResizeToContents
    if not hasattr(QtWidgets.QTreeWidget, "ExtendedSelection"):
        QtWidgets.QTreeWidget.ExtendedSelection = QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
    if not hasattr(QtCore.Qt, "CustomContextMenu"):
        QtCore.Qt.CustomContextMenu = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
    # About dialog enum aliases (PySide6-style).
    if not hasattr(QtCore.Qt, "RichText"):
        QtCore.Qt.RichText = QtCore.Qt.TextFormat.RichText
    if not hasattr(QtCore.Qt, "NonModal"):
        QtCore.Qt.NonModal = QtCore.Qt.WindowModality.NonModal
    if not hasattr(QtCore.Qt, "WA_DeleteOnClose"):
        QtCore.Qt.WA_DeleteOnClose = QtCore.Qt.WidgetAttribute.WA_DeleteOnClose
    if not hasattr(QtWidgets.QMessageBox, "Close"):
        QtWidgets.QMessageBox.Close = QtWidgets.QMessageBox.StandardButton.Close
    # Provide PySide6 import shims when running on PyQt6.
    pyside6 = types.ModuleType("PySide6")
    pyside6.__dict__.update(
        QtCore=QtCore,
        QtGui=QtGui,
        QtWidgets=QtWidgets,
        Signal=Signal,
        Slot=Slot,
        Property=Property,
    )
    sys.modules["PySide6"] = pyside6
    sys.modules["PySide6.QtCore"] = QtCore
    sys.modules["PySide6.QtGui"] = QtGui
    sys.modules["PySide6.QtWidgets"] = QtWidgets
elif _binding in {"pyside6", "pyside"}:
    from PySide6 import QtCore, QtGui, QtWidgets
    Signal = QtCore.Signal
    Slot = QtCore.Slot
    Property = QtCore.Property
else:
    raise ImportError(f"Unsupported QT_BINDING: {_binding}")


def __getattr__(name: str):
    """Resolve Qt symbols from QtCore/QtGui/QtWidgets."""
    for module in (QtCore, QtGui, QtWidgets):
        if hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(f"qt_bindings has no attribute {name!r}")


__all__ = ["QtCore", "QtGui", "QtWidgets", "Signal", "Slot", "Property"]
