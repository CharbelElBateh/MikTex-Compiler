"""Parser for LaTeX .log files.

LaTeX log format is complex: errors and warnings are embedded across multiple
lines, file open/close is tracked via parentheses, and line numbers appear in
different positions depending on the message type.
"""

import os
import re
from pathlib import Path

from src.compiler.error_model import CompilationError
from src.core.logging_config import get_logger

log = get_logger("compiler.log_parser")

# Patterns
_RE_ERROR = re.compile(r"^! (.+)$")
_RE_LINE = re.compile(r"^l\.(\d+)\s*(.*)")
_RE_WARNING = re.compile(
    r"^(?:LaTeX|Package \S+|Class \S+) [Ww]arning: (.+?)(?:\s+on input line (\d+)\.?)?$"
)
_RE_OVERFULL = re.compile(
    r"^(Overfull|Underfull) \\(hbox|vbox).+?(?:at lines? (\d+)(?:--\d+)?|\((\d+)\))?",
    re.IGNORECASE,
)
_RE_PAREN_OPEN = re.compile(r"\(([^()]+\.(?:tex|sty|cls|def|clo|fd|cfg|ltx|dtx))", re.IGNORECASE)


def _resolve(candidate: str, base_dir: Path | None) -> str:
    """Resolve a log file reference to an absolute path when possible.

    LaTeX logs record paths relative to the compile working directory, so
    anchor them to base_dir for the error list to be able to open them.
    """
    p = Path(candidate)
    if base_dir and not p.is_absolute():
        p = base_dir / p
    return os.path.normpath(str(p))


def _track_file_stack(line: str, file_stack: list[str], base_dir: Path | None) -> None:
    """Update the file stack by tracking parentheses that indicate file opens/closes."""
    # Count opens and closes in this line
    depth = 0
    for ch in line:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1

    # Check for file-open patterns
    for m in _RE_PAREN_OPEN.finditer(line):
        candidate = m.group(1).strip()
        if Path(candidate).suffix.lower() in {".tex", ".sty", ".cls", ".def", ".clo", ".fd"}:
            file_stack.append(_resolve(candidate, base_dir))
            return

    # Closing parens
    closes = line.count(")")
    if closes > 0 and len(file_stack) > 1:
        for _ in range(min(closes, len(file_stack) - 1)):
            file_stack.pop()


class LogParser:
    """Parse a LaTeX .log file and return a list of CompilationError."""

    def parse(
        self,
        log_path: Path,
        base_dir: Path | None = None,
        root_file: Path | None = None,
    ) -> list[CompilationError]:
        if not log_path.is_file():
            log.debug("Log file not found: %s", log_path)
            return []

        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            log.warning("Could not read log: %s", e)
            return []

        lines = text.splitlines()
        results: list[CompilationError] = []
        # Attribute errors to the main document until another file opens
        file_stack: list[str] = [str(root_file) if root_file else str(log_path.parent)]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Track file context via parentheses
            _track_file_stack(line, file_stack, base_dir)
            current_file = file_stack[-1] if file_stack else ""

            # ── Errors (start with "! ") ──
            m = _RE_ERROR.match(line)
            if m:
                error_msg = m.group(1)
                raw = [line]
                error_line = -1

                # Look ahead for the l.<n> line (within next 10 lines)
                j = i + 1
                while j < min(i + 10, len(lines)):
                    raw.append(lines[j])
                    lm = _RE_LINE.match(lines[j])
                    if lm:
                        error_line = int(lm.group(1))
                        break
                    j += 1

                results.append(
                    CompilationError(
                        level="error",
                        message=error_msg,
                        file_path=current_file,
                        line=error_line,
                        column=-1,
                        raw_context="\n".join(raw),
                    )
                )
                i = j + 1
                continue

            # ── Warnings (LaTeX Warning: / Package X Warning:) ──
            m = _RE_WARNING.match(line)
            if m:
                # Multi-line warnings: collect continuation lines
                msg_parts = [m.group(1)]
                warn_line = int(m.group(2)) if m.group(2) else -1
                raw = [line]

                # Continuation lines are indented or wrapped
                j = i + 1
                while j < min(i + 6, len(lines)):
                    next_line = lines[j]
                    if next_line.startswith("(") or next_line == "" or _RE_ERROR.match(next_line):
                        break
                    if warn_line == -1:
                        lm = re.search(r"on input line (\d+)", next_line)
                        if lm:
                            warn_line = int(lm.group(1))
                    msg_parts.append(next_line.strip())
                    raw.append(next_line)
                    j += 1

                results.append(
                    CompilationError(
                        level="warning",
                        message=" ".join(p for p in msg_parts if p),
                        file_path=current_file,
                        line=warn_line,
                        column=-1,
                        raw_context="\n".join(raw),
                    )
                )
                i = j
                continue

            # ── Overfull/Underfull boxes ──
            m = _RE_OVERFULL.match(line)
            if m:
                box_line = int(m.group(3) or m.group(4) or -1)
                results.append(
                    CompilationError(
                        level="badbox",
                        message=line.strip(),
                        file_path=current_file,
                        line=box_line,
                        column=-1,
                        raw_context=line,
                    )
                )

            i += 1

        log.debug(
            "Log parsed: %d errors, %d warnings, %d badboxes",
            sum(1 for e in results if e.level == "error"),
            sum(1 for e in results if e.level == "warning"),
            sum(1 for e in results if e.level == "badbox"),
        )
        return results
