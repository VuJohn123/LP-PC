import os
import re
from core.smali_utils import get_all_smali_files

class GMSSpoofer:
    def __init__(self, decompiled_path, log_callback=print, file_cache=None):
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

    def patch(self):
        self.log("[*] [GMSSpoofer] Đang giả mạo Google Play Services...")
        count = 0

        # Thêm GoogleApiAvailability stub
        gms_stub_dir = os.path.join(self.decompiled_path, 'smali', 'com', 'google', 'android', 'gms', 'common')
        os.makedirs(gms_stub_dir, exist_ok=True)

        google_api_stub = '''.class public Lcom/google/android/gms/common/GoogleApiAvailability;
.super Ljava/lang/Object;
.source "GMSSpoofer.java"

.method public static getInstance()Lcom/google/android/gms/common/GoogleApiAvailability;
    .registers 1
    new-instance v0, Lcom/google/android/gms/common/GoogleApiAvailability;
    invoke-direct {v0}, Lcom/google/android/gms/common/GoogleApiAvailability;-><init>()V
    return-object v0
.end method

.method public isGooglePlayServicesAvailable(Landroid/content/Context;)I
    .registers 1
    const/4 v0, 0x0
    return v0
.end method

.method public isUserResolvableError(I)Z
    .registers 1
    const/4 v0, 0x0
    return v0
.end method

.method public getErrorString(I)Ljava/lang/String;
    .registers 1
    const-string v0, "SUCCESS"
    return-object v0
.end method
'''
        stub_path = os.path.join(gms_stub_dir, 'GoogleApiAvailability.smali')
        if not os.path.exists(stub_path):
            with open(stub_path, 'w', encoding='utf-8') as f:
                f.write(google_api_stub)
            self.log("[+] [GMSSpoofer] Added GoogleApiAvailability stub")
            count += 1

        # Vá các method liên quan đến GMS
        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250: continue
            content = self._read_file(filepath)
            modified = False

            if 'isGooglePlayServicesAvailable' in content:
                pattern = r'(\.method\s+(?:public|private|static)\s+(?:final\s+)?(\S+)\s*\(.*?\)\s*I\s*.*?invoke.*?isGooglePlayServicesAvailable.*?\.end\s+method)'
                for match in re.finditer(pattern, content, re.DOTALL):
                    full = match.group(0)
                    header = full.split('\n')[0]
                    replacement = f"{header}\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n.end method"
                    content = content.replace(full, replacement)
                    modified = True
                    self.log(f"[+] [GMSSpoofer] Patched GMS check in {os.path.basename(filepath)}")
                    count += 1

            if 'GoogleSignIn' in content and 'getLastSignedInAccount' in content:
                pattern = r'(invoke-static\s+\{.*?\},\s+Lcom/google/android/gms/auth/api/signin/GoogleSignIn;->getLastSignedInAccount\(.*?\)Lcom/google/android/gms/auth/api/signin/GoogleSignInAccount;)'
                new_content, n = re.subn(pattern, r'# \1  # Disabled by LP-PC Suite', content)
                if n > 0:
                    content = new_content
                    modified = True
                    self.log(f"[+] [GMSSpoofer] Disabled GoogleSignIn in {os.path.basename(filepath)}")
                    count += n

            if modified:
                self._write_file(filepath, content)

        self.log(f"[*] [GMSSpoofer] Tổng số thay đổi: {count}")
        return count