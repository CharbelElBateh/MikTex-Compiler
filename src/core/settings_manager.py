from pathlib import Path

from PyQt6.QtCore import QSettings

from src.constants import (
    APP_DATA_DIR,
    APP_NAME,
    DEFAULT_ENGINE,
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    DEFAULT_MIKTEX_BIN_DIR,
    DEFAULT_RENDER_DPI,
    DEFAULT_TAB_WIDTH,
    DEFAULT_ZOOM,
    ORG_NAME,
)
from src.core.event_bus import event_bus


class SettingsManager:
    """Manages global application settings via an INI file."""

    def __init__(self) -> None:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings_path = str(APP_DATA_DIR / "settings.ini")
        self._settings = QSettings(settings_path, QSettings.Format.IniFormat)
        self._settings.setFallbacksEnabled(False)

    # ── Generic access ──

    def get(self, key: str, default: object = None, value_type: type = str) -> object:
        value = self._settings.value(key, default)
        if value is None:
            return default
        if value_type is bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if value_type is int:
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        return value

    def set(self, key: str, value: object) -> None:
        self._settings.setValue(key, value)
        parts = key.split("/", 1)
        section = parts[0] if len(parts) > 1 else ""
        name = parts[1] if len(parts) > 1 else parts[0]
        event_bus.settings_changed.emit(section, name, value)

    def sync(self) -> None:
        self._settings.sync()

    # ── Editor settings ──

    @property
    def editor_font_family(self) -> str:
        return self.get("Editor/font_family", DEFAULT_FONT_FAMILY)

    @editor_font_family.setter
    def editor_font_family(self, value: str) -> None:
        self.set("Editor/font_family", value)

    @property
    def editor_font_size(self) -> int:
        return self.get("Editor/font_size", DEFAULT_FONT_SIZE, int)

    @editor_font_size.setter
    def editor_font_size(self, value: int) -> None:
        self.set("Editor/font_size", value)

    @property
    def editor_tab_width(self) -> int:
        return self.get("Editor/tab_width", DEFAULT_TAB_WIDTH, int)

    @editor_tab_width.setter
    def editor_tab_width(self, value: int) -> None:
        self.set("Editor/tab_width", value)

    @property
    def editor_word_wrap(self) -> bool:
        return self.get("Editor/word_wrap", False, bool)

    @editor_word_wrap.setter
    def editor_word_wrap(self, value: bool) -> None:
        self.set("Editor/word_wrap", value)

    @property
    def editor_show_whitespace(self) -> bool:
        return self.get("Editor/show_whitespace", False, bool)

    @editor_show_whitespace.setter
    def editor_show_whitespace(self, value: bool) -> None:
        self.set("Editor/show_whitespace", value)

    # ── Compiler settings ──

    @property
    def compiler_default_engine(self) -> str:
        return self.get("Compiler/default_engine", DEFAULT_ENGINE)

    @compiler_default_engine.setter
    def compiler_default_engine(self, value: str) -> None:
        self.set("Compiler/default_engine", value)

    @property
    def compiler_auto_compile(self) -> bool:
        return self.get("Compiler/auto_compile_on_save", False, bool)

    @compiler_auto_compile.setter
    def compiler_auto_compile(self, value: bool) -> None:
        self.set("Compiler/auto_compile_on_save", value)

    # ── Viewer settings ──

    @property
    def viewer_default_zoom(self) -> int:
        return self.get("Viewer/default_zoom", DEFAULT_ZOOM, int)

    @viewer_default_zoom.setter
    def viewer_default_zoom(self, value: int) -> None:
        self.set("Viewer/default_zoom", value)

    @property
    def viewer_render_dpi(self) -> int:
        return self.get("Viewer/render_dpi", DEFAULT_RENDER_DPI, int)

    @viewer_render_dpi.setter
    def viewer_render_dpi(self, value: int) -> None:
        self.set("Viewer/render_dpi", value)

    # ── MiKTeX settings ──

    @property
    def miktex_bin_dir(self) -> Path:
        value = self.get("MiKTeX/bin_directory", str(DEFAULT_MIKTEX_BIN_DIR))
        return Path(value)

    @miktex_bin_dir.setter
    def miktex_bin_dir(self, value: Path) -> None:
        self.set("MiKTeX/bin_directory", str(value))

    # ── Theme settings ──

    @property
    def theme(self) -> str:
        return self.get("Appearance/theme", "dark")

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("Appearance/theme", value)

    # ── Recent projects ──

    @property
    def recent_projects(self) -> list[str]:
        value = self._settings.value("General/recent_projects", [])
        if isinstance(value, str):
            return [value] if value else []
        return list(value) if value else []

    def add_recent_project(self, path: str) -> None:
        projects = self.recent_projects
        if path in projects:
            projects.remove(path)
        projects.insert(0, path)
        projects = projects[:20]  # Keep last 20
        self._settings.setValue("General/recent_projects", projects)

    def clear_recent_projects(self) -> None:
        self._settings.setValue("General/recent_projects", [])

    # ── Session (window geometry, splitter sizes, etc.) ──

    def get_session(self, key: str, default: object = None) -> object:
        return self._settings.value(f"Session/{key}", default)

    def set_session(self, key: str, value: object) -> None:
        self._settings.setValue(f"Session/{key}", value)
