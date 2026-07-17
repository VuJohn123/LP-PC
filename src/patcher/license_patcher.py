import os
from core.smali_utils import get_all_smali_files, REGEX_BOOLEAN_METHOD, REGEX_SERVERMANAGEDPOLICY_CONSTRUCTOR

LICENSE_KEYWORDS = {'allow', 'dontAllow', 'checkLicense', 'isLicensed', 'verifyLicense'}

class LicensePatcher:
    def __init__(self, decompiled_path, log_callback=print, file_cache=None):
        self.decompiled_path = decompiled_path
        self.log = log_callback
        self.file_cache = file_cache

    def _read(self, path):
        if self.file_cache:
            return self.file_cache.read(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _write(self, path, content):
        if self.file_cache:
            self.file_cache.write(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

    def patch_license_check(self):
        self.log("[*] [LicensePatcher] Auto mode...")
        patched = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250:
                continue
            content = self._read(filepath)
            # Pre-filter cực nhanh
            if 'LicenseValidator' not in content and 'LicenseCheckerCallback' not in content:
                continue

            for match in REGEX_BOOLEAN_METHOD.finditer(content):
                name = match.group(1).split('(')[0]
                if name in LICENSE_KEYWORDS:
                    header = match.group(0).split('\n')[0]
                    content = content.replace(match.group(0),
                        f"{header}\n    .locals 1\n    const/4 v0, 0x1\n    return v0\n.end method")
                    self._write(filepath, content)
                    patched += 1
                    break

        self.log(f"[*] [LicensePatcher] Patched {patched} files")
        return patched

    def patch_reverse_auto(self):
        self.log("[*] [LicensePatcher] Reverse Auto...")
        patched = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250:
                continue
            content = self._read(filepath)
            if 'ServerManagedPolicy' not in content:
                continue
            for match in REGEX_SERVERMANAGEDPOLICY_CONSTRUCTOR.finditer(content):
                header = match.group(0).split('\n')[0]
                content = content.replace(match.group(0),
                    f"{header}\n    .locals 1\n    return-void\n.end method")
                self._write(filepath, content)
                patched += 1
                break
        self.log(f"[*] [LicensePatcher] Reverse auto patched {patched} files")
        return patched