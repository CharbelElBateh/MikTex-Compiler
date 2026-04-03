from pathlib import Path

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QKeyEvent

from src.constants import DEFAULT_FONT_FAMILY, DEFAULT_FONT_FAMILY_FALLBACK, DEFAULT_FONT_SIZE
from src.core.event_bus import event_bus
from src.core.logging_config import get_logger
from src.editor.completer import LaTeXCompleter
from src.editor.lexer_latex import LaTeXLexer
from src.editor.snippet_manager import SnippetManager

log = get_logger("editor.latex_editor")

# Shared snippet manager instance
_snippet_manager = SnippetManager()

# Delay (ms) between last keystroke and auto-save
_AUTOSAVE_DELAY_MS = 2_000


def _resolve_font(family: str, size: int) -> QFont:
    font = QFont(family, size)
    if not font.exactMatch():
        font = QFont(DEFAULT_FONT_FAMILY_FALLBACK, size)
    font.setFixedPitch(True)
    return font


class LaTeXEditor(QsciScintilla):
    """QScintilla-based editor configured for LaTeX documents."""

    def __init__(
        self,
        file_path: str,
        colors: dict[str, str],
        font_family: str = DEFAULT_FONT_FAMILY,
        font_size: int = DEFAULT_FONT_SIZE,
        tab_width: int = 4,
        word_wrap: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._file_path = file_path
        self._is_modified = False
        self._encoding = "utf-8"

        font = _resolve_font(font_family, font_size)
        self._setup_lexer(colors, font)
        self._setup_editor(font, tab_width, colors)
        if word_wrap:
            self.set_word_wrap(True)
        self._connect_signals()

        # Autocompletion
        self._completer = LaTeXCompleter(self)

        # Auto-save: fires 2 s after the last text change
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(_AUTOSAVE_DELAY_MS)
        self._autosave_timer.timeout.connect(self._autosave)

        log.debug("Editor created for %s", file_path)

    def _setup_lexer(self, colors: dict[str, str], font: QFont) -> None:
        self._lexer = LaTeXLexer(colors, font, self)
        self.setLexer(self._lexer)

    def _setup_editor(self, font: QFont, tab_width: int, colors: dict[str, str]) -> None:
        # Font
        self.setFont(font)

        # Indentation
        self.setTabWidth(tab_width)
        self.setIndentationsUseTabs(False)
        self.setAutoIndent(True)
        self.setIndentationGuides(True)

        # Line numbers margin
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsForegroundColor(QColor(colors.get("margin_fg", "#858585")))
        self.setMarginsBackgroundColor(QColor(colors.get("margin_bg", "#1e1e1e")))
        self.setMarginsFont(font)

        # Folding margin
        self.setMarginType(2, QsciScintilla.MarginType.SymbolMargin)
        self.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle, 2)
        self.setFoldMarginColors(
            QColor(colors.get("fold_margin_bg", "#1e1e1e")),
            QColor(colors.get("fold_margin_bg", "#1e1e1e")),
        )

        # Error/warning marker margin (will be populated by compiler results)
        self.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(1, 16)

        # Caret and selection
        self.setCaretForegroundColor(QColor(colors.get("caret", "#d4d4d4")))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor(colors.get("line_highlight", "#2a2d2e")))

        # Selection
        self.setSelectionBackgroundColor(QColor(colors.get("selection_bg", "#264f78")))
        self.resetSelectionForegroundColor()

        # Brace matching
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(QColor(colors.get("selection_bg", "#264f78")))

        # Scrollbar
        self.setScrollWidth(1)
        self.setScrollWidthTracking(True)

        # Edge line at column 100 (subtle visual guide)
        self.setEdgeMode(QsciScintilla.EdgeMode.EdgeLine)
        self.setEdgeColumn(100)
        self.setEdgeColor(QColor(colors.get("margin_bg", "#333333")))

        # EOL mode
        self.setEolMode(QsciScintilla.EolMode.EolWindows)

        # Enable UTF-8
        self.setUtf8(True)

    def _connect_signals(self) -> None:
        self.modificationChanged.connect(self._on_modification_changed)
        self.cursorPositionChanged.connect(self._on_cursor_changed)
        self.textChanged.connect(self._on_text_changed)

    def _on_modification_changed(self, modified: bool) -> None:
        if modified != self._is_modified:
            self._is_modified = modified
            event_bus.file_modified.emit(self._file_path, modified)

    def _on_cursor_changed(self, line: int, col: int) -> None:
        # QScintilla is 0-based; emit 1-based for UI display
        event_bus.cursor_moved.emit(self._file_path, line + 1, col + 1)

    def _on_text_changed(self) -> None:
        # Restart auto-save countdown on every text change
        self._autosave_timer.start()

    def _autosave(self) -> None:
        if self._is_modified:
            self.save_file()
            log.debug("Auto-saved: %s", self._file_path)

    # ── File I/O ──

    def load_file(self) -> bool:
        """Load the file from disk into the editor."""
        try:
            path = Path(self._file_path)
            text = path.read_text(encoding=self._encoding, errors="replace")
            self.setText(text)
            self.setModified(False)
            self._is_modified = False
            log.debug("Loaded %s", self._file_path)
            return True
        except OSError as e:
            log.error("Failed to load %s: %s", self._file_path, e)
            return False

    def save_file(self) -> bool:
        """Save the editor contents to disk."""
        try:
            path = Path(self._file_path)
            path.write_text(self.text(), encoding=self._encoding)
            self.setModified(False)
            self._is_modified = False
            event_bus.file_saved.emit(self._file_path)
            log.debug("Saved %s", self._file_path)
            return True
        except OSError as e:
            log.error("Failed to save %s: %s", self._file_path, e)
            return False

    def save_as(self, new_path: str) -> bool:
        """Save to a new path and update the file path."""
        self._file_path = new_path
        return self.save_file()

    # ── Properties ──

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def is_modified(self) -> bool:
        return self._is_modified

    # ── Word wrap ──

    def set_word_wrap(self, enabled: bool) -> None:
        """Enable or disable word-wrap mode."""
        if enabled:
            self.setWrapMode(QsciScintilla.WrapMode.WrapWord)
            self.setWrapIndentMode(QsciScintilla.WrapIndentMode.WrapIndentSame)
        else:
            self.setWrapMode(QsciScintilla.WrapMode.WrapNone)

    # ── Theme update ──

    def apply_colors(self, colors: dict[str, str], font_family: str, font_size: int) -> None:
        font = _resolve_font(font_family, font_size)
        self._lexer.update_colors(colors)
        self._setup_editor(font, self.tabWidth(), colors)

    # ── Keyboard overrides ──

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Ctrl+S → save
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_S:
            self.save_file()
            return
        # Tab → try snippet expansion first
        if event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if _snippet_manager.try_expand(self):
                return
        super().keyPressEvent(event)
