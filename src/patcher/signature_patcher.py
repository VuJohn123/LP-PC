import os
from core.smali_utils import get_all_smali_files, REGEX_SIGNATURE_METHOD

class SignatureVerifyPatcher:
    def __init__(self, decompiled_path, file_cache=None):
        self.decompiled_path = decompiled_path
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

    def patch(self):
        print("[*] [SignaturePatcher] Disabling self-signature checks...")
        patched = 0
        keywords = ['verifyPurchase', 'checkSignature', 'validatePurchase', 'Signature', 'RSA']
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)
            if not any(kw in content for kw in keywords): continue

            for match in REGEX_SIGNATURE_METHOD.finditer(content):
                full = match.group(0)
                method_name = match.group(1)
                if any(k in method_name.lower() for k in ['signature', 'verify', 'check']):
                    if '.annotation' not in full:
                        header = full.split('\n')[0]
                        replacement = f"{header}\n    .locals 1\n    const/4 v0, 0x1\n    return v0\n.end method"
                        content = content.replace(full, replacement)
                        patched += 1

            if content != self._read_file(filepath):
                self._write_file(filepath, content)
        print(f"[*] [SignaturePatcher] Patched {patched} files (app-level only)")
        return patched