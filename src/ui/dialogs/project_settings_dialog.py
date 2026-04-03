"""Per-project settings dialog."""

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
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.constants import SUPPORTED_ENGINES
from src.core.project import Project


class ProjectSettingsDialog(QDialog):
    """Edit per-project compiler and build settings."""

    def __init__(self, project: Project, parent=None) -> None:
        super().__init__(parent)
        self._project = project
        self.setWindowTitle(f"Project Settings — {project.name}")
        self.setMinimumWidth(500)
        self.setModal(True)

        # Engine
        self._engine_combo = QComboBox()
        engine_display = {"pdflatex": "pdfLaTeX", "xelatex": "XeLaTeX", "lualatex": "LuaLaTeX"}
        for eng in SUPPORTED_ENGINES:
            self._engine_combo.addItem(engine_display.get(eng, eng), eng)
        idx = self._engine_combo.findData(project.engine)
        if idx >= 0:
            self._engine_combo.setCurrentIndex(idx)

        # Main file
        self._main_file_edit = QLineEdit(project.main_file)
        browse_main = QPushButton("…")
        browse_main.setFixedWidth(28)
        browse_main.clicked.connect(self._browse_main_file)
        main_layout = QHBoxLayout()
        main_layout.addWidget(self._main_file_edit)
        main_layout.addWidget(browse_main)

        # Output directory
        self._output_dir_edit = QLineEdit(project.output_directory)

        # Bibliography
        self._bib_combo = QComboBox()
        self._bib_combo.addItems(["none", "bibtex", "biber"])
        self._bib_combo.setCurrentText(project.bibliography_tool)

        # SyncTeX
        self._synctex_check = QCheckBox("Enable SyncTeX (source↔PDF sync)")
        self._synctex_check.setChecked(project.synctex)

        # Max passes
        self._max_passes_spin = QSpinBox()
        self._max_passes_spin.setRange(1, 5)
        self._max_passes_spin.setValue(project.max_passes)

        # Extra args
        self._extra_args_edit = QLineEdit(" ".join(project.extra_args))
        self._extra_args_edit.setPlaceholderText("-shell-escape")

        # Compiler form
        compiler_form = QFormLayout()
        compiler_form.addRow("Engine:", self._engine_combo)
        compiler_form.addRow("Main File:", main_layout)
        compiler_form.addRow("Output Directory:", self._output_dir_edit)
        compiler_form.addRow("Bibliography:", self._bib_combo)
        compiler_form.addRow("Max Passes:", self._max_passes_spin)
        compiler_form.addRow("Extra Engine Args:", self._extra_args_edit)
        compiler_group = QGroupBox("Compiler")
        compiler_group.setLayout(compiler_form)

        # SyncTeX
        sync_group = QGroupBox("Navigation")
        sync_layout = QVBoxLayout(sync_group)
        sync_layout.addWidget(self._synctex_check)

        # Custom commands
        self._pre_build_edit = QPlainTextEdit("\n".join(project.pre_build))
        self._pre_build_edit.setPlaceholderText("One command per line")
        self._pre_build_edit.setMaximumHeight(80)

        self._post_build_edit = QPlainTextEdit("\n".join(project.post_build))
        self._post_build_edit.setPlaceholderText("One command per line")
        self._post_build_edit.setMaximumHeight(80)

        cmd_form = QFormLayout()
        cmd_form.addRow("Pre-build:", self._pre_build_edit)
        cmd_form.addRow("Post-build:", self._post_build_edit)
        cmd_group = QGroupBox("Custom Commands")
        cmd_group.setLayout(cmd_form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(compiler_group)
        layout.addWidget(sync_group)
        layout.addWidget(cmd_group)
        layout.addWidget(buttons)

    def _browse_main_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Main File",
            str(self._project.root_path),
            "LaTeX Files (*.tex)"
        )
        if path:
            try:
                rel = Path(path).relative_to(self._project.root_path)
                self._main_file_edit.setText(str(rel))
            except ValueError:
                self._main_file_edit.setText(path)

    def apply_to_project(self) -> None:
        """Write dialog values back to the project and save."""
        p = self._project
        p.engine = self._engine_combo.currentData() or "pdflatex"
        p.main_file = self._main_file_edit.text().strip()
        p.output_directory = self._output_dir_edit.text().strip() or "build"
        p.bibliography_tool = self._bib_combo.currentText()
        p.synctex = self._synctex_check.isChecked()
        p.max_passes = self._max_passes_spin.value()
        p.extra_args = self._extra_args_edit.text().split()
        p.pre_build = [l for l in self._pre_build_edit.toPlainText().splitlines() if l.strip()]
        p.post_build = [l for l in self._post_build_edit.toPlainText().splitlines() if l.strip()]
        p.save()
