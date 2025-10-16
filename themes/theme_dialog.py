import logging
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QTextEdit, QSplitter, QFrame, QWidget, QComboBox,
    QFormLayout, QGroupBox, QCheckBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor
from .theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class ThemePreviewWidget(QFrame):
    """Widget for previewing themes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the preview UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Theme Preview")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Sample content
        sample_text = QLabel("This is a sample text to preview the theme colors and styling.")
        sample_text.setWordWrap(True)
        layout.addWidget(sample_text)
        
        # Sample button
        sample_button = QPushButton("Sample Button")
        layout.addWidget(sample_button)
        
        # Sample input
        sample_input = QTextEdit()
        sample_input.setMaximumHeight(60)
        sample_input.setPlainText("Sample input field\nwith multiple lines")
        layout.addWidget(sample_input)
        
        layout.addStretch()
    
    def apply_theme(self, theme_data: dict):
        """Apply theme to the preview widget"""
        try:
            stylesheet = theme_data.get('stylesheet', '')
            if stylesheet:
                self.setStyleSheet(stylesheet)
            
            # Apply palette if available
            palette_data = theme_data.get('palette', {})
            if palette_data:
                self._apply_palette(palette_data)
        except Exception as e:
            logger.error(f"Failed to apply theme to preview: {e}")
    
    def _apply_palette(self, palette_data: dict):
        """Apply color palette to the preview widget"""
        palette = QPalette()
        
        color_roles = {
            'window': QPalette.ColorRole.Window,
            'window_text': QPalette.ColorRole.WindowText,
            'base': QPalette.ColorRole.Base,
            'alternate_base': QPalette.ColorRole.AlternateBase,
            'tool_tip_base': QPalette.ColorRole.ToolTipBase,
            'tool_tip_text': QPalette.ColorRole.ToolTipText,
            'text': QPalette.ColorRole.Text,
            'button': QPalette.ColorRole.Button,
            'button_text': QPalette.ColorRole.ButtonText,
            'bright_text': QPalette.ColorRole.BrightText,
            'link': QPalette.ColorRole.Link,
            'highlight': QPalette.ColorRole.Highlight,
            'highlighted_text': QPalette.ColorRole.HighlightedText
        }
        
        for role_name, color_value in palette_data.items():
            if role_name in color_roles:
                if isinstance(color_value, str):
                    color = QColor(color_value)
                elif isinstance(color_value, list) and len(color_value) >= 3:
                    if len(color_value) == 3:
                        color = QColor(color_value[0], color_value[1], color_value[2])
                    else:
                        color = QColor(color_value[0], color_value[1], color_value[2], color_value[3])
                else:
                    continue
                
                palette.setColor(color_roles[role_name], color)
        
        self.setPalette(palette)

class ThemeDialog(QDialog):
    """Dialog for selecting and managing themes"""
    
    themeSelected = Signal(str)  # Signal emitted when a theme is selected
    
    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.current_theme = theme_manager.get_current_theme()
        self.setup_ui()
        self.load_themes()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Theme Selection")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create splitter for theme list and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Theme list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Theme list
        theme_label = QLabel("Available Themes:")
        theme_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(theme_label)
        
        self.theme_list = QListWidget()
        self.theme_list.currentItemChanged.connect(self.on_theme_selected)
        left_layout.addWidget(self.theme_list)
        
        # Theme info
        self.theme_info = QTextEdit()
        self.theme_info.setMaximumHeight(100)
        self.theme_info.setReadOnly(True)
        left_layout.addWidget(self.theme_info)
        
        splitter.addWidget(left_widget)
        
        # Right side - Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        preview_label = QLabel("Theme Preview:")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(preview_label)
        
        self.preview_widget = ThemePreviewWidget()
        right_layout.addWidget(self.preview_widget)
        
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Theme")
        self.apply_button.clicked.connect(self.apply_selected_theme)
        self.apply_button.setEnabled(False)
        
        self.import_button = QPushButton("Import Theme")
        self.import_button.clicked.connect(self.import_theme)
        
        self.export_button = QPushButton("Export Theme")
        self.export_button.clicked.connect(self.export_theme)
        self.export_button.setEnabled(False)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def load_themes(self):
        """Load available themes into the list"""
        self.theme_list.clear()
        theme_names = self.theme_manager.get_theme_names()
        
        for theme_name in sorted(theme_names):
            item = QListWidgetItem(theme_name)
            if theme_name == self.current_theme:
                item.setText(f"{theme_name} (Current)")
                item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.theme_list.addItem(item)
    
    def on_theme_selected(self, current, previous):
        """Handle theme selection"""
        if not current:
            return
        
        theme_name = current.text().replace(" (Current)", "")
        theme_data = self.theme_manager.themes.get(theme_name)
        
        if theme_data:
            # Update preview
            self.preview_widget.apply_theme(theme_data)
            
            # Update info
            info_text = f"Name: {theme_data.get('name', theme_name)}\n"
            info_text += f"Description: {theme_data.get('description', 'No description')}\n"
            info_text += f"Type: {'Built-in' if theme_name in ['default', 'dark', 'light', 'blue', 'green', 'purple', 'orange', 'red', 'cyberpunk', 'minimal', 'legacy'] else 'Custom'}"
            
            self.theme_info.setPlainText(info_text)
            
            # Enable buttons
            self.apply_button.setEnabled(True)
            self.export_button.setEnabled(True)
        else:
            self.theme_info.setPlainText("Theme data not available")
            self.apply_button.setEnabled(False)
            self.export_button.setEnabled(False)
    
    def apply_selected_theme(self):
        """Apply the selected theme"""
        current_item = self.theme_list.currentItem()
        if not current_item:
            return
        
        theme_name = current_item.text().replace(" (Current)", "")
        
        if self.theme_manager.apply_theme(theme_name):
            self.current_theme = theme_name
            self.themeSelected.emit(theme_name)
            self.load_themes()  # Refresh the list to show current theme
            QMessageBox.information(self, "Success", f"Theme '{theme_name}' applied successfully!")
        else:
            QMessageBox.critical(self, "Error", f"Failed to apply theme '{theme_name}'")
    
    def import_theme(self):
        """Import a custom theme from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Theme",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                
                # Validate theme data
                if not isinstance(theme_data, dict):
                    raise ValueError("Invalid theme data format")
                
                if 'name' not in theme_data:
                    raise ValueError("Theme must have a 'name' field")
                
                theme_name = theme_data['name']
                
                # Check if theme already exists
                if theme_name in self.theme_manager.themes:
                    reply = QMessageBox.question(
                        self,
                        "Theme Exists",
                        f"Theme '{theme_name}' already exists. Do you want to overwrite it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.No:
                        return
                
                # Save the theme
                if self.theme_manager.save_custom_theme(theme_name, theme_data):
                    self.load_themes()
                    QMessageBox.information(self, "Success", f"Theme '{theme_name}' imported successfully!")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to import theme '{theme_name}'")
                    
            except Exception as e:
                logger.error(f"Failed to import theme: {e}")
                QMessageBox.critical(self, "Error", f"Failed to import theme: {str(e)}")
    
    def export_theme(self):
        """Export the selected theme to file"""
        current_item = self.theme_list.currentItem()
        if not current_item:
            return
        
        theme_name = current_item.text().replace(" (Current)", "")
        theme_data = self.theme_manager.themes.get(theme_name)
        
        if not theme_data:
            QMessageBox.warning(self, "Warning", "No theme data to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Theme",
            f"{theme_name}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(theme_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Success", f"Theme '{theme_name}' exported successfully!")
                    
            except Exception as e:
                logger.error(f"Failed to export theme: {e}")
                QMessageBox.critical(self, "Error", f"Failed to export theme: {str(e)}") 