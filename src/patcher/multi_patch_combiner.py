import os
from patcher.ad_remover import AdRemover
from patcher.license_patcher import LicensePatcher
from patcher.license_extreme import LicenseExtremePatcher
from patcher.iap_bypass import IAPBypass
from patcher.ads_blocklist import AdsBlocklistPatcher
from patcher.permission_changer import PermissionChanger
from patcher.custom_patch import CustomPatchParser, CustomPatchApplier
from patcher.aidl_proxy_patcher import AIDLProxyPatcher
from patcher.signature_patcher import SignatureVerifyPatcher

PATCHER_REGISTRY = {
    'ads': (AdRemover, 'remove_activities'),
    'license': (LicensePatcher, 'patch_license_check'),
    'license_reverse': (LicenseExtremePatcher, 'patch_reverse_auto'),
    'license_extreme': (LicenseExtremePatcher, 'patch_extreme'),
    'license_amazon': (LicenseExtremePatcher, 'patch_amazon_market'),
    'license_samsung': (LicenseExtremePatcher, 'patch_samsung_apps'),
    'iap_dex': (IAPBypass, 'execute', {'mode': 'dex'}),
    'iap_proxy': (IAPBypass, 'execute', {'mode': 'proxy'}),
    'ads_break': (AdsBlocklistPatcher, 'make_ads_offline'),
    'ads_offline': (AdsBlocklistPatcher, 'make_ads_offline'),
    'ads_other': (AdsBlocklistPatcher, 'remove_ad_urls_from_smali'),
    'ads_full_offline': (AdsBlocklistPatcher, 'make_ads_offline'),
    'change_perms': (PermissionChanger, None),
    'sig_disable': (SignatureVerifyPatcher, 'patch'),
    'aidl_proxy': (AIDLProxyPatcher, 'patch'),
}

class MultiPatchCombiner:
    def __init__(self, decompiled_path):
        self.decompiled_path = decompiled_path

    def apply_patches(self, modes, ad_activities=None):
        total = 0
        for m in modes:
            if m not in PATCHER_REGISTRY:
                print(f"[!] Unknown mode: {m}")
                continue
            cls, method, *extra = PATCHER_REGISTRY[m]
            extra = extra[0] if extra else {}
            try:
                instance = cls(self.decompiled_path)
                if m == 'ads' and ad_activities:
                    result = getattr(instance, method)(ad_activities)
                elif isinstance(extra, dict) and 'mode' in extra:
                    result = getattr(instance, method)()
                else:
                    result = getattr(instance, method)()
                total += result if isinstance(result, int) else (1 if result else 0)
            except Exception as e:
                print(f"[!] Error applying {m}: {e}")
        return total