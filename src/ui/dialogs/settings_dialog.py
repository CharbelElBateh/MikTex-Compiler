"""Global application settings dialog (tabbed)."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.constants import SUPPORTED_ENGINES
from src.core.settings_manager import SettingsManager


class SettingsDialog(QDialog):
    """Global application settings with tabs for Editor, Compiler, Viewer, MiKTeX."""

    def __init__(self, settings: SettingsManager, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)
        self.setModal(True)

        self._tabs = QTabWidget()
        self._build_editor_tab()
        self._build_compiler_tab()
        self._build_viewer_tab()
        self._build_miktex_tab()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        buttons.accepted.connect(self._apply_and_accept)
        buttons.rejected.connect(self.reject)
        apply_btn = buttons.button(QDialogButtonBox.StandardButton.Apply)
        if apply_btn:
            apply_btn.clicked.connect(self._apply)

        layout = QVBoxLayout(self)
        layout.addWidget(self._tabs)
        layout.addWidget(buttons)

    # ── Editor Tab ──

    def _build_editor_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        self._font_family = QLineEdit(self._settings.editor_font_family)
        form.addRow("Font Family:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(6, 72)
        self._font_size.setValue(self._settings.editor_font_size)
        form.addRow("Font Size:", self._font_size)

        self._tab_width = QSpinBox()
        self._tab_width.setRange(1, 8)
        self._tab_width.setValue(self._settings.editor_tab_width)
        form.addRow("Tab Width:", self._tab_width)

        self._word_wrap = QCheckBox("Enable word wrap")
        self._word_wrap.setChecked(self._settings.editor_word_wrap)
        form.addRow("", self._word_wrap)

        self._show_whitespace = QCheckBox("Show whitespace characters")
        self._show_whitespace.setChecked(self._settings.editor_show_whitespace)
        form.addRow("", self._show_whitespace)

        self._tabs.addTab(tab, "Editor")

    # ── Compiler Tab ──

    def _build_compiler_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        self._default_engine = QComboBox()
        engine_display = {"pdflatex": "pdfLaTeX", "xelatex": "XeLaTeX", "lualatex": "LuaLaTeX"}
        for eng in SUPPORTED_ENGINES:
            self._default_engine.addItem(engine_display.get(eng, eng), eng)
        idx = self._default_engine.findData(self._settings.compiler_default_engine)
        if idx >= 0:
            self._default_engine.setCurrentIndex(idx)
        form.addRow("Default Engine:", self._default_engine)

        self._auto_compile = QCheckBox("Auto-compile on save")
        self._auto_compile.setChecked(self._settings.compiler_auto_compile)
        form.addRow("", self._auto_compile)

        self._tabs.addTab(tab, "Compiler")

    # ── Viewer Tab ──

    def _build_viewer_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        self._default_zoom = QSpinBox()
        self._default_zoom.setRange(25, 400)
        self._default_zoom.setSuffix("%")
        self._default_zoom.setValue(self._settings.viewer_default_zoom)
        form.addRow("Default Zoom:", self._default_zoom)

        self._render_dpi = QSpinBox()
        self._render_dpi.setRange(72, 300)
        self._render_dpi.setValue(self._settings.viewer_render_dpi)
        form.addRow("Render DPI:", self._render_dpi)

        self._tabs.addTab(tab, "Viewer")

    # ── MiKTeX Tab ──

    def _build_miktex_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Bin directory
        group = QGroupBox("MiKTeX Installation")
        form = QFormLayout(group)

        self._miktex_path = QLineEdit(str(self._settings.miktex_bin_dir))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_miktex)
        path_row = QHBoxLayout()
        path_row.addWidget(self._miktex_path)
        path_row.addWidget(browse_btn)
        form.addRow("Bin Directory:", path_row)

        # Status
        bin_path = Path(self._miktex_path.text())
        status = "Found" if (bin_path / "pdflatex.exe").is_file() else "Not found"
        self._miktex_status = QLabel(f"Status: {status}")
        form.addRow("", self._miktex_status)

        layout.addWidget(group)
        layout.addStretch()

        self._tabs.addTab(tab, "MiKTeX")

    def _browse_miktex(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select MiKTeX bin directory", self._miktex_path.text()
        )
        if path:
            self._miktex_path.setText(path)
            has_pdflatex = (Path(path) / "pdflatex.exe").is_file()
            self._miktex_status.setText(f"Status: {'Found' if has_pdflatex else 'Not found'}")

    def _apply(self) -> None:
        s = self._settings
        s.editor_font_family = self._font_family.text().strip()
        s.editor_font_size = self._font_size.value()
        s.editor_tab_width = self._tab_width.value()
        s.editor_word_wrap = self._word_wrap.isChecked()
        s.editor_show_whitespace = self._show_whitespace.isChecked()
        s.compiler_default_engine = self._default_engine.currentData() or "pdflatex"
        s.compiler_auto_compile = self._auto_compile.isChecked()
        s.viewer_default_zoom = self._default_zoom.value()
        s.viewer_render_dpi = self._render_dpi.value()
        s.miktex_bin_dir = Path(self._miktex_path.text().strip())
        s.sync()

    def _apply_and_accept(self) -> None:
        self._apply()
        self.accept()
