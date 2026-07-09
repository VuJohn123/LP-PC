import os
import re

class IAPSmaliPatcher:
    def __init__(self, decompiled_path: str):
        self.decompiled_path = decompiled_path

    def patch_billing_calls(self, proxy_host: str = 'localhost', proxy_port: int = 8888) -> int:
        print("[*] [IAPSmaliPatcher] Đang tìm intent Billing Service để chuyển hướng...")
        patched_count = 0
        target_intent_action = "com.android.vending.billing.InAppBillingService.BIND"
        target_package = "com.android.vending"
        proxy_package = "com.android.vending.billing"

        for root, dirs, files in os.walk(self.decompiled_path):
            for file in files:
                if not file.endswith('.smali'): continue
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if target_intent_action not in content and target_package not in content: continue

                original = content
                modified = False

                if target_intent_action in content:
                    new_content = content.replace(
                        f'"{target_intent_action}"',
                        f'"com.android.vending.billing.IInAppBillingServiceProxy.BIND"'
                    )
                    if new_content != content:
                        content = new_content
                        modified = True
                        print(f"  - Replaced intent action in {os.path.basename(path)}")

                if target_package in content:
                    new_content = re.sub(
                        r'(invoke-virtual\s+\{.*?\},\s+Landroid/content/Intent;->setPackage\()"com\.android\.vending"',
                        f'\\1"{proxy_package}"',
                        content
                    )
                    if new_content != content:
                        content = new_content
                        modified = True
                        print(f"  - Replaced setPackage in {os.path.basename(path)}")
                    new_content = re.sub(
                        r'(const-string\s+\S+,\s*)"com\.android\.vending"',
                        f'\\1"{proxy_package}"',
                        content
                    )
                    if new_content != content:
                        content = new_content
                        modified = True
                        print(f"  - Replaced const-string com.android.vending in {os.path.basename(path)}")

                if modified:
                    with open(path, 'w', encoding='utf-8') as f: f.write(content)
                    patched_count += 1

        print(f"[*] [IAPSmaliPatcher] Tổng số file đã vá: {patched_count}")
        return patched_count