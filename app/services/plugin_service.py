from __future__ import annotations

import logging
from typing import Tuple, Dict, Any, List, Type

from plugins.base import plugin_registry
# Try to import from platforms first, fallback to ui plugins
try:
    from platforms.core_plugins import get_core_plugins
except ImportError:
    try:
        # If running from ui directory, try parent directory
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from platforms.core_plugins import get_core_plugins
    except ImportError:
        from plugins.core_plugins import get_core_plugins

logger = logging.getLogger(__name__)


def discover_and_register_all_plugins() -> Tuple[List[Type[Any]], Dict[str, Any]]:
    """Discover and register core and external plugins.

    Returns (registered_core_plugins, summary) where summary may contain counts/metadata.
    """
    registered_core: List[Type[Any]] = []
    summary: Dict[str, Any] = {"total_discovered": 0}

    try:
        # Register core plugins first (ensures bundling and availability under PyInstaller)
        try:
            core_plugins = get_core_plugins()
            for plugin_class in core_plugins:
                try:
                    plugin_registry.register_plugin(plugin_class, is_core=True)
                    registered_core.append(plugin_class)
                    logger.info("Registered core plugin: %s", getattr(plugin_class, "tab_name", plugin_class.__name__))
                except Exception as e:  # pragma: no cover - logging branch
                    logger.error("Failed to register core plugin %s: %s", plugin_class.__name__, e)
        except Exception as e:
            logger.debug("No core plugins or failed to load core plugins: %s", e)

        # Discover plugins (core plugins should also declare is_core_plugin = True)
        try:
            from plugins.discovery import discover_and_register_plugins as discover

            registration_results, discover_summary = discover()
            if isinstance(discover_summary, dict):
                summary.update(discover_summary)
            logger.info("Plugin discovery complete: %s plugins found", summary.get("total_discovered", 0))
        except Exception as e:  # pragma: no cover - optional discovery
            logger.warning("Plugin discovery failed: %s", e)
    except Exception as e:
        logger.error("Error during plugin discovery: %s", e)
        raise

    return registered_core, summary


