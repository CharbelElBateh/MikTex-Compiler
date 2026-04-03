"""Plugin discovery, loading, and lifecycle management."""

import importlib.util
import sys
from pathlib import Path

from src.core.event_bus import event_bus
from src.core.logging_config import get_logger
from src.core.plugin_api import PluginAPI, PluginBase

log = get_logger("core.plugin_manager")


class PluginManager:
    """Discovers and manages plugins from the plugins/ directory."""

    def __init__(self, plugin_dir: Path, api: PluginAPI) -> None:
        self._plugin_dir = plugin_dir
        self._api = api
        self._plugins: dict[str, PluginBase] = {}

    @property
    def loaded_plugins(self) -> dict[str, PluginBase]:
        return dict(self._plugins)

    def discover(self) -> list[str]:
        """Scan the plugins directory for available plugins.

        Each plugin must be in plugins/<name>/plugin.py and contain
        a class inheriting from PluginBase.
        """
        if not self._plugin_dir.is_dir():
            return []

        found = []
        for child in self._plugin_dir.iterdir():
            if child.is_dir() and (child / "plugin.py").is_file():
                found.append(child.name)
        log.debug("Discovered plugins: %s", found)
        return found

    def load(self, name: str) -> bool:
        """Load and activate a plugin by name."""
        if name in self._plugins:
            log.warning("Plugin '%s' already loaded", name)
            return True

        plugin_file = self._plugin_dir / name / "plugin.py"
        if not plugin_file.is_file():
            log.error("Plugin file not found: %s", plugin_file)
            return False

        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{name}", str(plugin_file)
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{name}"] = module
            spec.loader.exec_module(module)

            # Find the PluginBase subclass
            plugin_cls = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PluginBase)
                    and attr is not PluginBase
                ):
                    plugin_cls = attr
                    break

            if not plugin_cls:
                log.error("No PluginBase subclass found in %s", plugin_file)
                return False

            plugin = plugin_cls()
            plugin.activate(self._api)
            self._plugins[name] = plugin
            event_bus.plugin_loaded.emit(name)
            log.info("Plugin loaded: %s v%s", plugin.name, plugin.version)
            return True

        except Exception as e:
            log.exception("Failed to load plugin '%s': %s", name, e)
            return False

    def unload(self, name: str) -> bool:
        """Deactivate and unload a plugin."""
        plugin = self._plugins.pop(name, None)
        if not plugin:
            return False

        try:
            plugin.deactivate()
            event_bus.plugin_unloaded.emit(name)
            log.info("Plugin unloaded: %s", name)
        except Exception as e:
            log.exception("Error deactivating plugin '%s': %s", name, e)
        return True

    def load_all(self) -> None:
        """Discover and load all available plugins."""
        for name in self.discover():
            self.load(name)

    def unload_all(self) -> None:
        """Unload all loaded plugins."""
        for name in list(self._plugins.keys()):
            self.unload(name)
