"""
Example setup.py for creating installable CyberPatriot Tool plugins.

This shows how to package your custom tabs as installable plugins that can be
distributed and installed via pip.
"""

from setuptools import setup, find_packages

setup(
    name="cyberpatriot-custom-plugin",
    version="1.0.0",
    description="Custom plugin for CyberPatriot Tool",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "PySide6",  # Required for Qt widgets
        # Add any other dependencies your plugin needs
    ],
    # This is the key part for plugin discovery
    entry_points={
        "cyberpatriot_tabs": [
            # Format: "plugin_name = module.path:PluginClass"
            "my_custom_tab = my_plugin.custom_tab:MyCustomTabPlugin",
            "another_tab = my_plugin.another_tab:AnotherTabPlugin",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)

"""
Example pyproject.toml alternative:

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "cyberpatriot-custom-plugin"
version = "1.0.0"
description = "Custom plugin for CyberPatriot Tool"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = ["PySide6"]
requires-python = ">=3.8"

[project.entry-points.cyberpatriot_tabs]
my_custom_tab = "my_plugin.custom_tab:MyCustomTabPlugin"
another_tab = "my_plugin.another_tab:AnotherTabPlugin"

To install your plugin:
1. Package it: python setup.py sdist bdist_wheel
2. Install it: pip install dist/cyberpatriot-custom-plugin-1.0.0.tar.gz
3. Restart CyberPatriot Tool to see your new tabs
""" 