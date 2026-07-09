import re
from androguard.core.dex import DEX

def check_license(apk, apk_path, get_all_dex_bytes, findings, available_patches):
    blacklist = [
        'OfflineLicenseHelper', 'LicenseManager', 'BidToken', 'Moloco',
        'ImpLvlRevData', 'ClientBidToken', 'LicensingListener',
    ]
    dex_list = get_all_dex_bytes()
    for dex_name, dex_bytes in dex_list:
        try:
            dex = DEX(dex_bytes)
            for cls in dex.get_classes():
                class_name = cls.get_name()
                if any(bl in class_name for bl in blacklist):
                    continue
                if re.search(r'(license|licensing|lvl|LicenseCheck|LicenseValidat)', class_name, re.IGNORECASE):
                    methods = []
                    for method in cls.get_methods():
                        mn = method.get_name()
                        if re.search(r'(checkAccess|allow|verify|checkLicense|isLicensed)', mn, re.IGNORECASE):
                            methods.append(mn)
                    findings.append({
                        'type': 'license', 'color': 'green',
                        'title': 'License Verification Found',
                        'description': f'Class: {class_name}',
                        'details': methods[:3] if methods else ['License check detected'],
                        'action': 'remove_license'
                    })
                    available_patches.append('license')
                    return
        except Exception as e:
            print(f"[!] [AppDeepAnalyzer] Lỗi phân tích DEX {dex_name}: {e}")
            continue

    for activity in apk.get_activities():
        if 'license' in activity.lower() and 'exoplayer' not in activity.lower():
            findings.append({
                'type': 'license', 'color': 'green',
                'title': 'License Verification Found',
                'description': f'Activity: {activity}',
                'details': ['License-related activity detected'],
                'action': 'remove_license'
            })
            return

    findings.append({
        'type': 'no_license', 'color': None,
        'title': 'License Verification', 'description': 'Not detected',
        'details': ['No LVL or license check found'], 'action': None
    })