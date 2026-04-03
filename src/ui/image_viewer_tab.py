"""Scrollable image viewer displayed as an editor tab."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QWheelEvent
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ImageViewerTab(QWidget):
    """Lightweight image viewer shown in the editor tab area.

    Supports scroll-to-zoom (Ctrl+wheel) and fit-to-window default scale.
    """

    #: File extensions this viewer handles
    SUPPORTED_EXTENSIONS = frozenset({
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"
    })

    def __init__(self, file_path: str, parent=None) -> None:
        super().__init__(parent)
        self._file_path = file_path
        self._zoom = 1.0

        self._pixmap = QPixmap(file_path)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._label)
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setStyleSheet("QScrollArea { border: none; }")

        if self._pixmap.isNull():
            self._label.setText(
                f"Cannot display: {Path(file_path).name}\n\n"
                "(Unsupported or corrupt image)"
            )
            self._label.setStyleSheet("color: #888; font-size: 14px;")
        else:
            self._update_label()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll)

    # ── Rendering ────────────────────────────────────────────────────────────

    def _update_label(self) -> None:
        if self._pixmap.isNull():
            return
        scaled = self._pixmap.scaled(
            int(self._pixmap.width() * self._zoom),
            int(self._pixmap.height() * self._zoom),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(scaled)
        self._label.resize(scaled.size())

    # ── Zoom ─────────────────────────────────────────────────────────────────

    def zoom_in(self) -> None:
        self._zoom = min(8.0, self._zoom * 1.2)
        self._update_label()

    def zoom_out(self) -> None:
        self._zoom = max(0.05, self._zoom / 1.2)
        self._update_label()

    def zoom_reset(self) -> None:
        self._zoom = 1.0
        self._update_label()

    def fit_to_window(self) -> None:
        """Scale so the image fits within the current viewport."""
        if self._pixmap.isNull():
            return
        vw = self._scroll.viewport().width() - 8
        vh = self._scroll.viewport().height() - 8
        scale_w = vw / max(1, self._pixmap.width())
        scale_h = vh / max(1, self._pixmap.height())
        self._zoom = min(scale_w, scale_h, 1.0)
        self._update_label()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        # Fit on first display
        self.fit_to_window()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def is_modified(self) -> bool:
        return False  # Images are read-only