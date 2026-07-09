import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import MATERIAL_DARK_STYLE

class GUILogHandler(logging.Handler):
    """Handler gửi tất cả log của androguard đến LogWidget."""
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        msg = self.format(record)
        self.log_widget.append_log(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(MATERIAL_DARK_STYLE)
    win = MainWindow()
    win.show()

    # Cấu hình logger của androguard để dùng handler trên
    logger = logging.getLogger("androguard")
    logger.setLevel(logging.DEBUG)  # bắt tất cả DEBUG trở lên
    handler = GUILogHandler(win.log)  # win.log là LogWidget
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    sys.exit(app.exec())