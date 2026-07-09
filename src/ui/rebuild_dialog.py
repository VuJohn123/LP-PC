import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QWidget, QCheckBox, QFrame, QMessageBox,
    QComboBox, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .patch_config_dialog import PatchConfigDialog
from .preview_dialog import PreviewDialog


class RebuildDialog(QDialog):
    """Hộp thoại 'Tạo tệp tin APK đã sửa' mô phỏng Lucky Patcher."""
    rebuild_requested = pyqtSignal(str)

    def __init__(self, app_name, package, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tạo tệp tin APK đã sửa - {app_name}")
        self.setMinimumSize(550, 650)
        self.resize(600, 700)
        self.app_name = app_name
        self.package = package

        # Định nghĩa các patch có sẵn
        self.patches = [
            {
                'name': 'license', 'label': '🔑 Gỡ xác minh giấy phép (License)',
                'configurable': True, 'mode': 'auto',
                'options': {
                    'auto': 'Chế độ tự động',
                    'dex': 'Chế độ tự động (dex)',
                    'extreme': 'Cực đoan (Bytecode Pattern)',
                    'reverse': 'Đảo ngược (Reverse Auto)'
                },
                'tooltip': (
                    '🔑 Gỡ xác minh giấy phép:\n'
                    '• Auto: Tự động tìm và vá method allow/dontAllow\n'
                    '• Dex: Chế độ tối thiểu, cần Google Play\n'
                    '• Extreme: Dùng bytecode pattern cho app obfuscate\n'
                    '• Reverse: Vô hiệu hóa ServerManagedPolicy'
                )
            },
            {
                'name': 'ads', 'label': '🚫 Xóa Google Ads',
                'configurable': True, 'mode': 'remove',
                'options': {
                    'remove': 'Xóa Activity quảng cáo',
                    'offline': 'Làm hỏng nhận quảng cáo (Offline)',
                    'links': 'Xoá liên kết quảng cáo',
                    'full_offline': 'Tạo ngoại tuyến đầy đủ'
                },
                'tooltip': (
                    '🚫 Xóa Google Ads:\n'
                    '• Remove: Xóa activity quảng cáo khỏi manifest\n'
                    '• Break: Làm hỏng cơ chế nhận quảng cáo\n'
                    '• Offline: Ép module quảng cáo nghĩ rằng ngoại tuyến\n'
                    '• Full: Kết hợp tất cả phương pháp'
                )
            },
            {
                'name': 'iap', 'label': '💳 Mô phỏng InApp Purchase',
                'configurable': True, 'mode': 'dex',
                'options': {
                    'dex': 'Tái cấu trúc Dex (Im lặng & Tự động)',
                    'proxy': 'Máy chủ Proxy (Cần PC chạy proxy)',
                    'aidl': 'Nhúng AIDL Proxy Service'
                },
                'tooltip': (
                    '💳 Mô phỏng InApp Purchase:\n'
                    '• Dex: Vá trực tiếp code, tự động trả về thành công\n'
                    '• Proxy: Dùng PC làm máy chủ giả mạo billing (cần ADB)\n'
                    '• AIDL: Nhúng service proxy vào APK'
                )
            },
            {
                'name': 'change_perms', 'label': '⚙️ Thay đổi quyền (Permissions)',
                'configurable': False, 'mode': None, 'options': {},
                'tooltip': '⚙️ Thay đổi quyền:\nXóa các quyền nguy hiểm như SMS, Contacts khỏi ứng dụng'
            },
            {
                'name': 'custom', 'label': '📄 Custom Patch (.txt/.lpzip)',
                'configurable': False, 'mode': None, 'options': {},
                'tooltip': '📄 Custom Patch:\nÁp dụng bản vá tùy chỉnh từ file .txt hoặc .lpzip\nCó thể tải từ cộng đồng patch.chelpus.com'
            },
            {
                'name': 'resign', 'label': '✍️ Ký lại APK',
                'configurable': False, 'mode': None, 'options': {},
                'tooltip': '✍️ Ký lại APK:\nKý APK với chữ ký mới để cài đặt được trên thiết bị\nCần "Patch to Android" để update app mà không mất data'
            },
        ]

        # Các tùy chọn bổ sung
        self.extra_options = [
            {'name': 'save_purchase', 'label': '💾 Lưu giao dịch để khôi phục (Save purchase for restore)', 'checked': False,
             'tooltip': 'Lưu các giao dịch IAP đã thành công để có thể khôi phục sau'},
            {'name': 'auto_repeat', 'label': '🔄 Tự động lặp lại giao dịch (Auto-repeat purchases)', 'checked': False,
             'tooltip': 'Tự động lặp lại các giao dịch IAP đã lưu với cài đặt hiện tại'},
            {'name': 'sig_disable', 'label': '🔓 Vô hiệu hóa xác minh chữ ký (Disable signature verification)', 'checked': False,
             'tooltip': 'Vô hiệu hóa self-check chữ ký bên trong ứng dụng'},
            {'name': 'sig_zip_disable', 'label': '📦 Vô hiệu hóa xác minh chữ ký Zip', 'checked': False,
             'tooltip': 'Vô hiệu hóa kiểm tra chữ ký của file zip/APK'},
        ]

        self.patch_widgets = {}
        self.extra_widgets = {}
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        title = QLabel(f"<b style='color:#58a6ff;'>Chọn các bản vá cho {self.app_name}</b>")
        title.setFont(QFont("Segoe UI", 11))
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(6)

        # Các patch chính
        for patch in self.patches:
            row = self._create_patch_row(patch)
            self.scroll_layout.addWidget(row)

        # Separator
        self.scroll_layout.addWidget(QLabel("<b>Tùy chọn bổ sung:</b>"))

        # Các tùy chọn bổ sung
        for opt in self.extra_options:
            chk = QCheckBox(opt['label'])
            chk.setChecked(opt['checked'])
            if 'tooltip' in opt:
                chk.setToolTip(opt['tooltip'])
            self.scroll_layout.addWidget(chk)
            self.extra_widgets[opt['name']] = chk

        # Tùy chọn nâng cao
        adv_group = QGroupBox("Tùy chọn nâng cao")
        adv_layout = QVBoxLayout()
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Loại chữ ký:"))
        self.key_combo = QComboBox()
        self.key_combo.addItems(['testkey', 'platform', 'media', 'shared'])
        self.key_combo.setToolTip('Chọn loại chữ ký để ký APK sau khi rebuild')
        key_layout.addWidget(self.key_combo)
        adv_layout.addLayout(key_layout)
        pkg_layout = QHBoxLayout()
        pkg_layout.addWidget(QLabel("Forced Package ID (127 = auto):"))
        self.package_id_spin = QSpinBox()
        self.package_id_spin.setRange(1, 127)
        self.package_id_spin.setValue(127)
        self.package_id_spin.setToolTip('Thay đổi package ID để cài song song với app gốc. 127 = tự động')
        pkg_layout.addWidget(self.package_id_spin)
        adv_layout.addLayout(pkg_layout)
        adv_group.setLayout(adv_layout)
        self.scroll_layout.addWidget(adv_group)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Nút Preview
        btn_preview = QPushButton("🔍 Xem trước thay đổi")
        btn_preview.clicked.connect(self.show_preview)
        main_layout.addWidget(btn_preview)

        # Nút Build và Cancel
        btn_layout = QHBoxLayout()
        self.btn_build = QPushButton("🛠 Xây dựng lại")
        self.btn_build.clicked.connect(self.on_build)
        self.btn_build.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 10px 20px;")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_build)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _create_patch_row(self, patch):
        """Tạo một hàng gồm: checkbox | label + tooltip | nút cấu hình (nếu có)"""
        row = QFrame()
        row.setFrameShape(QFrame.Shape.StyledPanel)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 4, 8, 4)

        chk = QCheckBox()
        chk.setChecked(False)
        chk.toggled.connect(lambda checked, p=patch: self._on_patch_toggled(p, checked))
        row_layout.addWidget(chk)

        label = QLabel(patch['label'])
        label.setFont(QFont("Segoe UI", 10))
        if 'tooltip' in patch:
            label.setToolTip(patch['tooltip'])
        row_layout.addWidget(label, 1)

        if patch['configurable']:
            btn_config = QPushButton("⚙️")
            btn_config.setFixedSize(30, 30)
            btn_config.setToolTip("Cấu hình chế độ")
            btn_config.clicked.connect(lambda checked, p=patch: self._open_config_dialog(p))
            row_layout.addWidget(btn_config)
        else:
            spacer = QWidget()
            spacer.setFixedSize(30, 30)
            row_layout.addWidget(spacer)

        self.patch_widgets[patch['name']] = {'checkbox': chk, 'mode': patch['mode']}
        return row

    def _on_patch_toggled(self, patch, checked):
        pass

    def _open_config_dialog(self, patch):
        current = self.patch_widgets[patch['name']]['mode']
        dlg = PatchConfigDialog(patch['label'], patch['options'], current, self)
        if dlg.exec():
            new_mode = dlg.get_mode()
            self.patch_widgets[patch['name']]['mode'] = new_mode

    def show_preview(self):
        """Hiển thị dialog xem trước thay đổi."""
        patches = []
        for patch in self.patches:
            name = patch['name']
            if self.patch_widgets[name]['checkbox'].isChecked():
                patches.append({
                    'label': patch['label'],
                    'mode': self.patch_widgets[name]['mode'],
                    'description': patch.get('tooltip', '')
                })
        # Thêm các tùy chọn bổ sung
        for opt in self.extra_options:
            if self.extra_widgets[opt['name']].isChecked():
                patches.append({
                    'label': opt['label'],
                    'mode': 'N/A',
                    'description': opt.get('tooltip', '')
                })
        if not patches:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn ít nhất một bản vá.")
            return
        dlg = PreviewDialog(patches, self)
        if dlg.exec():
            self.on_build()

    def on_build(self):
        selected = []
        for patch in self.patches:
            name = patch['name']
            if self.patch_widgets[name]['checkbox'].isChecked():
                mode = self.patch_widgets[name]['mode']
                if mode:
                    selected.append(f"{name}:{mode}")
                else:
                    selected.append(name)

        # Thêm các tùy chọn bổ sung vào mode
        for opt in self.extra_options:
            if self.extra_widgets[opt['name']].isChecked():
                selected.append(opt['name'])

        if not selected:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn ít nhất một bản vá.")
            return

        mode_string = ','.join(selected)
        self.rebuild_requested.emit(mode_string)
        self.accept()