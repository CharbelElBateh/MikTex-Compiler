"""LaTeX \\begin/\\end environment matching and navigation."""

import re

from PyQt6.Qsci import QsciScintilla

from src.core.logging_config import get_logger

log = get_logger("editor.bracket_matcher")

_BEGIN_RE = re.compile(r'\\begin\{([^}]+)\}')
_END_RE = re.compile(r'\\end\{([^}]+)\}')


def find_matching_environment(editor: QsciScintilla) -> tuple[int, int] | None:
    """Find the matching \\begin/\\end for the current cursor position.

    Returns (line, col) of the match, or None.
    """
    line, col = editor.getCursorPosition()
    current_line_text = editor.text(line)

    # Check if cursor is on a \\begin
    for m in _BEGIN_RE.finditer(current_line_text):
        if m.start() <= col <= m.end():
            env_name = m.group(1)
            return _find_end(editor, env_name, line)

    # Check if cursor is on an \\end
    for m in _END_RE.finditer(current_line_text):
        if m.start() <= col <= m.end():
            env_name = m.group(1)
            return _find_begin(editor, env_name, line)

    return None


def _find_end(editor: QsciScintilla, env_name: str, start_line: int) -> tuple[int, int] | None:
    """Search forward for matching \\end{env_name}."""
    depth = 0
    total_lines = editor.lines()

    for i in range(start_line, total_lines):
        text = editor.text(i)
        for m in _BEGIN_RE.finditer(text):
            if m.group(1) == env_name:
                if i == start_line and m.start() < editor.getCursorPosition()[1]:
                    continue
                depth += 1
        for m in _END_RE.finditer(text):
            if m.group(1) == env_name:
                depth -= 1
                if depth == 0:
                    return (i, m.start())

    return None


def _find_begin(editor: QsciScintilla, env_name: str, end_line: int) -> tuple[int, int] | None:
    """Search backward for matching \\begin{env_name}."""
    depth = 0

    for i in range(end_line, -1, -1):
        text = editor.text(i)
        for m in reversed(list(_END_RE.finditer(text))):
            if m.group(1) == env_name:
                if i == end_line:
                    continue
                depth += 1
        for m in reversed(list(_BEGIN_RE.finditer(text))):
            if m.group(1) == env_name:
                depth -= 1
                if depth == 0:
                    return (i, m.start())

    return None


def goto_matching_environment(editor: QsciScintilla) -> bool:
    """Jump cursor to the matching \\begin/\\end. Returns True if successful."""
    result = find_matching_environment(editor)
    if result:
        editor.setCursorPosition(result[0], result[1])
        return True
    return False
