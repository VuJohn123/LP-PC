from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel, QButtonGroup, QHBoxLayout, QGroupBox
from PyQt6.QtCore import pyqtSignal

class LicensePatchDialog(QDialog):
    patch_requested = pyqtSignal(str)

    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Remove License Verification - {app_name}")
        self.setMinimumSize(500, 450)
        self.selected_mode = "auto"
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b style='color:#58a6ff;'>Chọn chế độ loại bỏ License:</b>"))
        options_group = QGroupBox("Các chế độ xác minh giấy phép:")
        options_layout = QVBoxLayout()
        self.mode_group = QButtonGroup(self)

        options = [
            ("auto_dex", "Chế độ tự động (dex)", "Số lượng bản vá tối thiểu"),
            ("auto", "Chế độ tự động", "Phù hợp với hầu hết ứng dụng"),
            ("reverse_auto", "Chế độ tự động (Đảo ngược)", "Khác biệt so với Auto mode"),
            ("extreme", "Các bản vá khác (Chế độ đặc biệt)", "Có thể gây mất ổn định"),
            ("amazon", "Chế độ tự động (Amazon Market)", "Dành cho Amazon Appstore"),
            ("samsung", "Chế độ tự động (SamsungApps)", "Dành cho Samsung Galaxy Store"),
            ("remove_deps", "Gỡ bỏ phần phụ thuộc Google Play", "Xóa mọi liên kết đến Google Play Services"),
        ]
        for mode, title, desc in options:
            radio = QRadioButton(title)
            radio.setChecked(mode == self.selected_mode)
            radio.toggled.connect(lambda checked, m=mode: self._on_select(m) if checked else None)
            self.mode_group.addButton(radio)
            options_layout.addWidget(radio)
            options_layout.addWidget(QLabel(f"    ↳ {desc}"))
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("Áp dụng")
        btn_apply.clicked.connect(self._on_apply)
        btn_apply.setStyleSheet("background-color: #238636; color: white; font-weight: bold;")
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _on_select(self, mode): self.selected_mode = mode

    def _on_apply(self):
        self.patch_requested.emit(f"license:{self.selected_mode}")
        self.accept()