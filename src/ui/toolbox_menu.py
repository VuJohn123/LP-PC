from PyQt6.QtWidgets import QMenu, QInputDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal

class ToolboxMenu(QMenu):
    patch_requested = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__("Toolbox", parent)
        self._build_menu()

    def _build_menu(self):
        patch_menu = self.addMenu("Patch to Android")
        self.sig_always_true = patch_menu.addAction("Signature Verification always True")
        self.sig_always_true.setCheckable(True)
        self.disable_apk_sig = patch_menu.addAction("Disable .apk Signature Verification")
        self.disable_apk_sig.setCheckable(True)
        self.disable_zip_sig = patch_menu.addAction("Disable Zip Signature Verification")
        self.disable_zip_sig.setCheckable(True)
        patch_menu.addSeparator()
        apply_act = patch_menu.addAction("Apply Selected Patches")
        apply_act.triggered.connect(self._apply_patches)
        test_act = patch_menu.addAction("Run Test For Patch")
        test_act.triggered.connect(lambda: self.patch_requested.emit('test_patch', {}))

        self.addSeparator()
        self.addAction("Install Modded Google Play Store", self._install_modded_playstore)
        self.addAction("Force set root check", self._force_root_check)

        xposed_menu = self.addMenu("Xposed Settings")
        xposed_menu.addAction("Support IAP & LVL Emulation (4th option)")
        xposed_menu.addAction("Enable Xposed Module")

        self.addSeparator()
        batch_menu = self.addMenu("Hoạt động hàng loạt")
        batch_menu.addAction("Sao lưu APK của ứng dụng đã chọn", self._batch_backup)
        batch_menu.addAction("Loại bỏ mục mua đã lưu", self._open_iap_manager)

        tools_menu = self.addMenu("Tools")
        tools_menu.addAction("Install SuperSU")
        tools_menu.addAction("Install/Update BusyBox")
        tools_menu.addAction("Clear Dalvik Cache")
        tools_menu.addAction("Move App to /system/app/")

        self.addSeparator()
        self.addAction("Disable Google Billing Emulation")
        self.addAction("Change Directory")
        self.addAction("Download Custom Patches", self._download_patch)

        self.addSeparator()
        self.addAction("📱 Clone App", self._clone_app)

    def _apply_patches(self):
        features = {}
        if self.sig_always_true.isChecked():
            features['signature_verification_always_true'] = True
        if self.disable_apk_sig.isChecked():
            features['disable_apk_signature_verification'] = True
        if self.disable_zip_sig.isChecked():
            features['disable_zip_signature_verification'] = True
        self.patch_requested.emit('system_patch', features)

    def _install_modded_playstore(self):
        QMessageBox.information(self, "Install Modded Play Store", "Tính năng này sẽ tải và cài đặt Google Play đã sửa đổi qua ADB.")

    def _force_root_check(self):
        from core.device_bridge import check_root
        if check_root():
            QMessageBox.information(self, "Root Check", "Thiết bị đã được root.")
        else:
            QMessageBox.warning(self, "Root Check", "Thiết bị chưa root hoặc không có quyền.")

    def _batch_backup(self):
        pass

    def _open_iap_manager(self):
        from ui.iap_manager_dialog import IAPManagerDialog
        main_window = self.parent()
        if main_window and hasattr(main_window, 'iap_manager'):
            dlg = IAPManagerDialog(main_window.iap_manager, self)
            dlg.exec()

    def _download_patch(self):
        patch_name, ok = QInputDialog.getText(self, "Tải Custom Patch", "Nhập tên file patch (vd: com.example.patch.lpzip):")
        if ok and patch_name:
            from patcher.custom_patch_downloader import CustomPatchDownloader
            downloader = CustomPatchDownloader()
            result = downloader.download_patch(patch_name)
            if result:
                QMessageBox.information(self, "Thành công", f"Đã tải về: {result}")
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể tải patch.")

    def _clone_app(self):
        package_name, ok = QInputDialog.getText(self, "Clone App", "Nhập package name mới:")
        if ok and package_name:
            main_window = self.parent()
            if main_window and hasattr(main_window, 'apk_path') and main_window.apk_path:
                from patcher.app_cloner import AppCloner
                cloner = AppCloner(main_window.apk_path, package_name)
                cloned_apk = cloner.clone()
                QMessageBox.information(self, "Thành công", f"Đã clone ra: {cloned_apk}")
            else:
                QMessageBox.warning(self, "Lỗi", "Chưa chọn APK.")