from dataclasses import dataclass, field


@dataclass
class CompilationError:
    """Structured representation of a LaTeX log error, warning, or info."""

    level: str        # "error" | "warning" | "badbox" | "info"
    message: str
    file_path: str    # resolved absolute path, or "" if unknown
    line: int         # 1-based; -1 if unknown
    column: int       # 1-based; -1 if unknown
    raw_context: str  # snippet of raw log text for this entry

    def __str__(self) -> str:
        loc = f"{self.file_path}:{self.line}" if self.line > 0 else self.file_path or "?"
        return f"[{self.level.upper()}] {loc}: {self.message}"
