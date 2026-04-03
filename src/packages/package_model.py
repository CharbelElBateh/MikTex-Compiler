"""Data model for MiKTeX packages."""

from dataclasses import dataclass, field


@dataclass
class PackageInfo:
    """Represents a MiKTeX package."""

    name: str
    title: str = ""
    description: str = ""
    installed: bool = False
    version: str = ""
    size_installed: int = 0  # bytes
    size_archive: int = 0  # bytes
    files: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)

    @property
    def size_display(self) -> str:
        """Human-readable installed size."""
        if self.size_installed < 1024:
            return f"{self.size_installed} B"
        elif self.size_installed < 1024 * 1024:
            return f"{self.size_installed / 1024:.1f} KB"
        else:
            return f"{self.size_installed / (1024 * 1024):.1f} MB"
