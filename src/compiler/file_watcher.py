"""File watcher with debounce for auto-compile on save."""

from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.constants import AUTO_COMPILE_DELAY_MS, TEX_EXTENSIONS
from src.core.logging_config import get_logger

log = get_logger("compiler.file_watcher")

try:
    from watchdog.events import FileModifiedEvent, FileSystemEventHandler
    from watchdog.observers import Observer
    _HAS_WATCHDOG = True
except ImportError:
    _HAS_WATCHDOG = False
    log.warning("watchdog not installed — auto-compile on save disabled")


class _ChangeHandler(FileSystemEventHandler if _HAS_WATCHDOG else object):
    """Watchdog handler that filters for TeX files and emits a Qt signal."""

    def __init__(self, callback) -> None:
        if _HAS_WATCHDOG:
            super().__init__()
        self._callback = callback

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in TEX_EXTENSIONS:
            self._callback(str(path))


class FileWatcher(QObject):
    """Watches a directory for TeX file changes and triggers auto-compile.

    Uses watchdog for OS-native file system events with a Qt timer debounce
    to avoid compiling on every keystroke when editors auto-save rapidly.
    """

    file_changed = pyqtSignal(str)  # path that changed
    auto_compile_triggered = pyqtSignal()

    def __init__(self, delay_ms: int | None = None, parent=None) -> None:
        super().__init__(parent)
        self._observer = None
        self._watch = None
        self._watched_path: Path | None = None
        self._enabled = False

        if delay_ms is None:
            delay_ms = AUTO_COMPILE_DELAY_MS

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(delay_ms)
        self._debounce_timer.timeout.connect(self._on_debounce_fire)

        self._pending_path: str = ""

    @property
    def available(self) -> bool:
        return _HAS_WATCHDOG

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if not value:
            self._debounce_timer.stop()

    def watch(self, directory: Path) -> None:
        """Start watching a directory for changes."""
        if not _HAS_WATCHDOG:
            return

        self.stop()
        if not directory.is_dir():
            log.warning("Cannot watch non-directory: %s", directory)
            return

        self._watched_path = directory
        handler = _ChangeHandler(self._on_file_changed)
        self._observer = Observer()
        self._watch = self._observer.schedule(handler, str(directory), recursive=True)
        self._observer.start()
        log.info("Watching directory: %s", directory)

    def stop(self) -> None:
        """Stop watching."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
            self._watch = None
            self._watched_path = None

    def _on_file_changed(self, path: str) -> None:
        """Called from watchdog thread — schedules debounced signal via timer."""
        self._pending_path = path
        self.file_changed.emit(path)
        if self._enabled:
            # Reset debounce timer (called from non-Qt thread, but QTimer.start is thread-safe)
            self._debounce_timer.start()

    def _on_debounce_fire(self) -> None:
        log.debug("Auto-compile triggered by: %s", self._pending_path)
        self.auto_compile_triggered.emit()
