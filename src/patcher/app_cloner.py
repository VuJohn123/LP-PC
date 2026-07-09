import os
import shutil
import tempfile
from core.apk_utils import decompile_apk, recompile_apk, sign_apk

class AppCloner:
    def __init__(self, apk_path, new_package_name):
        self.apk_path = apk_path
        self.new_package = new_package_name
        self.temp_dir = tempfile.mkdtemp()

    def clone(self):
        print(f"[*] [AppCloner] Cloning to {self.new_package}...")
        decompiled_dir = os.path.join(self.temp_dir, "decompiled")
        decompile_apk(self.apk_path, decompiled_dir, force=True)

        # Đọc package cũ
        manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = f.read()

        match = re.findall(r'package="([^"]+)"', manifest)
        if not match:
            raise ValueError("Cannot find package in manifest")
        old_package = match[0]

        # Thay đổi package name trong manifest và toàn bộ smali
        manifest = manifest.replace(old_package, self.new_package)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest)

        for root, dirs, files in os.walk(decompiled_dir):
            for file in files:
                if file.endswith('.smali') or file.endswith('.xml'):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    content = content.replace(old_package.replace('.', '/'), self.new_package.replace('.', '/'))
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)

        # Rebuild và sign
        output_apk = os.path.join(self.temp_dir, "cloned.apk")
        recompile_apk(decompiled_dir, output_apk)
        signed_apk = sign_apk(output_apk)
        dest = os.path.join(os.path.expanduser("~"), "Desktop", f"cloned_{os.path.basename(signed_apk)}")
        shutil.copy(signed_apk, dest)
        print(f"[✔] [AppCloner] Cloned APK saved to {dest}")
        return dest

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)