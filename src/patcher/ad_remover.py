import os
import re
from core.smali_utils import REGEX_MANIFEST_ACTIVITY, REGEX_MANIFEST_RECEIVER

class AdRemover:
    def __init__(self, decompiled_path, file_cache=None):
        self.manifest_path = os.path.join(decompiled_path, "AndroidManifest.xml")
        self.file_cache = file_cache

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

    def remove_activities(self, ad_activities):
        print(f"[*] [AdRemover] Removing {len(ad_activities)} ad activities...")
        content = self._read_manifest()
        original = content
        for act in ad_activities:
            pattern = r'<activity[^>]*android:name="' + re.escape(act) + r'"[^/]*/?>'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        if content != original:
            self._write_manifest(content)
            print("[+] [AdRemover] Activities removed")
            return True
        return False

    def remove_receivers(self, ad_receivers):
        print(f"[*] [AdRemover] Removing {len(ad_receivers)} ad receivers...")
        content = self._read_manifest()
        original = content
        for recv in ad_receivers:
            pattern = r'<receiver[^>]*android:name="' + re.escape(recv) + r'"[^/]*/?>'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        if content != original:
            self._write_manifest(content)
            print("[+] [AdRemover] Receivers removed")
            return True
        return False