from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.compiler.error_model import CompilationError
from src.core.event_bus import event_bus
from src.ui.error_list_widget import ErrorListWidget


class BuildLogView(QPlainTextEdit):
    """Read-only streaming build log with colour-coded output."""

    _COLORS = {
        "error":   "#f47878",
        "warning": "#dcdcaa",
        "success": "#4ec9b0",
        "header":  "#608bc4",
        "default": "#c8c8c8",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(10_000)
        font = QFont("Cascadia Code", 11)
        if not font.exactMatch():
            font = QFont("Consolas", 11)
        font.setFixedPitch(True)
        self.setFont(font)

    def append_line(self, line: str, timestamp: str = "") -> None:
        """Append a line with colour coding.

        ``timestamp`` is prepended (dimly) when provided.
        """
        lower = line.lower()
        if line.startswith("!") or "error" in lower:
            color_key = "error"
        elif "warning" in lower:
            color_key = "warning"
        elif line.startswith(">>>"):
            color_key = "header"
        else:
            color_key = "default"

        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        # Timestamp prefix (dimmer colour)
        if timestamp:
            ts_fmt = QTextCharFormat()
            ts_fmt.setForeground(QColor("#555566"))
            cursor.insertText(f"[{timestamp}] ", ts_fmt)

        # Main line
        main_fmt = QTextCharFormat()
        main_fmt.setForeground(QColor(self._COLORS[color_key]))
        cursor.insertText(line + "\n", main_fmt)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_success(self, line: str) -> None:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._COLORS["success"]))
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(line + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_log(self) -> None:
        self.clear()


class OutputPanel(QWidget):
    """Tabbed panel: Build Output | Errors | Warnings."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._start_time: datetime | None = None

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        # Tab 0: Raw build log
        self._log_view = BuildLogView()
        self._tabs.addTab(self._log_view, "Build Output")

        # Tab 1: Errors
        self._error_list = ErrorListWidget()
        self._tabs.addTab(self._error_list, "Errors (0)")

        # Tab 2: Warnings
        self._warning_list = ErrorListWidget()
        self._tabs.addTab(self._warning_list, "Warnings (0)")

        # Toolbar row: time label + clear button
        self._time_label = QLabel("")
        self._time_label.setStyleSheet(
            "font-size: 11px; color: #888888; background: transparent;"
        )
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(24)
        self._clear_btn.setProperty("flat", True)
        self._clear_btn.clicked.connect(self._on_clear)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._time_label, 1)
        btn_layout.addWidget(self._clear_btn)
        btn_layout.setContentsMargins(8, 2, 4, 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self._tabs)

        self._connect_signals()

    def _connect_signals(self) -> None:
        event_bus.compilation_started.connect(self._on_compilation_started)
        event_bus.compilation_output.connect(self._on_output_line)
        event_bus.compilation_finished.connect(self._on_compilation_finished)

    def _now(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _on_compilation_started(self, engine: str) -> None:
        self._start_time = datetime.now()
        self._log_view.clear_log()
        self._error_list.setRowCount(0)
        self._warning_list.setRowCount(0)
        self._tabs.setTabText(1, "Errors (0)")
        self._tabs.setTabText(2, "Warnings (0)")
        self._tabs.setCurrentIndex(0)
        self._time_label.setText("")
        ts = self._start_time.strftime("%H:%M:%S")
        self._log_view.append_line(f">>> [{ts}] Starting {engine}…")

    def _on_output_line(self, line: str) -> None:
        self._log_view.append_line(line)

    def _on_compilation_finished(self, success: bool, errors: list) -> None:
        errors_only = [e for e in errors if e.level == "error"]
        warnings_only = [e for e in errors if e.level in ("warning", "badbox")]

        self._error_list.populate(errors_only)
        self._warning_list.populate(warnings_only)

        self._tabs.setTabText(1, f"Errors ({len(errors_only)})")
        self._tabs.setTabText(2, f"Warnings ({len(warnings_only)})")

        # Compute elapsed time
        elapsed_str = ""
        if self._start_time:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            elapsed_str = f"{elapsed:.1f}s"
            self._time_label.setText(f"Finished in {elapsed_str}")

        ts = self._now()
        if success:
            suffix = f" in {elapsed_str}" if elapsed_str else ""
            self._log_view.append_success(f">>> [{ts}] ✓ Compilation successful{suffix}")
        else:
            e_word = "error" if len(errors_only) == 1 else "errors"
            suffix = f" ({len(errors_only)} {e_word})"
            self._log_view.append_line(f">>> [{ts}] ✗ Compilation failed{suffix}")

        if errors_only:
            self._tabs.setCurrentIndex(1)

    def _on_clear(self) -> None:
        self._log_view.clear_log()
        self._error_list.setRowCount(0)
        self._warning_list.setRowCount(0)
        self._tabs.setTabText(1, "Errors (0)")
        self._tabs.setTabText(2, "Warnings (0)")
        self._time_label.setText("")