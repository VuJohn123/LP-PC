import os
import re

class PatchConflictDetector:
    """
    Phát hiện xung đột giữa các patcher dựa trên file chúng sẽ sửa.
    """
    MODE_TARGETS = {
        'license': ['LicenseValidator.smali', 'LicenseChecker.smali'],
        'ads': ['AndroidManifest.xml'],
        'ads_offline': ['isOnline', 'isConnected'],
        'sig_disable': ['verifyPurchase', 'checkSignature'],
        'iap_dex': ['BillingClient', 'IInAppBillingService'],
        'iap_proxy': ['IInAppBillingService', 'AndroidManifest.xml'],
        'aidl_proxy': ['IInAppBillingServiceProxy', 'AndroidManifest.xml'],
        'change_perms': ['AndroidManifest.xml'],
        'clone': ['AndroidManifest.xml', 'smali'],
    }

    @classmethod
    def detect_conflicts(cls, modes):
        conflicts = []
        for i in range(len(modes)):
            for j in range(i + 1, len(modes)):
                targets_i = cls.MODE_TARGETS.get(modes[i], [])
                targets_j = cls.MODE_TARGETS.get(modes[j], [])
                if any(t in targets_j for t in targets_i):
                    conflicts.append((modes[i], modes[j]))
        return conflicts