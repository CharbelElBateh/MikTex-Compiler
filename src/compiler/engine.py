from dataclasses import dataclass, field
from pathlib import Path

from src.constants import SUPPORTED_ENGINES
from src.core.logging_config import get_logger

log = get_logger("compiler.engine")


@dataclass
class Engine:
    name: str           # "pdflatex", "xelatex", "lualatex"
    executable: Path
    display_name: str
    default_args: list[str] = field(default_factory=list)

    @property
    def supports_synctex(self) -> bool:
        return True  # All three engines support -synctex=1


class EngineRegistry:
    """Discovers and stores available TeX engines from a MiKTeX installation."""

    _DEFAULT_ARGS = [
        "-interaction=nonstopmode",
        "-synctex=1",
    ]

    _DISPLAY_NAMES = {
        "pdflatex": "pdfLaTeX",
        "xelatex": "XeLaTeX",
        "lualatex": "LuaLaTeX",
    }

    def __init__(self, miktex_bin_dir: Path) -> None:
        self._engines: dict[str, Engine] = {}
        self._detect(miktex_bin_dir)

    def _detect(self, bin_dir: Path) -> None:
        for name in SUPPORTED_ENGINES:
            exe = bin_dir / f"{name}.exe"
            if exe.is_file():
                self._engines[name] = Engine(
                    name=name,
                    executable=exe,
                    display_name=self._DISPLAY_NAMES.get(name, name),
                    default_args=list(self._DEFAULT_ARGS),
                )
                log.debug("Detected engine: %s at %s", name, exe)
            else:
                log.debug("Engine not found: %s", exe)

    def get(self, name: str) -> Engine | None:
        return self._engines.get(name)

    def available(self) -> list[Engine]:
        return list(self._engines.values())

    def available_names(self) -> list[str]:
        return list(self._engines.keys())
