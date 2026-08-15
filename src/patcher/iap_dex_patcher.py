import os
import re
from core.smali_utils import get_all_smali_files, REGEX_IAP_BILLING_METHOD

class IAPDexPatcher:
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
        return self.patch_with_report()['total_patched']

    def patch_with_report(self):
        self.log("[*] [IAPDexPatcher] Starting ultra-smart patch...")
        report = {'patterns': {}, 'total_patched': 0}
        target_methods = [
            'launchBillingFlow', 'getBuyIntent', 'queryPurchases', 'querySkuDetails',
            'isBillingSupported', 'consumePurchase', 'getPurchases',
            'UnityPurchasing', 'InitiatePurchase', 'PurchaseProduct',
            'ProcessPurchase', 'ConfirmPurchase', 'FinishTransaction',
            'InAppPurchase', 'MakePurchase', 'CompletePurchase',
            'startPurchase', 'buyProduct', 'makePurchase', 'doPayment',
            'requestPurchase', 'processPurchase', 'sendPurchase',
            'startPayment', 'doBilling', 'executePayment',
            'onPurchase', 'onBuy', 'onPayment', 'onCheckout',
        ]
        patched_files = 0
        skipped_files = 0

        for filepath in get_all_smali_files(self.decompiled_path):
            if len(filepath) > 250:
                skipped_files += 1
                continue
            try:
                content = self._read_file(filepath)
            except Exception:
                skipped_files += 1
                continue

            if not any(m in content for m in target_methods):
                continue

            modified = False
            for match in REGEX_IAP_BILLING_METHOD.finditer(content):
                full_method = match.group(0)
                method_signature = match.group(1)
                return_type = match.group(2)

                if not any(m.lower() in method_signature.lower() for m in target_methods):
                    continue

                if return_type == 'V':
                    replacement = self._generate_void_method(full_method.split('\n')[0])
                else:
                    replacement = self._generate_bundle_method(full_method.split('\n')[0], method_signature)

                content = content.replace(full_method, replacement)
                modified = True
                report['patterns'][method_signature] = True

            if modified:
                try:
                    self._write_file(filepath, content)
                    patched_files += 1
                    self.log(f"[+] [IAPDexPatcher] Đã vá: {os.path.basename(filepath)}")
                except Exception:
                    skipped_files += 1

        report['total_patched'] = patched_files
        self.log(f"[*] [IAPDexPatcher] Tổng số file đã vá: {patched_files}, bỏ qua: {skipped_files}")
        return report

    def _generate_void_method(self, header):
        return f"{header}\n    .locals 1\n    return-void\n.end method"

    def _generate_bundle_method(self, header, method_name):
        return f"""{header}
    .locals 3
    new-instance v0, Landroid/os/Bundle;
    invoke-direct {{v0}}, Landroid/os/Bundle;-><init>()V
    const-string v1, "RESPONSE_CODE"
    const/4 v2, 0x0
    invoke-virtual {{v0, v1, v2}}, Landroid/os/Bundle;->putInt(Ljava/lang/String;I)V
    return-object v0
.end method"""