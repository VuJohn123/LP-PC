import json
import os
import time
import hashlib
import zipfile
import subprocess

class Watermarker:
    """Thêm watermark vào APK để đánh dấu đã được vá."""
    MARKER_FILE = 'assets/lp_pc_suite_marker.json'

    @staticmethod
    def add_watermark(decompiled_path, patches_applied, apk_path):
        """Thêm file đánh dấu vào thư mục assets trước khi recompile."""
        marker_path = os.path.join(decompiled_path, Watermarker.MARKER_FILE)
        os.makedirs(os.path.dirname(marker_path), exist_ok=True)

        # Lấy hash của APK gốc
        with open(apk_path, 'rb') as f:
            apk_hash = hashlib.md5(f.read()).hexdigest()

        marker = {
            'tool': 'LP-PC Suite v4',
            'timestamp': time.time(),
            'original_hash': apk_hash,
            'patches': patches_applied
        }

        with open(marker_path, 'w', encoding='utf-8') as f:
            json.dump(marker, f, indent=2)

        print(f"[Watermarker] Added watermark: {patches_applied}")

    @staticmethod
    def check_watermark(apk_path):
        """Kiểm tra APK đã được vá bởi LP-PC Suite chưa."""
        try:
            with zipfile.ZipFile(apk_path, 'r') as z:
                if Watermarker.MARKER_FILE in z.namelist():
                    data = z.read(Watermarker.MARKER_FILE)
                    return json.loads(data.decode('utf-8'))
        except Exception:
            pass
        return None

    @staticmethod
    def check_watermark_installed(package_name):
        """Kiểm tra app đã cài đặt có watermark không (qua ADB)."""
        try:
            result = subprocess.run(
                ['adb', 'shell', 'run-as', package_name, 'cat', Watermarker.MARKER_FILE],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
        except Exception:
            pass
        return None