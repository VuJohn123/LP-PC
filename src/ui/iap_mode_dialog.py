from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel, QButtonGroup, QHBoxLayout, QGroupBox

class IAPModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("InApp Purchase Emulation Mode")
        self.setMinimumSize(500, 350)
        self.selected_mode = 'dex'
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(QLabel("<b style='color:#58a6ff;'>Chọn phương pháp giả lập InApp Purchase:</b>"))
        options_group = QGroupBox("Chế độ giả lập:")
        options_layout = QVBoxLayout()
        self.mode_group = QButtonGroup(self)

        self.radio_dex = QRadioButton("Tái cấu trúc Dex (Im lặng & Tự động) - Khuyên dùng")
        self.radio_dex.setChecked(True)
        self.mode_group.addButton(self.radio_dex)
        options_layout.addWidget(self.radio_dex)
        options_layout.addWidget(QLabel("    ↳ Vô hiệu hóa các hàm launchBillingFlow/getBuyIntent..."))

        self.radio_proxy = QRadioButton("Máy chủ Proxy (Cần PC chạy proxy server)")
        self.mode_group.addButton(self.radio_proxy)
        options_layout.addWidget(self.radio_proxy)
        options_layout.addWidget(QLabel("    ↳ Chuyển hướng yêu cầu billing đến proxy server trên PC..."))

        self.radio_support = QRadioButton("Hỗ trợ bản vá cho mô phỏng LVL và Inapp")
        self.mode_group.addButton(self.radio_support)
        options_layout.addWidget(self.radio_support)
        options_layout.addWidget(QLabel("    ↳ Chế độ đầy đủ, chuyển hướng mọi yêu cầu..."))

        self.radio_update = QRadioButton("Cập nhật bản vá trong ứng dụng đã vá")
        self.mode_group.addButton(self.radio_update)
        options_layout.addWidget(self.radio_update)
        options_layout.addWidget(QLabel("    ↳ Dành cho ứng dụng đã được patch..."))

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        note = QLabel("<i>💡 Lưu ý: Để có kết quả tốt nhất, bạn nên sử dụng bản vá 'Signature Verification status always True'...</i>")
        note.setStyleSheet("color: #d29922; font-size: 11px;")
        layout.addWidget(note)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Tiếp tục")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("background-color: #238636; color: white; font-weight: bold;")
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_mode(self):
        if self.radio_dex.isChecked(): return 'iap_dex'
        elif self.radio_proxy.isChecked(): return 'iap_proxy'
        elif self.radio_support.isChecked(): return 'iap:support_lvl_inapp'
        else: return 'iap_update'