"""Keyboard shortcuts reference dialog."""

from PyQt6.QtWidgets import (
    QDialog,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


# Default keybindings shown for reference
_KEYBINDINGS = [
    ("New File", "Ctrl+N"),
    ("Open File", "Ctrl+O"),
    ("Save", "Ctrl+S"),
    ("Save As", "Ctrl+Shift+S"),
    ("Close File", "Ctrl+W"),
    ("Undo", "Ctrl+Z"),
    ("Redo", "Ctrl+Y"),
    ("Cut", "Ctrl+X"),
    ("Copy", "Ctrl+C"),
    ("Paste", "Ctrl+V"),
    ("Select All", "Ctrl+A"),
    ("Find", "Ctrl+F"),
    ("Find & Replace", "Ctrl+H"),
    ("Go to Line", "Ctrl+G"),
    ("Compile", "F5"),
    ("Stop Compilation", "Ctrl+Break"),
    ("Toggle File Tree", "Ctrl+B"),
    ("Toggle PDF Viewer", "Ctrl+P"),
    ("Toggle Output Panel", "Ctrl+`"),
    ("Toggle Theme", "Ctrl+Shift+T"),
    ("Zoom In", "Ctrl+="),
    ("Zoom Out", "Ctrl+-"),
    ("Reset Zoom", "Ctrl+0"),
    ("Forward SyncTeX", "Ctrl+Enter"),
    ("Preferences", "Ctrl+,"),
    ("Exit", "Alt+F4"),
]


class KeybindingsDialog(QDialog):
    """Displays the application keyboard shortcuts."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(440, 500)
        self.setModal(True)

        table = QTableWidget(len(_KEYBINDINGS), 2)
        table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(1, 150)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        for row, (action, shortcut) in enumerate(_KEYBINDINGS):
            table.setItem(row, 0, QTableWidgetItem(action))
            table.setItem(row, 1, QTableWidgetItem(shortcut))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        layout = QVBoxLayout(self)
        layout.addWidget(table)
        layout.addWidget(close_btn)
