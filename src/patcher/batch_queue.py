import os
import threading
import time
from queue import Queue

class BatchQueue:
    """
    Hàng đợi xử lý nhiều APK tuần tự.
    """
    def __init__(self, pipeline_callback, log_callback=print):
        self.queue = Queue()
        self.pipeline_callback = pipeline_callback  # Hàm (apk_path, mode) -> None
        self.log = log_callback
        self.stop_event = threading.Event()
        self.current_apk = None
        self.progress_callback = None  # (current, total, apk_name)

    def add(self, apk_path, mode='all'):
        self.queue.put((apk_path, mode))
        self.log(f"[+] [BatchQueue] Đã thêm vào hàng đợi: {os.path.basename(apk_path)}")

    def start(self):
        threading.Thread(target=self._process_queue, daemon=True).start()
        self.log("[*] [BatchQueue] Bắt đầu xử lý hàng đợi...")

    def _process_queue(self):
        total = self.queue.qsize()
        processed = 0
        while not self.stop_event.is_set() and not self.queue.empty():
            apk_path, mode = self.queue.get()
            self.current_apk = apk_path
            self.log(f"[*] [BatchQueue] Đang xử lý ({processed + 1}/{total}): {os.path.basename(apk_path)}")
            if self.progress_callback:
                self.progress_callback(processed, total, os.path.basename(apk_path))
            try:
                self.pipeline_callback(apk_path, mode)
            except Exception as e:
                self.log(f"[!] [BatchQueue] Lỗi xử lý {os.path.basename(apk_path)}: {e}")
            processed += 1
            self.queue.task_done()
        self.log("[*] [BatchQueue] Hoàn thành tất cả!")

    def stop(self):
        self.stop_event.set()