"""Manages the lifecycle of projects: open, close, create, recent list."""

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.event_bus import event_bus
from src.core.exceptions import ProjectError, ProjectNotFoundError
from src.core.logging_config import get_logger
from src.core.project import Project
from src.core.settings_manager import SettingsManager

log = get_logger("core.project_manager")


class ProjectManager(QObject):
    """Manages opening, closing, creating, and remembering projects."""

    recent_changed = pyqtSignal()

    def __init__(self, settings: SettingsManager) -> None:
        super().__init__()
        self._settings = settings
        self._current: Project | None = None

    @property
    def current(self) -> Project | None:
        return self._current

    def is_open(self) -> bool:
        return self._current is not None

    # ── Open / Close ──

    def open(self, root_path: Path) -> Project:
        """Open an existing project. Raises ProjectNotFoundError if not found."""
        if not root_path.is_dir():
            raise ProjectNotFoundError(f"Directory not found: {root_path}")

        project = Project.load(root_path)
        self._set_current(project)
        return project

    def open_or_create(self, root_path: Path, **kwargs) -> Project:
        """Open a project if it exists, otherwise create one with the given kwargs."""
        if Project.exists_at(root_path):
            return self.open(root_path)
        return self.create(root_path, **kwargs)

    def create(
        self,
        root_path: Path,
        name: str = "",
        main_file: str = "main.tex",
        engine: str = "pdflatex",
        bibliography_tool: str = "none",
    ) -> Project:
        """Create a new project at root_path and save its config."""
        root_path.mkdir(parents=True, exist_ok=True)
        project = Project(
            root_path=root_path,
            name=name or root_path.name,
            main_file=main_file,
            engine=engine,
            bibliography_tool=bibliography_tool,
        )
        project.save()
        log.info("Created project '%s' at %s", project.name, root_path)
        self._set_current(project)
        return project

    def close(self) -> None:
        if self._current:
            log.info("Closing project '%s'", self._current.name)
            self._current = None
            event_bus.project_closed.emit()

    # ── Recent projects ──

    @property
    def recent_projects(self) -> list[Path]:
        return [Path(p) for p in self._settings.recent_projects if Path(p).is_dir()]

    def add_to_recent(self, root_path: Path) -> None:
        self._settings.add_recent_project(str(root_path))
        self.recent_changed.emit()

    def clear_recent(self) -> None:
        self._settings.clear_recent_projects()
        self.recent_changed.emit()

    # ── Internal ──

    def _set_current(self, project: Project) -> None:
        if self._current:
            self.close()
        self._current = project
        self.add_to_recent(project.root_path)
        event_bus.project_opened.emit(project)
        log.info("Opened project '%s' at %s", project.name, project.root_path)
