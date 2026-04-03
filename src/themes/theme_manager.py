from PyQt6.QtWidgets import QApplication

from src.core.event_bus import event_bus
from src.core.logging_config import get_logger
from src.themes.dark_theme import DARK_EDITOR_COLORS, DARK_THEME_QSS
from src.themes.light_theme import LIGHT_EDITOR_COLORS, LIGHT_THEME_QSS

log = get_logger("themes")

THEMES = {
    "dark": {"qss": DARK_THEME_QSS, "editor_colors": DARK_EDITOR_COLORS},
    "light": {"qss": LIGHT_THEME_QSS, "editor_colors": LIGHT_EDITOR_COLORS},
}


class ThemeManager:
    """Manages application theming with dark/light mode toggle."""

    def __init__(self) -> None:
        self._current_theme = "dark"

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def editor_colors(self) -> dict[str, str]:
        return THEMES[self._current_theme]["editor_colors"]

    def apply_theme(self, theme_name: str) -> None:
        if theme_name not in THEMES:
            log.warning("Unknown theme '%s', falling back to dark", theme_name)
            theme_name = "dark"

        self._current_theme = theme_name
        app = QApplication.instance()
        if app:
            app.setStyleSheet(THEMES[theme_name]["qss"])

        event_bus.theme_changed.emit(theme_name)
        log.info("Applied theme: %s", theme_name)

    def toggle_theme(self) -> str:
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.apply_theme(new_theme)
        return new_theme
