"""Semi-transparent highlight rectangle that fades out after forward sync."""

from PyQt6.QtCore import QPropertyAnimation, QRect, QRectF, Qt, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QGraphicsObject, QGraphicsRectItem


class SyncTeXHighlight(QGraphicsRectItem):
    """A coloured rectangle drawn over the PDF page to show a synctex target.

    Fades out automatically after a short delay.
    """

    def __init__(self, rect: QRectF, parent=None) -> None:
        super().__init__(rect, parent)
        self._opacity = 1.0

        color = QColor(255, 200, 0, 80)   # yellow, semi-transparent
        border = QColor(255, 160, 0, 200)
        self.setBrush(color)
        self.setPen(QPen(border, 2))
        self.setZValue(10)

    def fade_out(self, duration_ms: int = 2000) -> None:
        """Animate opacity to 0 then remove self from scene."""
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration_ms, self._remove)

    def _remove(self) -> None:
        if self.scene():
            self.scene().removeItem(self)
