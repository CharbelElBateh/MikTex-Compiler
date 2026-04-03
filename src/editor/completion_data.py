"""Loads and provides LaTeX completion data from JSON resources."""

import json
from pathlib import Path

from src.core.logging_config import get_logger

log = get_logger("editor.completion_data")

_COMMANDS_FILE = Path(__file__).parent.parent / "resources" / "completions" / "latex_commands.json"

_data: dict | None = None


def _load() -> dict:
    global _data
    if _data is not None:
        return _data
    try:
        _data = json.loads(_COMMANDS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.error("Failed to load completion data: %s", e)
        _data = {"commands": [], "environments": [], "document_classes": [], "common_packages": []}
    return _data


def command_labels() -> list[str]:
    """Return list of all LaTeX command labels (e.g. '\\section')."""
    return [c["label"] for c in _load().get("commands", [])]


def command_details() -> dict[str, str]:
    """Return {label: detail} for all commands."""
    return {c["label"]: c.get("detail", "") for c in _load().get("commands", [])}


def environment_names() -> list[str]:
    """Return list of environment names."""
    return [e["label"] for e in _load().get("environments", [])]


def environment_details() -> dict[str, str]:
    """Return {name: detail} for all environments."""
    return {e["label"]: e.get("detail", "") for e in _load().get("environments", [])}


def document_classes() -> list[str]:
    return _load().get("document_classes", [])


def common_packages() -> list[str]:
    return _load().get("common_packages", [])
