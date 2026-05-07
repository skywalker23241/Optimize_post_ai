from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QTextCursor
from PyQt6.QtCore import Qt


class ConsoleWidget(QTextEdit):
    """Terminal-like log console with colored output."""

    COLORS = {
        "success": "#4EC9B0",
        "error": "#F44747",
        "warning": "#CCA700",
        "info": "#D4D4D4",
        "dim": "#808080",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "console")
        self.setReadOnly(True)
        self.setMinimumHeight(150)
        self.setMaximumHeight(250)

        font = QFont("Cascadia Code", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self._clear_format()

    def _clear_format(self):
        self.clear()
        self._default_format()

    def _default_format(self) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.COLORS["info"]))
        return fmt

    def _make_format(self, color_key: str) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self.COLORS.get(color_key, self.COLORS["info"])))
        return fmt

    def append_log(self, message: str):
        """Append a log line with automatic color detection."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if "OK" in message or "saved" in message.lower() or "succeeded" in message.lower():
            fmt = self._make_format("success")
        elif "FAILED" in message or "Error" in message or "error" in message.lower():
            fmt = self._make_format("error")
        elif "warning" in message.lower() or "Warning" in message:
            fmt = self._make_format("warning")
        elif message.startswith("-") or message.startswith("["):
            fmt = self._make_format("dim")
        else:
            fmt = self._default_format()

        cursor.insertText(message + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_console(self):
        self.clear()
