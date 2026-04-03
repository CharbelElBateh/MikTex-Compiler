"""LaTeX autocompletion for QScintilla editor."""

from PyQt6.Qsci import QsciAPIs, QsciScintilla

from src.core.logging_config import get_logger
from src.editor.completion_data import (
    command_details,
    command_labels,
    common_packages,
    document_classes,
    environment_names,
)

log = get_logger("editor.completer")


class LaTeXCompleter:
    """Provides LaTeX command and environment autocompletion.

    Attaches to a QScintilla editor's lexer and populates the API
    list with LaTeX commands, environments, packages, and classes.
    """

    def __init__(self, editor: QsciScintilla) -> None:
        self._editor = editor
        self._api: QsciAPIs | None = None
        self._setup()

    def _setup(self) -> None:
        lexer = self._editor.lexer()
        if not lexer:
            log.warning("Cannot set up completer: no lexer attached")
            return

        self._api = QsciAPIs(lexer)

        # Add all commands (strip leading backslash for QScintilla API format)
        details = command_details()
        for label in command_labels():
            desc = details.get(label, "")
            if desc:
                self._api.add(f"{label} — {desc}")
            else:
                self._api.add(label)

        # Add environments (as \begin{env})
        for env in environment_names():
            self._api.add(f"\\begin{{{env}}}")

        # Add document classes
        for cls in document_classes():
            self._api.add(f"\\documentclass{{{cls}}}")

        # Add packages
        for pkg in common_packages():
            self._api.add(f"\\usepackage{{{pkg}}}")

        self._api.prepare()

        # Configure autocompletion behavior
        self._editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)
        self._editor.setAutoCompletionThreshold(1)
        self._editor.setAutoCompletionCaseSensitivity(False)
        self._editor.setAutoCompletionReplaceWord(False)
        self._editor.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

        log.debug("LaTeX completer configured with %d entries", len(command_labels()))

    def refresh(self) -> None:
        """Rebuild the API list (e.g. after adding custom commands)."""
        self._setup()
