from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QMessageBox, QListWidgetItem
from PyQt6.QtCore import Qt
import time

class IAPManagerDialog(QDialog):
    def __init__(self, iap_manager, parent=None):
        super().__init__(parent)
        self.iap_manager = iap_manager
        self.setWindowTitle("Quản lý giao dịch IAP đã lưu")
        self.resize(500, 400)
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.load_transactions()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_delete = QPushButton("Xóa đã chọn")
        btn_delete.clicked.connect(self.delete_selected)
        btn_layout.addWidget(btn_delete)

        btn_repeat = QPushButton("Lặp lại đã chọn")
        btn_repeat.clicked.connect(self.repeat_selected)
        btn_layout.addWidget(btn_repeat)

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_transactions(self):
        self.list_widget.clear()
        for t in self.iap_manager.get_saved_purchases():
            text = f"{t['package']} - {t['product']} ({time.strftime('%d/%m/%Y %H:%M', time.localtime(t['timestamp']))})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, t['id'])
            self.list_widget.addItem(item)

    def delete_selected(self):
        for item in self.list_widget.selectedItems():
            self.iap_manager.delete_purchase(item.data(Qt.ItemDataRole.UserRole))
        self.load_transactions()
        QMessageBox.information(self, "Thành công", "Đã xóa giao dịch đã chọn.")

    def repeat_selected(self):
        for item in self.list_widget.selectedItems():
            tid = item.data(Qt.ItemDataRole.UserRole)
            for t in self.iap_manager.transactions:
                if t['id'] == tid:
                    self.iap_manager.auto_repeat(t['package'], t['product'])
        QMessageBox.information(self, "Thành công", "Đã lặp lại giao dịch đã chọn.")