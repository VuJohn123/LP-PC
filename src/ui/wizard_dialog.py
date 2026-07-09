from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel, QButtonGroup, QHBoxLayout

class WizardDialog(QDialog):
    """Dialog hướng dẫn cho người mới bắt đầu."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LP-PC Suite Wizard - Bạn muốn làm gì?")
        self.setMinimumSize(450, 350)
        self.selected_mode = 'iap_dex'
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("<b style='color:#58a6ff;'>Chào mừng đến với LP-PC Suite!</b>")
        title.setWordWrap(True)
        layout.addWidget(title)

        subtitle = QLabel("Chọn một trong các tùy chọn bên dưới để bắt đầu:")
        layout.addWidget(subtitle)

        self.mode_group = QButtonGroup(self)
        options = [
            ("iap_dex", "🕹️ Chơi game miễn phí (IAP Bypass)",
             "Tự động vô hiệu hóa mua hàng trong ứng dụng, nhận vật phẩm miễn phí."),
            ("ads_full_offline", "🚫 Xóa toàn bộ quảng cáo",
             "Loại bỏ hoàn toàn quảng cáo khỏi ứng dụng (cả activity và network)."),
            ("license", "🔑 Dùng app trả phí miễn phí (License Bypass)",
             "Bỏ qua kiểm tra bản quyền, sử dụng app trả phí mà không cần mua."),
            ("multi:license,ads,iap_dex", "⭐ Tất cả trong một (Full Patch)",
             "Kết hợp tất cả các bản vá: License + Ads + IAP."),
            ("custom", "🔧 Tùy chỉnh...",
             "Tự chọn bản vá thủ công từ danh sách đầy đủ."),
        ]
        for mode, title, desc in options:
            radio = QRadioButton(f"{title}")
            radio.setToolTip(desc)
            self.mode_group.addButton(radio)
            layout.addWidget(radio)
            desc_label = QLabel(f"    ↳ {desc}")
            desc_label.setStyleSheet("color: #8b949e; font-size: 11px; margin-left: 20px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
            if mode == "iap_dex":
                radio.setChecked(True)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Bắt đầu")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px 16px;")
        btn_cancel = QPushButton("Thoát")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_mode(self):
        for i, radio in enumerate(self.mode_group.buttons()):
            if radio.isChecked():
                if i == 0: return "iap_dex"
                if i == 1: return "ads_full_offline"
                if i == 2: return "license"
                if i == 3: return "multi:license,ads,iap_dex"
                if i == 4: return "custom"
        return "iap_dex"