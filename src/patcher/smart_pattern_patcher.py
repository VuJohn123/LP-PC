import os
import re

class SmartPatternPatcher:
    """Base class cho các patcher sử dụng pattern cấu trúc thay vì chỉ tên method."""
    def __init__(self, decompiled_path, log_callback=print):
        self.decompiled_path = decompiled_path
        self.log = log_callback

    def apply_patterns(self, patterns, target_methods=None):
        total_patched = 0
        for root, dirs, files in os.walk(self.decompiled_path):
            for file in files:
                if not file.endswith('.smali'):
                    continue
                path = os.path.join(root, file)
                if len(path) > 250:
                    self.log(f"[!] [SmartPattern] Đường dẫn quá dài, bỏ qua: {os.path.basename(path)}")
                    continue
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except (OSError, IOError) as e:
                    self.log(f"[!] [SmartPattern] Không thể đọc file {os.path.basename(path)}: {e}")
                    continue

                if target_methods and not any(m in content for m in target_methods):
                    continue

                modified = False
                for p in patterns:
                    search = p['search']
                    replace = p['replace']
                    if callable(replace):
                        new_content = re.sub(search, replace, content, flags=re.DOTALL)
                        if new_content != content:
                            n = len(re.findall(search, content, re.DOTALL))
                            total_patched += n
                            content = new_content
                            modified = True
                    else:
                        new_content, n = re.subn(search, replace, content, flags=re.DOTALL)
                        if n > 0:
                            content = new_content
                            modified = True
                            total_patched += n

                if modified:
                    try:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.log(f"[+] [SmartPattern] Đã vá: {os.path.basename(path)}")
                    except (OSError, IOError) as e:
                        self.log(f"[!] [SmartPattern] Không thể ghi file {os.path.basename(path)}: {e}")

        self.log(f"[*] [SmartPattern] Tổng số lần thay thế: {total_patched}")
        return total_patched