# MIKTEX-Compiler

A Python-based LaTeX IDE built on top of MiKTeX, featuring a QScintilla editor, side-by-side PDF preview with SyncTeX, and integrated MiKTeX package management.

## Features

- **Multi-engine compilation** — pdflatex, xelatex, lualatex with multi-pass support (BibTeX/Biber, pre/post hooks)
- **LaTeX editor** — syntax highlighting, autocompletion (~LaTeX commands), snippet manager, bracket matching, find/replace
- **PDF viewer** — PyMuPDF-rendered side-by-side preview with zoom, page navigation, and SyncTeX forward/reverse sync
- **Package manager** — search, install, and uninstall MiKTeX packages via `mpm.exe` without leaving the IDE
- **Project management** — TOML-persisted project config (`.miktex-project/project.toml`), session restore, recent projects
- **Auto-compile** — file watcher triggers recompilation on save (1 s debounce)
- **Error panel** — structured error/warning list parsed from LaTeX logs, click-to-navigate
- **Dark and light themes**
- **Plugin system** — extend the IDE via the plugin API (`src/core/plugin_api.py`)

## Requirements

- **Windows** (MiKTeX is Windows-only in the default configuration)
- **MiKTeX 25.x** installed at `C:\Program Files\MiKTeX\miktex\bin\x64\`
- **Python ≥ 3.12**

## Installation

```bash
git clone https://github.com/<your-username>/MIKTEX-Compiler.git
cd MIKTEX-Compiler

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

### Development dependencies

```bash
pip install -r requirements-dev.txt
```

## Usage

```bash
python main.py                  # Launch IDE
python main.py --verbose        # Verbose logging
python main.py path/to/file.tex # Open a specific file
python main.py path/to/project  # Open a project directory
```

Settings are stored in `%APPDATA%\MIKTEX-Compiler\settings.ini`.
Logs are written to `%APPDATA%\MIKTEX-Compiler\logs\`.

## Project Structure

```
MIKTEX-Compiler/
├── main.py                   # Entry point
├── src/
│   ├── app.py                # Application bootstrap
│   ├── constants.py          # App-wide constants
│   ├── core/                 # EventBus, Project, Settings, Session, Plugin system
│   ├── compiler/             # CompilationController, pipeline, log parser, SyncTeX
│   ├── editor/               # QScintilla editor, LaTeX lexer, completer, snippets
│   ├── viewer/               # PyMuPDF PDF viewer, SyncTeX overlay
│   ├── packages/             # mpm.exe bridge, package worker
│   ├── themes/               # Dark/light theme definitions
│   ├── ui/                   # MainWindow, TabManager, FileTree, dialogs
│   └── utils/                # Path and process utilities
├── tests/
│   ├── test_compiler/
│   ├── test_core/
│   ├── test_editor/
│   ├── test_viewer/
│   ├── test_packages/
│   └── test_ui/
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

### Architecture

The application follows a **layered MVC** pattern with an **EventBus** (`src/core/event_bus.py`) as the primary communication channel between modules — cross-module calls go through signal emissions rather than direct imports.

**Startup flow**: `main.py` → `Application.run()` → detect MiKTeX → load settings/theme → init project/session/compiler managers → create `MainWindow` → load plugins → restore session or show welcome dialog.

## Development

```bash
# Run tests
pytest                            # All tests
pytest tests/test_core/           # Specific module
pytest -m integration             # Integration tests (require MiKTeX)
pytest --cov --cov-report=html    # Coverage report

# Code quality
black src/ tests/                 # Format (line length: 100)
ruff check src/ tests/            # Lint
mypy src/                         # Type check (strict)
```

> Integration tests marked `@pytest.mark.integration` require a live MiKTeX installation.

## Dependencies

| Package | Purpose |
|---|---|
| PyQt6 ≥ 6.7 | GUI framework |
| PyQt6-QScintilla ≥ 2.14 | Code editor widget |
| PyMuPDF ≥ 1.24 | PDF rendering |
| watchdog ≥ 4.0 | File system monitoring |
| Pygments ≥ 2.18 | Syntax highlighting support |
| tomli-w ≥ 1.0 | TOML project config serialization |

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
