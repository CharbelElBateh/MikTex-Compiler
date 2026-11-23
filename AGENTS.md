# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Running the Application

```bash
python main.py                        # Normal mode
python main.py --verbose              # Verbose logging
python main.py <file_or_project>      # Open specific file/project
```

## Development Commands

```bash
# Tests
pytest                                # Run all tests
pytest tests/test_core/               # Run a specific module's tests
pytest -m integration                 # Integration tests (require MiKTeX installed)
pytest --cov --cov-report=html        # Coverage report

# Code quality
black src/ tests/                     # Format code (line length: 100)
ruff check src/ tests/                # Lint (rules: E, F, I, W)
mypy src/                             # Type check (strict mode)
```

## Architecture Overview

**Pattern**: Layered MVC with a Qt signal-based EventBus for decoupled cross-module communication.

**Startup flow** (`main.py` → `src/app.py`): detect MiKTeX → load settings/theme → init project/session managers → init compiler → create `MainWindow` → load plugins → restore session or show welcome dialog.

**Module responsibilities**:
- `src/core/` — Foundation: `EventBus` (all inter-module signals), `Project`/`ProjectManager` (TOML-persisted project config), `SettingsManager` (INI backend), `SessionManager` (recent projects, open files), plugin system
- `src/compiler/` — `CompilationController` drives the `CompilationPipeline` (multi-pass pdflatex/xelatex/lualatex, bibtex/biber, pre/post hooks); `CompilerWorker` runs it on a QThread; `LogParser` extracts errors from LaTeX logs; `SyncTexBridge` handles forward/reverse sync
- `src/editor/` — QScintilla-based editor with a custom LaTeX lexer, autocompletion from `src/resources/completions/latex_commands.json`, snippet manager, bracket matching
- `src/viewer/` — PyMuPDF-based PDF viewer with page caching, zoom, navigation, and SyncTeX overlay
- `src/packages/` — Wraps `mpm.exe` (MiKTeX Package Manager) for package search/install/uninstall via a QThread worker
- `src/ui/` — All PyQt6 widgets: `MainWindow`, `TabManager`, `FileTree`, `OutputPanel`, `ErrorListWidget`, dialogs

**EventBus** (`src/core/event_bus.py`) is the primary communication channel between modules — prefer emitting signals over direct cross-module calls.

**Project config** lives in `.miktex-project/project.toml` within the project root. Application settings live in `%APPDATA%\MIKTEX-Compiler\settings.ini`.

## Key External Dependencies

- **PyQt6 + QScintilla** — GUI and editor widget
- **PyMuPDF** — PDF rendering
- **watchdog** — File system monitoring for auto-compile
- **MiKTeX** (`C:/Program Files/MiKTeX/miktex/bin/x64/`) — LaTeX engines (`pdflatex`, `xelatex`, `lualatex`), `mpm.exe`, `synctex.exe`

## Integration Tests

Tests marked `@pytest.mark.integration` require MiKTeX to be installed. Run them only in environments with MiKTeX available.

## Exception Hierarchy

All custom exceptions inherit from `MiktexCompilerError` (defined in `src/core/exceptions.py`): `MiKTeXNotFoundError`, `CompilationError`, `ProjectError`, `ProjectNotFoundError`, `SettingsError`, `PackageOperationError`, `PluginError`.