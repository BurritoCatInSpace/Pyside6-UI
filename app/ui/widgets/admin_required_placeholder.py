from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal


class AdminRequiredPlaceholder(QWidget):
    restartRequested = Signal()

    def __init__(self, tab_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        msg = QLabel(
            f"{tab_name} requires administrator privileges to run.\n"
            "Please restart the application as Administrator."
        )
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)

        btn = QPushButton("Restart as Administrator")
        btn.clicked.connect(self.restartRequested.emit)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)


