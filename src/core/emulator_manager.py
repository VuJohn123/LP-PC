import subprocess
import os
import time

class EmulatorManager:
    """
    Quản lý máy ảo Android (AVD) qua ADB.
    Yêu cầu: Android SDK đã cài đặt và biến môi trường ANDROID_HOME được thiết lập.
    """
    def __init__(self, avd_name='LP_PC_Emulator', log_callback=print):
        self.avd_name = avd_name
        self.log = log_callback
        self.adb = 'adb'
        self.emulator_path = self._find_emulator()

    def _find_emulator(self):
        """Tìm đường dẫn emulator.exe từ Android SDK."""
        android_home = os.environ.get('ANDROID_HOME', os.path.expanduser('~/Android/Sdk'))
        emulator = os.path.join(android_home, 'emulator', 'emulator.exe' if os.name == 'nt' else 'emulator')
        if os.path.exists(emulator):
            return emulator
        # Thử tìm trong PATH
        for path in os.environ.get('PATH', '').split(os.pathsep):
            test = os.path.join(path, 'emulator.exe' if os.name == 'nt' else 'emulator')
            if os.path.exists(test):
                return test
        return None

    def is_emulator_running(self):
        """Kiểm tra xem máy ảo có đang chạy không."""
        proc = subprocess.run([self.adb, 'devices'], capture_output=True, text=True)
        return 'emulator' in proc.stdout

    def start_emulator(self):
        """Khởi động máy ảo (nếu chưa chạy)."""
        if self.is_emulator_running():
            self.log("[*] [Emulator] Already running.")
            return True
        if not self.emulator_path:
            self.log("[!] [Emulator] Emulator not found. Please install Android SDK.")
            return False
        self.log(f"[*] [Emulator] Starting AVD: {self.avd_name}...")
        cmd = [self.emulator_path, '-avd', self.avd_name, '-no-snapshot', '-no-boot-anim']
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(15)
        return self.is_emulator_running()

    def install_apk(self, apk_path):
        """Cài đặt APK vào máy ảo."""
        if not self.is_emulator_running():
            self.log("[!] [Emulator] Not running. Start it first.")
            return False
        proc = subprocess.run([self.adb, '-e', 'install', '-r', apk_path], capture_output=True, text=True)
        if 'Success' in proc.stdout:
            self.log("[+] [Emulator] APK installed.")
            return True
        self.log(f"[!] [Emulator] Install failed: {proc.stderr}")
        return False

    def launch_app(self, package_name):
        """Khởi chạy ứng dụng trên máy ảo."""
        subprocess.run([self.adb, '-e', 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
                       capture_output=True)