# CyberPatriot Tool Plugin Architecture

The CyberPatriot Tool now supports a flexible plugin architecture that allows you to create custom tabs and extend the application's functionality. This document explains how to create, install, and manage plugins.

## Overview

The plugin system supports two types of plugins:

1. **Local Plugins**: Python files placed in the `plugins/` directory
2. **Entry Point Plugins**: Installable packages that register plugins via Python entry points

## Plugin Types

### Local Plugins

Local plugins are Python files placed in the `plugins/` directory. They're automatically discovered and loaded when the application starts.

**Advantages:**
- Easy to develop and test
- No installation required
- Immediate availability after restart

**Disadvantages:**
- Not easily distributable
- Must be manually copied to each installation

### Entry Point Plugins

Entry point plugins are packaged as installable Python packages with entry points that register the plugins.

**Advantages:**
- Easy to distribute and install via pip
- Version management through package managers
- Can include dependencies

**Disadvantages:**
- Requires packaging setup
- Must be installed before use

## Creating a Plugin

### Step 1: Create the Plugin Class

All plugins must inherit from `BaseTabPlugin` and implement the required methods:

```python
from plugins.base import BaseTabPlugin
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MyCustomPlugin(BaseTabPlugin):
    # Required class attributes
    tab_name = "My Custom Tab"
    tab_description = "Description of what this tab does"
    supported_platforms = ["Windows", "Linux"]  # or ["Windows"] or ["Linux"]
    requires_admin = False  # True if admin privileges are needed
    plugin_version = "1.0.0"
    plugin_author = "Your Name"
    
    @classmethod
    def create_widget(cls, parent=None):
        """Create and return the widget for this tab."""
        return MyCustomWidget(parent)

class MyCustomWidget(QWidget):
    """The actual widget displayed in the tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Hello from my custom plugin!"))
```

### Step 2: Choose Plugin Type

#### For Local Plugins

1. Save your plugin as a `.py` file in the `plugins/` directory
2. Example: `plugins/my_custom_plugin.py`
3. Restart the application

#### For Entry Point Plugins

1. Create a proper Python package structure
2. Add entry points in your `setup.py` or `pyproject.toml`
3. Install the package

## Plugin Interface Reference

### BaseTabPlugin Class

#### Required Attributes

- `tab_name` (str): The name displayed in the tab
- `tab_description` (str): Brief description of the plugin
- `supported_platforms` (List[str]): Platforms this plugin supports ("Windows", "Linux")
- `requires_admin` (bool): Whether admin privileges are required
- `plugin_version` (str): Version string for the plugin
- `plugin_author` (str): Author/creator of the plugin

#### Required Methods

- `create_widget(cls, parent=None)`: Class method that returns a QWidget instance

#### Optional Methods

- `is_supported_platform(cls, platform_name)`: Check platform compatibility
- `is_compatible(cls)`: Check if plugin is compatible with current environment
- `get_plugin_info(cls)`: Get comprehensive plugin information
- `validate_plugin(cls)`: Validate plugin configuration

## Entry Point Setup

### setup.py Example

```python
from setuptools import setup, find_packages

setup(
    name="my-cyberpatriot-plugin",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["PySide6"],
    entry_points={
        "cyberpatriot_tabs": [
            "my_tab = my_plugin.tab:MyTabPlugin",
        ]
    }
)
```

### pyproject.toml Example

```toml
[project.entry-points.cyberpatriot_tabs]
my_tab = "my_plugin.tab:MyTabPlugin"
```

## Plugin Discovery Process

1. **Core Plugins**: Built-in tabs are registered first
2. **Entry Point Discovery**: Search for installed packages with `cyberpatriot_tabs` entry points
3. **Local Plugin Discovery**: Scan `plugins/` directory for `.py` files
4. **Validation**: Check plugin compatibility and requirements
5. **Registration**: Add valid plugins to the plugin registry
6. **Tab Creation**: Create tab placeholders (lazy loading)

## Best Practices

### Code Organization

```
my_plugin/
├── __init__.py
├── main_tab.py          # Main plugin class
├── widgets/             # Custom widgets
│   ├── __init__.py
│   └── custom_widget.py
├── utils/               # Utility functions
│   ├── __init__.py
│   └── helpers.py
└── resources/           # Resources (if any)
    └── icons/
```

### Error Handling

Always wrap your plugin code in try-catch blocks:

```python
def create_widget(cls, parent=None):
    try:
        return MyWidget(parent)
    except Exception as e:
        # Return a simple error widget
        error_widget = QWidget(parent)
        layout = QVBoxLayout(error_widget)
        layout.addWidget(QLabel(f"Plugin error: {e}"))
        return error_widget
```

### Platform Compatibility

Use platform checks for platform-specific functionality:

```python
import platform

class MyPlugin(BaseTabPlugin):
    @classmethod
    def create_widget(cls, parent=None):
        if platform.system() == "Windows":
            return WindowsSpecificWidget(parent)
        else:
            return LinuxSpecificWidget(parent)
```

### Admin Privileges

For plugins requiring admin privileges:

```python
class AdminPlugin(BaseTabPlugin):
    requires_admin = True
    
    @classmethod
    def create_widget(cls, parent=None):
        # Check if running with admin privileges
        # Implement admin-only functionality
        pass
```

## Plugin Management

### Viewing Loaded Plugins

Plugin information is logged during startup. Check the logs for:
- Discovered plugins count
- Registration success/failure
- Plugin validation errors

### Troubleshooting

Common issues and solutions:

1. **Plugin not loading**: Check file naming and class inheritance
2. **Import errors**: Ensure all dependencies are installed
3. **Platform compatibility**: Verify `supported_platforms` setting
4. **Admin requirements**: Check `requires_admin` setting matches your needs

## Examples

### Simple Information Tab

```python
from plugins.base import BaseTabPlugin
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

class InfoTabPlugin(BaseTabPlugin):
    tab_name = "System Info"
    tab_description = "Display system information"
    supported_platforms = ["Windows", "Linux"]
    
    @classmethod
    def create_widget(cls, parent=None):
        return InfoWidget(parent)

class InfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("System Information"))
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setPlainText(self.get_system_info())
        layout.addWidget(info_text)
    
    def get_system_info(self):
        import platform
        return f"""
Platform: {platform.system()}
Version: {platform.version()}
Machine: {platform.machine()}
Processor: {platform.processor()}
        """
```

### Tool Integration Tab

```python
import subprocess
from plugins.base import BaseTabPlugin
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit

class ToolTabPlugin(BaseTabPlugin):
    tab_name = "Network Tools"
    tab_description = "Network diagnostic tools"
    supported_platforms = ["Windows", "Linux"]
    
    @classmethod
    def create_widget(cls, parent=None):
        return NetworkToolsWidget(parent)

class NetworkToolsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        ping_btn = QPushButton("Ping Google")
        ping_btn.clicked.connect(self.ping_google)
        layout.addWidget(ping_btn)
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)
    
    def ping_google(self):
        try:
            result = subprocess.run(
                ["ping", "-c", "4", "8.8.8.8"], 
                capture_output=True, 
                text=True
            )
            self.output.setPlainText(result.stdout)
        except Exception as e:
            self.output.setPlainText(f"Error: {e}")
```

## Migration from Old System

If you have existing tabs from the old system, convert them by:

1. Creating a plugin wrapper class
2. Moving the widget creation to `create_widget()`
3. Setting appropriate plugin attributes
4. Testing the conversion

Example conversion:

```python
# Old system
class MyOldTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... existing code ...

# New plugin system
class MyTabPlugin(BaseTabPlugin):
    tab_name = "My Tab"
    # ... other attributes ...
    
    @classmethod
    def create_widget(cls, parent=None):
        return MyOldTab(parent)  # Reuse existing widget
```

This allows gradual migration while maintaining functionality. 