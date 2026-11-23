"""High-level controller that bridges UI actions to the compilation pipeline."""

from pathlib import Path

from PyQt6.QtWidgets import QMessageBox, QWidget

from src.compiler.compilation_pipeline import CompilationPipeline
from src.compiler.compiler_worker import CompilerWorker
from src.compiler.engine import EngineRegistry
from src.core.event_bus import event_bus
from src.core.logging_config import get_logger
from src.core.settings_manager import SettingsManager

log = get_logger("compiler.controller")


class CompilationController:
    """Manages compilation requests, worker lifecycle, and EventBus integration."""

    def __init__(
        self,
        settings: SettingsManager,
        engine_registry: EngineRegistry,
        parent_widget: QWidget | None = None,
    ) -> None:
        self._settings = settings
        self._registry = engine_registry
        self._parent = parent_widget
        self._worker: CompilerWorker | None = None
        self._current_pipeline: CompilationPipeline | None = None

        # Active project info (set when project is opened, or derived from current file)
        self._main_tex: Path | None = None
        self._output_dir: Path | None = None
        self._bibliography_tool: str = "none"
        self._extra_args: list[str] = []
        self._max_passes: int = 3
        self._synctex: bool = True
        self._pre_build: list[str] = []
        self._post_build: list[str] = []

        event_bus.project_opened.connect(self._on_project_opened)
        event_bus.project_closed.connect(self._on_project_closed)

    def compile(self, main_tex: Path | None = None) -> bool:
        """Start compilation. Returns False if compilation couldn't start."""
        if self._worker and self._worker.isRunning():
            log.warning("Compilation already running")
            return False

        tex_file = main_tex or self._main_tex
        if not tex_file:
            QMessageBox.warning(
                self._parent, "No File", "No .tex file selected for compilation."
            )
            return False

        engine_name = self._settings.compiler_default_engine
        engine = self._registry.get(engine_name)
        if not engine:
            QMessageBox.warning(
                self._parent,
                "Engine Not Found",
                f"Engine '{engine_name}' not found in MiKTeX installation.",
            )
            return False

        output_dir = self._output_dir or (tex_file.parent / "build")
        output_dir.mkdir(parents=True, exist_ok=True)

        self._current_pipeline = CompilationPipeline(
            engine=engine,
            main_tex=tex_file,
            output_dir=output_dir,
            miktex_bin_dir=self._settings.miktex_bin_dir,
            bibliography_tool=self._bibliography_tool,
            extra_args=self._extra_args,
            max_passes=self._max_passes,
            synctex=self._synctex,
            pre_build=self._pre_build,
            post_build=self._post_build,
        )

        self._worker = CompilerWorker(self._current_pipeline, self._settings.miktex_bin_dir)
        self._worker.output_line.connect(event_bus.compilation_output)
        self._worker.step_started.connect(lambda name: log.debug("Step: %s", name))
        self._worker.finished.connect(self._on_worker_finished)

        event_bus.compilation_started.emit(engine_name)
        self._worker.start()
        log.info("Compilation started: %s with %s", tex_file.name, engine_name)
        return True

    def stop(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
            event_bus.compilation_cancelled.emit()

    def set_main_tex(self, path: Path) -> None:
        self._main_tex = path
        log.debug("Main TeX file set to: %s", path)

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def _on_worker_finished(self, success: bool, errors: list) -> None:
        event_bus.compilation_finished.emit(success, errors)
        log.info("Compilation finished: success=%s, issues=%d", success, len(errors))
        # Notify PDF viewer of new PDF
        if success and self._current_pipeline:
            pdf = self._current_pipeline.output_pdf
            if pdf.is_file():
                event_bus.pdf_ready.emit(str(pdf))

    def _on_project_opened(self, project) -> None:
        root = Path(getattr(project, "root_path", ""))
        main_file = getattr(project, "main_file", "")
        output_dir_name = getattr(project, "output_directory", "build")
        self._bibliography_tool = getattr(project, "bibliography_tool", "none")
        self._extra_args = list(getattr(project, "extra_args", []) or [])
        self._max_passes = int(getattr(project, "max_passes", 3) or 3)
        self._synctex = bool(getattr(project, "synctex", True))
        self._pre_build = list(getattr(project, "pre_build", []) or [])
        self._post_build = list(getattr(project, "post_build", []) or [])

        if root and main_file:
            self._main_tex = root / main_file
            self._output_dir = root / output_dir_name

    def _on_project_closed(self) -> None:
        self._main_tex = None
        self._output_dir = None
        self._bibliography_tool = "none"
        self._extra_args = []
        self._max_passes = 3
        self._synctex = True
        self._pre_build = []
        self._post_build = []
