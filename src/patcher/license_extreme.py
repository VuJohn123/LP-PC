import os
from core.smali_utils import (
    get_all_smali_files,
    REGEX_BOOLEAN_METHOD,
    REGEX_INVOKE_LICENSE,
    REGEX_INVOKE_ILICENSING
)

class LicenseExtremePatcher:
    def __init__(self, decompiled_path: str, log_callback=print, file_cache=None):
        self.decompiled_path = decompiled_path
        self.log = log_callback
        self.file_cache = file_cache

    def _read_file(self, path):
        if self.file_cache:
            return self.file_cache.read(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _write_file(self, path, content):
        if self.file_cache:
            self.file_cache.write(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

    def patch_extreme(self) -> int:
        self.log("[*] [LicenseExtreme] Extreme mode...")
        patched = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)

            if not ('LicenseChecker' in content or 'ILicensingService' in content or 'checkLicense' in content):
                continue

            original = content
            content = REGEX_INVOKE_LICENSE.sub('', content)
            content = REGEX_INVOKE_ILICENSING.sub('', content)

            if content != original:
                self._write_file(filepath, content)
                patched += 1

        self.log(f"[*] [LicenseExtreme] Patched {patched} files")
        return patched

    def patch_reverse_auto(self) -> int:
        self.log("[*] [LicenseExtreme] Reverse Auto mode...")
        return self.patch_extreme()

    def patch_amazon_market(self) -> int:
        self.log("[*] [LicenseExtreme] Amazon mode...")
        patched = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)
            if 'amazon' not in content.lower() and 'appstore' not in content.lower(): continue

            for match in REGEX_BOOLEAN_METHOD.finditer(content):
                full = match.group(0)
                header = full.split('\n')[0]
                replacement = f"{header}\n    .locals 1\n    const/4 v0, 0x1\n    return v0\n.end method"
                content = content.replace(full, replacement)
                self._write_file(filepath, content)
                patched += 1
                break

        self.log(f"[*] [LicenseExtreme] Amazon patched {patched} files")
        return patched

    def patch_samsung_apps(self) -> int:
        self.log("[*] [LicenseExtreme] Samsung mode...")
        patched = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)
            if 'samsung' not in content.lower() and 'galaxy' not in content.lower(): continue

            for match in REGEX_BOOLEAN_METHOD.finditer(content):
                full = match.group(0)
                header = full.split('\n')[0]
                replacement = f"{header}\n    .locals 1\n    const/4 v0, 0x1\n    return v0\n.end method"
                content = content.replace(full, replacement)
                self._write_file(filepath, content)
                patched += 1
                break

        self.log(f"[*] [LicenseExtreme] Samsung patched {patched} files")
        return patched