"""Find and replace engine for QScintilla editors."""

import re

from PyQt6.Qsci import QsciScintilla

from src.core.logging_config import get_logger

log = get_logger("editor.search_replace")


class SearchEngine:
    """Stateful find/replace engine wrapping QScintilla's search API."""

    def __init__(self) -> None:
        self._last_query: str = ""
        self._case_sensitive: bool = False
        self._whole_word: bool = False
        self._use_regex: bool = False
        self._wrap_around: bool = True

    def find_next(
        self,
        editor: QsciScintilla,
        query: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        use_regex: bool = False,
        wrap: bool = True,
        forward: bool = True,
    ) -> bool:
        """Find next occurrence. Returns True if found."""
        self._last_query = query
        self._case_sensitive = case_sensitive
        self._whole_word = whole_word
        self._use_regex = use_regex
        self._wrap_around = wrap

        if not query:
            return False

        return editor.findFirst(
            query,
            use_regex,     # isRegExp
            case_sensitive,  # isCaseSensitive
            whole_word,     # isWholeWord
            wrap,           # isWrap
            forward,        # isForward
        )

    def find_previous(self, editor: QsciScintilla) -> bool:
        """Find previous occurrence using last search parameters."""
        if not self._last_query:
            return False
        return editor.findFirst(
            self._last_query,
            self._use_regex,
            self._case_sensitive,
            self._whole_word,
            self._wrap_around,
            False,  # forward=False
        )

    def find_all(self, editor: QsciScintilla, query: str, **kwargs) -> int:
        """Count all occurrences of the query. Returns count."""
        if not query:
            return 0

        text = editor.text()
        flags = 0 if kwargs.get("case_sensitive", False) else re.IGNORECASE
        if kwargs.get("use_regex", False):
            try:
                pattern = re.compile(query, flags)
            except re.error:
                return 0
        else:
            escaped = re.escape(query)
            if kwargs.get("whole_word", False):
                escaped = rf"\b{escaped}\b"
            pattern = re.compile(escaped, flags)

        return len(pattern.findall(text))

    def replace_current(self, editor: QsciScintilla, replacement: str) -> bool:
        """Replace the current selection if it matches the last search."""
        if not editor.hasSelectedText():
            return False
        editor.replaceSelectedText(replacement)
        return True

    def replace_and_find(
        self,
        editor: QsciScintilla,
        query: str,
        replacement: str,
        **kwargs,
    ) -> bool:
        """Replace current match and find next."""
        if editor.hasSelectedText():
            editor.replaceSelectedText(replacement)
        return self.find_next(editor, query, **kwargs)

    def replace_all(
        self,
        editor: QsciScintilla,
        query: str,
        replacement: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        use_regex: bool = False,
    ) -> int:
        """Replace all occurrences. Returns count of replacements."""
        if not query:
            return 0

        text = editor.text()
        flags = 0 if case_sensitive else re.IGNORECASE

        if use_regex:
            try:
                pattern = re.compile(query, flags)
            except re.error:
                return 0
        else:
            escaped = re.escape(query)
            if whole_word:
                escaped = rf"\b{escaped}\b"
            pattern = re.compile(escaped, flags)

        new_text, count = pattern.subn(replacement, text)
        if count > 0:
            # Preserve cursor position as best we can
            line, col = editor.getCursorPosition()
            editor.setText(new_text)
            max_line = editor.lines() - 1
            editor.setCursorPosition(min(line, max_line), col)
            log.debug("Replaced %d occurrences", count)
        return count
