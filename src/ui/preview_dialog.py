from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
from PyQt6.QtCore import Qt

class PreviewDialog(QDialog):
    def __init__(self, patches, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Xem trước thay đổi")
        self.resize(550, 450)
        self.patches = patches
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("<b style='color:#58a6ff;'>Các bản vá sẽ được áp dụng:</b>")
        layout.addWidget(title)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("background-color: #0d1117; color: #c9d1d9; font-family: Consolas;")

        preview = ""
        for patch in self.patches:
            preview += f"• {patch['label']}\n"
            preview += f"  Chế độ: {patch['mode']}\n"
            if 'description' in patch:
                preview += f"  Mô tả: {patch['description']}\n"
            if 'files_affected' in patch:
                preview += f"  File dự kiến bị ảnh hưởng: {patch['files_affected']}\n"
            preview += "\n"

        preview += "\n⚠ Lưu ý: Đây là danh sách dự kiến. Số lượng file thực tế có thể thay đổi sau khi phân tích."
        text.setText(preview)
        layout.addWidget(text)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Tiếp tục xây dựng")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px 16px;")
        btn_cancel = QPushButton("Quay lại")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        self.setLayout(layout)