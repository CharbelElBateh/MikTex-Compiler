"""Plugin API: base class and facade for plugin development."""

from abc import ABC, abstractmethod

from src.core.event_bus import event_bus
from src.core.logging_config import get_logger

log = get_logger("core.plugin_api")


class PluginAPI:
    """Facade providing controlled access to application internals for plugins."""

    def __init__(self, main_window, settings) -> None:
        self._window = main_window
        self._settings = settings

    @property
    def event_bus(self):
        return event_bus

    @property
    def main_window(self):
        return self._window

    @property
    def settings(self):
        return self._settings

    @property
    def tab_manager(self):
        return self._window.tab_manager

    @property
    def output_panel(self):
        return self._window.output_panel

    def add_menu_action(self, menu_name: str, action_text: str, callback) -> None:
        """Add an action to an existing menu."""
        menu_bar = self._window.menuBar()
        for action in menu_bar.actions():
            if action.text().replace("&", "") == menu_name:
                menu = action.menu()
                if menu:
                    new_action = menu.addAction(action_text)
                    new_action.triggered.connect(callback)
                    return
        log.warning("Menu '%s' not found for plugin action", menu_name)

    def get_setting(self, key: str, default=None):
        return self._settings.get(f"Plugin/{key}", default)

    def set_setting(self, key: str, value) -> None:
        self._settings.set(f"Plugin/{key}", value)


class PluginBase(ABC):
    """Abstract base class for plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name."""
        ...

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return ""

    @abstractmethod
    def activate(self, api: PluginAPI) -> None:
        """Called when the plugin is loaded. Use the API to register functionality."""
        ...

    @abstractmethod
    def deactivate(self) -> None:
        """Called when the plugin is unloaded. Clean up resources."""
        ...
