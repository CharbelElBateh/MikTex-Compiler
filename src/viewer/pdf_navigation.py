"""Navigation toolbar for the PDF viewer."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QToolBar,
    QWidget,
)


class PDFNavigationBar(QWidget):
    """Toolbar for page navigation and zoom control."""

    page_changed = pyqtSignal(int)    # 0-based page number
    zoom_changed = pyqtSignal(float)  # zoom factor (1.0 = 100%)

    _ZOOM_PRESETS = [
        ("50%", 0.5), ("75%", 0.75), ("100%", 1.0),
        ("125%", 1.25), ("150%", 1.5), ("200%", 2.0),
        ("Fit Width", -1.0),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._page_count = 0
        self._current_zoom = 1.0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Page navigation
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.setToolTip("Previous page")
        self._prev_btn.clicked.connect(self._on_prev)

        self._page_spin = QSpinBox()
        self._page_spin.setMinimum(1)
        self._page_spin.setMaximum(1)
        self._page_spin.setFixedWidth(56)
        self._page_spin.editingFinished.connect(self._on_page_spin_changed)

        self._page_label = QLabel("/ 1")

        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedWidth(28)
        self._next_btn.setToolTip("Next page")
        self._next_btn.clicked.connect(self._on_next)

        layout.addWidget(self._prev_btn)
        layout.addWidget(self._page_spin)
        layout.addWidget(self._page_label)
        layout.addWidget(self._next_btn)
        layout.addSpacing(8)

        # Zoom controls
        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setFixedWidth(28)
        self._zoom_out_btn.clicked.connect(self._on_zoom_out)

        self._zoom_combo = QComboBox()
        self._zoom_combo.setFixedWidth(90)
        for label, _ in self._ZOOM_PRESETS:
            self._zoom_combo.addItem(label)
        self._zoom_combo.setCurrentText("100%")
        self._zoom_combo.currentIndexChanged.connect(self._on_zoom_preset)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedWidth(28)
        self._zoom_in_btn.clicked.connect(self._on_zoom_in)

        layout.addWidget(self._zoom_out_btn)
        layout.addWidget(self._zoom_combo)
        layout.addWidget(self._zoom_in_btn)
        layout.addStretch()

    # ── Public API ──

    def set_page_count(self, count: int) -> None:
        self._page_count = count
        self._page_spin.setMaximum(max(1, count))
        self._page_label.setText(f"/ {count}")

    def set_current_page(self, page_0: int) -> None:
        self._page_spin.blockSignals(True)
        self._page_spin.setValue(page_0 + 1)
        self._page_spin.blockSignals(False)

    def set_zoom(self, zoom: float) -> None:
        self._current_zoom = zoom
        # Try to match a preset label
        self._zoom_combo.blockSignals(True)
        matched = False
        for label, val in self._ZOOM_PRESETS:
            if val > 0 and abs(val - zoom) < 0.01:
                self._zoom_combo.setCurrentText(label)
                matched = True
                break
        if not matched:
            self._zoom_combo.setCurrentText(f"{int(zoom * 100)}%")
        self._zoom_combo.blockSignals(False)

    # ── Slots ──

    def _on_prev(self) -> None:
        p = self._page_spin.value() - 2  # convert to 0-based then go back
        if p >= 0:
            self._page_spin.setValue(p + 1)
            self.page_changed.emit(p)

    def _on_next(self) -> None:
        p = self._page_spin.value()  # current 1-based → 0-based next
        if p < self._page_count:
            self._page_spin.setValue(p + 1)
            self.page_changed.emit(p)

    def _on_page_spin_changed(self) -> None:
        self.page_changed.emit(self._page_spin.value() - 1)

    def _on_zoom_preset(self, idx: int) -> None:
        _, val = self._ZOOM_PRESETS[idx]
        if val > 0:
            self._current_zoom = val
            self.zoom_changed.emit(val)

    def _on_zoom_in(self) -> None:
        new_zoom = min(4.0, self._current_zoom * 1.25)
        self._current_zoom = new_zoom
        self.zoom_changed.emit(new_zoom)

    def _on_zoom_out(self) -> None:
        new_zoom = max(0.1, self._current_zoom / 1.25)
        self._current_zoom = new_zoom
        self.zoom_changed.emit(new_zoom)
