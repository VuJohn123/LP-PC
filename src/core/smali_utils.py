import os
import hashlib
import mmap
from concurrent.futures import ProcessPoolExecutor, as_completed

# Thử dùng re2 nếu có, nếu không fallback về re
try:
    import re2 as re
except ImportError:
    import re

# Thử dùng orjson nếu có
try:
    import orjson as json
    JSON_FAST = True
except ImportError:
    import json
    JSON_FAST = False

# Regex patterns được biên dịch sẵn để tối ưu hiệu suất
REGEX_LICENSE_METHOD = re.compile(
    r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?(\S+)\s*\(.*?\)\s*Z\s*.*?\.end\s+method)',
    re.DOTALL
)
REGEX_IAP_BILLING_METHOD = re.compile(
    r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?(\S+)\s*\([^)]*\)\s*(V|Landroid/os/Bundle;)\s*.*?\.end\s+method)',
    re.DOTALL
)
REGEX_ADS_URL = re.compile(r'"https?://[^"]*')
REGEX_INVOKE_LICENSE = re.compile(r'.*invoke.*LicenseChecker.*\n')
REGEX_INVOKE_ILICENSING = re.compile(r'.*invoke.*ILicensingService.*\n')
REGEX_MANIFEST_PERMISSION = re.compile(r'<uses-permission\s+android:name="([^"]+)"\s*/?>', re.IGNORECASE)
REGEX_MANIFEST_ACTIVITY = re.compile(r'<activity[^>]*android:name="([^"]+)"[^/]*/?>', re.DOTALL)
REGEX_MANIFEST_RECEIVER = re.compile(r'<receiver[^>]*android:name="([^"]+)"[^/]*/?>', re.DOTALL)
REGEX_SIGNATURE_METHOD = re.compile(
    r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?(\w+)\s*\(.*?\)\s*Z\s*\.registers\s+\d+\s*.*?\.end\s+method)',
    re.DOTALL
)
REGEX_INTEGRITY_METHOD = re.compile(
    r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?(\S+)\s*\(.*?\)\s*Z\s*.*?\.end\s+method)',
    re.DOTALL
)
REGEX_BOOLEAN_METHOD = re.compile(
    r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?(\S+)\s*\(.*?\)\s*Z\s*.*?\.end\s+method)',
    re.DOTALL
)
REGEX_SERVERMANAGEDPOLICY_CONSTRUCTOR = re.compile(
    r'(\.method\s+public\s+constructor\s+<init>\(.*?\)V\s*.*?\.end\s+method)',
    re.DOTALL
)

def get_smali_dirs(decompiled_path):
    """Trả về danh sách đường dẫn tuyệt đối đến các thư mục smali."""
    smali_dirs = []
    for item in os.listdir(decompiled_path):
        item_path = os.path.join(decompiled_path, item)
        if os.path.isdir(item_path) and item.startswith('smali'):
            smali_dirs.append(item_path)
    return smali_dirs if smali_dirs else [os.path.join(decompiled_path, 'smali')]

def get_all_smali_files(decompiled_path):
    """Trả về danh sách tất cả các file .smali trong các thư mục smali."""
    files = []
    for smali_dir in get_smali_dirs(decompiled_path):
        for root, dirs, filenames in os.walk(smali_dir):
            for f in filenames:
                if f.endswith('.smali'):
                    files.append(os.path.join(root, f))
    return files

class FileContentCache:
    """
    Cache nội dung file để giảm số lần đọc/ghi đĩa.
    Sử dụng memory-mapped file cho file lớn (>1MB).
    Ghi file theo batch với buffer lớn.
    """
    def __init__(self, decompiled_path):
        self.decompiled_path = decompiled_path
        self.cache = {}

    def read(self, filepath):
        """Đọc nội dung file từ cache hoặc từ đĩa."""
        if filepath not in self.cache:
            try:
                file_size = os.path.getsize(filepath)
                # Dùng memory-mapped file cho file lớn (>1MB)
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
        """Ghi nội dung vào cache (chưa ghi ra đĩa)."""
        self.cache[filepath] = content

    def flush(self, log_callback=print):
        """Ghi tất cả thay đổi trong cache ra đĩa với buffer lớn."""
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
        """Trả về danh sách các file đã bị thay đổi."""
        return list(self.cache.keys())

class ParallelFileProcessor:
    """Xử lý song song nhiều file với ProcessPoolExecutor để vượt GIL."""
    def __init__(self, max_workers=os.cpu_count()):
        self.max_workers = max_workers

    def process(self, files, worker_func, *args, **kwargs):
        total = 0
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(worker_func, f, *args, **kwargs): f for f in files}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    total += result if isinstance(result, int) else (1 if result else 0)
                except Exception as e:
                    filepath = futures[future]
                    print(f"[!] [Parallel] Lỗi xử lý {os.path.basename(filepath)}: {e}")
        return total

class APKCache:
    """Cache kết quả phân tích APK dựa trên MD5 của file."""
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
        apk_hash = hasher.hexdigest()
        return os.path.join(self.cache_dir, f"{apk_hash}.json")

    def get_cached_analysis(self, apk_path):
        cache_path = self.get_cache_path(apk_path)
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                if JSON_FAST:
                    return json.loads(f.read())
                else:
                    return json.load(f)
        return None

    def save_analysis(self, apk_path, findings, summary, colors):
        cache_path = self.get_cache_path(apk_path)
        data = {'findings': findings, 'summary': summary, 'colors': colors}
        with open(cache_path, 'w', encoding='utf-8') as f:
            if JSON_FAST:
                f.write(json.dumps(data).decode('utf-8'))
            else:
                json.dump(data, f, indent=2)