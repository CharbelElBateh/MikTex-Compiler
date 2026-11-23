from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import QMenuBar


class MenuBarBuilder:
    """Builds the application menu bar with all actions."""

    def __init__(self, main_window) -> None:
        self._window = main_window
        self._menu_bar: QMenuBar = main_window.menuBar()
        self.actions: dict[str, QAction] = {}

    def build(self) -> QMenuBar:
        self._build_file_menu()
        self._build_edit_menu()
        self._build_build_menu()
        self._build_view_menu()
        self._build_tools_menu()
        self._build_settings_menu()
        self._build_help_menu()
        return self._menu_bar

    def _create_action(
        self,
        name: str,
        text: str,
        shortcut: str | None = None,
        status_tip: str = "",
    ) -> QAction:
        action = QAction(text, self._window)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if status_tip:
            action.setStatusTip(status_tip)
        self.actions[name] = action
        return action

    def _build_file_menu(self) -> None:
        menu = self._menu_bar.addMenu("&File")

        menu.addAction(self._create_action("new_file", "&New File", "Ctrl+N"))
        menu.addAction(self._create_action("new_project", "New &Project"))
        menu.addSeparator()
        menu.addAction(self._create_action("open_file", "&Open File...", "Ctrl+O"))
        menu.addAction(self._create_action("open_project", "Open Pro&ject..."))

        self._recent_menu = menu.addMenu("Open &Recent")
        self.actions["open_recent_menu"] = None  # placeholder

        menu.addSeparator()
        menu.addAction(self._create_action("save", "&Save", "Ctrl+S"))
        menu.addAction(self._create_action("save_as", "Save &As...", "Ctrl+Shift+S"))
        menu.addAction(self._create_action("save_all", "Save A&ll"))
        menu.addSeparator()
        menu.addAction(self._create_action("close_file", "&Close File", "Ctrl+W"))
        menu.addAction(self._create_action("close_project", "Close Project"))
        menu.addSeparator()
        menu.addAction(self._create_action("exit", "E&xit", "Alt+F4"))

    def _build_edit_menu(self) -> None:
        menu = self._menu_bar.addMenu("&Edit")

        menu.addAction(self._create_action("undo", "&Undo", "Ctrl+Z"))
        menu.addAction(self._create_action("redo", "&Redo", "Ctrl+Y"))
        menu.addSeparator()
        menu.addAction(self._create_action("cut", "Cu&t", "Ctrl+X"))
        menu.addAction(self._create_action("copy", "&Copy", "Ctrl+C"))
        menu.addAction(self._create_action("paste", "&Paste", "Ctrl+V"))
        menu.addAction(self._create_action("select_all", "Select &All", "Ctrl+A"))
        menu.addSeparator()
        menu.addAction(self._create_action("find", "&Find...", "Ctrl+F"))
        menu.addAction(self._create_action("find_replace", "Find && &Replace...", "Ctrl+H"))
        menu.addAction(self._create_action("goto_line", "&Go to Line...", "Ctrl+G"))

    def _build_build_menu(self) -> None:
        menu = self._menu_bar.addMenu("&Build")

        menu.addAction(self._create_action(
            "compile", "&Compile", "F5", "Compile the current document"
        ))
        menu.addAction(self._create_action("clean_build", "C&lean Build"))
        menu.addAction(self._create_action("stop_compilation", "&Stop Compilation", "Ctrl+Break"))
        menu.addSeparator()

        engine_menu = menu.addMenu("Select &Engine")
        engine_group = QActionGroup(self._window)
        engine_group.setExclusive(True)
        self.actions["engine_pdflatex"] = QAction("pdfLaTeX", self._window, checkable=True)
        self.actions["engine_xelatex"] = QAction("XeLaTeX", self._window, checkable=True)
        self.actions["engine_lualatex"] = QAction("LuaLaTeX", self._window, checkable=True)
        self.actions["engine_pdflatex"].setChecked(True)
        for name in ("engine_pdflatex", "engine_xelatex", "engine_lualatex"):
            engine_group.addAction(self.actions[name])
            engine_menu.addAction(self.actions[name])

    def _build_view_menu(self) -> None:
        menu = self._menu_bar.addMenu("&View")

        menu.addAction(self._create_action(
            "toggle_file_tree", "Toggle &File Tree", "Ctrl+B"
        ))
        menu.addAction(self._create_action(
            "toggle_pdf_viewer", "Toggle &PDF Viewer", "Ctrl+P"
        ))
        menu.addAction(self._create_action(
            "toggle_output_panel", "Toggle &Output Panel", "Ctrl+`"
        ))
        menu.addSeparator()
        # Word wrap — checkable toggle (Alt+Z, same as VS Code)
        wrap_action = self._create_action("toggle_word_wrap", "&Word Wrap", "Alt+Z")
        wrap_action.setCheckable(True)
        menu.addAction(wrap_action)
        menu.addSeparator()
        menu.addAction(self._create_action(
            "toggle_theme", "Toggle &Dark/Light Theme", "Ctrl+Shift+T"
        ))
        menu.addSeparator()
        menu.addAction(self._create_action("zoom_in", "Zoom &In", "Ctrl+="))
        menu.addAction(self._create_action("zoom_out", "Zoom &Out", "Ctrl+-"))
        menu.addAction(self._create_action("zoom_reset", "&Reset Zoom", "Ctrl+0"))

    def _build_tools_menu(self) -> None:
        menu = self._menu_bar.addMenu("&Tools")

        menu.addAction(self._create_action(
            "package_manager", "&MiKTeX Package Manager..."
        ))
        menu.addAction(self._create_action("refresh_file_tree", "&Refresh File Tree"))
        menu.addAction(self._create_action("open_terminal", "Open &Terminal Here"))

    def _build_settings_menu(self) -> None:
        menu = self._menu_bar.addMenu("&Settings")

        menu.addAction(self._create_action(
            "preferences", "&Preferences...", "Ctrl+,"
        ))
        menu.addAction(self._create_action("project_settings", "Pro&ject Settings..."))
        menu.addAction(self._create_action("keybindings", "&Keybindings..."))

    def _build_help_menu(self) -> None:
        menu = self._menu_bar.addMenu("&Help")

        menu.addAction(self._create_action("about", "&About"))

    @property
    def recent_menu(self):
        return self._recent_menu
