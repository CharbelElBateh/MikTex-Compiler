"""Welcome dialog shown on startup when no session to restore."""

from pathlib import Path

from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from src.constants import APP_NAME, APP_VERSION


class _GradientHeader(QFrame):
    """Custom-painted gradient header banner for the welcome dialog."""

    def __init__(self, title: str, subtitle: str, parent=None) -> None:
        super().__init__(parent)
        self._title = title
        self._subtitle = subtitle
        self.setFixedHeight(118)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background gradient (left → right, deep blue → medium blue)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0b3566"))
        gradient.setColorAt(0.55, QColor("#0e639c"))
        gradient.setColorAt(1.0, QColor("#1475b5"))
        painter.fillRect(self.rect(), gradient)

        # ── Decorative background symbol (faint) ──
        painter.setOpacity(0.055)
        deco_font = QFont("Segoe UI", 110, QFont.Weight.Bold)
        painter.setFont(deco_font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(
            QRect(-10, -8, self.width() + 20, self.height() + 16),
            Qt.AlignmentFlag.AlignCenter,
            "∂",
        )
        painter.setOpacity(1.0)

        # ── Title ──
        title_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(
            QRect(0, 22, self.width(), 40),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            self._title,
        )

        # ── Subtitle ──
        sub_font = QFont("Segoe UI", 11)
        painter.setFont(sub_font)
        painter.setPen(QColor(255, 255, 255, 175))
        painter.drawText(
            QRect(0, 68, self.width(), 28),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            self._subtitle,
        )

        # ── Bottom edge accent line ──
        painter.setOpacity(0.25)
        painter.setPen(QColor("#ffffff"))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

        painter.end()


class WelcomeDialog(QDialog):
    """Startup dialog: create new project, open project, or choose from recents."""

    open_project_requested = pyqtSignal(str)   # root_path
    new_project_requested = pyqtSignal()

    def __init__(self, recent_paths: list[Path], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Welcome to {APP_NAME}")
        self.setFixedSize(620, 470)
        self.setModal(True)

        # ── Gradient header ──
        header = _GradientHeader(
            title=APP_NAME,
            subtitle=f"v{APP_VERSION}  ·  LaTeX IDE for MiKTeX on Windows",
        )

        # ── Action buttons ──
        new_btn = QPushButton("＋  New Project")
        new_btn.setFixedHeight(36)
        new_btn.setToolTip("Create a new LaTeX project")
        new_btn.clicked.connect(self._on_new)

        open_btn = QPushButton("⊘  Open Project")
        open_btn.setFixedHeight(36)
        open_btn.setToolTip("Open an existing project folder")
        open_btn.clicked.connect(self._on_open)

        open_file_btn = QPushButton("⊡  Open File")
        open_file_btn.setFixedHeight(36)
        open_file_btn.setProperty("flat", True)
        open_file_btn.setToolTip("Open a single .tex file without a project")
        open_file_btn.clicked.connect(self._on_open_file)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(open_file_btn)

        # ── Recent projects section ──
        recent_label = QLabel("Recent Projects")
        recent_label.setStyleSheet(
            "font-weight: 700; font-size: 12px; color: #888888; letter-spacing: 0.8px;"
        )

        self._recent_list = QListWidget()
        self._recent_list.setAlternatingRowColors(False)
        self._recent_list.setSpacing(1)

        for path in recent_paths:
            item = QListWidgetItem()
            # Two-line display: project name + full path
            item.setText(f"{path.name}\n{path}")
            item.setToolTip(str(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setSizeHint(QSize(0, 46))
            self._recent_list.addItem(item)

        if not recent_paths:
            placeholder = QListWidgetItem("No recent projects")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            placeholder.setForeground(Qt.GlobalColor.gray)
            self._recent_list.addItem(placeholder)

        self._recent_list.itemDoubleClicked.connect(self._on_recent_double_click)

        # ── Footer ──
        open_recent_btn = QPushButton("Open Selected")
        open_recent_btn.setFixedHeight(32)
        open_recent_btn.clicked.connect(self._on_open_recent)

        skip_btn = QPushButton("Continue without project")
        skip_btn.setFixedHeight(32)
        skip_btn.setProperty("flat", True)
        skip_btn.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(open_recent_btn)
        footer.addWidget(skip_btn)

        # ── Main layout ──
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)

        inner = QVBoxLayout()
        inner.setContentsMargins(22, 16, 22, 16)
        inner.setSpacing(10)
        inner.addLayout(btn_layout)
        inner.addSpacing(4)
        inner.addWidget(recent_label)
        inner.addWidget(self._recent_list, 1)
        inner.addLayout(footer)

        layout.addLayout(inner)

    # ── Slot helpers ─────────────────────────────────────────────────────────

    def _on_new(self) -> None:
        self.accept()
        self.new_project_requested.emit()

    def _on_open(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open Project Directory")
        if path:
            self.accept()
            self.open_project_requested.emit(path)

    def _on_open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "LaTeX Files (*.tex *.sty *.cls *.bib);;All Files (*)"
        )
        if path:
            self.accept()
            self.open_project_requested.emit("")
            self._open_file_path = path

    def _on_recent_double_click(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.accept()
            self.open_project_requested.emit(path)

    def _on_open_recent(self) -> None:
        item = self._recent_list.currentItem()
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                self.accept()
                self.open_project_requested.emit(path)

    @property
    def file_to_open(self) -> str:
        return getattr(self, "_open_file_path", "")