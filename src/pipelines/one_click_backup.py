import shutil
import os
from core.event_bus import event_bus

class OneClickBackupPipeline:
    """
    Tự động sao lưu APK gốc khi phát hiện sự kiện 'apk.ready'.
    """
    def __init__(self, backup_dir=None):
        self.backup_dir = backup_dir or os.path.join(os.path.expanduser("~"), "LP_Backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        event_bus.subscribe('apk.detected', self.on_apk_detected)

    def on_apk_detected(self, data):
        apk_path = data['path']
# TODO: Convert to logger: print(f"[OneClickBackup] Đang sao lưu: {apk_path}")
        dest = os.path.join(self.backup_dir, os.path.basename(apk_path))
        shutil.copy2(apk_path, dest)
# TODO: Convert to logger: print(f"[OneClickBackup] Đã sao lưu vào: {dest}")