import os
from core.smali_utils import get_all_smali_files, REGEX_INTEGRITY_METHOD

class SignatureFakeArchivePatcher:
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

    def patch(self) -> int:
        self.log("[*] [SigFakeArchive] Đang giả mạo archive...")
        patched = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)
            if 'ZipEntry' not in content and 'getEntry' not in content: continue

            for match in REGEX_INTEGRITY_METHOD.finditer(content):
                full = match.group(0)
                name = match.group(1).split('(')[0]
                if any(kw in name.lower() for kw in ['zip', 'archive', 'entry', 'apk']):
                    header = full.split('\n')[0]
                    replacement = f"{header}\n    .locals 1\n    const/4 v0, 0x1\n    return v0\n.end method"
                    content = content.replace(full, replacement)
                    patched += 1
                    self._write_file(filepath, content)

        self.log(f"[*] [SigFakeArchive] Đã vá {patched} file")
        return patched