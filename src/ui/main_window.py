import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QSplitter, QToolBar, QStatusBar,
    QComboBox, QLineEdit, QStackedWidget, QFrame, QProgressBar, QInputDialog,
    QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont

from .app_list_widget import AppListWidget
from .toolbox_menu import ToolboxMenu
from .log_widget import LogWidget
from .menu_of_patches import MenuOfPatchesDialog
from .rebuild_dialog import RebuildDialog
from .apk_detail_widget import APKDetailWidget
from .switches_panel import SwitchesPanel
from scanner.installed_apps import get_installed_apps
from scanner.app_classifier import AppDeepAnalyzer
from patcher.android_system_patcher import AndroidSystemPatcher
from patcher.iap_manager import IAPManager
from core.pipeline_signals import PipelineSignals
from core.apk_downloader import APKDownloader


class MainWindow(QMainWindow):
    analysis_complete = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LP-PC Suite v4 – Professional Modding Tool")
        self.resize(1200, 800)
        self.apk_path = None
        self.iap_manager = IAPManager()
        self.system_patcher = AndroidSystemPatcher()
        self.initUI()
        self.load_device_apps()

    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== SIDEBAR ==========
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 20, 8, 20)
        sidebar_layout.setSpacing(8)

        logo = QLabel("🛠 LP-PC Suite")
        logo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo.setStyleSheet("color: #58a6ff; padding: 12px 8px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(16)

        self.btn_apps = QPushButton("📱 Installed Apps")
        self.btn_apps.setCheckable(True)
        self.btn_apps.setChecked(True)
        self.btn_detail = QPushButton("🔍 APK Detail")
        self.btn_detail.setCheckable(True)
        self.btn_tools = QPushButton("⚙️ Tools")
        self.btn_tools.setCheckable(True)

        sidebar_layout.addWidget(self.btn_apps)
        sidebar_layout.addWidget(self.btn_detail)
        sidebar_layout.addWidget(self.btn_tools)
        sidebar_layout.addStretch()

        version_label = QLabel("v4.0.0")
        version_label.setStyleSheet("color: #484f58; font-size: 11px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        # ========== RIGHT CONTENT ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search apps...")
        self.search_edit.textChanged.connect(self.filter_apps)
        toolbar.addWidget(self.search_edit)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "License check", "Ads", "Custom patch", "System"])
        self.filter_combo.currentTextChanged.connect(self.filter_apps)
        toolbar.addWidget(self.filter_combo)
        toolbar.addSeparator()
        btn_browse = QPushButton("📁 Browse APK")
        btn_browse.clicked.connect(self.browse_apk_manual)
        toolbar.addWidget(btn_browse)
        btn_download = QPushButton("📥 Download APK")
        btn_download.clicked.connect(self.download_apk_dialog)
        toolbar.addWidget(btn_download)
        btn_workspace = QPushButton("📂 Workspace")
        btn_workspace.clicked.connect(self.open_workspace)
        toolbar.addWidget(btn_workspace)
        right_layout.addWidget(toolbar)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # Switches panel
        self.switches_panel = SwitchesPanel(self.iap_manager)
        right_layout.addWidget(self.switches_panel)

        # Stacked widget
        self.stacked = QStackedWidget()

        app_page = QWidget()
        app_layout = QVBoxLayout(app_page)
        app_layout.setContentsMargins(0, 0, 0, 0)
        self.app_list = AppListWidget()
        self.app_list.app_context_menu_requested.connect(self.open_menu_of_patches)
        self.app_list.itemDoubleClicked.connect(self.on_app_double_click)
        app_layout.addWidget(self.app_list)
        self.stacked.addWidget(app_page)

        detail_page = QWidget()
        detail_layout = QVBoxLayout(detail_page)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.apk_detail = APKDetailWidget()
        self.apk_detail.patch_action_requested.connect(self.handle_detail_action)
        self.apk_detail.rebuild_requested.connect(self.open_rebuild_dialog)
        detail_layout.addWidget(self.apk_detail)
        self.stacked.addWidget(detail_page)

        tools_page = QWidget()
        tools_layout = QVBoxLayout(tools_page)
        tools_layout.addWidget(QLabel("Tools & System Patches – Coming Soon"))
        self.stacked.addWidget(tools_page)

        right_layout.addWidget(self.stacked, 1)

        self.log = LogWidget()
        right_layout.addWidget(self.log, 1)

        main_layout.addWidget(right_widget, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Kết nối sidebar
        self.btn_apps.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        self.btn_detail.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        self.btn_tools.clicked.connect(lambda: self.stacked.setCurrentIndex(2))

        # Kết nối signal
        self.analysis_complete.connect(self.update_apk_detail)

    def update_apk_detail(self, result):
        self.apk_detail.populate(result)

    def browse_apk_manual(self):
        file, _ = QFileDialog.getOpenFileName(self, "Choose APK", "", "APK files (*.apk)")
        if file:
            self.apk_path = file
            self.status_bar.showMessage(f"Loaded: {Path(file).name}")

            self.apk_detail.clear()
            basic_info = {
                'findings': [],
                'summary': {
                    'app_name': Path(file).stem,
                    'package': 'Đang phân tích...',
                    'version': '',
                    'apk_path': file,
                    'size': Path(file).stat().st_size
                },
                'colors': ['white']
            }
            self.apk_detail.populate(basic_info)
            self.btn_detail.setChecked(True)
            self.stacked.setCurrentIndex(1)

            import threading
            def analyze():
                try:
                    analyzer = AppDeepAnalyzer(file)
                    findings = analyzer.analyze()
                    summary = analyzer.get_summary()
                    colors = analyzer.get_colors()
                    result = {'findings': findings, 'summary': summary, 'colors': colors}
                    self.analysis_complete.emit(result)
                    color_names = {'green': 'License', 'blue': 'Ads', 'yellow': 'Custom Patch',
                                   'purple': 'System Boot', 'orange': 'System', 'red': 'Protected'}
                    self.log.append_log(f"Detected: {', '.join([color_names.get(c, c) for c in colors])}")
                    for f in findings:
                        self.log.append_log(f"  - {f['title']}: {f['description']}")
                    # Gợi ý thông minh sau khi phân tích
                    self._show_smart_suggestions(findings)
                except Exception as e:
                    self.log.append_log(f"Analysis error: {e}")
            threading.Thread(target=analyze, daemon=True).start()

    def _show_smart_suggestions(self, findings):
        has_iap = any(f['type'] == 'iap' for f in findings)
        has_license = any(f['type'] == 'license' for f in findings)
        has_ads = any(f['type'] == 'ads' for f in findings)

        suggestions = []
        if has_iap:
            suggestions.append("💳 Phát hiện In-App Purchase. Bạn có muốn áp dụng chế độ 'IAP Im lặng' (Dex mode) để nhận vật phẩm miễn phí không?")
        if has_license:
            suggestions.append("🔑 Phát hiện License Check. Bạn có muốn gỡ bỏ để dùng app miễn phí không?")
        if has_ads:
            suggestions.append("🚫 Phát hiện Quảng cáo. Bạn có muốn xóa toàn bộ quảng cáo không?")

        if suggestions:
            msg = QMessageBox(self)
            msg.setWindowTitle("Gợi ý thông minh")
            msg.setText("Chúng tôi đã phát hiện một số đặc điểm trong APK của bạn:")
            msg.setInformativeText("\n".join(suggestions))
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            result = msg.exec()

            if result == QMessageBox.StandardButton.Yes:
                modes = []
                if has_iap: modes.append('iap:dex')
                if has_license: modes.append('license:auto')
                if has_ads: modes.append('ads:full_offline')
                if modes:
                    self.run_patch_pipeline(','.join(modes))

    def open_workspace(self):
        workspace = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace', 'decompiled')
        if os.path.exists(workspace):
            import subprocess
            if sys.platform == 'win32':
                os.startfile(workspace)
            elif sys.platform == 'darwin':
                subprocess.run(['open', workspace])
            else:
                subprocess.run(['xdg-open', workspace])

    def open_menu_of_patches(self, pkg, app_name, colors, findings=None):
        if findings is None:
            findings = []
        dlg = MenuOfPatchesDialog(app_name, pkg, colors, findings, self)
        dlg.exec()

    def on_app_double_click(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.open_menu_of_patches(data['package'], data['name'], data['colors'], data.get('findings', []))

    def open_rebuild_dialog(self):
        if not self.apk_path:
            QMessageBox.warning(self, "No APK", "Browse an APK first.")
            return
        dlg = RebuildDialog(Path(self.apk_path).stem, "unknown", parent=self)
        dlg.rebuild_requested.connect(self.run_patch_pipeline)
        dlg.exec()

    def handle_detail_action(self, action):
        if not self.apk_path:
            QMessageBox.warning(self, "No APK", "Browse an APK first.")
            return
        if action == 'open_rebuild':
            self.open_rebuild_dialog()
            return
        mode_map = {'remove_license': 'license', 'remove_ads': 'ads', 'iap_emulation': 'iap_dex', 'apply_custom_patch': 'custom'}
        mode = mode_map.get(action)
        if mode:
            if mode == 'custom':
                patch_file, _ = QFileDialog.getOpenFileName(self, "Select Custom Patch", "", "Patch files (*.txt *.lpzip)")
                if not patch_file:
                    return
                os.environ['LP_CUSTOM_PATCH'] = patch_file
            self.run_patch_pipeline(mode)

    def run_patch_pipeline(self, mode, key_type='testkey', forced_package_id=None, fast_mode=True, use_gda=True):
        if forced_package_id is not None and (not isinstance(forced_package_id, int) or forced_package_id <= 0):
            forced_package_id = None

        signals = PipelineSignals()
        signals.progress.connect(self.update_progress)
        signals.status.connect(self.log.append_log)
        signals.finished.connect(self.on_pipeline_finished)

        from main import run_pipeline
        import threading

        def patch():
            success, out, _ = run_pipeline(
                self.apk_path, mode=mode, log_callback=self.log.append_log,
                key_type=key_type, forced_package_id=forced_package_id,
                fast_mode=fast_mode, use_gda=use_gda,
                apktool_jobs=4, apktool_memory="4096m",
                signals=signals
            )
            signals.finished.emit(success, out if out else "")

        threading.Thread(target=patch, daemon=True).start()

    def update_progress(self, current, total):
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_pipeline_finished(self, success, output):
        self.progress_bar.setVisible(False)
        if success:
            self.log.append_log(f"[✔] Done! File: {output}")
        else:
            self.log.append_log("[!] Patch failed.")

    def load_device_apps(self):
        try:
            apps = get_installed_apps()
            for app in apps:
                colors = ['white']
                if 'google' in app['package']:
                    colors = ['blue']
                self.app_list.add_app(app['name'], app['package'], colors)
        except Exception as e:
            self.log.append_log(f"Could not load apps: {e}")
            sample = [("Example Game", "com.example.game", ["green", "blue"])]
            for name, pkg, cols in sample:
                self.app_list.add_app(name, pkg, cols)

    def filter_apps(self):
        text = self.search_edit.text().lower()
        filt = self.filter_combo.currentText()
        self.app_list.filter(text, filt)

    def download_apk_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Tải APK")
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel("<b>Tải APK từ nhiều nguồn</b>"))
        layout.addWidget(QLabel("Nhập package name hoặc URL Google Play:"))

        pkg_layout = QHBoxLayout()
        pkg_input = QLineEdit()
        pkg_input.setPlaceholderText("com.example.app")
        pkg_layout.addWidget(pkg_input)
        btn_search = QPushButton("🔍 Tìm kiếm")
        btn_search.clicked.connect(lambda: self._search_google_play(dlg, pkg_input))
        pkg_layout.addWidget(btn_search)
        layout.addLayout(pkg_layout)

        layout.addWidget(QLabel("Nguồn tải:"))
        source_combo = QComboBox()
        source_combo.addItems(['APKPure', 'APKMody', 'Uptodown', 'APKPure (via Google Play info)'])
        layout.addWidget(source_combo)

        layout.addWidget(QLabel("Hoặc dán URL trực tiếp (.apk / .xapk):"))
        url_input = QLineEdit()
        url_input.setPlaceholderText("https://example.com/app.apk")
        layout.addWidget(url_input)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setVisible(False)
        layout.addWidget(info_text)

        btn_layout = QHBoxLayout()
        btn_download = QPushButton("📥 Tải xuống")
        btn_download.clicked.connect(lambda: self._execute_download(
            dlg, pkg_input.text().strip(), url_input.text().strip(),
            source_combo.currentText()
        ))
        btn_download.setStyleSheet("background-color: #238636; color: white; font-weight: bold; padding: 8px 16px;")
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(dlg.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_download)
        layout.addLayout(btn_layout)

        dlg.exec()

    def _search_google_play(self, dialog, pkg_input):
        package = pkg_input.text().strip()
        if not package:
            return
        downloader = APKDownloader(log_callback=self.log.append_log)
        info = downloader.get_google_play_app_info(package)
        info_text = dialog.findChild(QTextEdit)
        if info:
            info_text.setVisible(True)
            info_text.setText(
                f"Tên: {info['title']}\n"
                f"Package: {info['package']}\n"
                f"Phiên bản: {info['version']}\n"
                f"Kích thước: {info.get('size', 'N/A')}\n"
                f"Lượt cài: {info.get('installs', 'N/A')}\n"
                f"Đánh giá: {info.get('score', 'N/A')}\n"
                f"Mô tả: {info.get('description', 'N/A')}"
            )
        else:
            info_text.setVisible(True)
            info_text.setText("Không tìm thấy thông tin ứng dụng.")

    def _execute_download(self, dialog, package, direct_url, source):
        if not package and not direct_url:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập package name hoặc URL.")
            return

        downloader = APKDownloader(log_callback=self.log.append_log)
        dialog.accept()

        def download():
            try:
                apk_path = None
                if direct_url:
                    apk_path = downloader.download_from_direct_url(direct_url)
                elif source == 'APKPure':
                    apk_path = downloader.download_from_apkpure(package)
                elif source == 'APKMody':
                    apk_path = downloader.download_from_apkmody(package)
                elif source == 'Uptodown':
                    apk_path = downloader.download_from_uptodown(package)
                elif source == 'APKPure (via Google Play info)':
                    self.log.append_log("[i] Google Play Scraper is for info only. Downloading via APKPure...")
                    apk_path = downloader.download_from_apkpure(package)
                else:
                    apk_path = downloader.download_from_apkpure(package)

                if apk_path:
                    if apk_path.endswith('.xapk'):
                        self.log.append_log("[*] XAPK detected, merging...")
                        apk_path = downloader.process_xapk(apk_path)
                    self.apk_path = apk_path
                    self.status_bar.showMessage(f"Downloaded: {Path(apk_path).name}")
                    self.browse_apk_manual()
                else:
                    QMessageBox.warning(self, "Download Failed", "Không thể tải APK. Vui lòng thử nguồn khác.")
            except Exception as e:
                QMessageBox.critical(self, "Download Error", str(e))

        import threading
        threading.Thread(target=download, daemon=True).start()

    def closeEvent(self, event):
        event.accept()