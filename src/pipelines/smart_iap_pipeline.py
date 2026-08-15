from core.event_bus import event_bus
from patcher.iap_bypass import IAPBypass
from patcher.iap_manager import IAPManager
import os, tempfile, shutil
from core.apk_utils import decompile_apk, recompile_apk, sign_apk

class SmartIAPPipeline:
    """
    Tự động áp dụng bản vá IAP khi phát hiện ứng dụng có hỗ trợ IAP.
    """
    def __init__(self):
        event_bus.subscribe('apk.analysis.complete', self.on_analysis_complete)

    def on_analysis_complete(self, data):
        apk_path = data['apk_path']
        findings = data['findings']
        has_iap = any(f['type'] == 'iap' for f in findings)
        
        if has_iap:
# TODO: Convert to logger: print(f"[SmartIAP] Phát hiện IAP trong {os.path.basename(apk_path)}, tự động vá...")
            self._apply_iap_patch(apk_path)

    def _apply_iap_patch(self, apk_path):
        temp_dir = tempfile.mkdtemp()
        decompiled_dir = os.path.join(temp_dir, "decompiled")
        try:
            decompile_apk(apk_path, decompiled_dir, jobs=4, max_memory="4096m")
            bypass = IAPBypass(decompiled_dir, mode='dex')
            bypass.execute()
            patched_apk = os.path.join(temp_dir, "patched.apk")
            recompile_apk(decompiled_dir, patched_apk)
            signed_apk = sign_apk(patched_apk)
            
            output_dir = os.path.join(os.path.dirname(apk_path), "patched")
            os.makedirs(output_dir, exist_ok=True)
            dest = os.path.join(output_dir, os.path.basename(signed_apk))
            shutil.copy(signed_apk, dest)
# TODO: Convert to logger: print(f"[SmartIAP] APK đã vá được lưu tại: {dest}")
            event_bus.emit('apk.patched', {'path': dest, 'original': apk_path})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)