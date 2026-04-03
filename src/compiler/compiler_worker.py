"""Background QThread that runs the compilation pipeline."""

import subprocess
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from src.compiler.compilation_pipeline import CompilationPipeline, PipelineStep
from src.compiler.error_model import CompilationError
from src.compiler.log_parser import LogParser
from src.core.logging_config import get_logger
from src.utils.process_utils import build_clean_env

log = get_logger("compiler.worker")


class CompilerWorker(QThread):
    """Runs a CompilationPipeline in a background thread.

    Emits real-time output and structured results via Qt signals.
    """

    output_line = pyqtSignal(str)          # raw line from engine stdout
    step_started = pyqtSignal(str)         # step name
    step_finished = pyqtSignal(str, int)   # step name, return code
    finished = pyqtSignal(bool, list)      # success, list[CompilationError]

    def __init__(self, pipeline: CompilationPipeline, miktex_bin_dir: Path) -> None:
        super().__init__()
        self._pipeline = pipeline
        self._miktex_bin_dir = miktex_bin_dir
        self._current_process: subprocess.Popen | None = None

    def run(self) -> None:
        # Ensure output directory exists
        self._pipeline.output_log.parent.mkdir(parents=True, exist_ok=True)

        steps = self._pipeline.build_steps()
        env = build_clean_env(self._miktex_bin_dir)

        for step in steps:
            if self.isInterruptionRequested():
                self.output_line.emit("[Compilation cancelled]")
                return

            # Skip optional steps when their input doesn't exist
            if step.optional and not self._optional_input_exists(step):
                log.debug("Skipping optional step: %s", step.name)
                continue

            self.step_started.emit(step.name)
            self.output_line.emit(f"\n>>> {step.name}")
            self.output_line.emit(f">>> {' '.join(step.command)}\n")

            returncode = self._run_step(step, env)
            self.step_finished.emit(step.name, returncode)

            if returncode != 0:
                log.debug("Step '%s' returned %d", step.name, returncode)
                if step.stop_on_failure:
                    break

        # Parse log file for structured errors
        errors = LogParser().parse(self._pipeline.output_log)
        has_errors = any(e.level == "error" for e in errors)
        pdf_exists = self._pipeline.output_pdf.is_file()
        success = not has_errors and pdf_exists

        if success:
            self.output_line.emit(f"\n>>> Compilation successful: {self._pipeline.output_pdf}")
        else:
            self.output_line.emit(f"\n>>> Compilation finished with errors.")

        self.finished.emit(success, errors)

    def _run_step(self, step: PipelineStep, env: dict) -> int:
        try:
            self._current_process = subprocess.Popen(
                step.command,
                cwd=str(step.cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in self._current_process.stdout:
                if self.isInterruptionRequested():
                    self._current_process.terminate()
                    return -1
                self.output_line.emit(line.rstrip())

            self._current_process.wait()
            return self._current_process.returncode

        except FileNotFoundError:
            self.output_line.emit(f"[Error] Executable not found: {step.command[0]}")
            return -1
        except Exception as e:
            self.output_line.emit(f"[Error] {e}")
            return -1
        finally:
            self._current_process = None

    def _optional_input_exists(self, step: PipelineStep) -> bool:
        """Check if the input file for an optional step exists (e.g., .idx for makeindex)."""
        # The last argument of optional steps is typically the input file
        if not step.command:
            return False
        candidate = Path(step.command[-1])
        # For makeindex: check .idx; for bibtex/biber: check .aux
        if "makeindex" in step.command[0]:
            return candidate.with_suffix(".idx").is_file()
        if "bibtex" in step.command[0] or "biber" in step.command[0]:
            # Check for \bibliography in aux file
            aux = candidate.with_suffix(".aux")
            if aux.is_file():
                return "\\bibdata" in aux.read_text(encoding="utf-8", errors="replace")
        return True

    def cancel(self) -> None:
        self.requestInterruption()
        if self._current_process:
            try:
                self._current_process.terminate()
            except Exception:
                pass
