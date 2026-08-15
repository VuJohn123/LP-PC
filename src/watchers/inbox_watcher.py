import os
import time
import logging
from pathlib import Path
import threading
from core.event_bus import event_bus

logger = logging.getLogger(__name__)

class InboxWatcher:
    """
    Quan sát một thư mục. Khi có APK mới, phát ra sự kiện 'apk.detected'.
    Giống như PackageChangeReceiver của Lucky Patcher.
    """
    def __init__(self, inbox_path, check_interval=5):
        self.inbox_path = Path(inbox_path)
        self.check_interval = check_interval
        self.known_files = set()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        logger.info(f"Bắt đầu quan sát thư mục: {self.inbox_path}")
        self.known_files = self._scan_directory()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def _scan_directory(self):
        """Quét tất cả file APK trong thư mục."""
        if not self.inbox_path.exists():
            self.inbox_path.mkdir(parents=True, exist_ok=True)
            return set()
        return {f for f in self.inbox_path.iterdir() if f.suffix == '.apk'}

    def _monitor_loop(self):
        """Vòng lặp kiểm tra thư mục định kỳ."""
        while not self._stop_event.is_set():
            current_files = self._scan_directory()
            new_files = current_files - self.known_files

            for new_file in new_files:
                logger.info(f"Phát hiện APK mới: {new_file.name}")
                event_bus.emit('apk.detected', {'path': str(new_file)})

            self.known_files = current_files
            time.sleep(self.check_interval)