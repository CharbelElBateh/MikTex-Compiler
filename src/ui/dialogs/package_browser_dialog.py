"""MiKTeX Package Browser dialog."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.core.logging_config import get_logger
from src.packages.package_manager import PackageManager
from src.packages.package_worker import PackageWorker

log = get_logger("ui.package_browser")


class PackageBrowserDialog(QDialog):
    """Browse, search, install and uninstall MiKTeX packages."""

    def __init__(self, miktex_bin_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MiKTeX Package Manager")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self._manager = PackageManager(miktex_bin_dir)
        self._worker = PackageWorker(self._manager, self)
        self._worker.operation_done.connect(self._on_operation_done)
        self._worker.progress_message.connect(self._on_progress)

        # Search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search packages...")
        self._search.textChanged.connect(self._apply_filter)

        # Filter combo
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Installed", "Not Installed"])
        self._filter_combo.currentTextChanged.connect(self._apply_filter)

        search_row = QHBoxLayout()
        search_row.addWidget(self._search)
        search_row.addWidget(self._filter_combo)

        # Package table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Status", "Package", "Description"])
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 70)
        self._table.setColumnWidth(1, 180)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        # Action buttons
        self._install_btn = QPushButton("Install")
        self._install_btn.clicked.connect(self._on_install)
        self._uninstall_btn = QPushButton("Uninstall")
        self._uninstall_btn.clicked.connect(self._on_uninstall)
        self._update_btn = QPushButton("Update All")
        self._update_btn.clicked.connect(self._on_update_all)
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._on_refresh)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._install_btn)
        btn_row.addWidget(self._uninstall_btn)
        btn_row.addWidget(self._update_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._refresh_btn)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._status_label = QLabel("")

        status_row = QHBoxLayout()
        status_row.addWidget(self._status_label)
        status_row.addWidget(self._progress)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        layout = QVBoxLayout(self)
        layout.addLayout(search_row)
        layout.addWidget(self._table)
        layout.addLayout(btn_row)
        layout.addLayout(status_row)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # Initial load
        self._on_refresh()

    def _populate_table(self, packages) -> None:
        self._table.setRowCount(len(packages))
        for row, pkg in enumerate(packages):
            status_item = QTableWidgetItem("Installed" if pkg.installed else "")
            name_item = QTableWidgetItem(pkg.name)
            title_item = QTableWidgetItem(pkg.title)

            # Store package name for later retrieval
            name_item.setData(Qt.ItemDataRole.UserRole, pkg.name)

            self._table.setItem(row, 0, status_item)
            self._table.setItem(row, 1, name_item)
            self._table.setItem(row, 2, title_item)

    def _apply_filter(self) -> None:
        query = self._search.text().strip()
        filter_mode = self._filter_combo.currentText()

        if query:
            packages = self._manager.search(query)
        else:
            packages = self._manager.packages

        if filter_mode == "Installed":
            packages = [p for p in packages if p.installed]
        elif filter_mode == "Not Installed":
            packages = [p for p in packages if not p.installed]

        self._populate_table(packages)
        self._status_label.setText(f"{len(packages)} packages")

    def _selected_package(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 1)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _set_busy(self, busy: bool) -> None:
        self._progress.setVisible(busy)
        self._install_btn.setEnabled(not busy)
        self._uninstall_btn.setEnabled(not busy)
        self._update_btn.setEnabled(not busy)
        self._refresh_btn.setEnabled(not busy)

    def _on_install(self) -> None:
        name = self._selected_package()
        if not name:
            return
        self._set_busy(True)
        self._worker.install(name)

    def _on_uninstall(self) -> None:
        name = self._selected_package()
        if not name:
            return
        reply = QMessageBox.question(
            self, "Uninstall Package",
            f"Uninstall '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._set_busy(True)
            self._worker.uninstall(name)

    def _on_update_all(self) -> None:
        self._set_busy(True)
        self._worker.update()

    def _on_refresh(self) -> None:
        self._set_busy(True)
        self._worker.refresh_list()

    def _on_progress(self, msg: str) -> None:
        self._status_label.setText(msg)

    def _on_operation_done(self, op: str, name: str, success: bool, msg: str) -> None:
        self._set_busy(False)
        if op == "refresh":
            self._apply_filter()
        else:
            status = "completed" if success else "failed"
            self._status_label.setText(f"{op} {name}: {status}")
            if not success:
                QMessageBox.warning(self, "Package Operation Failed", msg)
            self._apply_filter()
