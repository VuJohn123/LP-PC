import os
import hashlib
import mmap
from concurrent.futures import ProcessPoolExecutor, as_completed

# Ưu tiên re2 > re
try:
    import re2 as re
    RE_ENGINE = "re2"
except ImportError:
    import re
    RE_ENGINE = "re"

# Ưu tiên orjson > json
try:
    import orjson
    def json_loads(data):
        return orjson.loads(data)
    def json_dumps(data):
        return orjson.dumps(data).decode('utf-8')
    JSON_FAST = True
except ImportError:
    import json
    def json_loads(data):
        return json.loads(data)
    def json_dumps(data):
        return json.dumps(data)
    JSON_FAST = False

# Regex đã biên dịch - Cải tiến để match chính xác Smali bytecode với nhiều modifiers
REGEX_BOOLEAN_METHOD = re.compile(
    r'(\.method\s+(?:(?:public|private|protected)\s+)*(?:static\s+)?(?:final\s+)?\w+\s*\([^)]*\)Z[\s\S]*?\.end\s+method)',
    re.DOTALL
)
REGEX_IAP_BILLING_METHOD = re.compile(
    r'(\.method\s+(?:(?:public|private|protected)\s+)*(?:static\s+)?(?:final\s+)?\w+\s*\([^)]*\)(?:V|Landroid/os/Bundle;)[\s\S]*?\.end\s+method)',
    re.DOTALL
)
REGEX_SIGNATURE_METHOD = re.compile(
    r'(\.method\s+(?:(?:public|private|protected)\s+)*(?:static\s+)?(?:final\s+)?\w+\s*\([^)]*\)Z[\s\S]*?\.end\s+method)',
    re.DOTALL
)
REGEX_INTEGRITY_METHOD = re.compile(
    r'(\.method\s+(?:(?:public|private|protected)\s+)*(?:static\s+)?(?:final\s+)?\w+\s*\([^)]*\)Z[\s\S]*?\.end\s+method)',
    re.DOTALL
)
REGEX_SERVERMANAGEDPOLICY_CONSTRUCTOR = re.compile(
    r'(\.method\s+public\s+constructor\s+<init>\(.*?\)V\s*.*?\.end\s+method)',
    re.DOTALL
)
REGEX_INVOKE_LICENSE = re.compile(r'.*invoke.*LicenseChecker.*')
REGEX_INVOKE_ILICENSING = re.compile(r'.*invoke.*ILicensingService.*')
REGEX_MANIFEST_PERMISSION = re.compile(r'<uses-permission\s+android:name="([^"]+)"\s*/?>', re.IGNORECASE)
REGEX_MANIFEST_ACTIVITY = re.compile(r'<activity[^>]*android:name="([^"]+)"[^/]*/?>', re.IGNORECASE)
REGEX_MANIFEST_RECEIVER = re.compile(r'<receiver[^>]*android:name="([^"]+)"[^/]*/?>', re.IGNORECASE)
REGEX_ADS_URL = re.compile(r'"https?://[^\"]*(?:doubleclick\.net|googleadservices\.com|googlesyndication\.com|admob\.com)[^\"]*"', re.IGNORECASE)


def get_smali_dirs(decompiled_path):
    smali_dirs = [os.path.join(decompiled_path, d) for d in os.listdir(decompiled_path)
                  if os.path.isdir(os.path.join(decompiled_path, d)) and d.startswith('smali')]
    return smali_dirs if smali_dirs else [os.path.join(decompiled_path, 'smali')]


def get_all_smali_files(decompiled_path):
    files = []
    for smali_dir in get_smali_dirs(decompiled_path):
        for root, _, filenames in os.walk(smali_dir):
            for f in filenames:
                if f.endswith('.smali'):
                    files.append(os.path.join(root, f))
    return files


class FileContentCache:
    def __init__(self, decompiled_path):
        self.decompiled_path = decompiled_path
        self.cache = {}

    def read(self, filepath):
        if filepath not in self.cache:
            try:
                file_size = os.path.getsize(filepath)
                if file_size > 1024 * 1024:
                    with open(filepath, 'r+b') as f:
                        with mmap.mmap(f.fileno(), 0) as mmapped:
                            self.cache[filepath] = mmapped.read().decode('utf-8', errors='ignore')
                else:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        self.cache[filepath] = f.read()
            except (OSError, IOError):
                self.cache[filepath] = ""
        return self.cache[filepath]

    def write(self, filepath, content):
        self.cache[filepath] = content

    def flush(self, log_callback=print):
        count = 0
        for filepath, content in self.cache.items():
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8', buffering=128*1024) as f:
                    f.write(content)
                count += 1
            except (OSError, IOError) as e:
                log_callback(f"[!] [FileCache] Không thể ghi {filepath}: {e}")
        log_callback(f"[*] [FileCache] Đã ghi {count} file ra đĩa")
        self.cache.clear()

    def get_modified_files(self):
        return list(self.cache.keys())


class ParallelFileProcessor:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or min(os.cpu_count() or 4, 8)

    def process(self, files, worker_func, *args, **kwargs):
        total = 0
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(worker_func, f, *args, **kwargs): f for f in files}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    total += result if isinstance(result, int) else (1 if result else 0)
                except Exception as e:
                    print(f"[!] [Parallel] Lỗi: {e}")
        return total


class APKCache:
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace', 'cache')
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_cache_path(self, apk_path):
        hasher = hashlib.md5()
        with open(apk_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return os.path.join(self.cache_dir, f"{hasher.hexdigest()}.json")

    def get_cached_analysis(self, apk_path):
        cache_path = self.get_cache_path(apk_path)
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json_loads(f.read())
        return None

    def save_analysis(self, apk_path, findings, summary, colors):
        cache_path = self.get_cache_path(apk_path)
        data = json_dumps({'findings': findings, 'summary': summary, 'colors': colors})
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(data)