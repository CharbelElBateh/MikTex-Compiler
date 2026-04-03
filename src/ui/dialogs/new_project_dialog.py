"""New Project creation wizard dialog."""

from pathlib import Path

from PyQt6.QtCore import Qt
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
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.constants import SUPPORTED_ENGINES


class NewProjectDialog(QDialog):
    """Dialog for creating a new LaTeX project."""

    def __init__(self, default_engine: str = "pdflatex", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(500)
        self.setModal(True)

        # Project name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("My Thesis")

        # Directory
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Choose project directory...")
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_dir)
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(6)
        dir_layout.addWidget(self._dir_edit, 1)
        dir_layout.addWidget(browse_btn)

        # Subdirectory option
        self._create_subdir = QCheckBox("Create project in a new subdirectory")
        self._create_subdir.setChecked(True)
        self._create_subdir.setToolTip(
            "When checked, a subdirectory named after the project will be created.\n"
            "Uncheck this to use the selected directory directly (e.g. for existing projects)."
        )

        # Main file
        self._main_file_edit = QLineEdit("main.tex")

        # Engine
        self._engine_combo = QComboBox()
        engine_display = {"pdflatex": "pdfLaTeX", "xelatex": "XeLaTeX", "lualatex": "LuaLaTeX"}
        for eng in SUPPORTED_ENGINES:
            self._engine_combo.addItem(engine_display.get(eng, eng), eng)
        idx = self._engine_combo.findData(default_engine)
        if idx >= 0:
            self._engine_combo.setCurrentIndex(idx)

        # Bibliography
        self._bib_combo = QComboBox()
        self._bib_combo.addItems(["None", "BibTeX", "Biber"])
        self._bib_combo.setCurrentText("None")

        # Create main.tex template checkbox
        self._create_template = QCheckBox("Create a starter main.tex template")
        self._create_template.setChecked(True)

        # Form
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)
        form.addRow("Project Name:", self._name_edit)
        form.addRow("Directory:", dir_layout)
        form.addRow("", self._create_subdir)
        form.addRow("Main File:", self._main_file_edit)
        form.addRow("Engine:", self._engine_combo)
        form.addRow("Bibliography:", self._bib_combo)

        group = QGroupBox("Project Settings")
        group.setLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(group)
        layout.addWidget(self._create_template)
        layout.addWidget(buttons)

        self._name_edit.textChanged.connect(self._on_name_changed)

    def _browse_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if path:
            self._dir_edit.setText(path)
            # Auto-detect: if directory already has .tex files, uncheck subdirectory
            p = Path(path)
            if any(p.glob("*.tex")):
                self._create_subdir.setChecked(False)
                # If no name set, use the directory name
                if not self._name_edit.text().strip():
                    self._name_edit.setText(p.name)

    def _on_name_changed(self, name: str) -> None:
        """Update the effective path preview in tooltip."""
        pass

    def _validate_and_accept(self) -> None:
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Project name cannot be empty.")
            return
        if not self._dir_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Please choose a project directory.")
            return
        main_file = self._main_file_edit.text().strip()
        if not main_file:
            QMessageBox.warning(self, "Validation", "Main file name cannot be empty.")
            return
        if not main_file.endswith(".tex"):
            self._main_file_edit.setText(main_file + ".tex")
        self.accept()

    # ── Result accessors ──

    @property
    def project_name(self) -> str:
        return self._name_edit.text().strip()

    @property
    def project_dir(self) -> Path:
        base = Path(self._dir_edit.text().strip())
        if self._create_subdir.isChecked():
            return base / self.project_name.replace(" ", "_")
        return base

    @property
    def main_file(self) -> str:
        f = self._main_file_edit.text().strip()
        return f if f.endswith(".tex") else f + ".tex"

    @property
    def engine(self) -> str:
        return self._engine_combo.currentData() or "pdflatex"

    @property
    def bibliography_tool(self) -> str:
        return self._bib_combo.currentText().lower()

    @property
    def create_template(self) -> bool:
        return self._create_template.isChecked()
