"""Background thread for async package operations."""

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.logging_config import get_logger
from src.packages.package_manager import PackageManager

log = get_logger("packages.worker")


class PackageWorker(QThread):
    """Runs package operations (install/uninstall/update) in a background thread."""

    operation_done = pyqtSignal(str, str, bool, str)  # operation, pkg_name, success, message
    progress_message = pyqtSignal(str)  # status text

    def __init__(self, manager: PackageManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._operation: str = ""
        self._package_name: str = ""

    def install(self, name: str) -> None:
        self._operation = "install"
        self._package_name = name
        self.start()

    def uninstall(self, name: str) -> None:
        self._operation = "uninstall"
        self._package_name = name
        self.start()

    def update(self, name: str | None = None) -> None:
        self._operation = "update"
        self._package_name = name or ""
        self.start()

    def update_db(self) -> None:
        self._operation = "update_db"
        self._package_name = ""
        self.start()

    def refresh_list(self) -> None:
        self._operation = "refresh"
        self._package_name = ""
        self.start()

    def run(self) -> None:
        op = self._operation
        name = self._package_name

        try:
            if op == "install":
                self.progress_message.emit(f"Installing {name}...")
                success, msg = self._manager.install(name)
            elif op == "uninstall":
                self.progress_message.emit(f"Uninstalling {name}...")
                success, msg = self._manager.uninstall(name)
            elif op == "update":
                label = name or "all packages"
                self.progress_message.emit(f"Updating {label}...")
                success, msg = self._manager.update(name or None)
            elif op == "update_db":
                self.progress_message.emit("Updating package database...")
                success, msg = self._manager.update_db()
            elif op == "refresh":
                self.progress_message.emit("Loading package list...")
                self._manager.load()
                success, msg = True, "Package list loaded"
            else:
                success, msg = False, f"Unknown operation: {op}"

            self.operation_done.emit(op, name, success, msg)
        except Exception as e:
            log.exception("Package operation failed")
            self.operation_done.emit(op, name, False, str(e))
