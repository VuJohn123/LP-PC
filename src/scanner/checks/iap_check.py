from androguard.core.dex import DEX

def check_iap(apk, get_all_dex_bytes, findings, available_patches):
    permissions = apk.get_permissions()
    if 'com.android.vending.BILLING' in permissions:
        findings.append({
            'type': 'iap', 'color': 'green',
            'title': 'InApp Purchases Available',
            'description': 'Manifest requests BILLING permission',
            'details': ['com.android.vending.BILLING permission found'],
            'action': 'iap_emulation'
        })
        if 'iap' not in available_patches:
            available_patches.append('iap')
        return

    dex_list = get_all_dex_bytes()
    for dex_name, dex_bytes in dex_list:
        try:
            dex = DEX(dex_bytes)
            for cls in dex.get_classes():
                class_name = cls.get_name()
                if 'com/android/billingclient/api/BillingClient' in class_name:
                    findings.append({
                        'type': 'iap', 'color': 'green',
                        'title': 'InApp Purchases Available',
                        'description': 'BillingClient library found',
                        'details': [class_name], 'action': 'iap_emulation'
                    })
                    if 'iap' not in available_patches: available_patches.append('iap')
                    return
                if 'IInAppBillingService' in class_name:
                    findings.append({
                        'type': 'iap', 'color': 'green',
                        'title': 'InApp Purchases Available',
                        'description': 'IInAppBillingService interface detected',
                        'details': [class_name], 'action': 'iap_emulation'
                    })
                    if 'iap' not in available_patches: available_patches.append('iap')
                    return
            for cls in dex.get_classes():
                for method in cls.get_methods():
                    if method.get_name() in ['launchBillingFlow', 'queryPurchases', 'querySkuDetails']:
                        findings.append({
                            'type': 'iap', 'color': 'green',
                            'title': 'InApp Purchases Available',
                            'description': f'Method {method.get_name()} found',
                            'details': [f'Class: {cls.get_name()}'], 'action': 'iap_emulation'
                        })
                        if 'iap' not in available_patches: available_patches.append('iap')
                        return
        except Exception as e:
            print(f"[!] [AppDeepAnalyzer] Lỗi phân tích DEX {dex_name}: {e}")
            continue

    findings.append({
        'type': 'no_iap', 'color': None,
        'title': 'InApp Purchases', 'description': 'Not detected',
        'details': ['No billing permission, BillingClient, IInAppBillingService or known methods found'],
        'action': None
    })