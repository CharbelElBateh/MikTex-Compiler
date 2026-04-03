from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel, QStatusBar

from src.core.event_bus import event_bus

# Per-widget stylesheets that override the theme's static blue
_SS_BLUE = (
    "QStatusBar{background-color:#007acc;}"
    "QStatusBar QLabel{color:#ffffff;padding:0 10px;font-size:12px;background:transparent;}"
)
_SS_AMBER = (
    "QStatusBar{background-color:#a86c00;}"
    "QStatusBar QLabel{color:#ffffff;padding:0 10px;font-size:12px;background:transparent;}"
)
_SS_GREEN = (
    "QStatusBar{background-color:#1b7a1b;}"
    "QStatusBar QLabel{color:#ffffff;padding:0 10px;font-size:12px;background:transparent;}"
)
_SS_RED = (
    "QStatusBar{background-color:#b52b2b;}"
    "QStatusBar QLabel{color:#ffffff;padding:0 10px;font-size:12px;background:transparent;}"
)

_SPINNER = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]


class StatusBar(QStatusBar):
    """Application status bar with animated compilation states."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._status_label = QLabel("Ready")
        self._engine_label = QLabel("pdflatex")
        self._encoding_label = QLabel("UTF-8")
        self._cursor_label = QLabel("Ln 1, Col 1")

        for label in (self._status_label, self._engine_label,
                      self._encoding_label, self._cursor_label):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Left: status message (stretches)
        self.addWidget(self._status_label, 1)

        # Right: permanent info
        self._add_separator()
        self.addPermanentWidget(self._engine_label)
        self._add_separator()
        self.addPermanentWidget(self._encoding_label)
        self._add_separator()
        self.addPermanentWidget(self._cursor_label)

        # Spinner animation timer (fires every ~110ms)
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(110)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._spinner_frame = 0

        # Revert-to-ready timer (single-shot, fires after success/failure display)
        self._revert_timer = QTimer(self)
        self._revert_timer.setSingleShot(True)
        self._revert_timer.timeout.connect(self._revert_to_ready)

        self._connect_signals()

    # ── Private helpers ──────────────────────────────────────────────────────

    def _add_separator(self) -> None:
        sep = QLabel("|")
        sep.setStyleSheet("color: rgba(255,255,255,0.35); padding: 0 2px; background: transparent;")
        self.addPermanentWidget(sep)

    def _tick_spinner(self) -> None:
        self._spinner_frame = (self._spinner_frame + 1) % len(_SPINNER)
        self._status_label.setText(f"{_SPINNER[self._spinner_frame]}  Compiling…")

    def _revert_to_ready(self) -> None:
        self.setStyleSheet(_SS_BLUE)
        self._status_label.setText("Ready")

    # ── Signal handlers ──────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        event_bus.cursor_moved.connect(self._on_cursor_moved)
        event_bus.compilation_started.connect(self._on_compilation_started)
        event_bus.compilation_finished.connect(self._on_compilation_finished)
        event_bus.compilation_cancelled.connect(self._on_compilation_cancelled)

    def _on_cursor_moved(self, file_path: str, line: int, col: int) -> None:
        self._cursor_label.setText(f"Ln {line}, Col {col}")

    def _on_compilation_started(self, engine: str) -> None:
        self._revert_timer.stop()
        self._engine_label.setText(engine)
        self.setStyleSheet(_SS_AMBER)
        self._spinner_frame = 0
        self._status_label.setText(f"{_SPINNER[0]}  Compiling…")
        self._spinner_timer.start()

    def _on_compilation_finished(self, success: bool, errors: list) -> None:
        self._spinner_timer.stop()
        if success:
            warning_count = sum(1 for e in errors if getattr(e, "level", "") == "warning")
            self.setStyleSheet(_SS_GREEN)
            if warning_count:
                w = "warning" if warning_count == 1 else "warnings"
                self._status_label.setText(f"✓  Build succeeded  ({warning_count} {w})")
            else:
                self._status_label.setText("✓  Build succeeded")
        else:
            error_count = sum(1 for e in errors if getattr(e, "level", "") == "error")
            self.setStyleSheet(_SS_RED)
            e_word = "error" if error_count == 1 else "errors"
            self._status_label.setText(f"✗  Build failed  ({error_count} {e_word})")
        # Revert to blue after 6 seconds
        self._revert_timer.start(6000)

    def _on_compilation_cancelled(self) -> None:
        self._spinner_timer.stop()
        self.setStyleSheet(_SS_BLUE)
        self._status_label.setText("Build cancelled")

    # ── Public API ───────────────────────────────────────────────────────────

    def set_engine(self, engine: str) -> None:
        self._engine_label.setText(engine)

    def set_encoding(self, encoding: str) -> None:
        self._encoding_label.setText(encoding)