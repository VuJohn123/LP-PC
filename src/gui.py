# src/gui_v2.py
import sys, os, json, subprocess, tempfile
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QCheckBox, QTextEdit, QProgressBar,
    QGroupBox, QLineEdit, QMessageBox, QRadioButton, QButtonGroup,
    QListWidget, QListWidgetItem, QAbstractItemView, QSplitter,
    QFrame, QScrollArea, QTabWidget, QComboBox, QSlider, QSpinBox,
    QDialog, QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QMenu,
    QToolBar, QStatusBar, QStyleFactory, QStyle, QGridLayout
)
from PyQt6.QtCore import QProcess, Qt, pyqtSignal, QObject, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette, QBrush
from pathlib import Path
import time

# Import các module hiện có
from scanner.app_classifier import AppClassifier
from core.apk_utils import decompile_apk, recompile_apk, sign_apk
from core.device_bridge import install_apk, setup_reverse_port


class ColorCodedAppItem(QWidget):
    """Widget hiển thị một ứng dụng với mã màu."""
    def __init__(self, app_name, package_name, colors, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Color indicator
        self.color_label = QLabel()
        self.color_label.setFixedSize(20, 20)
        color_map = {
            'green': '#4CAF50', 'yellow': '#FFC107', 'blue': '#2196F3',
            'purple': '#9C27B0', 'orange': '#FF9800', 'red': '#F44336',
            'white': '#E0E0E0'
        }
        primary_color = colors[0] if colors else 'white'
        self.color_label.setStyleSheet(
            f"background-color: {color_map.get(primary_color, '#E0E0E0')}; "
            f"border-radius: 10px; border: 1px solid #999;"
        )
        layout.addWidget(self.color_label)

        # App name
        name_label = QLabel(app_name)
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(name_label)

        # Package name
        pkg_label = QLabel(f"({package_name})")
        pkg_label.setFont(QFont("Arial", 8))
        pkg_label.setStyleSheet("color: gray;")
        layout.addWidget(pkg_label)

        layout.addStretch()
        self.setLayout(layout)
        self.setToolTip(f"Colors: {', '.join(colors)}")

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Open Menu of Patches", lambda: print("Menu of Patches"))
        menu.addAction("Create Modified APK", lambda: print("Create Modified APK"))
        menu.addAction("Remove License Verification", lambda: print("LVL"))
        menu.addAction("Remove Google Ads", lambda: print("Ads"))
        menu.addAction("Custom Patch", lambda: print("Custom Patch"))
        menu.addSeparator()
        menu.addAction("App Info", lambda: print("App Info"))
        menu.addAction("Launch App", lambda: print("Launch"))
        menu.exec(event.globalPos())


class ToolboxMenu(QMenu):
    """Menu Toolbox mô phỏng LP gốc."""
    def __init__(self, parent=None):
        super().__init__("Toolbox", parent)
        self._build_menu()

    def _build_menu(self):
        # System Patches
        system_menu = self.addMenu("Patch on Android")
        system_menu.addAction("Signature Verification always True")
        system_menu.addAction("Disable APK Signature Verification")
        system_menu.addAction("Disable Zip Signature Verification")
        system_menu.addSeparator()
        system_menu.addAction("Apply Selected Patches")

        self.addSeparator()

        # Modded Play Store
        self.addAction("Install Modded Google Play Store")

        # Xposed settings
        xposed_menu = self.addMenu("Xposed Settings")
        xposed_menu.addAction("Enable Xposed Module")
        xposed_menu.addAction("Support IAP & LVL Emulation (4th option)")

        self.addSeparator()

        # Backup & Restore
        self.addAction("Backup Apps")
        self.addAction("Restore Apps")

        # Tools
        tools_menu = self.addMenu("Tools")
        tools_menu.addAction("Install SuperSU")
        tools_menu.addAction("Install/Update BusyBox")
        tools_menu.addAction("Clear Dalvik Cache")
        tools_menu.addAction("Move App to /system/app/")

        self.addSeparator()

        # Settings
        self.addAction("Disable Google Billing Emulation")
        self.addAction("Change Directory")
        self.addAction("Download Custom Patches")


class MenuOfPatchesDialog(QDialog):
    """Dialog mô phỏng Menu of Patches của LP."""
    def __init__(self, app_name, package_name, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Menu of Patches - {app_name}")
        self.resize(400, 500)
        self.app_name = app_name
        self.package_name = package_name
        self.colors = colors
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # App info header
        header = QLabel(f"App: {self.app_name}\nPackage: {self.package_name}")
        header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(header)

        # Color indicators
        color_names = {
            'green': '🟢 License check detected',
            'blue': '🔵 Google Ads detected',
            'purple': '🟣 System app',
            'yellow': '🟡 Custom patch available',
            'red': '🔴 Cannot patch'
        }
        for c in self.colors:
            if c in color_names:
                layout.addWidget(QLabel(color_names[c]))

        layout.addWidget(QFrame().setFrameShape(QFrame.Shape.HLine))

        # Patch options
        patches_group = QGroupBox("Available Patches")
        patches_layout = QVBoxLayout()

        # Create Modified APK
        self.btn_modified_apk = QPushButton("Create Modified APK File")
        self.btn_modified_apk.clicked.connect(self._on_create_modified_apk)
        patches_layout.addWidget(self.btn_modified_apk)

        # Remove License Verification
        self.btn_lvl = QPushButton("Remove License Verification")
        self.btn_lvl.clicked.connect(self._on_remove_lvl)
        patches_layout.addWidget(self.btn_lvl)

        # Remove Google Ads
        self.btn_ads = QPushButton("Remove Google Ads")
        self.btn_ads.clicked.connect(self._on_remove_ads)
        patches_layout.addWidget(self.btn_ads)

        # Custom Patch
        self.btn_custom = QPushButton("Custom Patch")
        self.btn_custom.clicked.connect(self._on_custom_patch)
        patches_layout.addWidget(self.btn_custom)

        # Change Permissions
        self.btn_perms = QPushButton("Change Permissions")
        self.btn_perms.clicked.connect(self._on_change_perms)
        patches_layout.addWidget(self.btn_perms)

        patches_group.setLayout(patches_layout)
        layout.addWidget(patches_group)

        # Other actions
        other_group = QGroupBox("Other Actions")
        other_layout = QVBoxLayout()
        self.btn_backup = QPushButton("Backup App")
        self.btn_restore = QPushButton("Restore App")
        self.btn_launch = QPushButton("Launch App")
        self.btn_info = QPushButton("App Info")
        other_layout.addWidget(self.btn_backup)
        other_layout.addWidget(self.btn_restore)
        other_layout.addWidget(self.btn_launch)
        other_layout.addWidget(self.btn_info)
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)

    def _on_create_modified_apk(self):
        dialog = RebuildAPKDialog(self.app_name, self.package_name, self)
        dialog.exec()

    def _on_remove_lvl(self):
        # Mở dialog chọn mode
        msg = QMessageBox(self)
        msg.setWindowTitle("Remove License Verification")
        msg.setText("Select patching mode:")
        btn_auto = msg.addButton("Auto Mode", QMessageBox.ButtonRole.ActionRole)
        btn_reverse = msg.addButton("Reverse Auto", QMessageBox.ButtonRole.ActionRole)
        btn_extreme = msg.addButton("Extreme Auto", QMessageBox.ButtonRole.ActionRole)
        btn_manual = msg.addButton("Manual", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

    def _on_remove_ads(self):
        QMessageBox.information(self, "Remove Google Ads", "Select 'APK without Google Ads' to rebuild")

    def _on_custom_patch(self):
        file, _ = QFileDialog.getOpenFileName(self, "Chọn custom patch", "", "Patch files (*.txt *.lpzip)")
        if file:
            QMessageBox.information(self, "Custom Patch", f"Applying: {file}")

    def _on_change_perms(self):
        QMessageBox.information(self, "Change Permissions", "Permission editor coming soon")


class RebuildAPKDialog(QDialog):
    """Dialog mô phỏng Create Modified APK của LP."""
    def __init__(self, app_name, package_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Create Modified APK - {app_name}")
        self.resize(500, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Chọn loại rebuild
        rebuild_group = QGroupBox("Rebuild Type")
        rebuild_layout = QVBoxLayout()
        self.radio_iap_proxy = QRadioButton("Support patch for InApp & LVL emulation (Proxy Server)")
        self.radio_iap_dex = QRadioButton("Support patch for InApp & LVL emulation (Reassembly Dex)")
        self.radio_ads = QRadioButton("APK without Google Ads")
        self.radio_custom = QRadioButton("Custom Patch")
        self.radio_iap_proxy.setChecked(True)
        rebuild_layout.addWidget(self.radio_iap_proxy)
        rebuild_layout.addWidget(self.radio_iap_dex)
        rebuild_layout.addWidget(self.radio_ads)
        rebuild_layout.addWidget(self.radio_custom)
        rebuild_group.setLayout(rebuild_layout)
        layout.addWidget(rebuild_group)

        # Options for IAP
        options_group = QGroupBox("IAP Options")
        options_layout = QVBoxLayout()
        self.chk_auto = QCheckBox("Auto mode")
        self.chk_reverse = QCheckBox("Reverse auto mode")
        self.chk_extreme = QCheckBox("Extreme auto mode")
        self.chk_auto.setChecked(True)
        options_layout.addWidget(self.chk_auto)
        options_layout.addWidget(self.chk_reverse)
        options_layout.addWidget(self.chk_extreme)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Output directory
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit("/sdcard/LuckyPatcher/Modified/")
        output_layout.addWidget(QLabel("Save to:"))
        output_layout.addWidget(self.output_edit)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_rebuild = QPushButton("Rebuild The App")
        btn_rebuild.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 14px;")
        btn_rebuild.clicked.connect(self._on_rebuild)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_rebuild)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _on_rebuild(self):
        if self.radio_iap_proxy.isChecked():
            mode = 'iap_proxy'
        elif self.radio_iap_dex.isChecked():
            mode = 'iap_dex'
        elif self.radio_ads.isChecked():
            mode = 'ads'
        elif self.radio_custom.isChecked():
            mode = 'custom'
        else:
            mode = 'all'
        QMessageBox.information(self, "Rebuild", f"Starting rebuild with mode: {mode}")
        self.accept()


class LPPCSuiteV2(QMainWindow):
    """GUI chính của LP-PC Suite v2 - Mô phỏng Lucky Patcher."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LP-PC Suite v2.1 – Lucky Patcher for PC")
        self.resize(1000, 700)
        self.apk_path = None
        self.app_list = []  # Danh sách app đã phân tích
        self.log_emitter = LogEmitter()
        self.log_emitter.signal.connect(self.append_log)
        self.initUI()
        self._load_sample_apps()  # Load app mẫu

    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ---- Toolbar ----
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        # Menu hamburger
        btn_menu = QPushButton("☰")
        btn_menu.setFixedSize(40, 40)
        btn_menu.setMenu(self._create_hamburger_menu())
        toolbar.addWidget(btn_menu)
        toolbar.addSeparator()
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search apps...")
        self.search_edit.textChanged.connect(self._filter_apps)
        toolbar.addWidget(self.search_edit)
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "All apps", "License verification", "Google Ads", 
            "Custom patch", "Dalvik cache fix", "No patch found", "Modified"
        ])
        self.filter_combo.currentTextChanged.connect(self._filter_apps)
        toolbar.addWidget(self.filter_combo)
        self.addToolBar(toolbar)

        # ---- Splitter: App list + Log ----
        splitter = QSplitter(Qt.Orientation.Vertical)

        # App list area
        app_group = QGroupBox("Installed Apps")
        app_layout = QVBoxLayout()
        self.app_list_widget = QListWidget()
        self.app_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.app_list_widget.itemDoubleClicked.connect(self._on_app_double_click)
        self.app_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.app_list_widget.customContextMenuRequested.connect(self._on_app_context_menu)
        app_layout.addWidget(self.app_list_widget)
        app_group.setLayout(app_layout)
        splitter.addWidget(app_group)

        # Log area
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        log_layout.addWidget(self.log)
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        log_layout.addWidget(self.progress)
        log_group.setLayout(log_layout)
        splitter.addWidget(log_group)

        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)

        # ---- Bottom menu (giống LP) ----
        bottom_layout = QHBoxLayout()

        # Toolbox button (góc trái dưới)
        self.btn_toolbox = QPushButton("🧰 Toolbox")
        self.btn_toolbox.setMenu(ToolboxMenu(self))
        bottom_layout.addWidget(self.btn_toolbox)

        # Rebuild & Install button
        self.btn_rebuild_install = QPushButton("🔨 Rebuild & Install")
        self.btn_rebuild_install.setStyleSheet(
            "font-size: 14px; padding: 10px; background-color: #4CAF50; color: white;"
        )
        self.btn_rebuild_install.clicked.connect(self._on_rebuild_install)
        bottom_layout.addWidget(self.btn_rebuild_install)

        # Patch button
        self.btn_patch = QPushButton("⚡ Quick Patch & Install")
        self.btn_patch.clicked.connect(self._on_quick_patch)
        bottom_layout.addWidget(self.btn_patch)

        bottom_layout.addStretch()

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")

        main_layout.addLayout(bottom_layout)
        self.setStatusBar(self.status_bar)

    def _create_hamburger_menu(self):
        menu = QMenu()
        menu.addAction("Settings", lambda: print("Settings"))
        menu.addAction("Force set root check", lambda: print("Force root"))
        menu.addAction("Download Custom Patches", lambda: print("Download patches"))
        menu.addAction("Change Directory", lambda: print("Change dir"))
        menu.addSeparator()
        menu.addAction("About", lambda: QMessageBox.about(self, "About", "LP-PC Suite v2.1"))
        return menu

    def _load_sample_apps(self):
        """Load sample apps để demo (sau này thay bằng ADB list)."""
        sample_apps = [
            ("Example Game", "com.example.game", ["green", "blue"]),
            ("Premium App", "com.premium.app", ["green"]),
            ("Ad Blaster", "com.ad.blaster", ["blue"]),
            ("System Service", "com.android.system", ["purple", "orange"]),
            ("Unpatchable", "com.unpatchable.app", ["red"]),
            ("Custom Patched", "com.custom.app", ["yellow"]),
        ]
        for app_name, pkg, colors in sample_apps:
            self._add_app_to_list(app_name, pkg, colors)

    def _add_app_to_list(self, app_name, package_name, colors):
        item = QListWidgetItem(self.app_list_widget)
        widget = ColorCodedAppItem(app_name, package_name, colors)
        item.setSizeHint(widget.sizeHint())
        self.app_list_widget.setItemWidget(item, widget)
        item.setData(Qt.ItemDataRole.UserRole, {
            'app_name': app_name,
            'package_name': package_name,
            'colors': colors
        })
        self.app_list.append(item)

    def _filter_apps(self):
        filter_text = self.filter_combo.currentText()
        search_text = self.search_edit.text().lower()
        for i in range(self.app_list_widget.count()):
            item = self.app_list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            app_name = data['app_name'].lower()
            colors = data['colors']
            visible = True
            # Filter by search
            if search_text and search_text not in app_name:
                visible = False
            # Filter by category
            if filter_text == "License verification" and 'green' not in colors:
                visible = False
            elif filter_text == "Google Ads" and 'blue' not in colors:
                visible = False
            elif filter_text == "Custom patch" and 'yellow' not in colors:
                visible = False
            item.setHidden(not visible)

    def _on_app_double_click(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        dialog = MenuOfPatchesDialog(
            data['app_name'], data['package_name'], data['colors'], self
        )
        dialog.exec()

    def _on_app_context_menu(self, position):
        item = self.app_list_widget.itemAt(position)
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        dialog = MenuOfPatchesDialog(
            data['app_name'], data['package_name'], data['colors'], self
        )
        dialog.exec()

    def _on_rebuild_install(self):
        """Mở dialog rebuild."""
        if not self.apk_path:
            # Chọn APK trước
            self._browse_apk()
            if not self.apk_path:
                return
        dialog = RebuildAPKDialog("Selected APK", "package.name", self)
        dialog.exec()

    def _on_quick_patch(self):
        """Patch nhanh với cấu hình mặc định."""
        if not self.apk_path:
            self._browse_apk()
            if not self.apk_path:
                return
        # Chạy pipeline
        self._run_patch_pipeline(mode='all')

    def _browse_apk(self):
        file, _ = QFileDialog.getOpenFileName(self, "Chọn APK", "", "APK files (*.apk)")
        if file:
            self.apk_path = file
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file)}")
            # Phân tích màu
            try:
                classifier = AppClassifier(file)
                colors = classifier.classify()
                self.append_log(f"App classification: {colors}")
            except Exception as e:
                self.append_log(f"Classification error: {e}")

    def _run_patch_pipeline(self, mode='all'):
        """Chạy pipeline patch."""
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        # Chạy trong QProcess
        self.process = QProcess()
        self.process.setProgram(sys.executable)
        args = [
            os.path.join(os.path.dirname(__file__), "main.py"),
            self.apk_path,
            "--mode", mode
        ]
        self.process.setArguments(args)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_process_finished)
        self.process.start()

    def _on_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.log_emitter.signal.emit(data.strip())

    def _on_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.log_emitter.signal.emit(f"[stderr] {data.strip()}")

    def _on_process_finished(self, exit_code):
        self.progress.setVisible(False)
        if exit_code == 0:
            self.log_emitter.signal.emit("[✔] Patch completed successfully!")
            self.status_bar.showMessage("Patch completed")
        else:
            self.log_emitter.signal.emit(f"[!] Patch failed with exit code {exit_code}")

    def append_log(self, message):
        self.log.append(message)


class LogEmitter(QObject):
    signal = pyqtSignal(str)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    app.setPalette(palette)
    win = LPPCSuiteV2()
    win.show()
    sys.exit(app.exec())