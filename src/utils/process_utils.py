import os
import subprocess
from pathlib import Path

from src.core.logging_config import get_logger

log = get_logger("utils.process")


def build_clean_env(miktex_bin_dir: Path) -> dict[str, str]:
    """Build a clean environment for MiKTeX subprocess calls.

    Strips potentially problematic PATH entries and ensures MiKTeX bin
    directory is included along with essential Windows system paths.
    """
    env = os.environ.copy()

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    clean_path_parts = [
        str(miktex_bin_dir),
        os.path.join(system_root, "system32"),
        system_root,
        os.path.join(system_root, "System32", "Wbem"),
    ]
    env["PATH"] = os.pathsep.join(clean_path_parts)

    return env


def run_miktex_command(
    args: list[str],
    miktex_bin_dir: Path,
    cwd: str | Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    """Run a MiKTeX command with a clean environment.

    Returns the CompletedProcess result. Does not raise on non-zero return code.
    """
    env = build_clean_env(miktex_bin_dir)

    log.debug("Running: %s (cwd=%s)", " ".join(args), cwd)

    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def start_miktex_process(
    args: list[str],
    miktex_bin_dir: Path,
    cwd: str | Path | None = None,
) -> subprocess.Popen:
    """Start a MiKTeX process for streaming output.

    Returns a Popen instance with stdout piped for line-by-line reading.
    """
    env = build_clean_env(miktex_bin_dir)

    log.debug("Starting: %s (cwd=%s)", " ".join(args), cwd)

    return subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
