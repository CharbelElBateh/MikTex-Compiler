import os
from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QPushButton,
    QTabBar,
    QTabWidget,
    QWidget,
)

from src.core.event_bus import event_bus
from src.core.logging_config import get_logger
from src.core.settings_manager import SettingsManager
from src.editor.latex_editor import LaTeXEditor
from src.themes.theme_manager import ThemeManager
from src.ui.image_viewer_tab import ImageViewerTab

log = get_logger("ui.tab_manager")

# Close-button style templates keyed by theme
_CLOSE_BTN_SS = {
    "dark": (
        "QPushButton{background:transparent;border:none;color:#777777;"
        "font-size:14px;font-weight:400;padding:0;border-radius:3px;}"
        "QPushButton:hover{background:rgba(255,255,255,0.18);color:#d4d4d4;}"
        "QPushButton:pressed{background:rgba(255,255,255,0.28);}"
    ),
    "light": (
        "QPushButton{background:transparent;border:none;color:#888888;"
        "font-size:14px;font-weight:400;padding:0;border-radius:3px;}"
        "QPushButton:hover{background:rgba(0,0,0,0.12);color:#333333;}"
        "QPushButton:pressed{background:rgba(0,0,0,0.20);}"
    ),
}


def _norm(path: str) -> str:
    return os.path.normpath(path)


class TabManager(QTabWidget):
    """Manages editor tabs — open, close, switch, and track modified state."""

    def __init__(
        self,
        settings: SettingsManager,
        theme_manager: ThemeManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme_manager = theme_manager
        # text-file editors
        self._open_files: dict[str, LaTeXEditor] = {}
        # all tab widgets (editors + image viewers) keyed by normalised path
        self._tab_widgets: dict[str, QWidget] = {}
        # close buttons for theme update
        self._close_buttons: list[QPushButton] = []

        self.setTabsClosable(False)   # we supply our own × buttons
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        self.currentChanged.connect(self._on_current_changed)

        event_bus.file_modified.connect(self._on_file_modified)
        event_bus.theme_changed.connect(self._on_theme_changed)

    # ── Tab management helpers ────────────────────────────────────────────────

    def _make_close_button(self, widget: QWidget) -> QPushButton:
        """Create a themed × close button and attach it to the tab."""
        btn = QPushButton("×")
        btn.setFixedSize(QSize(18, 18))
        theme = getattr(self._theme_manager, "current_theme", "dark")
        btn.setStyleSheet(_CLOSE_BTN_SS.get(theme, _CLOSE_BTN_SS["dark"]))
        btn.setToolTip("Close tab")
        btn.clicked.connect(lambda: self._close_widget(widget))
        self._close_buttons.append(btn)
        return btn

    def _attach_close_button(self, idx: int, widget: QWidget) -> None:
        btn = self._make_close_button(widget)
        self.tabBar().setTabButton(idx, QTabBar.ButtonPosition.RightSide, btn)

    def _close_widget(self, widget: QWidget) -> None:
        if isinstance(widget, LaTeXEditor):
            self.close_file(widget.file_path)
        else:
            # Image or unknown — just remove
            key = _norm(getattr(widget, "file_path", ""))
            idx = self.indexOf(widget)
            if idx >= 0:
                self.removeTab(idx)
            self._tab_widgets.pop(key, None)
            # Remove close button reference
            self._close_buttons = [
                b for b in self._close_buttons
                if b.parent() is not None
            ]

    # ── Public: open text files ───────────────────────────────────────────────

    def open_file(self, file_path: str) -> LaTeXEditor | None:
        """Open a LaTeX/text file in a new tab (or focus the existing one)."""
        key = _norm(file_path)

        if key in self._open_files:
            self.setCurrentIndex(self.indexOf(self._open_files[key]))
            return self._open_files[key]

        if not Path(key).is_file():
            log.error("File not found: %s", key)
            return None

        editor = LaTeXEditor(
            file_path=key,
            colors=self._theme_manager.editor_colors,
            font_family=self._settings.editor_font_family,
            font_size=self._settings.editor_font_size,
            tab_width=self._settings.editor_tab_width,
            word_wrap=self._settings.editor_word_wrap,
        )

        if not editor.load_file():
            return None

        tab_title = Path(key).name
        idx = self.addTab(editor, tab_title)
        self.setTabToolTip(idx, key)
        self.setCurrentIndex(idx)
        self._attach_close_button(idx, editor)

        self._open_files[key] = editor
        self._tab_widgets[key] = editor
        event_bus.file_opened.emit(key)
        log.info("Opened tab: %s", key)
        return editor

    # ── Public: open image files ──────────────────────────────────────────────

    def open_image(self, file_path: str) -> ImageViewerTab | None:
        """Open an image file in a viewer tab (or focus the existing one)."""
        key = _norm(file_path)

        if key in self._tab_widgets:
            widget = self._tab_widgets[key]
            self.setCurrentIndex(self.indexOf(widget))
            return widget if isinstance(widget, ImageViewerTab) else None

        if not Path(key).is_file():
            log.error("Image not found: %s", key)
            return None

        viewer = ImageViewerTab(key)
        tab_title = Path(key).name
        idx = self.addTab(viewer, tab_title)
        self.setTabToolTip(idx, key)
        self.setCurrentIndex(idx)
        self._attach_close_button(idx, viewer)

        self._tab_widgets[key] = viewer
        log.info("Opened image tab: %s", key)
        return viewer

    # ── Save ─────────────────────────────────────────────────────────────────

    def close_file(self, file_path: str) -> bool:
        key = _norm(file_path)
        if key not in self._open_files:
            return True

        editor = self._open_files[key]
        if not self._confirm_close(editor):
            return False

        idx = self.indexOf(editor)
        self.removeTab(idx)
        del self._open_files[key]
        self._tab_widgets.pop(key, None)
        # Prune dead close buttons
        self._close_buttons = [b for b in self._close_buttons if b.parent() is not None]
        event_bus.file_closed.emit(key)
        log.info("Closed tab: %s", key)
        return True

    def save_current(self) -> bool:
        editor = self.current_editor
        return editor.save_file() if editor else False

    def save_current_as(self) -> bool:
        editor = self.current_editor
        if not editor:
            return False

        new_path, _ = QFileDialog.getSaveFileName(
            self, "Save As", editor.file_path, "LaTeX Files (*.tex);;All Files (*)"
        )
        if not new_path:
            return False

        old_key = _norm(editor.file_path)
        new_key = _norm(new_path)
        success = editor.save_as(new_key)
        if success:
            del self._open_files[old_key]
            self._tab_widgets.pop(old_key, None)
            self._open_files[new_key] = editor
            self._tab_widgets[new_key] = editor
            idx = self.indexOf(editor)
            self.setTabText(idx, Path(new_key).name)
            self.setTabToolTip(idx, new_key)
        return success

    def save_all(self) -> None:
        for editor in self._open_files.values():
            editor.save_file()

    def close_current(self) -> bool:
        widget = self.currentWidget()
        if not widget:
            return True
        if isinstance(widget, LaTeXEditor):
            return self.close_file(widget.file_path)
        # Image or other non-editor tab — just close
        self._close_widget(widget)
        return True

    def close_all(self) -> bool:
        for file_path in list(self._open_files.keys()):
            if not self.close_file(file_path):
                return False
        # Close image tabs
        for key in list(self._tab_widgets.keys()):
            widget = self._tab_widgets.get(key)
            if widget and not isinstance(widget, LaTeXEditor):
                idx = self.indexOf(widget)
                if idx >= 0:
                    self.removeTab(idx)
                self._tab_widgets.pop(key, None)
        return True

    # ── Word wrap ─────────────────────────────────────────────────────────────

    def set_word_wrap_all(self, enabled: bool) -> None:
        """Apply word wrap to all open editors."""
        for editor in self._open_files.values():
            editor.set_word_wrap(enabled)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def current_editor(self) -> LaTeXEditor | None:
        widget = self.currentWidget()
        return widget if isinstance(widget, LaTeXEditor) else None

    @property
    def open_file_paths(self) -> list[str]:
        return list(self._open_files.keys())

    # ── Internals ─────────────────────────────────────────────────────────────

    def _confirm_close(self, editor: LaTeXEditor) -> bool:
        if not editor.is_modified:
            return True
        name = Path(editor.file_path).name
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            f"'{name}' has unsaved changes.\nSave before closing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Save:
            return editor.save_file()
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        return True  # Discard

    def _on_current_changed(self, index: int) -> None:
        widget = self.widget(index)
        if isinstance(widget, LaTeXEditor):
            event_bus.file_opened.emit(widget.file_path)

    def _on_file_modified(self, file_path: str, modified: bool) -> None:
        key = _norm(file_path)
        if key not in self._open_files:
            return
        editor = self._open_files[key]
        idx = self.indexOf(editor)
        name = Path(key).name
        self.setTabText(idx, f"● {name}" if modified else name)

    def _on_theme_changed(self, theme_name: str) -> None:
        # Update editor colors
        colors = self._theme_manager.editor_colors
        for editor in self._open_files.values():
            editor.apply_colors(
                colors,
                self._settings.editor_font_family,
                self._settings.editor_font_size,
            )
        # Update close button styles
        ss = _CLOSE_BTN_SS.get(theme_name, _CLOSE_BTN_SS["dark"])
        for btn in self._close_buttons:
            if btn.parent() is not None:
                btn.setStyleSheet(ss)