"""SyncTeX bridge: forward and reverse sync between source and PDF.

Forward sync: source (file, line, col) → PDF (page, x, y)
Reverse sync: PDF (page, x, y) → source (file, line, col)

Uses synctex.exe from the MiKTeX installation.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from src.core.logging_config import get_logger
from src.utils.process_utils import run_miktex_command

log = get_logger("compiler.synctex")


@dataclass
class ForwardSyncResult:
    """A region in the PDF corresponding to a source location."""
    page: int       # 1-based
    x: float        # points from left (72 dpi)
    y: float        # points from top (72 dpi)
    width: float
    height: float


@dataclass
class ReverseSyncResult:
    """A source location corresponding to a PDF position."""
    file_path: str
    line: int       # 1-based
    column: int     # 1-based


class SyncTeXBridge:
    """Wraps synctex.exe for bi-directional source↔PDF navigation."""

    def __init__(self, miktex_bin_dir: Path) -> None:
        self._bin_dir = miktex_bin_dir
        self._synctex_exe = miktex_bin_dir / "synctex.exe"

    @property
    def available(self) -> bool:
        return self._synctex_exe.is_file()

    def forward_sync(
        self, tex_file: Path, line: int, col: int, pdf_file: Path
    ) -> list[ForwardSyncResult]:
        """Find PDF regions corresponding to (tex_file, line, col)."""
        if not self.available:
            log.warning("synctex.exe not found")
            return []

        # synctex view -i line:col:file -o pdf
        result = run_miktex_command(
            [
                str(self._synctex_exe),
                "view",
                "-i", f"{line}:{col}:{tex_file}",
                "-o", str(pdf_file),
            ],
            self._bin_dir,
            cwd=tex_file.parent,
            timeout=10,
        )

        if result.returncode != 0:
            log.debug("synctex view failed (rc=%d): %s", result.returncode, result.stdout[:200])
            return []

        return self._parse_view_output(result.stdout)

    def reverse_sync(
        self, pdf_file: Path, page: int, x: float, y: float
    ) -> ReverseSyncResult | None:
        """Find the source location corresponding to (page, x, y) in the PDF."""
        if not self.available:
            return None

        # synctex edit -o page:x:y:file
        result = run_miktex_command(
            [
                str(self._synctex_exe),
                "edit",
                "-o", f"{page}:{x:.2f}:{y:.2f}:{pdf_file}",
            ],
            self._bin_dir,
            cwd=pdf_file.parent,
            timeout=10,
        )

        if result.returncode != 0:
            log.debug("synctex edit failed (rc=%d)", result.returncode)
            return None

        return self._parse_edit_output(result.stdout)

    # ── Output parsers ──

    def _parse_view_output(self, text: str) -> list[ForwardSyncResult]:
        """Parse synctex view output into ForwardSyncResult objects."""
        results = []
        current: dict = {}

        for line in text.splitlines():
            line = line.strip()
            if line.startswith("Page:"):
                if current:
                    r = self._dict_to_forward(current)
                    if r:
                        results.append(r)
                current = {"page": int(line.split(":", 1)[1])}
            elif ":" in line:
                key, _, val = line.partition(":")
                current[key.strip().lower()] = val.strip()

        if current:
            r = self._dict_to_forward(current)
            if r:
                results.append(r)

        return results

    def _dict_to_forward(self, d: dict) -> ForwardSyncResult | None:
        try:
            return ForwardSyncResult(
                page=int(d.get("page", 0)),
                x=float(d.get("x", 0)),
                y=float(d.get("y", 0)),
                width=float(d.get("w", 10)),
                height=float(d.get("h", 10)),
            )
        except (ValueError, KeyError):
            return None

    def _parse_edit_output(self, text: str) -> ReverseSyncResult | None:
        """Parse synctex edit output into a ReverseSyncResult."""
        data: dict = {}
        for line in text.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                data[key.strip().lower()] = val.strip()

        try:
            return ReverseSyncResult(
                file_path=data.get("input", ""),
                line=int(data.get("line", -1)),
                column=int(data.get("column", 1)),
            )
        except (ValueError, KeyError):
            return None
