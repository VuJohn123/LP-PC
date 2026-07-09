from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QFrame, QMessageBox
from .license_patch_dialog import LicensePatchDialog
from .ads_patch_dialog import AdsPatchDialog
from .rebuild_dialog import RebuildDialog

class MenuOfPatchesDialog(QDialog):
    def __init__(self, app_name, package, colors, findings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Menu of Patches - {app_name}")
        self.resize(420, 500)
        self.app_name = app_name
        self.package = package
        self.colors = colors
        self.findings = findings
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<b>{self.app_name}</b>"))
        layout.addWidget(QLabel(f"Package: {self.package}"))
        color_names = {'green':'🟢 License check detected','blue':'🔵 Google Ads detected'}
        for c in self.colors:
            if c in color_names: layout.addWidget(QLabel(color_names[c]))
        layout.addWidget(QFrame().setFrameShape(QFrame.Shape.HLine))

        btn_rebuild = QPushButton("Create Modified APK File")
        btn_rebuild.clicked.connect(self.open_rebuild)
        layout.addWidget(btn_rebuild)

        btn_lvl = QPushButton("Remove License Verification")
        btn_lvl.setEnabled(any(f['type'] == 'license' for f in self.findings))
        btn_lvl.clicked.connect(self.open_license_dialog)
        layout.addWidget(btn_lvl)

        btn_ads = QPushButton("Remove Google Ads")
        btn_ads.setEnabled(any(f['type'] == 'ads' for f in self.findings))
        btn_ads.clicked.connect(self.open_ads_dialog)
        layout.addWidget(btn_ads)

        btn_custom = QPushButton("Custom Patch")
        layout.addWidget(btn_custom)
        btn_perms = QPushButton("Change Permissions")
        layout.addWidget(btn_perms)
        btn_backup = QPushButton("Backup App")
        layout.addWidget(btn_backup)
        layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        self.setLayout(layout)

    def open_rebuild(self):
        dlg = RebuildDialog(self.app_name, self.package, self)
        dlg.rebuild_requested.connect(self._on_rebuild_requested)
        dlg.exec()

    def open_license_dialog(self):
        dlg = LicensePatchDialog(self.app_name, self)
        dlg.patch_requested.connect(self._on_rebuild_requested)
        dlg.exec()

    def open_ads_dialog(self):
        dlg = AdsPatchDialog(self.app_name, self)
        dlg.patch_requested.connect(self._on_rebuild_requested)
        dlg.exec()

    def _on_rebuild_requested(self, mode):
        parent = self.parent()
        if parent and hasattr(parent, 'run_patch_pipeline'):
            parent.run_patch_pipeline(mode)
        else:
            QMessageBox.information(self, "Rebuild", f"Mode selected: {mode}")