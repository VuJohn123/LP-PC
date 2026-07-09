import os
from core.smali_utils import REGEX_MANIFEST_PERMISSION

class PermissionChanger:
    def __init__(self, decompiled_path, permissions_to_remove=None, file_cache=None):
        self.manifest_path = os.path.join(decompiled_path, "AndroidManifest.xml")
        self.file_cache = file_cache
        self.permissions_to_remove = permissions_to_remove or [
            'android.permission.READ_SMS',
            'android.permission.SEND_SMS',
            'android.permission.RECEIVE_SMS',
            'android.permission.READ_CONTACTS',
        ]

    def _read_manifest(self):
        if self.file_cache:
            return self.file_cache.read(self.manifest_path)
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _write_manifest(self, content):
        if self.file_cache:
            self.file_cache.write(self.manifest_path, content)
        else:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def remove_permissions(self):
        content = self._read_manifest()
        removed = False
        for perm in self.permissions_to_remove:
            pattern = r'<uses-permission\s+android:name="' + re.escape(perm) + r'"\s*/?>'
            new_content, n = re.subn(pattern, '', content, flags=re.IGNORECASE)
            if n > 0:
                content = new_content
                removed = True
                print(f"[+] [PermChanger] Removed {perm}")
        if removed:
            self._write_manifest(content)
        return removed