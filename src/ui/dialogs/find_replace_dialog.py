"""Find and Replace dialog."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.editor.search_replace import SearchEngine


class FindReplaceDialog(QDialog):
    """Non-modal find/replace dialog attached to the current editor."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Find and Replace")
        self.setMinimumWidth(420)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.Tool
        )

        self._engine = SearchEngine()
        self._editor = None

        # Find row
        self._find_edit = QLineEdit()
        self._find_edit.setPlaceholderText("Find...")
        self._find_edit.returnPressed.connect(self._on_find_next)
        self._match_label = QLabel("")

        # Replace row
        self._replace_edit = QLineEdit()
        self._replace_edit.setPlaceholderText("Replace with...")

        # Options
        self._case_check = QCheckBox("Match &case")
        self._word_check = QCheckBox("&Whole word")
        self._regex_check = QCheckBox("&Regex")
        self._wrap_check = QCheckBox("Wrap a&round")
        self._wrap_check.setChecked(True)

        opts = QHBoxLayout()
        opts.addWidget(self._case_check)
        opts.addWidget(self._word_check)
        opts.addWidget(self._regex_check)
        opts.addWidget(self._wrap_check)
        opts.addStretch()

        # Buttons
        find_next_btn = QPushButton("Find &Next")
        find_next_btn.setDefault(True)
        find_next_btn.clicked.connect(self._on_find_next)

        find_prev_btn = QPushButton("Find &Previous")
        find_prev_btn.clicked.connect(self._on_find_prev)

        count_btn = QPushButton("C&ount")
        count_btn.clicked.connect(self._on_count)

        replace_btn = QPushButton("&Replace")
        replace_btn.clicked.connect(self._on_replace)

        replace_all_btn = QPushButton("Replace &All")
        replace_all_btn.clicked.connect(self._on_replace_all)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        # Layout
        grid = QGridLayout()
        grid.addWidget(QLabel("Find:"), 0, 0)
        grid.addWidget(self._find_edit, 0, 1)
        grid.addWidget(self._match_label, 0, 2)
        grid.addWidget(QLabel("Replace:"), 1, 0)
        grid.addWidget(self._replace_edit, 1, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(find_next_btn)
        btn_layout.addWidget(find_prev_btn)
        btn_layout.addWidget(count_btn)
        btn_layout.addWidget(replace_btn)
        btn_layout.addWidget(replace_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(grid)
        layout.addLayout(opts)
        layout.addLayout(btn_layout)

    def set_editor(self, editor) -> None:
        self._editor = editor

    def set_find_text(self, text: str) -> None:
        self._find_edit.setText(text)
        self._find_edit.selectAll()

    def _search_kwargs(self) -> dict:
        return {
            "case_sensitive": self._case_check.isChecked(),
            "whole_word": self._word_check.isChecked(),
            "use_regex": self._regex_check.isChecked(),
            "wrap": self._wrap_check.isChecked(),
        }

    def _on_find_next(self) -> None:
        if not self._editor:
            return
        found = self._engine.find_next(
            self._editor, self._find_edit.text(), **self._search_kwargs()
        )
        self._match_label.setText("" if found else "Not found")

    def _on_find_prev(self) -> None:
        if not self._editor:
            return
        # First set parameters, then find previous
        kwargs = self._search_kwargs()
        self._engine.find_next(
            self._editor, self._find_edit.text(),
            forward=False, **kwargs,
        )

    def _on_count(self) -> None:
        if not self._editor:
            return
        count = self._engine.find_all(
            self._editor, self._find_edit.text(), **self._search_kwargs()
        )
        self._match_label.setText(f"{count} matches")

    def _on_replace(self) -> None:
        if not self._editor:
            return
        self._engine.replace_and_find(
            self._editor,
            self._find_edit.text(),
            self._replace_edit.text(),
            **self._search_kwargs(),
        )

    def _on_replace_all(self) -> None:
        if not self._editor:
            return
        count = self._engine.replace_all(
            self._editor,
            self._find_edit.text(),
            self._replace_edit.text(),
            **{k: v for k, v in self._search_kwargs().items() if k != "wrap"},
        )
        self._match_label.setText(f"Replaced {count}")
