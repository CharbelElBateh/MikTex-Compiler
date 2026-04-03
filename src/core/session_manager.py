"""Saves and restores window session state between runs."""

import json
from pathlib import Path

from src.core.logging_config import get_logger
from src.core.settings_manager import SettingsManager

log = get_logger("core.session")


class SessionManager:
    """Persists and restores UI session state via SettingsManager."""

    def __init__(self, settings: SettingsManager) -> None:
        self._settings = settings

    # ── Save ──

    def save(
        self,
        project_path: str | None,
        open_files: list[dict],  # [{"path": str, "line": int, "col": int}]
        active_tab_index: int,
        splitter_h: list[int],
        splitter_v: list[int],
        panels_visible: dict[str, bool],
        last_pdf: str = "",
    ) -> None:
        s = self._settings
        s.set_session("last_project", project_path or "")
        s.set_session("open_files", json.dumps(open_files))
        s.set_session("active_tab_index", active_tab_index)
        s.set_session("splitter_h_sizes", json.dumps(splitter_h))
        s.set_session("splitter_v_sizes", json.dumps(splitter_v))
        s.set_session("file_tree_visible", panels_visible.get("file_tree", True))
        s.set_session("pdf_viewer_visible", panels_visible.get("pdf_viewer", True))
        s.set_session("output_panel_visible", panels_visible.get("output_panel", True))
        s.set_session("last_pdf", last_pdf)
        s.sync()
        log.debug("Session saved")

    # ── Restore ──

    def last_project(self) -> Path | None:
        val = self._settings.get_session("last_project", "")
        if val and Path(val).is_dir():
            return Path(val)
        return None

    def open_files(self) -> list[dict]:
        raw = self._settings.get_session("open_files", "[]")
        try:
            data = json.loads(raw)
            # Filter out files that no longer exist
            return [f for f in data if Path(f.get("path", "")).is_file()]
        except (json.JSONDecodeError, TypeError):
            return []

    def active_tab_index(self) -> int:
        val = self._settings.get_session("active_tab_index", 0)
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def splitter_h_sizes(self) -> list[int] | None:
        raw = self._settings.get_session("splitter_h_sizes", "")
        try:
            return json.loads(raw) if raw else None
        except (json.JSONDecodeError, TypeError):
            return None

    def splitter_v_sizes(self) -> list[int] | None:
        raw = self._settings.get_session("splitter_v_sizes", "")
        try:
            return json.loads(raw) if raw else None
        except (json.JSONDecodeError, TypeError):
            return None

    def last_pdf(self) -> str:
        """Return the path of the last open PDF, or empty string."""
        return self._settings.get_session("last_pdf", "") or ""

    def panels_visible(self) -> dict[str, bool]:
        def _bool(key: str, default: bool) -> bool:
            val = self._settings.get_session(key, default)
            if isinstance(val, str):
                return val.lower() in ("true", "1")
            return bool(val)

        return {
            "file_tree": _bool("file_tree_visible", True),
            "pdf_viewer": _bool("pdf_viewer_visible", True),
            "output_panel": _bool("output_panel_visible", True),
        }
