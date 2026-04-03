LIGHT_THEME_QSS = """
/* ── Base ── */
QMainWindow {
    background-color: #ffffff;
}

QWidget {
    background-color: #ffffff;
    color: #1f1f1f;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ── Menu Bar ── */
QMenuBar {
    background-color: #f0f0f0;
    color: #1f1f1f;
    border-bottom: 1px solid #d0d0d0;
    padding: 1px 0;
    font-size: 13px;
}

QMenuBar::item {
    padding: 5px 12px;
    border-radius: 0;
}

QMenuBar::item:selected {
    background-color: #cde8fb;
    color: #1f1f1f;
}

QMenu {
    background-color: #f8f8f8;
    color: #1f1f1f;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px 0;
}

QMenu::item {
    padding: 6px 32px 6px 20px;
}

QMenu::item:selected {
    background-color: #cde8fb;
    color: #1f1f1f;
}

QMenu::item:disabled {
    color: #aaaaaa;
}

QMenu::separator {
    height: 1px;
    background-color: #d4d4d4;
    margin: 4px 12px;
}

/* ── Toolbar ── */
QToolBar {
    background-color: #f0f0f0;
    border-bottom: 1px solid #d0d0d0;
    spacing: 2px;
    padding: 4px 8px;
    min-height: 38px;
}

QToolBar::separator {
    width: 1px;
    background-color: #d0d0d0;
    margin: 6px 5px;
}

QToolButton {
    background-color: transparent;
    color: #1f1f1f;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 11px;
    font-size: 12px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: rgba(0, 0, 0, 0.07);
    border: 1px solid rgba(0, 0, 0, 0.05);
}

QToolButton:pressed {
    background-color: rgba(0, 0, 0, 0.12);
}

QToolButton:checked {
    background-color: rgba(0, 122, 204, 0.18);
    border: 1px solid rgba(0, 122, 204, 0.35);
    color: #0067b0;
}

/* Compile button — primary action */
QToolButton[compile_btn="true"] {
    background-color: #16825d;
    color: #ffffff;
    border: 1px solid #138050;
    border-radius: 4px;
    padding: 4px 13px;
    font-weight: 600;
}

QToolButton[compile_btn="true"]:hover {
    background-color: #1a9969;
    border-color: #138050;
}

QToolButton[compile_btn="true"]:pressed {
    background-color: #116648;
}

/* Stop button — destructive action */
QToolButton[stop_btn="true"] {
    color: #c0392b;
}

QToolButton[stop_btn="true"]:hover {
    background-color: rgba(192, 57, 43, 0.10);
    border: 1px solid rgba(192, 57, 43, 0.25);
    color: #e74c3c;
}

QToolButton[stop_btn="true"]:pressed {
    background-color: rgba(192, 57, 43, 0.18);
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
    border-top: 1px solid #d0d0d0;
    background-color: #ffffff;
}

QTabBar {
    background-color: #f0f0f0;
    border-bottom: 1px solid #d0d0d0;
}

QTabBar::tab {
    background-color: #e8e8e8;
    color: #7a7a7a;
    border: none;
    border-right: 1px solid #f0f0f0;
    padding: 7px 16px 7px 16px;
    min-width: 80px;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1f1f1f;
    border-top: 2px solid #007acc;
    padding-top: 5px;
    border-right: 1px solid #d0d0d0;
}

QTabBar::tab:hover:!selected {
    background-color: #e0e0e0;
    color: #3a3a3a;
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
    background-color: rgba(0, 0, 0, 0.12);
}

/* ── File Tree Header ── */
QLabel#file_tree_header {
    background-color: #f3f3f3;
    color: #555555;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding-left: 14px;
    border-bottom: 1px solid #d0d0d0;
}

/* ── Tree View ── */
QTreeView {
    background-color: #f3f3f3;
    color: #1f1f1f;
    border: none;
    outline: none;
    font-size: 13px;
}

QTreeView::item {
    padding: 3px 4px;
}

QTreeView::item:hover {
    background-color: #e8e8e8;
}

QTreeView::item:selected {
    background-color: #cde8fb;
    color: #1f1f1f;
}

QTreeView::branch {
    background-color: #f3f3f3;
}

/* ── Splitters ── */
QSplitter::handle {
    background-color: #d0d0d0;
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
    background-color: #ffffff;
    color: #1e1e1e;
    border: none;
    selection-background-color: #add6ff;
    font-family: "Cascadia Code", "Consolas", monospace;
}

/* ── Scroll Bars ── */
QScrollBar:vertical {
    background-color: transparent;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: rgba(100, 100, 100, 0.28);
    min-height: 24px;
    border-radius: 3px;
    margin: 2px 2px 2px 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(80, 80, 80, 0.50);
}

QScrollBar::handle:vertical:pressed {
    background-color: rgba(60, 60, 60, 0.60);
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
    background-color: rgba(100, 100, 100, 0.28);
    min-width: 24px;
    border-radius: 3px;
    margin: 3px 2px 2px 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: rgba(80, 80, 80, 0.50);
}

QScrollBar::handle:horizontal:pressed {
    background-color: rgba(60, 60, 60, 0.60);
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
    background-color: #d8d8d8;
    color: #aaaaaa;
}

QPushButton:flat, QPushButton[flat="true"] {
    background-color: transparent;
    color: #333333;
    border: 1px solid #cccccc;
}

QPushButton:flat:hover, QPushButton[flat="true"]:hover {
    background-color: rgba(0, 0, 0, 0.07);
    border-color: #aaaaaa;
}

/* ── Inputs ── */
QLineEdit {
    background-color: #ffffff;
    color: #1f1f1f;
    border: 1px solid #c0c0c0;
    padding: 5px 8px;
    border-radius: 4px;
    selection-background-color: #add6ff;
}

QLineEdit:focus {
    border: 1px solid #007acc;
}

QLineEdit:hover {
    border: 1px solid #999999;
}

QComboBox {
    background-color: #ffffff;
    color: #1f1f1f;
    border: 1px solid #c0c0c0;
    padding: 4px 8px;
    border-radius: 4px;
    min-height: 20px;
}

QComboBox:hover {
    border: 1px solid #999999;
}

QComboBox:focus {
    border: 1px solid #007acc;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #f8f8f8;
    color: #1f1f1f;
    border: 1px solid #cccccc;
    selection-background-color: #cde8fb;
    outline: none;
}

/* ── Spin Box ── */
QSpinBox {
    background-color: #ffffff;
    color: #1f1f1f;
    border: 1px solid #c0c0c0;
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
    color: #1f1f1f;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1.5px solid #c0c0c0;
    border-radius: 3px;
    background-color: #ffffff;
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
    background-color: #efefef;
    color: #555555;
    border: none;
    border-right: 1px solid #d4d4d4;
    border-bottom: 1px solid #d4d4d4;
    padding: 5px 10px;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.3px;
}

QTableWidget {
    background-color: #ffffff;
    color: #1f1f1f;
    gridline-color: #eeeeee;
    border: 1px solid #d0d0d0;
    outline: none;
    alternate-background-color: #fafafa;
}

QTableWidget::item {
    padding: 4px 10px;
    border-bottom: 1px solid #eeeeee;
}

QTableWidget::item:selected {
    background-color: #cde8fb;
    color: #1f1f1f;
}

QTableWidget::item:hover:!selected {
    background-color: #f0f7ff;
}

/* ── Groups ── */
QGroupBox {
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: 600;
    color: #1f1f1f;
    background-color: #ffffff;
}

QGroupBox::title {
    color: #666666;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    left: 12px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    background-color: #ffffff;
}

/* ── List Widget ── */
QListWidget {
    background-color: #ffffff;
    color: #1f1f1f;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    padding: 7px 12px;
    border-bottom: 1px solid #f0f0f0;
}

QListWidget::item:selected {
    background-color: #cde8fb;
    color: #1f1f1f;
}

QListWidget::item:hover:!selected {
    background-color: #f0f7ff;
}

/* ── Progress Bar ── */
QProgressBar {
    background-color: #e4e4e4;
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
    background-color: #f5f5f5;
}

QDialogButtonBox QPushButton {
    min-width: 84px;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #f8f8f8;
    color: #1f1f1f;
    border: 1px solid #cccccc;
    padding: 4px 10px;
    font-size: 12px;
    border-radius: 3px;
}

/* ── Frame separators ── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #d0d0d0;
}
"""

# Editor colors for QScintilla in light mode
LIGHT_EDITOR_COLORS = {
    "background": "#ffffff",
    "foreground": "#1e1e1e",
    "caret": "#1e1e1e",
    "selection_bg": "#add6ff",
    "line_highlight": "#f5f5f5",
    "margin_bg": "#f3f3f3",
    "margin_fg": "#858585",
    "fold_margin_bg": "#f3f3f3",
    # LaTeX token colors
    "command": "#0000ff",       # \command
    "environment": "#267f99",   # \begin, \end
    "math": "#a31515",          # $...$, \[...\]
    "comment": "#008000",       # %...
    "brace": "#b8860b",         # { }
    "bracket": "#af00db",       # [ ]
    "string": "#a31515",
    "number": "#098658",
    "error": "#e51400",
}