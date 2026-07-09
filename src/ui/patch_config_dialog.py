from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel, QHBoxLayout, QButtonGroup
from PyQt6.QtCore import Qt

class PatchConfigDialog(QDialog):
    def __init__(self, patch_name, options, current_mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Cấu hình cho {patch_name}")
        self.resize(350, 200)
        self.selected_mode = current_mode
        self.options = options  # dict: {mode_key: "Mô tả"}

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<b>Chọn chế độ cho {patch_name}:</b>"))

        self.group = QButtonGroup(self)
        for key, desc in options.items():
            radio = QRadioButton(desc)
            radio.setChecked(key == current_mode)
            radio.toggled.connect(lambda checked, k=key: self._on_select(k) if checked else None)
            self.group.addButton(radio)
            layout.addWidget(radio)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _on_select(self, key):
        self.selected_mode = key

    def get_mode(self):
        return self.selected_mode