from pathlib import Path

APP_NAME = "MIKTEX-Compiler"
APP_VERSION = "0.1.0"
ORG_NAME = "MIKTEXCompiler"

# Default MiKTeX paths (Windows)
DEFAULT_MIKTEX_BIN_DIR = Path("C:/Program Files/MiKTeX/miktex/bin/x64")
MIKTEX_USER_CONFIG_DIR = Path.home() / "AppData" / "Local" / "MiKTeX"

# Application data directory
APP_DATA_DIR = Path.home() / "AppData" / "Roaming" / APP_NAME
SETTINGS_FILE = APP_DATA_DIR / "settings.ini"
LOG_DIR = APP_DATA_DIR / "logs"

# Project config
PROJECT_CONFIG_DIR = ".miktex-project"
PROJECT_CONFIG_FILE = "project.toml"

# Editor defaults
DEFAULT_FONT_FAMILY = "Cascadia Code"
DEFAULT_FONT_FAMILY_FALLBACK = "Consolas"
DEFAULT_FONT_SIZE = 12
DEFAULT_TAB_WIDTH = 4

# Compilation
DEFAULT_ENGINE = "pdflatex"
DEFAULT_OUTPUT_DIR = "build"
SUPPORTED_ENGINES = ["pdflatex", "xelatex", "lualatex"]

# Viewer
DEFAULT_ZOOM = 100
DEFAULT_RENDER_DPI = 150
PAGE_CACHE_SIZE = 20

# File types
TEX_EXTENSIONS = {".tex", ".sty", ".cls", ".bib", ".bst", ".dtx", ".ins"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".eps", ".svg"}
ALL_PROJECT_EXTENSIONS = TEX_EXTENSIONS | IMAGE_EXTENSIONS | {".cfg", ".def", ".fd"}

# Auto-compile debounce delay (ms)
AUTO_COMPILE_DELAY_MS = 1000
