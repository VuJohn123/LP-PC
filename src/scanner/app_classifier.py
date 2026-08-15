import re
import zipfile
from pathlib import Path
from androguard.core.apk import APK
from androguard.core.dex import DEX
from patcher.watermarker import Watermarker
from core.smali_utils import APKCache, json_loads, json_dumps

apk_cache = APKCache()


class AppClassifier:
    def __init__(self, apk_path=None):
        self.apk_path = apk_path
        self.apk = APK(apk_path) if apk_path else None

    def classify(self):
        if not self.apk:
            return ['white']
        colors = []
        if self._has_license():
            colors.append('green')
        if self._has_ads():
            colors.append('blue')
        if self._is_system():
            colors.append('purple')
        return colors if colors else ['white']

    def _has_license(self):
        try:
            dex_bytes = self._get_dex_bytes()
            if dex_bytes and len(dex_bytes) >= 2:
                dex = DEX(dex_bytes)
                for cls in dex.get_classes():
                    class_name = cls.get_name()
                    if 'OfflineLicenseHelper' in class_name:
                        continue
                    if re.search(r'(license|licensing|lvl|LicenseCheck)', class_name, re.IGNORECASE):
                        return True
        except Exception:
            pass
        return False

    def _has_ads(self):
        for act in self.apk.get_activities():
            if re.search(r'com\.google\.android\.gms\.ads|com\.facebook\.ads|com\.unity3d\.ads', act):
                return True
        return False

    def _is_system(self):
        return self.apk.get_package().startswith(('com.android.', 'com.google.android.'))

    def _get_dex_bytes(self):
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as z:
                dex_files = [n for n in z.namelist() if n.endswith('.dex')]
                if dex_files:
                    data = z.read(dex_files[0])
                    if len(data) >= 2:
                        return data
        except Exception:
            pass
        return None


class AppDeepAnalyzer:
    def __init__(self, apk_path, patches_dir=None):
        self.apk_path = apk_path
        self.apk = APK(apk_path)
        self.patches_dir = patches_dir or str(Path(apk_path).parent.parent / "patches")
        self.findings = []
        self.available_patches = []

    def analyze(self, force_reanalyze=False):
        if not force_reanalyze:
            cached = apk_cache.get_cached_analysis(self.apk_path)
            if cached:
                self.findings = cached['findings']
                return self.findings

        self._check_watermark()
        self._check_license()
        self._check_ads()
        self._check_iap_billing()
        self._check_custom_patch()
        self._check_system_app()
        self._check_dangerous_permissions()
        self._count_components()
        self._check_root_detection()
        self._check_lp_detection()

        apk_cache.save_analysis(self.apk_path, self.findings, self.get_summary(), self.get_colors())
        return self.findings

    def get_colors(self):
        return list(set(f['color'] for f in self.findings if f.get('color'))) or ['white']

    def get_summary(self):
        package = self.apk.get_package()
        try:
            app_name = self.apk.get_app_name()
        except Exception:
            app_name = Path(self.apk_path).stem if self.apk_path else "Unknown"
        try:
            version = self.apk.get_androidversion_name()
        except Exception:
            version = ''
        size = Path(self.apk_path).stat().st_size if self.apk_path and Path(self.apk_path).exists() else 0
        return {'app_name': app_name, 'package': package, 'version': version, 'apk_path': self.apk_path, 'size': size}

    def _get_all_dex_bytes(self):
        dex_list = []
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.dex'):
                        try:
                            data = z.read(name)
                            if len(data) >= 2:
                                dex_list.append((name, data))
                        except Exception:
                            pass
        except Exception:
            pass
        return dex_list

    def _check_watermark(self):
        marker = Watermarker.check_watermark(self.apk_path)
        if marker:
            import time as tm
            self.findings.append({
                'type': 'watermark', 'color': None,
                'title': 'LP-PC Suite Patched',
                'description': f"Đã vá vào {tm.strftime('%Y-%m-%d %H:%M', tm.localtime(marker['timestamp']))}",
                'details': marker.get('patches', []), 'action': None
            })

    def _check_license(self):
        blacklist = ['OfflineLicenseHelper', 'LicenseManager', 'BidToken', 'LicensingListener']
        for _, dex_bytes in self._get_all_dex_bytes():
            try:
                dex = DEX(dex_bytes)
                for cls in dex.get_classes():
                    class_name = cls.get_name()
                    if any(bl in class_name for bl in blacklist):
                        continue
                    if re.search(r'(license|licensing|lvl|LicenseCheck)', class_name, re.IGNORECASE):
                        self.findings.append({
                            'type': 'license', 'color': 'green',
                            'title': 'License Verification Found',
                            'description': f'Class: {class_name}',
                            'details': ['License check detected'], 'action': 'remove_license'
                        })
                        return
            except Exception:
                continue
        self.findings.append({
            'type': 'no_license', 'color': None,
            'title': 'License Verification', 'description': 'Not detected',
            'details': ['No LVL found'], 'action': None
        })

    def _check_ads(self):
        ad_networks = {'AdMob': [r'com\.google\.android\.gms\.ads'], 'Facebook': [r'com\.facebook\.ads'],
                       'Unity': [r'com\.unity3d\.ads'], 'AppLovin': [r'com\.applovin'],
                       'IronSource': [r'com\.ironsource'], 'Vungle': [r'com\.vungle']}
        found = []
        for activity in self.apk.get_activities():
            for name, patterns in ad_networks.items():
                if any(re.search(p, activity) for p in patterns):
                    if name not in found:
                        found.append(name)
        if found:
            self.findings.append({
                'type': 'ads', 'color': 'blue', 'title': 'Google Ads Detected',
                'description': f'Ad networks: {", ".join(found)}', 'details': found, 'action': 'remove_ads'
            })
        else:
            self.findings.append({
                'type': 'no_ads', 'color': None, 'title': 'Google Ads', 'description': 'Not detected',
                'details': ['No ad networks found'], 'action': None
            })

    def _check_iap_billing(self):
        if 'com.android.vending.BILLING' in self.apk.get_permissions():
            self.findings.append({
                'type': 'iap', 'color': 'green', 'title': 'InApp Purchases Available',
                'description': 'Manifest requests BILLING permission',
                'details': ['com.android.vending.BILLING permission found'], 'action': 'iap_emulation'
            })
            return
        self.findings.append({
            'type': 'no_iap', 'color': None, 'title': 'InApp Purchases', 'description': 'Not detected',
            'details': ['No billing found'], 'action': None
        })

    def _check_custom_patch(self):
        self.findings.append({
            'type': 'no_custom_patch', 'color': None, 'title': 'Custom Patch', 'description': 'Not available',
            'details': [], 'action': None
        })

    def _check_system_app(self):
        if self.apk.get_package().startswith(('com.android.', 'com.google.android.')):
            self.findings.append({
                'type': 'system', 'color': 'orange', 'title': 'System Application',
                'description': 'Pre-installed system app', 'details': [], 'action': None
            })

    def _check_dangerous_permissions(self):
        dangerous = ['READ_SMS', 'SEND_SMS', 'RECEIVE_SMS', 'READ_CONTACTS', 'CAMERA', 'RECORD_AUDIO']
        found = [p.split('.')[-1] for p in self.apk.get_permissions() if any(d in p for d in dangerous)]
        if found:
            self.findings.append({
                'type': 'permissions', 'color': None, 'title': 'Dangerous Permissions',
                'description': f'{len(found)} dangerous permission(s)', 'details': found, 'action': 'manage_permissions'
            })

    def _count_components(self):
        acts = len(self.apk.get_activities())
        srv = len(self.apk.get_services())
        recv = len(self.apk.get_receivers())
        prov = len(self.apk.get_providers())
        self.findings.append({
            'type': 'components', 'color': None, 'title': 'App Components',
            'description': f'Activities: {acts}, Services: {srv}, Receivers: {recv}, Providers: {prov}',
            'details': [f'Activities: {acts}', f'Services: {srv}', f'Receivers: {recv}', f'Providers: {prov}'],
            'action': None
        })

    def _check_root_detection(self):
        keywords = ['root', 'magisk', 'supersu', 'busybox', 'isDeviceRooted', 'checkRoot']
        for _, dex_bytes in self._get_all_dex_bytes():
            try:
                dex = DEX(dex_bytes)
                for cls in dex.get_classes():
                    for method in cls.get_methods():
                        if any(kw in method.get_name().lower() for kw in keywords):
                            self.findings.append({
                                'type': 'root_detection', 'color': None, 'title': 'Root Detection',
                                'description': 'App may detect root access', 'details': [], 'action': None
                            })
                            return
            except Exception:
                continue

    def _check_lp_detection(self):
        keywords = ['luckypatcher', 'com.chelpu']
        for _, dex_bytes in self._get_all_dex_bytes():
            try:
                dex = DEX(dex_bytes)
                for cls in dex.get_classes():
                    if any(kw in cls.get_name().lower() for kw in keywords):
                        self.findings.append({
                            'type': 'lp_detection', 'color': 'red', 'title': 'LP Detection',
                            'description': 'App may detect Lucky Patcher', 'details': [], 'action': None
                        })
                        return
            except Exception:
                continue