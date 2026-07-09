import os
import shutil
import tempfile
import zipfile
from core.apk_utils import sign_apk, decompile_apk, recompile_apk

class ResignPatcher:
    def __init__(self, apk_path):
        self.apk_path = apk_path
        self.temp_dir = tempfile.mkdtemp()

    def resign_with_testkey(self):
        print("[*] [Resign] Signing with testkey...")
        signed = sign_apk(self.apk_path)
        return signed

    def resign_with_original_signature(self, original_apk):
        """
        CẢNH BÁO: Phương pháp này chỉ hoạt động nếu đã áp dụng bản vá hệ thống
        'Signature Verification always True'. Không thể dùng để qua mặt Android OS.
        """
        print("[!] [Resign] WARNING: This method requires system-level signature verification bypass.")
        print("[*] [Resign] Copying APK without resigning...")
        dest = os.path.join(self.temp_dir, os.path.basename(self.apk_path))
        shutil.copy2(self.apk_path, dest)
        return dest

    def change_package_name(self, new_package_name):
        print(f"[*] [Resign] Changing package name to {new_package_name}...")
        decompiled_dir = os.path.join(self.temp_dir, "decompiled")
        decompile_apk(self.apk_path, decompiled_dir)
        
        manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        match = re.findall(r'package="([^"]+)"', content)
        if not match:
            raise ValueError("Cannot find package in manifest")
        old_package = match[0]
        content = content.replace(old_package, new_package_name)
        
        for root, dirs, files in os.walk(decompiled_dir):
            for file in files:
                if file.endswith('.smali'):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        smali = f.read()
                    smali = smali.replace(old_package.replace('.', '/'), new_package_name.replace('.', '/'))
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(smali)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        output_apk = os.path.join(self.temp_dir, "renamed.apk")
        recompile_apk(decompiled_dir, output_apk)
        return output_apk

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)