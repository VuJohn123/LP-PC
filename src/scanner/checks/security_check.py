from androguard.core.dex import DEX

def check_root_detection(get_all_dex_bytes, findings):
    keywords = ['root', 'magisk', 'supersu', 'busybox', 'isDeviceRooted', 'checkRoot']
    dex_list = get_all_dex_bytes()
    for dex_name, dex_bytes in dex_list:
        try:
            dex = DEX(dex_bytes)
            for cls in dex.get_classes():
                for method in cls.get_methods():
                    mn = method.get_name()
                    if any(kw in mn.lower() for kw in keywords):
                        findings.append({
                            'type': 'root_detection', 'color': None,
                            'title': 'Root Detection', 'description': 'App may detect root access',
                            'details': [f'Method: {mn}'], 'action': None
                        })
                        return
        except Exception as e:
            print(f"[!] [AppDeepAnalyzer] Lỗi phân tích DEX {dex_name}: {e}")
            continue

def check_lp_detection(get_all_dex_bytes, findings):
    keywords = ['luckypatcher', 'lucky_patcher', 'lucky patcher', 'com.chelpu', 'com.android.vending.billing']
    dex_list = get_all_dex_bytes()
    for dex_name, dex_bytes in dex_list:
        try:
            dex = DEX(dex_bytes)
            for cls in dex.get_classes():
                cn = cls.get_name()
                if any(kw in cn.lower() for kw in keywords):
                    findings.append({
                        'type': 'lp_detection', 'color': 'red',
                        'title': '⚠ Lucky Patcher Detection',
                        'description': 'App may detect Lucky Patcher',
                        'details': [f'Class: {cn}'], 'action': None
                    })
                    return
        except Exception as e:
            print(f"[!] [AppDeepAnalyzer] Lỗi phân tích DEX {dex_name}: {e}")
            continue