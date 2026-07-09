import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel,
    QHBoxLayout, QGroupBox, QCheckBox, QScrollArea, QWidget,
    QButtonGroup, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class RebuildTreeDialog(QDialog):
    action_requested = pyqtSignal(str)
    rebuild_params = pyqtSignal(str, str, int)  # mode, key_type, forced_package_id

    def __init__(self, app_name, package, preselected_action=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tạo tệp tin APK đã sửa - {app_name}")
        self.setMinimumSize(550, 750)
        self.app_name = app_name
        self.package = package
        self.selected_mode = None
        self.preselected_action = preselected_action
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        title = QLabel(f"<b style='color:#58a6ff;'>Tạo tệp tin APK đã sửa cho {self.app_name}</b>")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Tree options
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.build_options_tree()
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        scroll_layout.addWidget(self.tree)

        # Multi-patch group
        self.multi_group = QGroupBox("Chọn các bản vá (Multi-patch):")
        multi_layout = QVBoxLayout()
        self.chk_license = QCheckBox("Gỡ License (Auto)")
        self.chk_license_extreme = QCheckBox("Gỡ License (Cực đoan)")
        self.chk_ads = QCheckBox("Xóa Google Ads")
        self.chk_ads_offline = QCheckBox("Quảng cáo ngoại tuyến")
        self.chk_iap = QCheckBox("Mô phỏng InApp Purchase")
        self.chk_aidl = QCheckBox("Nhúng AIDL Proxy (InApp)")
        self.chk_perms = QCheckBox("Thay đổi quyền")
        self.chk_resign = QCheckBox("Ký lại APK")
        multi_layout.addWidget(self.chk_license)
        multi_layout.addWidget(self.chk_license_extreme)
        multi_layout.addWidget(self.chk_ads)
        multi_layout.addWidget(self.chk_ads_offline)
        multi_layout.addWidget(self.chk_iap)
        multi_layout.addWidget(self.chk_aidl)
        multi_layout.addWidget(self.chk_perms)
        multi_layout.addWidget(self.chk_resign)
        self.multi_group.setLayout(multi_layout)
        self.multi_group.setVisible(False)
        scroll_layout.addWidget(self.multi_group)

        # IAP mode
        self.iap_mode_group = QGroupBox("Phương thức InApp")
        iap_layout = QHBoxLayout()
        self.radio_dex = QRadioButton("Tái cấu trúc Dex")
        self.radio_proxy = QRadioButton("Máy chủ Proxy")
        self.radio_dex.setChecked(True)
        iap_layout.addWidget(self.radio_dex)
        iap_layout.addWidget(self.radio_proxy)
        self.iap_mode_group.setLayout(iap_layout)
        self.iap_mode_group.setVisible(False)
        scroll_layout.addWidget(self.iap_mode_group)

        # Additional options
        options_group = QGroupBox("Tùy chọn nâng cao")
        options_layout = QVBoxLayout()
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Loại chữ ký:"))
        self.key_combo = QComboBox()
        self.key_combo.addItems(['testkey', 'platform', 'media', 'shared'])
        key_layout.addWidget(self.key_combo)
        options_layout.addLayout(key_layout)
        pkg_layout = QHBoxLayout()
        pkg_layout.addWidget(QLabel("Forced Package ID (127 = auto):"))
        self.package_id_spin = QSpinBox()
        self.package_id_spin.setRange(1, 127)
        self.package_id_spin.setValue(127)
        pkg_layout.addWidget(self.package_id_spin)
        options_layout.addLayout(pkg_layout)
        options_group.setLayout(options_layout)
        scroll_layout.addWidget(options_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_rebuild = QPushButton("🛠 Xây dựng lại")
        btn_rebuild.clicked.connect(self.start_rebuild)
        btn_rebuild.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 10px;")
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_rebuild)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        if self.preselected_action:
            self.select_action(self.preselected_action)

    def build_options_tree(self):
        root = QTreeWidgetItem(self.tree, ["📦 Chọn kiểu xây dựng lại"])
        root.setExpanded(True)

        multi = QTreeWidgetItem(root, ["📦 Apk với Multi-patch"])
        multi.setData(0, Qt.ItemDataRole.UserRole, "multi_patch")

        license_root = QTreeWidgetItem(root, ["🔑 APK không có Giấy phép Xác minh"])
        QTreeWidgetItem(license_root, ["Chế độ tự động (dex)"]).setData(0, Qt.ItemDataRole.UserRole, "license_auto_dex")
        QTreeWidgetItem(license_root, ["Chế độ tự động"]).setData(0, Qt.ItemDataRole.UserRole, "license_auto")
        QTreeWidgetItem(license_root, ["Chế độ tự động (Đảo ngược)"]).setData(0, Qt.ItemDataRole.UserRole, "license_reverse_auto")
        QTreeWidgetItem(license_root, ["Các bản vá khác (Cực đoan)"]).setData(0, Qt.ItemDataRole.UserRole, "license_extreme")

        ads_root = QTreeWidgetItem(root, ["🚫 APK không có Google Ads"])
        QTreeWidgetItem(ads_root, ["Xoá liên kết"]).setData(0, Qt.ItemDataRole.UserRole, "ads_remove_links")
        QTreeWidgetItem(ads_root, ["Làm hỏng nhận quảng cáo"]).setData(0, Qt.ItemDataRole.UserRole, "ads_offline")

        iap_root = QTreeWidgetItem(root, ["💳 Giả lập InApp và LVL"])
        QTreeWidgetItem(iap_root, ["Tái cấu trúc Dex"]).setData(0, Qt.ItemDataRole.UserRole, "iap_dex")
        QTreeWidgetItem(iap_root, ["Máy Chủ Proxy"]).setData(0, Qt.ItemDataRole.UserRole, "iap_proxy")

        QTreeWidgetItem(root, ["⚙️ APK với quyền đã thay đổi"]).setData(0, Qt.ItemDataRole.UserRole, "change_perms")
        QTreeWidgetItem(root, ["✍️ Ký lại APK"]).setData(0, Qt.ItemDataRole.UserRole, "resign")
        QTreeWidgetItem(root, ["🔌 Nhúng AIDL Proxy"]).setData(0, Qt.ItemDataRole.UserRole, "aidl_proxy")

    def on_tree_item_clicked(self, item, column):
        action = item.data(0, Qt.ItemDataRole.UserRole)
        if action:
            self.select_action(action)

    def select_action(self, action):
        self.multi_group.setVisible(False)
        self.iap_mode_group.setVisible(False)
        if action == 'multi_patch':
            self.multi_group.setVisible(True)
        elif action in ['iap_dex', 'iap_proxy']:
            self.iap_mode_group.setVisible(True)
            self.radio_dex.setChecked(action == 'iap_dex')
            self.radio_proxy.setChecked(action == 'iap_proxy')
        self.preselected_action = action

    def get_selected_mode(self):
        if self.preselected_action == 'multi_patch':
            modes = []
            if self.chk_license.isChecked(): modes.append('license')
            if self.chk_license_extreme.isChecked(): modes.append('license_extreme')
            if self.chk_ads.isChecked(): modes.append('ads')
            if self.chk_ads_offline.isChecked(): modes.append('ads_offline')
            if self.chk_iap.isChecked():
                iap_method = 'iap_dex' if self.radio_dex.isChecked() else 'iap_proxy'
                modes.append(iap_method)
            if self.chk_aidl.isChecked(): modes.append('aidl_proxy')
            if self.chk_perms.isChecked(): modes.append('change_perms')
            if self.chk_resign.isChecked(): modes.append('resign')
            if not modes:
                QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất một bản vá.")
                return None
            return 'multi:' + ','.join(modes)
        else:
            if self.preselected_action in ['iap_dex', 'iap_proxy']:
                return 'iap_dex' if self.radio_dex.isChecked() else 'iap_proxy'
            return self.preselected_action

    def get_key_type(self):
        return self.key_combo.currentText()

    def get_forced_package_id(self):
        val = self.package_id_spin.value()
        # Trả về None nếu là 127 (auto) hoặc giá trị không hợp lệ
        if val == 127 or val <= 0:
            return None
        return val

    def start_rebuild(self):
        mode = self.get_selected_mode()
        if not mode:
            return
        self.selected_mode = mode
        self.rebuild_params.emit(mode, self.get_key_type(), self.get_forced_package_id())
        self.accept()