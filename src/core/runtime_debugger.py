import subprocess
import threading
import re

class RuntimeDebugger:
    """
    Theo dõi logcat của ứng dụng đã cài đặt, phát hiện lỗi và đề xuất patch.
    """
    def __init__(self, package_name, log_callback=print, suggestion_callback=None):
        self.package_name = package_name
        self.log = log_callback
        self.suggestion_callback = suggestion_callback  # Gọi khi phát hiện lỗi
        self.stop_event = threading.Event()
        self.patterns = {
            'gms_error': (r'Google Play services.*not available|isGooglePlayServicesAvailable.*error',
                         "Phát hiện lỗi GMS! Đề xuất chạy thêm chế độ 'gms_spoof'."),
            'license_error': (r'License check.*fail|dontAllow|NOT_LICENSED',
                            "Phát hiện lỗi License! Đề xuất chạy thêm chế độ 'license:extreme'."),
            'billing_error': (r'Billing.*error|purchase.*fail|RESPONSE_CODE.*[^0]',
                            "Phát hiện lỗi Billing! Đề xuất chạy thêm chế độ 'iap:dex'."),
            'signature_error': (r'Signature.*mismatch|verify.*fail',
                              "Phát hiện lỗi Signature! Đề xuất chạy thêm chế độ 'sig_disable'."),
        }

    def start(self):
        cmd = ['adb', 'logcat', '-s', f'{self.package_name}:*', '*:E']
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        threading.Thread(target=self._read_output, daemon=True).start()
        self.log(f"[*] [Debugger] Bắt đầu theo dõi logcat cho {self.package_name}")

    def _read_output(self):
        for line in self.process.stdout:
            if self.stop_event.is_set():
                break
            self.log(f"[Device] {line.strip()}")
            self._analyze_line(line)

    def _analyze_line(self, line):
        for error_type, (pattern, suggestion) in self.patterns.items():
            if re.search(pattern, line):
                self.log(f"[!] [Debugger] {suggestion}")
                if self.suggestion_callback:
                    self.suggestion_callback(error_type, suggestion)
                break

    def stop(self):
        self.stop_event.set()
        self.process.terminate()