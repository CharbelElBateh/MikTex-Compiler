from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QLabel, QToolBar, QToolButton


class MainToolBar(QToolBar):
    """Main application toolbar with common actions."""

    def __init__(self, actions: dict, parent=None) -> None:
        super().__init__("Main Toolbar", parent)
        self._actions = actions

        self.setMovable(False)
        self.setFloatable(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

        self._build()

    def _build(self) -> None:
        # File operations
        self._add_button("new_file",  "New",   "New file (Ctrl+N)")
        self._add_button("open_file", "Open",  "Open file (Ctrl+O)")
        self._add_button("save",      "Save",  "Save (Ctrl+S)")
        self.addSeparator()

        # Build operations — compile is the primary action
        self._add_button("compile",          "▶  Compile", "Compile document (F5)",  prop="compile_btn")
        self._add_button("stop_compilation", "■  Stop",    "Stop compilation",        prop="stop_btn")
        self.addSeparator()

        # Engine selector
        engine_label = QLabel("Engine: ")
        engine_label.setStyleSheet("background-color: transparent; font-size: 12px;")
        self.addWidget(engine_label)

        self._engine_combo = QComboBox()
        self._engine_combo.addItems(["pdfLaTeX", "XeLaTeX", "LuaLaTeX"])
        self._engine_combo.setToolTip("Select compilation engine")
        self._engine_combo.setMinimumWidth(110)
        self._engine_combo.setFixedHeight(26)
        self.addWidget(self._engine_combo)
        self.addSeparator()

        # View toggles
        self._add_button("toggle_file_tree",    "Files",  "Toggle file tree (Ctrl+B)")
        self._add_button("toggle_pdf_viewer",   "PDF",    "Toggle PDF viewer (Ctrl+P)")
        self._add_button("toggle_output_panel", "Output", "Toggle output panel (Ctrl+`)")
        self.addSeparator()

        # Theme toggle
        self._add_button("toggle_theme", "Theme", "Toggle dark/light theme (Ctrl+Shift+T)")

    def _add_button(self, action_name: str, text: str,
                    tooltip: str = "", prop: str | None = None) -> QToolButton | None:
        action = self._actions.get(action_name)
        if not action:
            return None
        btn = QToolButton()
        btn.setDefaultAction(action)
        btn.setText(text)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        if tooltip:
            btn.setToolTip(tooltip)
        if prop:
            btn.setProperty(prop, True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.addWidget(btn)
        return btn

    @property
    def engine_combo(self) -> QComboBox:
        return self._engine_combo
