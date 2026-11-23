"""Compilation pipeline: defines the ordered steps to build a LaTeX document."""

import os
from dataclasses import dataclass
from pathlib import Path

from src.compiler.engine import Engine
from src.core.logging_config import get_logger

log = get_logger("compiler.pipeline")


@dataclass
class PipelineStep:
    name: str
    command: list[str]
    cwd: Path
    stop_on_failure: bool = True
    optional: bool = False  # If True, skip when precondition not met
    input_file: Path | None = None  # Precondition file for optional steps


class CompilationPipeline:
    """Builds the ordered list of steps needed to compile a LaTeX project."""

    def __init__(
        self,
        engine: Engine,
        main_tex: Path,
        output_dir: Path,
        miktex_bin_dir: Path,
        bibliography_tool: str = "none",
        extra_args: list[str] | None = None,
        max_passes: int = 3,
        synctex: bool = True,
        pre_build: list[str] | None = None,
        post_build: list[str] | None = None,
    ) -> None:
        self._engine = engine
        self._main_tex = main_tex
        self._output_dir = output_dir
        self._miktex_bin_dir = miktex_bin_dir
        self._bibliography_tool = bibliography_tool
        self._extra_args = extra_args or []
        self._max_passes = max_passes
        self._synctex = synctex
        self._pre_build = pre_build or []
        self._post_build = post_build or []

    def build_steps(self) -> list[PipelineStep]:
        """Return the ordered list of compilation steps."""
        cwd = self._main_tex.parent
        stem = self._main_tex.stem
        output_dir = self._output_dir

        default_args = list(self._engine.default_args)
        if not self._synctex:
            default_args = [a for a in default_args if not a.startswith("-synctex")]

        engine_args = (
            default_args
            + [f"-output-directory={output_dir}"]
            + self._extra_args
            + [str(self._main_tex.name)]
        )

        engine_cmd = [str(self._engine.executable)] + engine_args

        steps: list[PipelineStep] = []

        # Pre-build hooks
        for i, hook in enumerate(self._pre_build, 1):
            steps.append(PipelineStep(
                name=f"Pre-build hook {i}",
                command=["cmd.exe", "/c", hook],
                cwd=cwd,
            ))

        # Pass 1
        steps.append(PipelineStep(
            name="LaTeX (pass 1)",
            command=engine_cmd,
            cwd=cwd,
            stop_on_failure=False,  # Continue to parse the log even on error
        ))

        # Bibliography
        if self._bibliography_tool == "bibtex":
            bibtex = self._miktex_bin_dir / "bibtex.exe"
            # Use a path relative to cwd — bibtex's output security can
            # refuse absolute paths.
            aux_stem = os.path.relpath(output_dir / stem, cwd)
            steps.append(PipelineStep(
                name="BibTeX",
                command=[str(bibtex), aux_stem],
                cwd=cwd,
                stop_on_failure=False,
                optional=True,
                input_file=output_dir / f"{stem}.aux",
            ))
        elif self._bibliography_tool == "biber":
            biber = self._miktex_bin_dir / "biber.exe"
            steps.append(PipelineStep(
                name="Biber",
                command=[str(biber), "--input-directory", str(output_dir),
                         "--output-directory", str(output_dir), stem],
                cwd=cwd,
                stop_on_failure=False,
                optional=True,
                input_file=output_dir / f"{stem}.bcf",
            ))

        # MakeIndex (optional — only run if .idx file exists after pass 1)
        makeindex = self._miktex_bin_dir / "makeindex.exe"
        steps.append(PipelineStep(
            name="MakeIndex",
            command=[str(makeindex), str(output_dir / f"{stem}.idx")],
            cwd=cwd,
            stop_on_failure=False,
            optional=True,
            input_file=output_dir / f"{stem}.idx",
        ))

        # Pass 2
        if self._max_passes >= 2:
            steps.append(PipelineStep(
                name="LaTeX (pass 2)",
                command=engine_cmd,
                cwd=cwd,
                stop_on_failure=False,
            ))

        # Pass 3 (resolves cross-references that changed in pass 2)
        if self._max_passes >= 3:
            steps.append(PipelineStep(
                name="LaTeX (pass 3)",
                command=engine_cmd,
                cwd=cwd,
                stop_on_failure=False,
            ))

        # Post-build hooks
        for i, hook in enumerate(self._post_build, 1):
            steps.append(PipelineStep(
                name=f"Post-build hook {i}",
                command=["cmd.exe", "/c", hook],
                cwd=cwd,
                stop_on_failure=False,
            ))

        return steps

    @property
    def main_tex(self) -> Path:
        return self._main_tex

    @property
    def source_dir(self) -> Path:
        return self._main_tex.parent

    @property
    def output_pdf(self) -> Path:
        return self._output_dir / f"{self._main_tex.stem}.pdf"

    @property
    def output_log(self) -> Path:
        return self._output_dir / f"{self._main_tex.stem}.log"
