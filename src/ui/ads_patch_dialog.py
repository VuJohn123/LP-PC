from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel, QButtonGroup, QHBoxLayout, QGroupBox
from PyQt6.QtCore import pyqtSignal

class AdsPatchDialog(QDialog):
    patch_requested = pyqtSignal(str)

    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Remove Google Ads - {app_name}")
        self.setMinimumSize(500, 420)
        self.selected_mode = "remove_links"
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b style='color:#58a6ff;'>Chọn phương pháp loại bỏ quảng cáo:</b>"))
        options_group = QGroupBox("Các chế độ loại bỏ quảng cáo:")
        options_layout = QVBoxLayout()
        self.mode_group = QButtonGroup(self)

        options = [
            ("remove_links", "Xoá liên kết khỏi APK", "Loại bỏ các liên kết http:// dùng AdsBlockList"),
            ("break_receiver", "Làm hỏng phần nhận quảng cáo", "Phá vỡ cơ chế nhận Google Ads"),
            ("offline", "Vá ngoại tuyến", "Làm module quảng cáo nghĩ rằng thiết bị đang ngoại tuyến"),
            ("other", "Các bản vá khác", "Bản vá bổ sung loại bỏ quảng cáo"),
            ("full_offline", "Tạo ngoại tuyến đầy đủ", "Thử làm ứng dụng hoạt động hoàn toàn ngoại tuyến"),
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
        self.patch_requested.emit(f"ads:{self.selected_mode}")
        self.accept()