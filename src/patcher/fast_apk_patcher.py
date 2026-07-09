import os, shutil, tempfile, zipfile
from core.apk_utils import decompile_apk, recompile_apk, sign_apk

class FastAPKPatcher:
    """
    Vá APK nhanh bằng cách chỉ dịch ngược các class chính.
    Phù hợp với các tác vụ đơn giản: xóa ads, sửa license, thay đổi quyền.
    """
    def __init__(self, apk_path, output_dir=None):
        self.apk_path = apk_path
        self.temp_dir = tempfile.mkdtemp()
        self.decompiled_dir = os.path.join(self.temp_dir, "decompiled")
        self.output_apk = output_dir or os.path.join(self.temp_dir, "patched.apk")

    def patch_manifest(self, modifier_func):
        """Nhận một hàm sửa nội dung AndroidManifest.xml, áp dụng rồi build lại."""
        # Giải nén nhanh chỉ main classes
        decompile_apk(self.apk_path, self.decompiled_dir, no_main_classes=True, jobs=2)
        manifest_path = os.path.join(self.decompiled_dir, "AndroidManifest.xml")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = f.read()
        modified = modifier_func(manifest)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        # Build lại, bổ sung file từ APK gốc
        recompile_apk(self.decompiled_dir, self.output_apk, no_main_classes=True, original_apk=self.apk_path)
        signed = sign_apk(self.output_apk)
        return signed

    def patch_smali_files(self, target_files, search_replace_dict):
        """
        Chỉ giải nén các file smali cần thiết (theo đường dẫn tương đối), sửa và build.
        search_replace_dict: {pattern: replacement}
        """
        # Giải nén toàn bộ vẫn cần cho smali (có thể tối ưu bằng cách chỉ extract các file đó từ ZIP)
        # Nhưng để đơn giản, ta dùng apktool với --only-main-classes cũng giúp giảm thời gian.
        decompile_apk(self.apk_path, self.decompiled_dir, no_main_classes=True, jobs=4)
        for target in target_files:
            full_path = os.path.join(self.decompiled_dir, target)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                for pattern, replacement in search_replace_dict.items():
                    content = content.replace(pattern, replacement)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        recompile_apk(self.decompiled_dir, self.output_apk, no_main_classes=True, original_apk=self.apk_path)
        return sign_apk(self.output_apk)

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)