import os
import subprocess
from pathlib import Path

from src.core.logging_config import get_logger

log = get_logger("utils.process")


def build_clean_env(miktex_bin_dir: Path) -> dict[str, str]:
    """Build an environment for MiKTeX subprocess calls.

    Prepends the MiKTeX bin directory so it takes precedence over any other
    TeX distribution on PATH, while keeping the rest of the user's PATH so
    build hooks and tool sub-invocations still resolve.
    """
    env = os.environ.copy()

    existing_path = env.get("PATH", "")
    env["PATH"] = os.pathsep.join(
        [str(miktex_bin_dir)] + ([existing_path] if existing_path else [])
    )

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
        encoding="utf-8",
        errors="replace",
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
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
