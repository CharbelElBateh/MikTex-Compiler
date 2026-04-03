DARK_THEME_QSS = """
/* ── Base ── */
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── Menu Bar ── */
QMenuBar {
    background-color: #2c2c2e;
    color: #cccccc;
    border-bottom: 1px solid #3a3a3d;
    padding: 1px 0;
    font-size: 13px;
}

QMenuBar::item {
    padding: 5px 12px;
    border-radius: 0;
}

QMenuBar::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QMenu {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #454545;
    border-radius: 4px;
    padding: 4px 0;
}

QMenu::item {
    padding: 6px 32px 6px 20px;
    border-radius: 0;
}

QMenu::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QMenu::item:disabled {
    color: #666666;
}

QMenu::separator {
    height: 1px;
    background-color: #3a3a3d;
    margin: 4px 12px;
}

QMenu::icon {
    padding-left: 8px;
}

/* ── Toolbar ── */
QToolBar {
    background-color: #2c2c2e;
    border-bottom: 1px solid #3a3a3d;
    spacing: 2px;
    padding: 4px 8px;
    min-height: 38px;
}

QToolBar::separator {
    width: 1px;
    background-color: #454545;
    margin: 6px 5px;
}

QToolButton {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 11px;
    font-size: 12px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: rgba(255, 255, 255, 0.09);
    border: 1px solid rgba(255, 255, 255, 0.07);
}

QToolButton:pressed {
    background-color: rgba(255, 255, 255, 0.14);
}

QToolButton:checked {
    background-color: rgba(0, 122, 204, 0.25);
    border: 1px solid rgba(0, 122, 204, 0.4);
    color: #4fc3f7;
}

/* Compile button — primary action */
QToolButton[compile_btn="true"] {
    background-color: #16825d;
    color: #ffffff;
    border: 1px solid #1a9969;
    border-radius: 4px;
    padding: 4px 13px;
    font-weight: 600;
}

QToolButton[compile_btn="true"]:hover {
    background-color: #1a9969;
    border-color: #20b07b;
}

QToolButton[compile_btn="true"]:pressed {
    background-color: #116648;
}

/* Stop button — destructive action */
QToolButton[stop_btn="true"] {
    color: #e07070;
}

QToolButton[stop_btn="true"]:hover {
    background-color: rgba(224, 112, 112, 0.12);
    border: 1px solid rgba(224, 112, 112, 0.28);
    color: #f48771;
}

QToolButton[stop_btn="true"]:pressed {
    background-color: rgba(224, 112, 112, 0.22);
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    border: none;
    font-size: 12px;
    min-height: 24px;
}

QStatusBar::item {
    border: none;
}

QStatusBar QLabel {
    color: #ffffff;
    padding: 0 10px;
    font-size: 12px;
    background-color: transparent;
}

/* ── Tabs ── */
QTabWidget::pane {
    border: none;
    border-top: 1px solid #3a3a3d;
    background-color: #1e1e1e;
}

QTabBar {
    background-color: #252526;
    border-bottom: 1px solid #3a3a3d;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #8a8a8a;
    border: none;
    border-right: 1px solid #252526;
    padding: 7px 16px 7px 16px;
    min-width: 80px;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
    border-top: 2px solid #007acc;
    padding-top: 5px;
    border-right: 1px solid #3a3a3d;
}

QTabBar::tab:hover:!selected {
    background-color: #323232;
    color: #d0d0d0;
}

QTabBar::close-button {
    subcontrol-position: right;
    padding: 2px 1px;
    margin-left: 4px;
    border-radius: 3px;
    width: 14px;
    height: 14px;
}

QTabBar::close-button:hover {
    background-color: rgba(255, 255, 255, 0.16);
}

/* ── File Tree Header ── */
QLabel#file_tree_header {
    background-color: #252526;
    color: #aaaaaa;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding-left: 14px;
    border-bottom: 1px solid #3a3a3d;
}

/* ── Tree View (File Tree) ── */
QTreeView {
    background-color: #252526;
    color: #cccccc;
    border: none;
    outline: none;
    font-size: 13px;
}

QTreeView::item {
    padding: 3px 4px;
    border-radius: 0;
}

QTreeView::item:hover {
    background-color: #2a2d2e;
}

QTreeView::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QTreeView::branch {
    background-color: #252526;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    color: #888;
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
    color: #888;
}

/* ── Splitters ── */
QSplitter::handle {
    background-color: #3a3a3d;
}

QSplitter::handle:hover {
    background-color: #007acc;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

/* ── Text Areas ── */
QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: none;
    selection-background-color: #264f78;
    font-family: "Cascadia Code", "Consolas", monospace;
}

/* ── Scroll Bars ── */
QScrollBar:vertical {
    background-color: transparent;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: rgba(121, 121, 121, 0.35);
    min-height: 24px;
    border-radius: 3px;
    margin: 2px 2px 2px 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(160, 160, 160, 0.65);
}

QScrollBar::handle:vertical:pressed {
    background-color: rgba(180, 180, 180, 0.75);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: rgba(121, 121, 121, 0.35);
    min-width: 24px;
    border-radius: 3px;
    margin: 3px 2px 2px 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(160, 160, 160, 0.65);
}

QScrollBar::handle:horizontal:pressed {
    background-color: rgba(180, 180, 180, 0.75);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar::add-page, QScrollBar::sub-page {
    background: none;
}

/* ── Labels ── */
QLabel {
    background-color: transparent;
}

/* ── Buttons ── */
QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: none;
    padding: 6px 18px;
    border-radius: 4px;
    font-size: 13px;
    min-height: 26px;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #094771;
}

QPushButton:disabled {
    background-color: #3a3a3d;
    color: #666666;
}

QPushButton:flat, QPushButton[flat="true"] {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid #454545;
}

QPushButton:flat:hover, QPushButton[flat="true"]:hover {
    background-color: rgba(255, 255, 255, 0.09);
    border-color: #606060;
}

/* ── Inputs ── */
QLineEdit {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    padding: 5px 8px;
    border-radius: 4px;
    selection-background-color: #264f78;
}

QLineEdit:focus {
    border: 1px solid #007acc;
    background-color: #3f3f3f;
}

QLineEdit:hover {
    border: 1px solid #666666;
}

QComboBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    padding: 4px 8px;
    border-radius: 4px;
    min-height: 20px;
}

QComboBox:hover {
    border: 1px solid #777777;
}

QComboBox:focus {
    border: 1px solid #007acc;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d30;
    color: #cccccc;
    border: 1px solid #454545;
    selection-background-color: #094771;
    outline: none;
}

/* ── Spin Box ── */
QSpinBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    padding: 4px 8px;
    border-radius: 4px;
}

QSpinBox:focus {
    border: 1px solid #007acc;
}

/* ── Check Box ── */
QCheckBox {
    background-color: transparent;
    spacing: 8px;
    color: #cccccc;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #555555;
    border-radius: 3px;
    background-color: #3c3c3c;
}

QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}

QCheckBox::indicator:hover {
    border-color: #007acc;
}

/* ── Tables ── */
QHeaderView::section {
    background-color: #2a2a2a;
    color: #aaaaaa;
    border: none;
    border-right: 1px solid #3a3a3d;
    border-bottom: 1px solid #3a3a3d;
    padding: 5px 10px;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.3px;
}

QTableWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    gridline-color: #2d2d2d;
    border: 1px solid #3a3a3d;
    outline: none;
    alternate-background-color: #222222;
}

QTableWidget::item {
    padding: 4px 10px;
    border-bottom: 1px solid #2a2a2a;
}

QTableWidget::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QTableWidget::item:hover:!selected {
    background-color: #2a2d2e;
}

/* ── Groups ── */
QGroupBox {
    border: 1px solid #3a3a3d;
    border-radius: 6px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: 600;
    color: #cccccc;
}

QGroupBox::title {
    color: #9b9b9b;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    left: 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

/* ── List Widget ── */
QListWidget {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3a3a3d;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    padding: 7px 12px;
    border-bottom: 1px solid #2d2d2d;
    border-radius: 0;
}

QListWidget::item:selected {
    background-color: #094771;
    color: #ffffff;
    border-bottom: 1px solid #0a5a8c;
}

QListWidget::item:hover:!selected {
    background-color: #2a2d2e;
}

/* ── Progress Bar ── */
QProgressBar {
    background-color: #3a3a3d;
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 3px;
}

/* ── Dialogs ── */
QDialog {
    background-color: #252526;
}

QDialogButtonBox QPushButton {
    min-width: 84px;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #2a2a2a;
    color: #cccccc;
    border: 1px solid #4a4a4a;
    padding: 4px 10px;
    font-size: 12px;
    border-radius: 3px;
}

/* ── Frame separators ── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #3a3a3d;
}
"""

# Editor colors for QScintilla in dark mode
DARK_EDITOR_COLORS = {
    "background": "#1e1e1e",
    "foreground": "#d4d4d4",
    "caret": "#d4d4d4",
    "selection_bg": "#264f78",
    "line_highlight": "#2a2d2e",
    "margin_bg": "#1e1e1e",
    "margin_fg": "#858585",
    "fold_margin_bg": "#1e1e1e",
    # LaTeX token colors
    "command": "#569cd6",       # \command
    "environment": "#4ec9b0",   # \begin, \end
    "math": "#ce9178",          # $...$, \[...\]
    "comment": "#6a9955",       # %...
    "brace": "#ffd700",         # { }
    "bracket": "#da70d6",       # [ ]
    "string": "#ce9178",
    "number": "#b5cea8",
    "error": "#f44747",
}