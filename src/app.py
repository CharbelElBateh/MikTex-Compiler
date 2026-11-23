import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.constants import APP_NAME, APP_VERSION, ORG_NAME
from src.core.event_bus import event_bus
from src.core.logging_config import get_logger, setup_logging
from src.core.project_manager import ProjectManager
from src.core.session_manager import SessionManager
from src.core.settings_manager import SettingsManager
from src.themes.theme_manager import ThemeManager
from src.ui.main_window import MainWindow
from src.utils.path_utils import find_miktex_bin_dir

log = get_logger("app")


class Application:
    """Application bootstrap and lifecycle management."""

    def __init__(self, verbose: bool = False, open_target: str | None = None) -> None:
        # 1. Logging
        setup_logging(verbose=verbose)
        log.info("Starting %s v%s", APP_NAME, APP_VERSION)

        # File or project directory passed on the command line
        self._open_target = Path(open_target).resolve() if open_target else None

        # 2. QApplication
        self._qapp = QApplication.instance() or QApplication(sys.argv)
        self._qapp.setApplicationName(APP_NAME)
        self._qapp.setOrganizationName(ORG_NAME)
        self._qapp.setApplicationVersion(APP_VERSION)

        # 3. Settings
        self._settings = SettingsManager()

        # 4. Detect MiKTeX
        self._miktex_bin_dir = find_miktex_bin_dir(self._settings.miktex_bin_dir)
        if self._miktex_bin_dir:
            self._settings.miktex_bin_dir = self._miktex_bin_dir
            log.info("MiKTeX bin directory: %s", self._miktex_bin_dir)
        else:
            log.warning("MiKTeX not found - compilation features will be disabled")

        # 5. Theme
        self._theme_manager = ThemeManager()
        self._theme_manager.apply_theme(self._settings.theme)

        # 6. Project & session management
        self._project_manager = ProjectManager(self._settings)
        self._session_manager = SessionManager(self._settings)

        # 7. Compilation controller + SyncTeX bridge (only when MiKTeX found)
        self._compilation_controller = None
        self._synctex_bridge = None
        self._pdf_viewer = None

        if self._miktex_bin_dir:
            from src.compiler.compilation_controller import CompilationController
            from src.compiler.engine import EngineRegistry
            from src.compiler.synctex_bridge import SyncTeXBridge
            from src.viewer.pdf_viewer_widget import PDFViewerWidget

            self._engine_registry = EngineRegistry(self._miktex_bin_dir)
            log.info("Available engines: %s", self._engine_registry.available_names())

            self._synctex_bridge = SyncTeXBridge(self._miktex_bin_dir)
            log.info("SyncTeX available: %s", self._synctex_bridge.available)

            self._compilation_controller = CompilationController(
                settings=self._settings,
                engine_registry=self._engine_registry,
            )

            self._pdf_viewer = PDFViewerWidget(
                synctex_bridge=self._synctex_bridge,
                dpi=self._settings.viewer_render_dpi,
                default_zoom=self._settings.viewer_default_zoom,
            )

        # 8. Main window
        self._main_window = MainWindow(
            settings=self._settings,
            theme_manager=self._theme_manager,
            project_manager=self._project_manager,
            session_manager=self._session_manager,
            compilation_controller=self._compilation_controller,
            pdf_viewer=self._pdf_viewer,
        )

        if self._compilation_controller:
            self._compilation_controller._parent = self._main_window

        # 9. File watcher for auto-compile
        from src.compiler.file_watcher import FileWatcher
        self._file_watcher = FileWatcher(parent=self._main_window)
        self._file_watcher.enabled = self._settings.compiler_auto_compile
        if self._compilation_controller:
            self._file_watcher.auto_compile_triggered.connect(
                lambda: self._main_window._on_compile()
            )
        event_bus.project_opened.connect(self._on_project_watch)
        event_bus.settings_changed.connect(self._on_settings_changed)

        # 10. Plugin system
        from src.core.plugin_api import PluginAPI
        from src.core.plugin_manager import PluginManager
        plugin_dir = Path(__file__).parent.parent / "plugins"
        self._plugin_api = PluginAPI(self._main_window, self._settings)
        self._plugin_manager = PluginManager(plugin_dir, self._plugin_api)
        self._plugin_manager.load_all()

        # 11. Wire recent projects menu
        self._populate_recent_menu()
        self._project_manager.recent_changed.connect(self._populate_recent_menu)

    def _populate_recent_menu(self) -> None:
        """Rebuild the Open Recent submenu from recent project list."""
        menu = self._main_window._menu_builder.recent_menu
        menu.clear()

        recents = self._project_manager.recent_projects
        if not recents:
            no_action = menu.addAction("(No recent projects)")
            no_action.setEnabled(False)
            return

        for path in recents:
            action = menu.addAction(f"{path.name}  —  {path}")
            action.setData(str(path))
            action.triggered.connect(
                lambda checked, p=path: self._open_recent_project(p)
            )

        menu.addSeparator()
        clear_action = menu.addAction("Clear Recent Projects")
        clear_action.triggered.connect(self._clear_recent_projects)

    def _open_recent_project(self, path: Path) -> None:
        from src.core.exceptions import ProjectError
        try:
            self._project_manager.open(path)
        except ProjectError as e:
            QMessageBox.warning(self._main_window, "Open Recent Project", str(e))

    def _clear_recent_projects(self) -> None:
        self._project_manager.clear_recent()

    def _on_project_watch(self, project) -> None:
        """Start watching the project directory for auto-compile."""
        root = Path(getattr(project, "root_path", ""))
        if root.is_dir():
            self._file_watcher.watch(root)

    def _on_settings_changed(self, section: str, key: str, value) -> None:
        if section == "Compiler" and key == "auto_compile_on_save":
            self._file_watcher.enabled = bool(value)
        elif section == "Editor":
            # Apply font/tab/wrap/whitespace changes to open editors immediately
            self._main_window.tab_manager.apply_editor_settings()
        elif section == "Viewer" and self._pdf_viewer:
            if key == "render_dpi":
                self._pdf_viewer.set_dpi(self._settings.viewer_render_dpi)
            elif key == "default_zoom":
                self._pdf_viewer.set_default_zoom(self._settings.viewer_default_zoom)
        elif section == "MiKTeX" and key == "bin_directory":
            if not self._compilation_controller:
                from src.utils.path_utils import find_miktex_bin_dir
                if find_miktex_bin_dir(Path(str(value))):
                    QMessageBox.information(
                        self._main_window,
                        "MiKTeX Found",
                        "MiKTeX detected at the new location.\n\n"
                        "Restart the application to enable compilation features.",
                    )

    def _restore_session(self) -> None:
        """Restore the last session or show the welcome dialog."""
        last_project = self._session_manager.last_project()

        if last_project:
            log.info("Restoring last project: %s", last_project)
            from src.core.exceptions import ProjectError
            try:
                self._project_manager.open(last_project)
            except ProjectError as e:
                log.warning("Could not restore last project: %s", e)
                self._show_welcome_dialog()
                return

            # Restore open files
            open_files = self._session_manager.open_files()
            for entry in open_files:
                self._main_window._open_file(entry["path"])
                editor = self._main_window.tab_manager._open_files.get(entry["path"])
                if editor:
                    editor.setCursorPosition(entry.get("line", 0), entry.get("col", 0))

            # Restore active tab
            idx = self._session_manager.active_tab_index()
            if 0 <= idx < self._main_window.tab_manager.count():
                self._main_window.tab_manager.setCurrentIndex(idx)

            # Restore last open PDF in the viewer
            last_pdf = self._session_manager.last_pdf()
            if last_pdf and Path(last_pdf).is_file() and self._pdf_viewer:
                self._pdf_viewer.open_pdf(Path(last_pdf))
        else:
            self._show_welcome_dialog()

    def _open_startup_target(self, target: Path) -> None:
        """Open the file or project directory passed on the command line."""
        from src.core.exceptions import ProjectError

        if target.is_dir():
            try:
                self._project_manager.open(target)
            except ProjectError as e:
                QMessageBox.warning(self._main_window, "Open Project", str(e))
        elif target.is_file():
            self._main_window._open_file(str(target))
        else:
            QMessageBox.warning(
                self._main_window, "Open", f"Path not found: {target}"
            )

    def _show_welcome_dialog(self) -> None:
        from src.ui.dialogs.welcome_dialog import WelcomeDialog
        recent_paths = self._project_manager.recent_projects
        dlg = WelcomeDialog(recent_paths, self._main_window)
        dlg.open_project_requested.connect(self._on_welcome_open_project)
        dlg.new_project_requested.connect(self._main_window._on_new_project)
        dlg.exec()

        # If "Open File" was chosen
        file_to_open = dlg.file_to_open
        if file_to_open:
            self._main_window._open_file(file_to_open)

    def _on_welcome_open_project(self, path_str: str) -> None:
        if not path_str:
            return
        from src.core.exceptions import ProjectError
        try:
            self._project_manager.open(Path(path_str))
        except ProjectError as e:
            QMessageBox.warning(self._main_window, "Open Project", str(e))

    def run(self) -> int:
        self._main_window.show()
        log.info("Application ready")

        if not self._miktex_bin_dir:
            QMessageBox.warning(
                self._main_window,
                "MiKTeX Not Found",
                "Could not locate a MiKTeX installation.\n\n"
                "Compilation features will be disabled.\n"
                "Please configure the MiKTeX path in Settings > Preferences.",
            )

        # An explicit command-line target takes precedence over session restore
        if self._open_target:
            self._open_startup_target(self._open_target)
        else:
            # Session restore happens after show() so geometry is applied correctly
            self._restore_session()

        exit_code = self._qapp.exec()

        # Cleanup
        self._file_watcher.stop()
        self._plugin_manager.unload_all()

        return exit_code

    @property
    def main_window(self) -> MainWindow:
        return self._main_window

    @property
    def settings(self) -> SettingsManager:
        return self._settings

    @property
    def theme_manager(self) -> ThemeManager:
        return self._theme_manager
