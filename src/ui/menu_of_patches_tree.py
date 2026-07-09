# src/ui/menu_of_patches_tree.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem,
    QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class MenuOfPatchesTreeDialog(QDialog):
    """Menu dạng cây mô phỏng Lucky Patcher."""
    action_requested = pyqtSignal(str, str)  # category, action

    def __init__(self, app_name, package, colors, findings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Menu of Patches - {app_name}")
        self.resize(520, 620)
        self.app_name = app_name
        self.package = package
        self.colors = colors
        self.findings = findings
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Header
        title = QLabel(f"<b style='color:#58a6ff;'>Menu các bản vá cho {self.app_name}</b>")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        layout.addWidget(QLabel(f"Package: {self.package}"))

        # Color indicators
        color_names = {
            'green': '🟢 Có thể tách khỏi Google Play',
            'blue': '🔵 Chứa Google Ads',
            'yellow': '🟡 Có custom patch',
            'purple': '🟣 Ứng dụng hệ thống (boot)',
            'orange': '🟠 Ứng dụng hệ thống',
            'red': '🔴 Không thể patch'
        }
        for c in self.colors:
            if c in color_names:
                layout.addWidget(QLabel(color_names[c]))

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.build_tree()
        layout.addWidget(self.tree)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def build_tree(self):
        """Xây dựng cây menu."""
        # Root: Menu of Patches
        root = QTreeWidgetItem(self.tree, ["📋 Menu of Patches"])
        root.setExpanded(True)

        # 1. Create Modified APK File
        modified_apk = QTreeWidgetItem(root, ["🔧 Create Modified APK File"])
        modified_apk.setToolTip(0, "Tạo file APK đã chỉnh sửa với các bản vá")

        # Sub-menu cho Create Modified APK
        self.add_item(modified_apk, "📦 Apk với Multi-patch", "multi_patch",
                      "Kết hợp nhiều bản vá trong một lần rebuild")

        license_menu = QTreeWidgetItem(modified_apk, ["🔑 APK không có Giấy phép Xác minh"])
        self.add_item(license_menu, "Chế độ tự động (dex)", "license_auto_dex", "Số lượng bản vá tối thiểu")
        self.add_item(license_menu, "Chế độ tự động", "license_auto", "Phù hợp hầu hết ứng dụng")
        self.add_item(license_menu, "Chế độ tự động (Đảo ngược)", "license_reverse_auto", "Khác biệt so với Auto mode")
        self.add_item(license_menu, "Các bản vá khác (Chế độ đặc biệt)", "license_extreme", "Có thể gây mất ổn định")
        self.add_item(license_menu, "Chế độ tự động (SamsungApps)", "license_samsung", "Cho ứng dụng từ Samsung")

        ads_menu = QTreeWidgetItem(modified_apk, ["🚫 APK không có Google Ads"])
        self.add_item(ads_menu, "Xoá liên kết khỏi APK", "ads_remove_links", "Dùng AdsBlockList")
        self.add_item(ads_menu, "Làm hỏng phần nhận quảng cáo", "ads_offline", "Phá vỡ cơ chế nhận Ads")
        self.add_item(ads_menu, "Tạo ngoại tuyến đầy đủ", "ads_full_offline", "Làm ứng dụng ngoại tuyến")

        iap_menu = QTreeWidgetItem(modified_apk, ["💳 APK đã xây dựng lại cho giả lập InApp và LVL"])
        self.add_item(iap_menu, "Tái cấu trúc Dex", "iap_dex", "Không cần proxy server")
        self.add_item(iap_menu, "Máy Chủ Proxy", "iap_proxy", "Dùng PC làm fake billing server")

        self.add_item(modified_apk, "⚙️ APK với quyền và hoạt động đã được thay đổi", "change_perms",
                      "Sửa permissions và components")
        self.add_item(modified_apk, "✍️ Ký lại với phép kiểm tra chữ ký", "resign",
                      "Ký lại APK với chữ ký mới")

        # 2. Remove License Verification
        self.add_item(root, "🔑 Remove License Verification", "remove_license",
                      "Vô hiệu hóa kiểm tra giấy phép Google")

        # 3. Remove Google Ads
        self.add_item(root, "🚫 Remove Google Ads", "remove_ads",
                      "Loại bỏ quảng cáo Google")

        # 4. Custom Patch
        self.add_item(root, "📄 Custom Patch", "apply_custom_patch",
                      "Áp dụng bản vá tùy chỉnh (.txt/.lpzip)")

        # 5. Change Permissions
        self.add_item(root, "⚙️ Change Permissions", "change_perms",
                      "Thay đổi quyền ứng dụng")

        # 6. Backup App
        self.add_item(root, "💾 Backup App", "backup_app",
                      "Sao lưu ứng dụng và dữ liệu")

    def add_item(self, parent, text, action, tooltip=""):
        """Thêm một mục vào cây."""
        item = QTreeWidgetItem(parent, [text])
        item.setData(0, Qt.ItemDataRole.UserRole, action)
        if tooltip:
            item.setToolTip(0, tooltip)
        # Bold cho các mục chính
        if parent.text(0).startswith("📋"):
            item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
        return item

    def on_item_double_clicked(self, item, column):
        action = item.data(0, Qt.ItemDataRole.UserRole)
        if action:
            # Nếu là một trong các chế độ rebuild, mở dialog rebuild
            if action in ['multi_patch', 'license_auto_dex', 'license_auto', 
                          'license_reverse_auto', 'license_extreme', 'license_samsung',
                          'ads_remove_links', 'ads_offline', 'ads_full_offline',
                          'iap_dex', 'iap_proxy', 'change_perms', 'resign']:
                self.action_requested.emit('open_rebuild', action)
            else:
                # Gọi trực tiếp pipeline
                self.action_requested.emit('direct_action', action)
            self.accept()