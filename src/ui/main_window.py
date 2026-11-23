from pathlib import Path

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from src.ui.image_viewer_tab import ImageViewerTab

from src.constants import APP_NAME, APP_VERSION
from src.core.event_bus import event_bus
from src.core.logging_config import get_logger
from src.core.project_manager import ProjectManager
from src.core.session_manager import SessionManager
from src.core.settings_manager import SettingsManager
from src.themes.theme_manager import ThemeManager
from src.ui.dialogs.find_replace_dialog import FindReplaceDialog
from src.ui.file_tree import FileTreeWidget
from src.ui.menu_bar import MenuBarBuilder
from src.ui.output_panel import OutputPanel
from src.ui.splitter_layout import SplitterLayout
from src.ui.status_bar import StatusBar
from src.ui.tab_manager import TabManager
from src.ui.toolbar import MainToolBar

log = get_logger("ui.main_window")


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(
        self,
        settings: SettingsManager,
        theme_manager: ThemeManager,
        project_manager: ProjectManager,
        session_manager: SessionManager,
        compilation_controller=None,
        pdf_viewer=None,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._theme_manager = theme_manager
        self._project_manager = project_manager
        self._session_manager = session_manager
        self._compilation_controller = compilation_controller
        self._last_diagnostics: list = []

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(QSize(800, 600))

        # Core sub-widgets
        self._file_tree = FileTreeWidget()
        self._tab_manager = TabManager(settings, theme_manager)
        self._output_panel = OutputPanel()
        self._pdf_viewer = pdf_viewer
        self._file_tree.set_open_callback(self._open_file)

        # Menu / toolbar
        self._menu_builder = MenuBarBuilder(self)
        self._menu_builder.build()

        # Layout
        self._layout = SplitterLayout(
            file_tree=self._file_tree,
            editor_area=self._tab_manager,
            pdf_viewer=self._pdf_viewer,
            output_panel=self._output_panel,
        )
        self.setCentralWidget(self._layout.central_widget)

        self._toolbar = MainToolBar(self._menu_builder.actions, self)
        self.addToolBar(self._toolbar)

        self._status_bar = StatusBar(self)
        self.setStatusBar(self._status_bar)

        # Find/Replace dialog (shared, non-modal)
        self._find_replace_dialog = FindReplaceDialog(self)

        self._connect_actions()
        self._connect_event_bus()
        self._restore_window_state()
        self._status_bar.set_engine(self._settings.compiler_default_engine)

        # Sync the engine combo (and menu checkmarks) with the saved setting
        engine_map = {"pdflatex": "pdfLaTeX", "xelatex": "XeLaTeX", "lualatex": "LuaLaTeX"}
        display = engine_map.get(self._settings.compiler_default_engine)
        if display:
            idx = self._toolbar.engine_combo.findText(display)
            if idx >= 0:
                self._toolbar.engine_combo.setCurrentIndex(idx)

        # Sync word-wrap menu checkmark with persisted setting
        if self._menu_builder.actions.get("toggle_word_wrap"):
            self._menu_builder.actions["toggle_word_wrap"].setChecked(
                self._settings.editor_word_wrap
            )

        log.info("Main window initialized")

    def _connect_actions(self) -> None:
        actions = self._menu_builder.actions

        # File
        if actions.get("new_file"):
            actions["new_file"].triggered.connect(self._on_new_file)
        if actions.get("new_project"):
            actions["new_project"].triggered.connect(self._on_new_project)
        if actions.get("open_file"):
            actions["open_file"].triggered.connect(self._on_open_file_dialog)
        if actions.get("open_project"):
            actions["open_project"].triggered.connect(self._on_open_project_dialog)
        if actions.get("save"):
            actions["save"].triggered.connect(self._tab_manager.save_current)
        if actions.get("save_as"):
            actions["save_as"].triggered.connect(self._tab_manager.save_current_as)
        if actions.get("save_all"):
            actions["save_all"].triggered.connect(self._tab_manager.save_all)
        if actions.get("close_file"):
            actions["close_file"].triggered.connect(self._tab_manager.close_current)
        if actions.get("close_project"):
            actions["close_project"].triggered.connect(self._on_close_project)

        # Edit
        if actions.get("undo"):
            actions["undo"].triggered.connect(lambda: self._tab_manager.current_editor and self._tab_manager.current_editor.undo())
        if actions.get("redo"):
            actions["redo"].triggered.connect(lambda: self._tab_manager.current_editor and self._tab_manager.current_editor.redo())
        if actions.get("cut"):
            actions["cut"].triggered.connect(lambda: self._tab_manager.current_editor and self._tab_manager.current_editor.cut())
        if actions.get("copy"):
            actions["copy"].triggered.connect(lambda: self._tab_manager.current_editor and self._tab_manager.current_editor.copy())
        if actions.get("paste"):
            actions["paste"].triggered.connect(lambda: self._tab_manager.current_editor and self._tab_manager.current_editor.paste())
        if actions.get("select_all"):
            actions["select_all"].triggered.connect(lambda: self._tab_manager.current_editor and self._tab_manager.current_editor.selectAll())

        # Edit - Find / Replace / GoTo
        if actions.get("find"):
            actions["find"].triggered.connect(self._on_find)
        if actions.get("find_replace"):
            actions["find_replace"].triggered.connect(self._on_find_replace)
        if actions.get("goto_line"):
            actions["goto_line"].triggered.connect(self._on_goto_line)

        # Build
        if actions.get("compile"):
            actions["compile"].triggered.connect(self._on_compile)
        if actions.get("stop_compilation"):
            actions["stop_compilation"].triggered.connect(self._on_stop_compilation)
            actions["stop_compilation"].setEnabled(False)
        if actions.get("clean_build"):
            actions["clean_build"].triggered.connect(self._on_clean_build)

        # Build is unavailable without MiKTeX
        if not self._compilation_controller:
            for name in ("compile", "stop_compilation", "clean_build"):
                if actions.get(name):
                    actions[name].setEnabled(False)
                    actions[name].setToolTip("MiKTeX not found — compilation disabled")
            self._toolbar.engine_combo.setEnabled(False)

        # Engine selection menu (radio-style, synced with the toolbar combo)
        engine_display = {"engine_pdflatex": "pdfLaTeX",
                          "engine_xelatex": "XeLaTeX",
                          "engine_lualatex": "LuaLaTeX"}
        for action_name, display in engine_display.items():
            if actions.get(action_name):
                actions[action_name].triggered.connect(
                    lambda checked, d=display: self._on_engine_menu_selected(d)
                )

        # View toggles
        if actions.get("toggle_file_tree"):
            actions["toggle_file_tree"].triggered.connect(self._layout.toggle_file_tree)
        if actions.get("toggle_pdf_viewer"):
            actions["toggle_pdf_viewer"].triggered.connect(self._layout.toggle_pdf_viewer)
        if actions.get("toggle_output_panel"):
            actions["toggle_output_panel"].triggered.connect(self._layout.toggle_output_panel)
        if actions.get("toggle_word_wrap"):
            actions["toggle_word_wrap"].triggered.connect(self._on_toggle_word_wrap)

        # View - Zoom
        if actions.get("zoom_in"):
            actions["zoom_in"].triggered.connect(self._on_zoom_in)
        if actions.get("zoom_out"):
            actions["zoom_out"].triggered.connect(self._on_zoom_out)
        if actions.get("zoom_reset"):
            actions["zoom_reset"].triggered.connect(self._on_zoom_reset)

        # Tools
        if actions.get("package_manager"):
            actions["package_manager"].triggered.connect(self._on_package_manager)
        if actions.get("refresh_file_tree"):
            actions["refresh_file_tree"].triggered.connect(self._file_tree.refresh)
        if actions.get("open_terminal"):
            actions["open_terminal"].triggered.connect(self._on_open_terminal)

        # Theme / settings
        if actions.get("toggle_theme"):
            actions["toggle_theme"].triggered.connect(self._on_toggle_theme)
        if actions.get("preferences"):
            actions["preferences"].triggered.connect(self._on_preferences)
        if actions.get("project_settings"):
            actions["project_settings"].triggered.connect(self._on_project_settings)
        if actions.get("keybindings"):
            actions["keybindings"].triggered.connect(self._on_keybindings)

        # Misc
        if actions.get("exit"):
            actions["exit"].triggered.connect(self.close)
        if actions.get("about"):
            actions["about"].triggered.connect(self._show_about)

        # Forward SyncTeX shortcut
        sync_sc = QShortcut(QKeySequence("Ctrl+Return"), self)
        sync_sc.activated.connect(self._on_forward_sync)

        # Engine selector
        self._toolbar.engine_combo.currentTextChanged.connect(self._on_engine_changed)

    def _connect_event_bus(self) -> None:
        event_bus.synctex_reverse.connect(self._on_jump_to_source)
        event_bus.project_opened.connect(self._on_project_opened)
        event_bus.compilation_started.connect(self._on_compilation_started_ui)
        event_bus.compilation_finished.connect(self._on_compilation_finished_ui)
        event_bus.compilation_cancelled.connect(self._on_compilation_ended_ui)

    # ── Compilation UI state ──

    def _on_compilation_started_ui(self, engine: str) -> None:
        self._set_build_actions_running(True)
        self._tab_manager.clear_diagnostics()

    def _on_compilation_finished_ui(self, success: bool, errors: list) -> None:
        self._set_build_actions_running(False)
        self._last_diagnostics = errors
        self._tab_manager.apply_diagnostics(errors)

    def _on_compilation_ended_ui(self) -> None:
        self._set_build_actions_running(False)

    def _set_build_actions_running(self, running: bool) -> None:
        actions = self._menu_builder.actions
        if actions.get("compile"):
            actions["compile"].setEnabled(not running)
        if actions.get("clean_build"):
            actions["clean_build"].setEnabled(not running)
        if actions.get("stop_compilation"):
            actions["stop_compilation"].setEnabled(running)

    # ── Project actions ──

    def _on_new_project(self) -> None:
        from src.ui.dialogs.new_project_dialog import NewProjectDialog
        dlg = NewProjectDialog(self._settings.compiler_default_engine, self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        project = self._project_manager.create(
            root_path=dlg.project_dir,
            name=dlg.project_name,
            main_file=dlg.main_file,
            engine=dlg.engine,
            bibliography_tool=dlg.bibliography_tool,
        )

        if dlg.create_template:
            self._create_main_tex_template(project.main_tex_path, project.name)

        self._tab_manager.close_all()
        self._open_file(str(project.main_tex_path))

    def _on_open_project_dialog(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Open Project Directory")
        if path:
            self._open_project(Path(path))

    def _open_project(self, root_path: Path) -> None:
        from src.core.exceptions import ProjectError
        try:
            self._project_manager.open(root_path)
        except ProjectError as e:
            QMessageBox.warning(self, "Open Project", str(e))

    def _on_close_project(self) -> None:
        if not self._project_manager.is_open():
            return
        self._tab_manager.close_all()
        self._project_manager.close()

    def _on_project_settings(self) -> None:
        project = self._project_manager.current
        if not project:
            QMessageBox.information(self, "Project Settings", "No project is open.")
            return
        from src.ui.dialogs.project_settings_dialog import ProjectSettingsDialog
        dlg = ProjectSettingsDialog(project, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            dlg.apply_to_project()
            # Update compilation controller with new project settings
            if self._compilation_controller:
                self._compilation_controller._on_project_opened(project)

    def _on_project_opened(self, project) -> None:
        self.setWindowTitle(f"{project.name} — {APP_NAME}")
        # Update engine toolbar to match project engine
        engine_map = {"pdflatex": "pdfLaTeX", "xelatex": "XeLaTeX", "lualatex": "LuaLaTeX"}
        display = engine_map.get(project.engine, project.engine)
        idx = self._toolbar.engine_combo.findText(display)
        if idx >= 0:
            # Let the change propagate to settings so compilation actually
            # uses the project's engine, not a stale global default.
            self._toolbar.engine_combo.setCurrentIndex(idx)
        self._status_bar.set_engine(project.engine)
        # Open the main .tex file
        if project.main_tex_path.is_file():
            self._open_file(str(project.main_tex_path))

    def _create_main_tex_template(self, path: Path, project_name: str) -> None:
        if path.exists():
            return
        template = (
            f"\\documentclass{{article}}\n"
            f"\\title{{{project_name}}}\n"
            f"\\author{{}}\n"
            f"\\date{{\\today}}\n\n"
            f"\\begin{{document}}\n"
            f"\\maketitle\n\n"
            f"\\section{{Introduction}}\n"
            f"Your text here.\n\n"
            f"\\end{{document}}\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template, encoding="utf-8")

    # ── File actions ──

    def _open_file(self, path: str) -> None:
        if not path:
            return
        path_lower = path.lower()

        # Route PDF files to the PDF viewer panel
        if path_lower.endswith(".pdf"):
            if self._pdf_viewer:
                self._pdf_viewer.open_pdf(Path(path))
                if self._layout.pdf_viewer:
                    self._layout.pdf_viewer.setVisible(True)
            return

        # Route images to the image viewer tab
        if Path(path).suffix.lower() in ImageViewerTab.SUPPORTED_EXTENSIONS:
            self._tab_manager.open_image(path)
            return

        # Default: open as text in editor
        editor = self._tab_manager.open_file(path)
        if editor:
            # Show any diagnostics from the last build in the new tab
            if self._last_diagnostics:
                self._tab_manager.apply_diagnostics(self._last_diagnostics)
            if self._compilation_controller:
                if path_lower.endswith(".tex") and not self._compilation_controller._main_tex:
                    self._compilation_controller.set_main_tex(Path(path))

    def _on_new_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "New File", "", "LaTeX Files (*.tex);;All Files (*)"
        )
        if path:
            Path(path).touch()
            self._open_file(path)

    def _on_open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "",
            "LaTeX Files (*.tex *.sty *.cls *.bib);;All Files (*)",
        )
        if path:
            self._open_file(path)

    # ── Compilation ──

    def _on_compile(self) -> None:
        if not self._compilation_controller:
            return
        tex_file = None
        if not self._compilation_controller._main_tex:
            editor = self._tab_manager.current_editor
            if editor and editor.file_path.lower().endswith(".tex"):
                editor.save_file()
                tex_file = Path(editor.file_path)
            else:
                QMessageBox.information(self, "Compile", "Open a .tex file to compile.")
                return
        else:
            self._tab_manager.save_all()
        self._layout.output_panel.setVisible(True)
        self._compilation_controller.compile(tex_file)

    def _on_stop_compilation(self) -> None:
        if self._compilation_controller:
            self._compilation_controller.stop()

    # Build artifacts removed by Clean Build (the PDF is kept)
    _CLEAN_SUFFIXES = (
        ".aux", ".log", ".out", ".toc", ".lof", ".lot", ".bbl", ".blg",
        ".bcf", ".run.xml", ".idx", ".ind", ".ilg", ".synctex", ".synctex.gz",
        ".fls", ".fdb_latexmk", ".nav", ".snm", ".vrb", ".xdv",
    )

    def _on_clean_build(self) -> None:
        if not self._compilation_controller:
            return
        main_tex = self._compilation_controller._main_tex
        if not main_tex:
            QMessageBox.information(self, "Clean Build", "No main .tex file set.")
            return
        output_dir = self._compilation_controller._output_dir or (main_tex.parent / "build")
        removed = 0
        if output_dir.is_dir():
            for f in output_dir.iterdir():
                if f.is_file() and f.name.lower().endswith(self._CLEAN_SUFFIXES):
                    try:
                        f.unlink()
                        removed += 1
                    except OSError as e:
                        log.warning("Could not delete %s: %s", f, e)
        self._tab_manager.clear_diagnostics()
        self._last_diagnostics = []
        self.statusBar().showMessage(
            f"Clean Build: removed {removed} auxiliary file(s)", 4000
        )

    def _on_forward_sync(self) -> None:
        editor = self._tab_manager.current_editor
        if not editor or not editor.file_path.lower().endswith(".tex"):
            return
        line, col = editor.getCursorPosition()
        event_bus.synctex_forward.emit(editor.file_path, line + 1, col + 1)

    # ── Navigation ──

    def _on_jump_to_source(self, file_path: str, line: int, col: int) -> None:
        editor = self._tab_manager.open_file(file_path)
        if editor and line > 0:
            editor.setCursorPosition(line - 1, max(0, col - 1))
            editor.setFocus()

    # ── Word wrap ──

    def _on_toggle_word_wrap(self) -> None:
        action = self._menu_builder.actions.get("toggle_word_wrap")
        enabled = action.isChecked() if action else False
        self._settings.editor_word_wrap = enabled
        self._tab_manager.set_word_wrap_all(enabled)

    # ── Theme / engine ──

    def _on_toggle_theme(self) -> None:
        new_theme = self._theme_manager.toggle_theme()
        self._settings.theme = new_theme

    def _on_engine_menu_selected(self, display_name: str) -> None:
        idx = self._toolbar.engine_combo.findText(display_name)
        if idx >= 0:
            self._toolbar.engine_combo.setCurrentIndex(idx)

    def _on_engine_changed(self, display_name: str) -> None:
        mapping = {"pdfLaTeX": "pdflatex", "XeLaTeX": "xelatex", "LuaLaTeX": "lualatex"}
        engine = mapping.get(display_name, "pdflatex")
        self._settings.compiler_default_engine = engine
        self._status_bar.set_engine(engine)
        # Keep the Build > Select Engine menu checkmarks in sync
        actions = self._menu_builder.actions
        for name in ("engine_pdflatex", "engine_xelatex", "engine_lualatex"):
            if actions.get(name):
                actions[name].setChecked(name == f"engine_{engine}")

    # ── Find / Replace / GoTo ──

    def _on_find(self) -> None:
        editor = self._tab_manager.current_editor
        if not editor:
            return
        self._find_replace_dialog.set_editor(editor)
        # Pre-fill with selected text
        if editor.hasSelectedText():
            self._find_replace_dialog.set_find_text(editor.selectedText())
        self._find_replace_dialog.show()
        self._find_replace_dialog.raise_()
        self._find_replace_dialog.activateWindow()

    def _on_find_replace(self) -> None:
        self._on_find()  # Same dialog, just shows it

    def _on_goto_line(self) -> None:
        editor = self._tab_manager.current_editor
        if not editor:
            return
        from PyQt6.QtWidgets import QInputDialog
        line, ok = QInputDialog.getInt(
            self, "Go to Line", "Line number:",
            editor.getCursorPosition()[0] + 1, 1, editor.lines(),
        )
        if ok:
            editor.setCursorPosition(line - 1, 0)
            editor.setFocus()

    # ── Zoom ──

    def _on_zoom_in(self) -> None:
        editor = self._tab_manager.current_editor
        if editor:
            editor.zoomIn(2)

    def _on_zoom_out(self) -> None:
        editor = self._tab_manager.current_editor
        if editor:
            editor.zoomOut(2)

    def _on_zoom_reset(self) -> None:
        editor = self._tab_manager.current_editor
        if editor:
            editor.zoomTo(0)

    # ── Tools ──

    def _on_package_manager(self) -> None:
        from src.ui.dialogs.package_browser_dialog import PackageBrowserDialog
        miktex_bin = self._settings.miktex_bin_dir
        dlg = PackageBrowserDialog(miktex_bin, self)
        dlg.exec()

    def _on_open_terminal(self) -> None:
        import shutil
        import subprocess
        project = self._project_manager.current
        cwd = str(project.root_path) if project else "."
        # Prefer Windows Terminal, then PowerShell, then cmd
        wt = shutil.which("wt")
        if wt:
            subprocess.Popen([wt, "-d", cwd])
            return
        shell = shutil.which("pwsh") or shutil.which("powershell") or "cmd.exe"
        subprocess.Popen([shell], cwd=cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)

    # ── Settings dialogs ──

    def _on_preferences(self) -> None:
        from src.ui.dialogs.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._settings, self)
        dlg.exec()

    def _on_keybindings(self) -> None:
        from src.ui.dialogs.keybindings_dialog import KeybindingsDialog
        dlg = KeybindingsDialog(self)
        dlg.exec()

    def _show_about(self) -> None:
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3><p>Version {APP_VERSION}</p>"
            f"<p>A Python-based LaTeX IDE for MiKTeX.</p>"
            f"<p>Built with PyQt6 and QScintilla.</p>",
        )

    # ── Session save / restore ──

    def _restore_window_state(self) -> None:
        geometry = self._settings.get_session("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1400, 900)
        state = self._settings.get_session("window_state")
        if state:
            self.restoreState(state)

        # Restore splitter sizes
        h_sizes = self._session_manager.splitter_h_sizes()
        v_sizes = self._session_manager.splitter_v_sizes()
        if h_sizes:
            self._layout.h_splitter.setSizes(h_sizes)
        if v_sizes:
            self._layout.v_splitter.setSizes(v_sizes)

        # Restore panel visibility
        vis = self._session_manager.panels_visible()
        self._layout.file_tree.setVisible(vis.get("file_tree", True))
        if self._layout.pdf_viewer:
            self._layout.pdf_viewer.setVisible(vis.get("pdf_viewer", True))
        self._layout.output_panel.setVisible(vis.get("output_panel", True))

    def save_session(self) -> None:
        """Save full session: window geometry + open files + splitter sizes."""
        self._settings.set_session("window_geometry", self.saveGeometry())
        self._settings.set_session("window_state", self.saveState())

        open_files = []
        for path in self._tab_manager.open_file_paths:
            editor = self._tab_manager._open_files.get(path)
            line, col = (editor.getCursorPosition() if editor else (0, 0))
            open_files.append({"path": path, "line": line, "col": col})

        last_pdf = (
            str(self._pdf_viewer.current_pdf)
            if (self._pdf_viewer and self._pdf_viewer.current_pdf)
            else ""
        )

        project = self._project_manager.current
        self._session_manager.save(
            project_path=str(project.root_path) if project else None,
            open_files=open_files,
            active_tab_index=self._tab_manager.currentIndex(),
            splitter_h=self._layout.h_splitter.sizes(),
            splitter_v=self._layout.v_splitter.sizes(),
            panels_visible={
                "file_tree": self._layout.file_tree.isVisible(),
                "pdf_viewer": (self._layout.pdf_viewer.isVisible()
                               if self._layout.pdf_viewer else True),
                "output_panel": self._layout.output_panel.isVisible(),
            },
            last_pdf=last_pdf,
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._compilation_controller and self._compilation_controller.is_running:
            self._compilation_controller.stop()
        # Save the session before closing tabs — close_all() empties the
        # open-file list, so saving afterwards would persist an empty session.
        self.save_session()
        if not self._tab_manager.close_all():
            event.ignore()
            return
        log.info("Window closed")
        event.accept()

    # ── Properties ──

    @property
    def layout_manager(self) -> SplitterLayout:
        return self._layout

    @property
    def tab_manager(self) -> TabManager:
        return self._tab_manager

    @property
    def file_tree(self) -> FileTreeWidget:
        return self._file_tree

    @property
    def output_panel(self) -> OutputPanel:
        return self._output_panel

    @property
    def pdf_viewer(self):
        return self._pdf_viewer

    @property
    def menu_actions(self) -> dict[str, QAction]:
        return self._menu_builder.actions

    @property
    def toolbar(self) -> MainToolBar:
        return self._toolbar

    @property
    def app_status_bar(self) -> StatusBar:
        return self._status_bar

    @property
    def project_manager(self) -> ProjectManager:
        return self._project_manager
