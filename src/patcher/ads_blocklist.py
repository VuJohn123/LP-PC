import os
import re
from core.smali_utils import get_all_smali_files, REGEX_ADS_URL

class AdsBlocklistPatcher:
    def __init__(self, decompiled_path, blocklist_file=None, log_callback=print, file_cache=None):
        self.decompiled_path = decompiled_path
        self.log = log_callback
        self.file_cache = file_cache
        self.blocklist = self._load_blocklist(blocklist_file)

    def _load_blocklist(self, filepath):
        defaults = ["doubleclick.net", "googleadservices.com", "googlesyndication.com", "admob.com",
                    "applovin.com", "unity3d.com/ads", "facebook.com/ads", "ironsrc.com", "vungle.com"]
        if filepath and os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return defaults

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

    def remove_ad_urls_from_smali(self):
        self.log("[*] [AdsBlocklist] Removing ad URLs from smali...")
        count = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)
            modified = False
            for domain in self.blocklist:
                pattern = r'"https?://[^"]*' + re.escape(domain) + r'[^"]*"'
                new_content, n = re.subn(pattern, '"http://127.0.0.1"', content)
                if n > 0:
                    content = new_content
                    modified = True
                    count += n
            if modified:
                self._write_file(filepath, content)
        self.log(f"[*] [AdsBlocklist] Removed {count} ad URLs")
        return count

    def make_ads_offline(self):
        self.log("[*] [AdsBlocklist] Making ads offline...")
        count = 0
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)
            modified = False
            for method in ['isOnline', 'isConnected', 'hasInternetConnection', 'checkNetwork']:
                pattern = r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?' + method + r'\(.*?\)Z.*?\.end\s+method)'
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    full = match.group(0)
                    if '.annotation' not in full.split('.end method')[0]:
                        header = full.split('\n')[0]
                        replacement = f"{header}\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n.end method"
                        content = content.replace(full, replacement)
                        modified = True
                        count += 1
            if modified:
                self._write_file(filepath, content)
        self.log(f"[*] [AdsBlocklist] Offline mode applied to {count} methods")
        return count