import logging
from typing import Optional, List, Dict, Type

# Import after BaseTabPlugin is defined to avoid circular import issues
from .base import BaseTabPlugin  # type: ignore

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing discovered plugins."""

    def __init__(self):
        self._plugins: Dict[str, Type[BaseTabPlugin]] = {}
        self._core_plugins: Dict[str, Type[BaseTabPlugin]] = {}
        self._external_plugins: Dict[str, Type[BaseTabPlugin]] = {}
        self._disabled_plugins: set = set()
        # Track plugins seen in this runtime to apply default-disabled only once per session
        self._seen_plugins: set = set()

    def register_plugin(self, plugin_class: Type[BaseTabPlugin], is_core: bool = False):
        """
        Register a plugin in the registry.

        Args:
            plugin_class: The plugin class to register
            is_core: Whether this is a core plugin
        """
        plugin_name = plugin_class.tab_name

        # Validate plugin
        errors = plugin_class.validate_plugin()
        if errors:
            raise ValueError(f"Invalid plugin '{plugin_name}': {', '.join(errors)}")

        # Check compatibility
        if not plugin_class.is_compatible():
            return  # Skip incompatible plugins

        # Handle name conflicts: core plugins take priority over external plugins
        if plugin_name in self._plugins:
            existing_is_core = plugin_name in self._core_plugins
            if existing_is_core and not is_core:
                # Skip external plugin that conflicts with existing core plugin
                logger.warning(f"Skipping external plugin '{plugin_name}' - conflicts with existing core plugin")
                return
            elif not existing_is_core and is_core:
                # Replace external plugin with core plugin (core takes priority)
                logger.info(f"Replacing external plugin '{plugin_name}' with core plugin")
                # Remove from external plugins
                if plugin_name in self._external_plugins:
                    del self._external_plugins[plugin_name]

        self._plugins[plugin_name] = plugin_class

        if is_core:
            self._core_plugins[plugin_name] = plugin_class
        else:
            self._external_plugins[plugin_name] = plugin_class

        # Apply default disabled state only on first sight in this app session,
        # and do not override an existing user-enabled state
        try:
            if (
                getattr(plugin_class, 'disabled_by_default', False)
                and plugin_name not in self._seen_plugins
                and plugin_name not in self._disabled_plugins
            ):
                self._disabled_plugins.add(plugin_name)
        except Exception:
            pass

        # Mark as seen for this session
        self._seen_plugins.add(plugin_name)

    def get_all_plugins(self) -> Dict[str, BaseTabPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()

    def get_core_plugins(self) -> Dict[str, BaseTabPlugin]:
        """Get core plugins only."""
        return self._core_plugins.copy()

    def get_external_plugins(self) -> Dict[str, BaseTabPlugin]:
        """Get external plugins only."""
        return self._external_plugins.copy()

    def get_plugin(self, name: str) -> Optional[BaseTabPlugin]:
        """Get a specific plugin by name."""
        return self._plugins.get(name)

    def list_plugin_names(self) -> List[str]:
        """Get list of all plugin names."""
        return list(self._plugins.keys())

    def clear(self):
        """Clear all registered plugins."""
        self._plugins.clear()
        self._core_plugins.clear()
        self._external_plugins.clear()

    def disable_plugin(self, name: str):
        """Disable a plugin by name."""
        self._disabled_plugins.add(name)

    def enable_plugin(self, name: str):
        """Enable a plugin by name."""
        self._disabled_plugins.discard(name)

    def is_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled."""
        return name not in self._disabled_plugins

    def get_enabled_plugins(self) -> Dict[str, Type[BaseTabPlugin]]:
        """Get all enabled plugins."""
        return {k: v for k, v in self._plugins.items() if self.is_enabled(k)}


# Global plugin registry instance
plugin_registry = PluginRegistry()


