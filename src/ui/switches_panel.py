from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class SwitchesPanel(QWidget):
    def __init__(self, iap_manager, parent=None):
        super().__init__(parent)
        self.iap_manager = iap_manager
        layout = QHBoxLayout()
        layout.setSpacing(8)

        self.btn_billing = QPushButton("💰 Giả lập Google Thanh toán: BẬT")
        self.btn_billing.setCheckable(True)
        self.btn_billing.setChecked(True)
        self.btn_billing.toggled.connect(self.toggle_billing)
        layout.addWidget(self.btn_billing)

        self.btn_proxy = QPushButton("🌐 Máy chủ Proxy: BẬT")
        self.btn_proxy.setCheckable(True)
        self.btn_proxy.setChecked(True)
        self.btn_proxy.toggled.connect(self.toggle_proxy)
        layout.addWidget(self.btn_proxy)

        self.btn_autorepeat = QPushButton("🔄 Tự động lặp: TẮT")
        self.btn_autorepeat.setCheckable(True)
        self.btn_autorepeat.toggled.connect(self.toggle_autorepeat)
        layout.addWidget(self.btn_autorepeat)

        self.btn_save = QPushButton("💾 Lưu giao dịch: TẮT")
        self.btn_save.setCheckable(True)
        self.btn_save.toggled.connect(self.toggle_save)
        layout.addWidget(self.btn_save)

        self.btn_reset = QPushButton("♻️ Đặt mặc định")
        self.btn_reset.clicked.connect(self.reset_defaults)
        layout.addWidget(self.btn_reset)

        layout.addStretch()
        self.setLayout(layout)

    def toggle_billing(self, checked):
        self.btn_billing.setText(f"💰 Giả lập Google Thanh toán: {'BẬT' if checked else 'TẮT'}")

    def toggle_proxy(self, checked):
        self.btn_proxy.setText(f"🌐 Máy chủ Proxy: {'BẬT' if checked else 'TẮT'}")

    def toggle_autorepeat(self, checked):
        self.btn_autorepeat.setText(f"🔄 Tự động lặp: {'BẬT' if checked else 'TẮT'}")
        self.iap_manager.auto_repeat_enabled = checked

    def toggle_save(self, checked):
        self.btn_save.setText(f"💾 Lưu giao dịch: {'BẬT' if checked else 'TẮT'}")
        self.iap_manager.save_for_restore_enabled = checked

    def reset_defaults(self):
        self.btn_billing.setChecked(True)
        self.btn_proxy.setChecked(True)
        self.btn_autorepeat.setChecked(False)
        self.btn_save.setChecked(False)