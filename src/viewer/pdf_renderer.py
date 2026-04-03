"""PDF page renderer using PyMuPDF with an LRU cache."""

from collections import OrderedDict
from pathlib import Path

import fitz  # PyMuPDF
from PyQt6.QtGui import QImage, QPixmap

from src.constants import DEFAULT_RENDER_DPI, PAGE_CACHE_SIZE
from src.core.logging_config import get_logger

log = get_logger("viewer.renderer")


class PDFRenderer:
    """Opens a PDF and renders pages to QPixmap with an LRU page cache."""

    def __init__(self, dpi: int = DEFAULT_RENDER_DPI, cache_size: int = PAGE_CACHE_SIZE) -> None:
        self._dpi = dpi
        self._cache_size = cache_size
        self._doc: fitz.Document | None = None
        self._pdf_path: Path | None = None
        # LRU cache: key=(page_num, zoom) → QPixmap
        self._cache: OrderedDict[tuple, QPixmap] = OrderedDict()

    # ── Document lifecycle ──

    def open(self, path: Path) -> bool:
        self.close()
        try:
            self._doc = fitz.open(str(path))
            self._pdf_path = path
            self._cache.clear()
            log.info("Opened PDF: %s (%d pages)", path.name, self._doc.page_count)
            return True
        except Exception as e:
            log.error("Failed to open PDF %s: %s", path, e)
            self._doc = None
            return False

    def close(self) -> None:
        if self._doc:
            self._doc.close()
            self._doc = None
        self._pdf_path = None
        self._cache.clear()

    def reload(self) -> bool:
        """Re-open the same PDF (after recompilation)."""
        if self._pdf_path:
            return self.open(self._pdf_path)
        return False

    # ── Rendering ──

    def render_page(self, page_num: int, zoom: float = 1.0) -> QPixmap | None:
        """Render a page to QPixmap. Returns cached result if available."""
        if not self._doc or page_num < 0 or page_num >= self._doc.page_count:
            return None

        cache_key = (page_num, round(zoom, 3))
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        try:
            page = self._doc[page_num]
            scale = zoom * self._dpi / 72.0
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            qimage = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888,
            )
            pixmap = QPixmap.fromImage(qimage)

            # Evict oldest entry if cache is full
            if len(self._cache) >= self._cache_size:
                self._cache.popitem(last=False)
            self._cache[cache_key] = pixmap
            return pixmap

        except Exception as e:
            log.error("Render error page %d: %s", page_num, e)
            return None

    # ── Page info ──

    @property
    def page_count(self) -> int:
        return self._doc.page_count if self._doc else 0

    @property
    def is_open(self) -> bool:
        return self._doc is not None

    @property
    def pdf_path(self) -> Path | None:
        return self._pdf_path

    def page_size_pts(self, page_num: int) -> tuple[float, float]:
        """Return (width, height) of a page in 72-dpi points."""
        if not self._doc or page_num >= self._doc.page_count:
            return (595.0, 842.0)  # A4 fallback
        rect = self._doc[page_num].rect
        return (rect.width, rect.height)

    def page_size_px(self, page_num: int, zoom: float) -> tuple[int, int]:
        """Return rendered pixel dimensions for a page at the given zoom."""
        w_pts, h_pts = self.page_size_pts(page_num)
        scale = zoom * self._dpi / 72.0
        return (int(w_pts * scale), int(h_pts * scale))

    def pts_to_px(self, zoom: float, x_pts: float, y_pts: float) -> tuple[float, float]:
        """Convert PDF point coordinates to pixel coordinates at zoom level."""
        scale = zoom * self._dpi / 72.0
        return (x_pts * scale, y_pts * scale)

    def px_to_pts(self, zoom: float, x_px: float, y_px: float) -> tuple[float, float]:
        """Convert pixel coordinates to PDF point coordinates."""
        scale = zoom * self._dpi / 72.0
        return (x_px / scale, y_px / scale)

    def invalidate_cache(self) -> None:
        self._cache.clear()

    def set_dpi(self, dpi: int) -> None:
        if dpi != self._dpi:
            self._dpi = dpi
            self._cache.clear()
