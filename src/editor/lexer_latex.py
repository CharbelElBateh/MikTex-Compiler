from PyQt6.Qsci import QsciLexerTeX
from PyQt6.QtGui import QColor, QFont


class LaTeXLexer(QsciLexerTeX):
    """Enhanced LaTeX lexer built on QScintilla's built-in TeX lexer.

    Applies theme-aware colors for LaTeX tokens.
    """

    def __init__(self, colors: dict[str, str], font: QFont, parent=None) -> None:
        super().__init__(parent)
        self._colors = colors
        self._font = font
        self._apply_styles()

    def _apply_styles(self) -> None:
        c = self._colors
        bg = QColor(c["background"])
        fg = QColor(c["foreground"])

        # Set default paper (background) and color (foreground) for all styles
        self.setDefaultPaper(bg)
        self.setDefaultColor(fg)

        # QsciLexerTeX style indices:
        # 0  = Default
        # 1  = Special
        # 2  = Group
        # 3  = Symbol
        # 4  = Command
        # 5  = Text
        # 10 = Comment (%)

        # Default text
        self._set_style(0, fg, bg, self._font)
        # Special characters
        self._set_style(1, QColor(c.get("brace", fg.name())), bg, self._font)
        # Group (braces {})
        self._set_style(2, QColor(c.get("brace", fg.name())), bg, self._font)
        # Symbol ($, ^, _, ~, etc.)
        self._set_style(3, QColor(c.get("math", fg.name())), bg, self._font)
        # Command (\word)
        self._set_style(4, QColor(c.get("command", fg.name())), bg, self._font)
        # Text
        self._set_style(5, fg, bg, self._font)
        # Comment (%)
        comment_font = QFont(self._font)
        comment_font.setItalic(True)
        self._set_style(10, QColor(c.get("comment", fg.name())), bg, comment_font)

    def _set_style(self, style_id: int, color: QColor, paper: QColor, font: QFont) -> None:
        self.setColor(color, style_id)
        self.setPaper(paper, style_id)
        self.setFont(font, style_id)

    def update_colors(self, colors: dict[str, str]) -> None:
        self._colors = colors
        self._apply_styles()

    def language(self) -> str:
        return "LaTeX"
