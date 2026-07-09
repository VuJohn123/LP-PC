from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGroupBox, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class APKDetailWidget(QWidget):
    patch_action_requested = pyqtSignal(str)
    rebuild_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("apkDetailWidget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)

    def clear(self):
        """Xóa toàn bộ nội dung hiện tại."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def populate(self, analyzer_result):
        self.clear()
        findings = analyzer_result.get('findings', [])
        summary = analyzer_result.get('summary', {})

        # ----- HEADER -----
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        icon = QLabel("📱")
        icon.setFont(QFont("Segoe UI", 36))
        header_layout.addWidget(icon)

        info_layout = QVBoxLayout()
        name = QLabel(summary.get('app_name', 'Unknown'))
        name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name.setStyleSheet("color: #f0f6fc;")
        info_layout.addWidget(name)

        pkg = QLabel(f"Package: {summary.get('package', 'N/A')}")
        pkg.setStyleSheet("color: #8b949e; font-size: 12px;")
        pkg.setWordWrap(True)
        info_layout.addWidget(pkg)

        ver = QLabel(f"Version: {summary.get('version', 'N/A')} | Size: {self._format_size(summary.get('size', 0))}")
        ver.setStyleSheet("color: #6e7681; font-size: 11px;")
        info_layout.addWidget(ver)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        self.content_layout.addWidget(header_widget)

        # ----- REBUILD BUTTON -----
        rebuild_btn = QPushButton("🔨 Tạo tệp tin APK đã sửa (Rebuild)")
        rebuild_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 12px; font-size: 14px;")
        rebuild_btn.clicked.connect(lambda: self.rebuild_requested.emit())
        self.content_layout.addWidget(rebuild_btn)

        # ----- COLOR BAR -----
        colors = analyzer_result.get('colors', ['white'])
        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_map = {
            'green': ('🟢 License', '#238636'),
            'yellow': ('🟡 Custom Patch', '#d29922'),
            'blue': ('🔵 Ads', '#1f6feb'),
            'purple': ('🟣 System (Boot)', '#8957e5'),
            'orange': ('🟠 System App', '#d29922'),
            'red': ('🔴 Protected', '#da3633'),
            'white': ('⚪ No special', '#8b949e')
        }
        for c in colors:
            text, clr = color_map.get(c, ('', '#8b949e'))
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {clr}; font-weight: bold; margin-right: 12px;")
            color_layout.addWidget(lbl)
        color_layout.addStretch()
        self.content_layout.addWidget(color_widget)

        # ----- FEATURES TABLE -----
        feat_group = QGroupBox("🔍 Detected Features")
        feat_layout = QGridLayout(feat_group)
        feat_layout.setVerticalSpacing(12)
        feat_layout.setHorizontalSpacing(16)

        row = 0
        for f in findings:
            icon_lbl = QLabel()
            if f.get('color') == 'green': icon_lbl.setText("🟢")
            elif f.get('color') == 'blue': icon_lbl.setText("🔵")
            elif f.get('color') == 'yellow': icon_lbl.setText("🟡")
            elif f.get('color') == 'purple': icon_lbl.setText("🟣")
            elif f.get('color') == 'orange': icon_lbl.setText("🟠")
            elif f.get('color') == 'red': icon_lbl.setText("🔴")
            else: icon_lbl.setText("⚪")
            feat_layout.addWidget(icon_lbl, row, 0)

            title = QLabel(f.get('title', ''))
            title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            title.setStyleSheet("color: #f0f6fc;")
            title.setWordWrap(True)
            feat_layout.addWidget(title, row, 1)

            desc = QLabel(f.get('description', ''))
            desc.setStyleSheet("color: #8b949e; font-size: 11px;")
            desc.setWordWrap(True)
            desc.setMinimumWidth(250)
            feat_layout.addWidget(desc, row, 2)

            # Action button hoặc placeholder
            btn = self._create_action_button(f) if f.get('action') else None
            if btn is None:
                btn = QLabel("")
            feat_layout.addWidget(btn, row, 3)

            row += 1

        self.content_layout.addWidget(feat_group)

        # ----- QUICK ACTIONS -----
        action_items = [f for f in findings if f.get('action')]
        if action_items:
            act_group = QGroupBox("🛠 Quick Actions")
            act_layout = QVBoxLayout(act_group)
            act_layout.setSpacing(10)
            for f in action_items:
                btn = self._create_action_button(f)
                if btn is not None:
                    act_layout.addWidget(btn)
            self.content_layout.addWidget(act_group)

        self.content_layout.addStretch()

    def _create_action_button(self, finding):
        action_map = {
            'remove_license': ('Remove License Verification', 'green'),
            'remove_ads': ('Remove Google Ads', 'blue'),
            'iap_emulation': ('IAP Emulation (Create Modified APK)', 'orange'),
            'apply_custom_patch': ('Apply Custom Patch', 'yellow'),
        }
        info = action_map.get(finding.get('action'))
        if not info:
            return None

        btn = QPushButton(info[0])
        btn.setProperty('cssClass', info[1])
        btn.setStyleSheet("")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(36)
        btn.setMaximumWidth(350)
        btn.clicked.connect(lambda checked, f=finding: self.patch_action_requested.emit(f['action']))
        return btn

    def _format_size(self, size_bytes):
        if size_bytes == 0:
            return '0 B'
        sizes = ['B', 'KB', 'MB', 'GB']
        i = 0
        size = size_bytes
        while size >= 1024 and i < len(sizes)-1:
            size /= 1024.0
            i += 1
        return f"{size:.1f} {sizes[i]}"