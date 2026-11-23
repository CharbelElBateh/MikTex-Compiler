import os
from pathlib import Path

from PyQt6.QtCore import QDir, QModelIndex, QSize, Qt
from PyQt6.QtGui import QColor, QFileSystemModel, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from src.constants import ALL_PROJECT_EXTENSIONS, TEX_EXTENSIONS
from src.core.event_bus import event_bus
from src.core.logging_config import get_logger

log = get_logger("ui.file_tree")

# Extension → (dark_color, light_color)
_EXT_COLORS: dict[str, tuple[str, str]] = {
    # LaTeX source
    ".tex":  ("#7ab4e8", "#1a6dbf"),
    ".bib":  ("#dcdcaa", "#8a7a00"),
    ".bst":  ("#d7ba7d", "#7a6000"),
    ".dtx":  ("#9cdcfe", "#0070c1"),
    ".ins":  ("#9cdcfe", "#0070c1"),
    # Style / class
    ".sty":  ("#c586c0", "#8b2cc0"),
    ".cls":  ("#da70d6", "#8b008b"),
    ".def":  ("#c586c0", "#8b2cc0"),
    ".fd":   ("#c586c0", "#8b2cc0"),
    ".cfg":  ("#c586c0", "#8b2cc0"),
    # Output / images
    ".pdf":  ("#f48771", "#c0392b"),
    ".png":  ("#4ec9b0", "#1a8c7a"),
    ".jpg":  ("#4ec9b0", "#1a8c7a"),
    ".jpeg": ("#4ec9b0", "#1a8c7a"),
    ".gif":  ("#4ec9b0", "#1a8c7a"),
    ".bmp":  ("#4ec9b0", "#1a8c7a"),
    ".svg":  ("#6dc6a8", "#1b7a6e"),
    ".eps":  ("#b5cea8", "#3a6b30"),
    # Text / misc
    ".md":   ("#6a9955", "#2d7a2d"),
    ".txt":  ("#cccccc", "#555555"),
}


class _FileTreeDelegate(QStyledItemDelegate):
    """Colorises file names according to their extension."""

    def __init__(self, model: QFileSystemModel, parent=None) -> None:
        super().__init__(parent)
        self._model = model

    def initStyleOption(  # noqa: N802
        self, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        super().initStyleOption(option, index)

        file_path = self._model.filePath(index)
        if not file_path or self._model.isDir(index):
            # Directories: bold
            option.font.setBold(True)
            return

        ext = Path(file_path).suffix.lower()
        if ext not in _EXT_COLORS:
            return

        # Detect dark/light theme from the widget's palette
        bg = option.palette.color(QPalette.ColorRole.Base)
        is_dark = bg.lightness() < 128

        dark_c, light_c = _EXT_COLORS[ext]
        color_str = dark_c if is_dark else light_c

        if not (option.state & option.state.__class__.State_Selected):
            # Only color when not selected (selected items use highlight color)
            option.palette.setColor(QPalette.ColorRole.Text, QColor(color_str))


class FileTreeWidget(QWidget):
    """Project file tree using QFileSystemModel + QTreeView."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._root_path: str | None = None
        self._open_callback = None

        # Explorer-style section header (VS Code sidebar style)
        self._header = QLabel("EXPLORER")
        self._header.setObjectName("file_tree_header")
        self._header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._header.setContentsMargins(0, 0, 0, 0)
        self._header.setFixedHeight(28)

        self._model = QFileSystemModel()
        self._model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        self._model.setNameFilters(self._build_name_filters())
        self._model.setNameFilterDisables(False)

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(18)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.setIconSize(QSize(16, 16))  # ensures OS icons render at proper size

        # Apply extension-colour delegate
        self._delegate = _FileTreeDelegate(self._model, self._tree)
        self._tree.setItemDelegate(self._delegate)

        # Hide size, type, date columns
        for col in range(1, 4):
            self._tree.setColumnHidden(col, True)

        # clicked covers single-click opens; activated covers Enter/double-click
        self._tree.activated.connect(self._on_activated)
        self._tree.clicked.connect(self._on_clicked)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addWidget(self._tree)

        event_bus.project_opened.connect(self._on_project_opened)
        event_bus.project_closed.connect(self._on_project_closed)

    def set_open_callback(self, callback) -> None:
        self._open_callback = callback

    def set_root(self, path: str) -> None:
        self._root_path = path
        root_index = self._model.setRootPath(path)
        self._tree.setRootIndex(root_index)
        log.debug("File tree root: %s", path)

    def clear(self) -> None:
        self._root_path = None
        self._model.setRootPath("")

    def refresh(self) -> None:
        """Force the model to re-read the watched directory."""
        if self._root_path:
            self.set_root(self._root_path)

    def _build_name_filters(self) -> list[str]:
        filters = []
        for ext in sorted(ALL_PROJECT_EXTENSIONS):
            filters.append(f"*{ext}")
        return filters

    def _on_clicked(self, index: QModelIndex) -> None:
        if self._model.isDir(index):
            return
        file_path = os.path.normpath(self._model.filePath(index))
        log.info("File tree click: %s", file_path)
        if self._open_callback:
            self._open_callback(file_path)

    def _on_activated(self, index: QModelIndex) -> None:
        if self._model.isDir(index):
            return
        file_path = os.path.normpath(self._model.filePath(index))
        if self._open_callback:
            self._open_callback(file_path)

    def _on_context_menu(self, pos) -> None:
        index = self._tree.indexAt(pos)
        if not index.isValid():
            return

        file_path = os.path.normpath(self._model.filePath(index))
        is_dir = self._model.isDir(index)

        menu = QMenu(self)

        if not is_dir:
            open_action = menu.addAction("Open")
            open_action.triggered.connect(
                lambda: self._open_callback and self._open_callback(file_path)
            )

        copy_path_action = menu.addAction("Copy Path")
        copy_path_action.triggered.connect(lambda: self._copy_to_clipboard(file_path))

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _copy_to_clipboard(self, text: str) -> None:
        QApplication.clipboard().setText(text)

    def _on_project_opened(self, project) -> None:
        root = str(getattr(project, "root_path", ""))
        if root:
            self.set_root(root)
        name = getattr(project, "name", None)
        self._header.setText(name.upper() if name else "EXPLORER")

    def _on_project_closed(self) -> None:
        self.clear()
        self._header.setText("EXPLORER")
