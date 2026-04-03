"""Code snippet insertion with simple tab-stop expansion."""

import json
import re
from pathlib import Path

from PyQt6.Qsci import QsciScintilla

from src.core.logging_config import get_logger

log = get_logger("editor.snippets")

_SNIPPETS_FILE = Path(__file__).parent.parent / "resources" / "snippets" / "latex_snippets.json"


class Snippet:
    """A single code snippet with trigger and body."""

    def __init__(self, trigger: str, label: str, body: str) -> None:
        self.trigger = trigger
        self.label = label
        self.body = body

    def expand(self) -> str:
        """Return the body with tab stops stripped for plain insertion."""
        text = self.body
        # Replace ${N:placeholder} with placeholder
        text = re.sub(r'\$\{(\d+):([^}]*)\}', r'\2', text)
        # Remove bare $N
        text = re.sub(r'\$\d+', '', text)
        return text


class SnippetManager:
    """Manages loading and inserting code snippets into a QScintilla editor."""

    def __init__(self) -> None:
        self._snippets: dict[str, Snippet] = {}
        self._load_snippets()

    def _load_snippets(self) -> None:
        try:
            data = json.loads(_SNIPPETS_FILE.read_text(encoding="utf-8"))
            for entry in data.get("snippets", []):
                s = Snippet(
                    trigger=entry["trigger"],
                    label=entry.get("label", entry["trigger"]),
                    body=entry["body"],
                )
                self._snippets[s.trigger] = s
            log.debug("Loaded %d snippets", len(self._snippets))
        except (OSError, json.JSONDecodeError) as e:
            log.error("Failed to load snippets: %s", e)

    def triggers(self) -> list[str]:
        return list(self._snippets.keys())

    def get(self, trigger: str) -> Snippet | None:
        return self._snippets.get(trigger)

    def try_expand(self, editor: QsciScintilla) -> bool:
        """Check if the word before the cursor matches a snippet trigger.

        If so, replace the trigger text with the snippet body and return True.
        """
        line, col = editor.getCursorPosition()
        text_before = editor.text(line)[:col]

        # Find the last word (trigger candidate)
        match = re.search(r'(\w+)$', text_before)
        if not match:
            return False

        trigger = match.group(1)
        snippet = self._snippets.get(trigger)
        if not snippet:
            return False

        # Replace the trigger text with the expanded snippet
        start_col = match.start()
        expanded = snippet.expand()

        editor.setSelection(line, start_col, line, col)
        editor.replaceSelectedText(expanded)

        log.debug("Expanded snippet '%s'", trigger)
        return True
