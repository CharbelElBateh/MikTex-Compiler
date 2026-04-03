"""Continuous-scroll PDF page display using QGraphicsView."""

from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QWheelEvent
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)

from src.core.logging_config import get_logger
from src.viewer.pdf_renderer import PDFRenderer
from src.viewer.synctex_overlay import SyncTeXHighlight

log = get_logger("viewer.page_widget")

_PAGE_MARGIN = 8    # pixels between pages
_BACKGROUND = QColor("#3c3c3c")
_PAGE_SHADOW = QColor(0, 0, 0, 60)


class PDFPageWidget(QGraphicsView):
    """Displays all PDF pages in a vertical continuous-scroll layout.

    Ctrl+click triggers reverse SyncTeX sync.
    Ctrl+scroll changes zoom level.
    """

    zoom_changed_by_wheel = pyqtSignal(float)  # emitted on Ctrl+scroll zoom

    def __init__(self, renderer: PDFRenderer, parent=None) -> None:
        super().__init__(parent)
        self._renderer = renderer
        self._zoom = 1.0
        self._page_items: list[QGraphicsPixmapItem] = []
        self._page_tops: list[float] = []      # y-offset of each page in scene coords
        self._reverse_sync_cb = None           # callback(page, x_pts, y_pts)

        scene = QGraphicsScene(self)
        scene.setBackgroundBrush(_BACKGROUND)
        self.setScene(scene)

        self.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def set_reverse_sync_callback(self, cb) -> None:
        """Set callback invoked on Ctrl+click: cb(page: int, x_pts: float, y_pts: float)"""
        self._reverse_sync_cb = cb

    # ── Rendering ──

    def render_all(self, zoom: float | None = None) -> None:
        """Render all pages at the given (or current) zoom level."""
        if zoom is not None:
            self._zoom = zoom

        if not self._renderer.is_open:
            return

        self.scene().clear()
        self._page_items.clear()
        self._page_tops.clear()

        y_offset = float(_PAGE_MARGIN)
        max_width = 0.0

        for page_num in range(self._renderer.page_count):
            w_px, h_px = self._renderer.page_size_px(page_num, self._zoom)
            max_width = max(max_width, w_px)

            # Shadow rectangle behind page
            shadow = QGraphicsRectItem(QRectF(3, y_offset + 3, w_px, h_px))
            shadow.setBrush(_PAGE_SHADOW)
            shadow.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene().addItem(shadow)

            # Pixmap item (lazy: load first visible page immediately, others on demand)
            pixmap = self._renderer.render_page(page_num, self._zoom)
            item = QGraphicsPixmapItem()
            if pixmap:
                item.setPixmap(pixmap)
            item.setPos(0, y_offset)
            item.setData(0, page_num)  # store page number
            self.scene().addItem(item)

            self._page_items.append(item)
            self._page_tops.append(y_offset)

            y_offset += h_px + _PAGE_MARGIN

        self.scene().setSceneRect(QRectF(0, 0, max_width, y_offset))

    def refresh_page(self, page_num: int) -> None:
        """Re-render a single page (e.g. after reload)."""
        if 0 <= page_num < len(self._page_items):
            pixmap = self._renderer.render_page(page_num, self._zoom)
            if pixmap:
                self._page_items[page_num].setPixmap(pixmap)

    def set_zoom(self, zoom: float) -> None:
        if abs(zoom - self._zoom) < 0.001:
            return
        # Preserve scroll fraction
        vbar = self.verticalScrollBar()
        vmax = vbar.maximum() or 1
        scroll_frac = vbar.value() / vmax

        self.render_all(zoom)

        new_max = self.verticalScrollBar().maximum()
        self.verticalScrollBar().setValue(int(scroll_frac * new_max))

    # ── Scrolling to page/position ──

    def scroll_to_page(self, page_num: int) -> None:
        """Scroll so that the top of page_num is visible."""
        if 0 <= page_num < len(self._page_tops):
            self.ensureVisible(
                QRectF(0, self._page_tops[page_num], 10, 10), 0, 20
            )

    def scroll_to_position(self, page_num: int, x_pts: float, y_pts: float) -> None:
        """Scroll to a specific point on a page and add a highlight."""
        if page_num < 0 or page_num >= len(self._page_tops):
            return

        x_px, y_px = self._renderer.pts_to_px(self._zoom, x_pts, y_pts)
        scene_y = self._page_tops[page_num] + y_px

        w_px, h_px = self._renderer.page_size_px(page_num, self._zoom)
        # Highlight a region around the target
        hl_w, hl_h = self._renderer.pts_to_px(self._zoom, 100, 12)
        hl_rect = QRectF(x_px - hl_w / 2, scene_y - hl_h / 2, hl_w, hl_h)

        # Remove existing highlights
        for item in self.scene().items():
            if isinstance(item, SyncTeXHighlight):
                self.scene().removeItem(item)

        highlight = SyncTeXHighlight(hl_rect)
        self.scene().addItem(highlight)
        highlight.fade_out(2500)

        self.ensureVisible(QRectF(0, scene_y - 50, w_px, 150), 0, 50)

    # ── Current page tracking ──

    def current_page(self) -> int:
        """Return the 0-based index of the page most visible in the viewport."""
        center_y = self.mapToScene(self.viewport().rect().center()).y()
        for i in range(len(self._page_tops) - 1, -1, -1):
            if center_y >= self._page_tops[i]:
                return i
        return 0

    # ── Mouse / keyboard events ──

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            scene_pos = self.mapToScene(event.pos())
            page_num, x_pts, y_pts = self._scene_to_pdf_coords(scene_pos)
            if page_num >= 0 and self._reverse_sync_cb:
                self._reverse_sync_cb(page_num + 1, x_pts, y_pts)  # 1-based page
            return
        super().mousePressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1 / 1.15
            new_zoom = max(0.25, min(4.0, self._zoom * factor))
            self.set_zoom(new_zoom)
            self.zoom_changed_by_wheel.emit(new_zoom)
            event.accept()
        else:
            super().wheelEvent(event)

    # ── Coordinate helpers ──

    def _scene_to_pdf_coords(self, scene_pos: QPointF) -> tuple[int, float, float]:
        """Convert a scene position to (page_num_0based, x_pts, y_pts).

        Returns (-1, 0, 0) if not over any page.
        """
        for i in range(len(self._page_tops) - 1, -1, -1):
            if scene_pos.y() >= self._page_tops[i]:
                y_in_page = scene_pos.y() - self._page_tops[i]
                x_pts, y_pts = self._renderer.px_to_pts(self._zoom, scene_pos.x(), y_in_page)
                return (i, x_pts, y_pts)
        return (-1, 0.0, 0.0)

    @property
    def zoom(self) -> float:
        return self._zoom
