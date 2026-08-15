import os
import time
import json
from pathlib import Path
import threading

class AutoUpdater:
    """
    Tự động phát hiện APK mới trong thư mục Downloads,
    so sánh với lịch sử patch và tự động áp dụng lại patch.
    """
    def __init__(self, watch_dir=None, history_dir=None, log_callback=print, pipeline_callback=None):
        self.watch_dir = Path(watch_dir or os.path.join(os.path.expanduser("~"), "Downloads"))
        self.history_dir = Path(history_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace', 'history'
        ))
        self.patch_history_file = self.history_dir / 'patch_history.json'
        self.log = log_callback
        self.pipeline_callback = pipeline_callback  # Hàm gọi run_pipeline
        self.known_files = set()
        self.stop_event = threading.Event()

    def start(self, interval=10):
        self.log(f"[*] [AutoUpdater] Đang theo dõi thư mục: {self.watch_dir}")
        self.known_files = set(self.watch_dir.glob('*.apk'))
        self.known_files.update(set(self.watch_dir.glob('*.xapk')))
        self._run(interval)

    def _run(self, interval):
        while not self.stop_event.is_set():
            current_files = set(self.watch_dir.glob('*.apk'))
            current_files.update(set(self.watch_dir.glob('*.xapk')))
            new_files = current_files - self.known_files

            for apk_file in new_files:
                self._process_new_apk(str(apk_file))

            self.known_files = current_files
            time.sleep(interval)

    def _process_new_apk(self, apk_path):
        self.log(f"[*] [AutoUpdater] Phát hiện file mới: {os.path.basename(apk_path)}")

        # Xử lý .xapk
        if apk_path.endswith('.xapk'):
            from core.apk_downloader import APKDownloader
            downloader = APKDownloader(log_callback=self.log)
            apk_path = downloader.process_xapk(apk_path)

        # Trích xuất package name
        try:
            from androguard.core.apk import APK
            apk = APK(apk_path)
            package_name = apk.get_package()
        except Exception as e:
            self.log(f"[!] [AutoUpdater] Không thể phân tích APK: {e}")
            return

        # Tìm trong lịch sử
        history = self._load_history()
        patches = None
        for record in history:
            if record.get('apk', '').find(package_name) != -1:
                patches = record.get('patches', [])
                break

        if not patches:
            self.log(f"[!] [AutoUpdater] Không tìm thấy lịch sử patch cho {package_name}")
            return

        self.log(f"[*] [AutoUpdater] Đang áp dụng lại patch: {patches}")
        if self.pipeline_callback:
            mode = ','.join(patches) if isinstance(patches, list) else patches
            self.pipeline_callback(apk_path, mode)

    def _load_history(self):
        if self.patch_history_file.exists():
            try:
                with open(self.patch_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def stop(self):
        self.stop_event.set()