"""Project data model and TOML serialization."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import tomli_w

from src.constants import (
    DEFAULT_ENGINE,
    DEFAULT_OUTPUT_DIR,
    PROJECT_CONFIG_DIR,
    PROJECT_CONFIG_FILE,
)
from src.core.exceptions import ProjectError, ProjectNotFoundError
from src.core.logging_config import get_logger

log = get_logger("core.project")


@dataclass
class Project:
    root_path: Path
    name: str
    main_file: str              # relative to root_path, e.g. "main.tex"
    engine: str = DEFAULT_ENGINE
    output_directory: str = DEFAULT_OUTPUT_DIR
    bibliography_tool: str = "none"   # "none" | "bibtex" | "biber"
    synctex: bool = True
    extra_args: list[str] = field(default_factory=list)
    max_passes: int = 3
    pre_build: list[str] = field(default_factory=list)
    post_build: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    last_opened: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # ── Derived paths ──

    @property
    def config_dir(self) -> Path:
        return self.root_path / PROJECT_CONFIG_DIR

    @property
    def config_file(self) -> Path:
        return self.config_dir / PROJECT_CONFIG_FILE

    @property
    def main_tex_path(self) -> Path:
        return self.root_path / self.main_file

    @property
    def output_dir_path(self) -> Path:
        return self.root_path / self.output_directory

    # ── Persistence ──

    def save(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "project": {
                "name": self.name,
                "main_file": self.main_file,
                "created_at": self.created_at,
                "last_opened": self.last_opened,
            },
            "compiler": {
                "engine": self.engine,
                "output_directory": self.output_directory,
                "bibliography_tool": self.bibliography_tool,
                "synctex": self.synctex,
                "extra_args": self.extra_args,
                "max_passes": self.max_passes,
                "custom_commands": {
                    "pre_build": self.pre_build,
                    "post_build": self.post_build,
                },
            },
        }
        self.config_file.write_bytes(tomli_w.dumps(data).encode())
        log.debug("Project saved: %s", self.config_file)

    @classmethod
    def load(cls, root_path: Path) -> "Project":
        config_file = root_path / PROJECT_CONFIG_DIR / PROJECT_CONFIG_FILE
        if not config_file.is_file():
            raise ProjectNotFoundError(f"No project config at {config_file}")
        try:
            data = tomllib.loads(config_file.read_text(encoding="utf-8"))
        except Exception as e:
            raise ProjectError(f"Failed to parse project config: {e}") from e

        p = data.get("project", {})
        c = data.get("compiler", {})
        cc = c.get("custom_commands", {})

        return cls(
            root_path=root_path,
            name=p.get("name", root_path.name),
            main_file=p.get("main_file", "main.tex"),
            created_at=p.get("created_at", ""),
            last_opened=datetime.now().isoformat(timespec="seconds"),
            engine=c.get("engine", DEFAULT_ENGINE),
            output_directory=c.get("output_directory", DEFAULT_OUTPUT_DIR),
            bibliography_tool=c.get("bibliography_tool", "none"),
            synctex=c.get("synctex", True),
            extra_args=c.get("extra_args", []),
            max_passes=c.get("max_passes", 3),
            pre_build=cc.get("pre_build", []),
            post_build=cc.get("post_build", []),
        )

    @classmethod
    def exists_at(cls, root_path: Path) -> bool:
        return (root_path / PROJECT_CONFIG_DIR / PROJECT_CONFIG_FILE).is_file()
