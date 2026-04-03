from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from src.compiler.error_model import CompilationError
from src.core.event_bus import event_bus


class ErrorListWidget(QTableWidget):
    """Clickable table of compilation errors/warnings.

    Double-clicking a row jumps to the source file and line in the editor.
    """

    _LEVEL_ICONS = {
        "error": "✖",
        "warning": "⚠",
        "badbox": "□",
        "info": "ℹ",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["", "File", "Line", "Message"])
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(0, 28)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 56)

        self.verticalHeader().setVisible(False)
        self.cellDoubleClicked.connect(self._on_double_clicked)

    def populate(self, errors: list[CompilationError], level_filter: str | None = None) -> None:
        self.setSortingEnabled(False)
        self.setRowCount(0)

        for err in errors:
            if level_filter and err.level != level_filter:
                continue

            row = self.rowCount()
            self.insertRow(row)

            icon = self._LEVEL_ICONS.get(err.level, "?")
            icon_item = QTableWidgetItem(icon)
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_item.setToolTip(err.level.capitalize())

            file_name = Path(err.file_path).name if err.file_path else "?"
            file_item = QTableWidgetItem(file_name)
            file_item.setToolTip(err.file_path)

            line_item = QTableWidgetItem(str(err.line) if err.line > 0 else "")
            line_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            msg_item = QTableWidgetItem(err.message)
            msg_item.setToolTip(err.raw_context)

            # Store the full error on the row for navigation
            icon_item.setData(Qt.ItemDataRole.UserRole, err)

            self.setItem(row, 0, icon_item)
            self.setItem(row, 1, file_item)
            self.setItem(row, 2, line_item)
            self.setItem(row, 3, msg_item)

        self.setSortingEnabled(True)

    def _on_double_clicked(self, row: int, _col: int) -> None:
        item = self.item(row, 0)
        if not item:
            return
        err: CompilationError | None = item.data(Qt.ItemDataRole.UserRole)
        if err and err.file_path and err.line > 0:
            event_bus.synctex_reverse.emit(err.file_path, err.line, 1)
