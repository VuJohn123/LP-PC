from PyQt6.QtWidgets import QTextEdit

class LogWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

    def append_log(self, msg):
        self.append(msg)