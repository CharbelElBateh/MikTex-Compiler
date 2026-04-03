from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSplitter, QWidget


class PlaceholderWidget(QLabel):
    """Placeholder widget shown when a panel has no content."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "color: #6e6e6e; font-size: 13px; font-style: italic; border: none;"
        )


class SplitterLayout:
    """Manages the main window's splitter-based layout.

    Layout:
        ┌──────────┬──────────────┬──────────────┐
        │ File     │   Editor     │   PDF        │
        │ Tree     │   (tabs)     │   Viewer     │
        │          │              │              │
        ├──────────┴──────────────┴──────────────┤
        │              Output Panel               │
        └─────────────────────────────────────────┘
    """

    def __init__(
        self,
        file_tree: QWidget | None = None,
        editor_area: QWidget | None = None,
        pdf_viewer: QWidget | None = None,
        output_panel: QWidget | None = None,
    ) -> None:
        self.file_tree: QWidget = file_tree if file_tree is not None else PlaceholderWidget("File Tree")
        self.editor_area: QWidget = editor_area if editor_area is not None else PlaceholderWidget(
            "Open a .tex file to start editing"
        )
        self.pdf_viewer: QWidget = pdf_viewer if pdf_viewer is not None else PlaceholderWidget("No PDF to display")
        self.output_panel: QWidget = output_panel if output_panel is not None else PlaceholderWidget("Output Panel")

        # Horizontal splitter: file tree | editor | pdf viewer
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.addWidget(self.file_tree)
        self.h_splitter.addWidget(self.editor_area)
        self.h_splitter.addWidget(self.pdf_viewer)
        self.h_splitter.setSizes([200, 600, 400])
        self.h_splitter.setStretchFactor(0, 0)  # File tree: fixed
        self.h_splitter.setStretchFactor(1, 1)  # Editor: stretches
        self.h_splitter.setStretchFactor(2, 0)  # PDF viewer: fixed

        # Vertical splitter: top area | output panel
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.addWidget(self.h_splitter)
        self.v_splitter.addWidget(self.output_panel)
        self.v_splitter.setSizes([600, 200])
        self.v_splitter.setStretchFactor(0, 1)  # Top area: stretches
        self.v_splitter.setStretchFactor(1, 0)  # Output: fixed

    @property
    def central_widget(self) -> QWidget:
        return self.v_splitter

    def toggle_file_tree(self) -> None:
        self.file_tree.setVisible(not self.file_tree.isVisible())

    def toggle_pdf_viewer(self) -> None:
        self.pdf_viewer.setVisible(not self.pdf_viewer.isVisible())

    def toggle_output_panel(self) -> None:
        self.output_panel.setVisible(not self.output_panel.isVisible())

    def save_state(self) -> dict:
        return {
            "h_splitter_sizes": self.h_splitter.sizes(),
            "v_splitter_sizes": self.v_splitter.sizes(),
            "file_tree_visible": self.file_tree.isVisible(),
            "pdf_viewer_visible": self.pdf_viewer.isVisible(),
            "output_panel_visible": self.output_panel.isVisible(),
        }

    def restore_state(self, state: dict) -> None:
        if "h_splitter_sizes" in state:
            self.h_splitter.setSizes(state["h_splitter_sizes"])
        if "v_splitter_sizes" in state:
            self.v_splitter.setSizes(state["v_splitter_sizes"])
        if "file_tree_visible" in state:
            self.file_tree.setVisible(state["file_tree_visible"])
        if "pdf_viewer_visible" in state:
            self.pdf_viewer.setVisible(state["pdf_viewer_visible"])
        if "output_panel_visible" in state:
            self.output_panel.setVisible(state["output_panel_visible"])
