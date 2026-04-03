"""Composite PDF viewer: navigation bar + scrollable page display."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.compiler.synctex_bridge import SyncTeXBridge
from src.constants import DEFAULT_RENDER_DPI, DEFAULT_ZOOM
from src.core.event_bus import event_bus
from src.core.logging_config import get_logger
from src.viewer.pdf_navigation import PDFNavigationBar
from src.viewer.pdf_page_widget import PDFPageWidget
from src.viewer.pdf_renderer import PDFRenderer

log = get_logger("viewer.widget")


class PDFViewerWidget(QWidget):
    """Self-contained PDF viewer with navigation, zoom, and SyncTeX support."""

    def __init__(
        self,
        synctex_bridge: SyncTeXBridge | None = None,
        dpi: int = DEFAULT_RENDER_DPI,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._synctex_bridge = synctex_bridge
        self._current_pdf: Path | None = None

        self._renderer = PDFRenderer(dpi=dpi)
        self._nav_bar = PDFNavigationBar()
        self._page_view = PDFPageWidget(self._renderer)

        # "No PDF" placeholder
        self._placeholder = QLabel("PDF preview will appear here after compilation")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #858585; font-size: 13px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._nav_bar)
        layout.addWidget(self._page_view)
        layout.addWidget(self._placeholder)

        self._nav_bar.setVisible(False)
        self._page_view.setVisible(False)
        self._placeholder.setVisible(True)

        self._connect_signals()

    def _connect_signals(self) -> None:
        # Navigation bar → page view
        self._nav_bar.page_changed.connect(self._page_view.scroll_to_page)
        self._nav_bar.zoom_changed.connect(self._on_zoom_changed)

        # Page view wheel zoom → update nav bar
        self._page_view.zoom_changed_by_wheel.connect(self._on_wheel_zoom)

        # EventBus
        event_bus.pdf_ready.connect(self._on_pdf_ready)
        event_bus.synctex_forward.connect(self._on_forward_sync)

        # Reverse sync from page view → EventBus
        self._page_view.set_reverse_sync_callback(self._on_reverse_sync)

    # ── Public API ──

    def open_pdf(self, path: Path) -> bool:
        """Open a PDF file and display it."""
        if self._renderer.open(path):
            self._current_pdf = path
            self._page_view.render_all(DEFAULT_ZOOM / 100.0)
            self._nav_bar.set_page_count(self._renderer.page_count)
            self._nav_bar.set_zoom(DEFAULT_ZOOM / 100.0)
            self._nav_bar.setVisible(True)
            self._page_view.setVisible(True)
            self._placeholder.setVisible(False)
            log.info("Displaying PDF: %s", path.name)
            return True
        return False

    def reload(self) -> None:
        """Reload the current PDF after recompilation, preserving scroll position."""
        if not self._current_pdf:
            return

        # Save scroll position
        vbar = self._page_view.verticalScrollBar()
        vmax = vbar.maximum() or 1
        scroll_frac = vbar.value() / vmax
        zoom = self._page_view.zoom

        if self._renderer.reload():
            self._page_view.render_all(zoom)
            self._nav_bar.set_page_count(self._renderer.page_count)
            # Restore scroll
            new_max = self._page_view.verticalScrollBar().maximum()
            self._page_view.verticalScrollBar().setValue(int(scroll_frac * new_max))
            log.debug("PDF reloaded: %s", self._current_pdf.name)

    # ── Event handlers ──

    def _on_pdf_ready(self, pdf_path_str: str) -> None:
        """Called after successful compilation with the path to the output PDF."""
        pdf_path = Path(pdf_path_str)
        if not pdf_path.is_file():
            return
        if self._current_pdf == pdf_path:
            self.reload()
        else:
            self.open_pdf(pdf_path)

    def _on_zoom_changed(self, zoom: float) -> None:
        if zoom < 0:
            # "Fit Width" preset
            zoom = self._calculate_fit_width_zoom()
        self._page_view.set_zoom(zoom)
        self._nav_bar.set_zoom(zoom)

    def _on_wheel_zoom(self, zoom: float) -> None:
        """Sync nav bar when user Ctrl+scrolls in the page view."""
        self._nav_bar.set_zoom(zoom)

    def _calculate_fit_width_zoom(self) -> float:
        """Calculate zoom so the first page fits the viewport width."""
        if not self._renderer.is_open or self._renderer.page_count == 0:
            return 1.0
        # Get page width at zoom=1.0
        w_px, _ = self._renderer.page_size_px(0, 1.0)
        viewport_w = self._page_view.viewport().width() - 20  # small margin
        if w_px <= 0 or viewport_w <= 0:
            return 1.0
        return max(0.25, min(4.0, viewport_w / w_px))

    def _on_forward_sync(self, tex_file: str, line: int, col: int) -> None:
        """Forward sync: jump to PDF location corresponding to editor position."""
        if not self._synctex_bridge or not self._current_pdf:
            return
        results = self._synctex_bridge.forward_sync(
            Path(tex_file), line, col, self._current_pdf
        )
        if results:
            r = results[0]
            self._page_view.scroll_to_position(r.page - 1, r.x, r.y)
            self._nav_bar.set_current_page(r.page - 1)
            log.debug("Forward sync: page=%d x=%.1f y=%.1f", r.page, r.x, r.y)

    def _on_reverse_sync(self, page_1: int, x_pts: float, y_pts: float) -> None:
        """Reverse sync: emit EventBus signal to jump editor to source location."""
        if not self._synctex_bridge or not self._current_pdf:
            return
        result = self._synctex_bridge.reverse_sync(self._current_pdf, page_1, x_pts, y_pts)
        if result and result.file_path:
            event_bus.synctex_reverse.emit(result.file_path, result.line, result.column)
            log.debug("Reverse sync → %s:%d", result.file_path, result.line)

    @property
    def current_pdf(self) -> Path | None:
        return self._current_pdf
