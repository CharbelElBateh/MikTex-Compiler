import shutil
from pathlib import Path

from src.constants import DEFAULT_MIKTEX_BIN_DIR, SUPPORTED_ENGINES
from src.core.logging_config import get_logger

log = get_logger("utils.path")

# Common MiKTeX install locations on Windows
_MIKTEX_SEARCH_PATHS = [
    DEFAULT_MIKTEX_BIN_DIR,
    Path.home() / "AppData" / "Local" / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64",
    Path("C:/MiKTeX/miktex/bin/x64"),
]


def find_miktex_bin_dir(configured_path: Path | None = None) -> Path | None:
    """Locate the MiKTeX bin directory.

    Checks in order: configured path, known install locations, then PATH.
    Returns None if not found.
    """
    # 1. User-configured path
    if configured_path and _validate_miktex_dir(configured_path):
        return configured_path

    # 2. Known install locations
    for candidate in _MIKTEX_SEARCH_PATHS:
        if _validate_miktex_dir(candidate):
            log.info("Found MiKTeX at %s", candidate)
            return candidate

    # 3. Search PATH
    pdflatex_path = shutil.which("pdflatex")
    if pdflatex_path:
        bin_dir = Path(pdflatex_path).parent
        if _validate_miktex_dir(bin_dir):
            log.info("Found MiKTeX on PATH at %s", bin_dir)
            return bin_dir

    log.warning("MiKTeX installation not found")
    return None


def _validate_miktex_dir(path: Path) -> bool:
    """Check that a directory contains MiKTeX executables."""
    if not path.is_dir():
        return False
    return (path / "pdflatex.exe").is_file()


def get_engine_path(miktex_bin_dir: Path, engine_name: str) -> Path | None:
    """Get the full path to a TeX engine executable."""
    if engine_name not in SUPPORTED_ENGINES:
        return None
    exe_path = miktex_bin_dir / f"{engine_name}.exe"
    return exe_path if exe_path.is_file() else None


def get_available_engines(miktex_bin_dir: Path) -> list[str]:
    """List which TeX engines are available in the given MiKTeX installation."""
    return [
        engine
        for engine in SUPPORTED_ENGINES
        if (miktex_bin_dir / f"{engine}.exe").is_file()
    ]
