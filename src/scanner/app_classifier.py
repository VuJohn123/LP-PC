import re, zipfile
from pathlib import Path
from androguard.core.apk import APK
from androguard.core.dex import DEX
from patcher.watermarker import Watermarker
from scanner.checks.license_check import check_license
from scanner.checks.ads_check import check_ads
from scanner.checks.iap_check import check_iap
from scanner.checks.security_check import check_root_detection, check_lp_detection
from core.smali_utils import APKCache

apk_cache = APKCache()

class AppClassifier:
    def __init__(self, apk_path=None):
        self.apk_path = apk_path
        self.apk = APK(apk_path) if apk_path else None

    def classify(self):
        if not self.apk: return ['white']
        colors = []
        if self._has_license(): colors.append('green')
        if self._has_ads(): colors.append('blue')
        if self._is_system(): colors.append('purple')
        return colors if colors else ['white']

    def _has_license(self):
        try:
            dex_bytes = self._get_dex_bytes()
            if dex_bytes and len(dex_bytes) >= 2:
                dex = DEX(dex_bytes)
                for cls in dex.get_classes():
                    class_name = cls.get_name()
                    if 'OfflineLicenseHelper' in class_name or 'LicenseManager' in class_name: continue
                    if re.search(r'(license|licensing|lvl|LicenseCheck|LicenseValidat)', class_name, re.IGNORECASE):
                        return True
        except: pass
        return False

    def _has_ads(self):
        ad_pat = r'com\.google\.android\.gms\.ads|com\.facebook\.ads|com\.unity3d\.ads'
        for act in self.apk.get_activities():
            if re.search(ad_pat, act): return True
        return False

    def _is_system(self):
        pkg = self.apk.get_package()
        return pkg.startswith('com.android.') or pkg.startswith('com.google.android.')

    def _get_dex_bytes(self):
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as z:
                dex_files = [n for n in z.namelist() if n.endswith('.dex')]
                if dex_files:
                    data = z.read(dex_files[0])
                    if len(data) >= 2: return data
        except: pass
        return None


class AppDeepAnalyzer:
    def __init__(self, apk_path, patches_dir=None):
        self.apk_path = apk_path
        self.apk = APK(apk_path)
        self.patches_dir = patches_dir or str(Path(apk_path).parent.parent / "patches")
        self.findings = []
        self.available_patches = []

    def analyze(self, force_reanalyze=False):
        # Kiểm tra cache
        if not force_reanalyze:
            cached = apk_cache.get_cached_analysis(self.apk_path)
            if cached:
                self.findings = cached['findings']
                self.available_patches = [f['action'] for f in self.findings if f.get('action')]
                return self.findings

        self._check_watermark()
        check_license(self.apk, self.apk_path, self._get_all_dex_bytes, self.findings, self.available_patches)
        check_ads(self.apk, self.findings, self.available_patches)
        check_iap(self.apk, self._get_all_dex_bytes, self.findings, self.available_patches)
        self._check_custom_patch()
        self._check_system_app()
        self._check_dangerous_permissions()
        self._count_components()
        check_root_detection(self._get_all_dex_bytes, self.findings)
        check_lp_detection(self._get_all_dex_bytes, self.findings)

        # Lưu cache
        summary = self.get_summary()
        colors = self.get_colors()
        apk_cache.save_analysis(self.apk_path, self.findings, summary, colors)

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
                            if len(data) >= 2: dex_list.append((name, data))
                        except Exception as e:
                            print(f"[!] [AppDeepAnalyzer] Không thể đọc {name}: {e}")
        except Exception as e:
            print(f"[!] [AppDeepAnalyzer] Không thể mở APK: {e}")
        return dex_list

    def _check_watermark(self):
        marker = Watermarker.check_watermark(self.apk_path)
        if marker:
            import time as time_module
            self.findings.append({
                'type': 'watermark', 'color': None,
                'title': '✅ LP-PC Suite Patched',
                'description': f"Đã vá vào {time_module.strftime('%Y-%m-%d %H:%M', time_module.localtime(marker['timestamp']))}",
                'details': marker.get('patches', []), 'action': None
            })

    def _check_custom_patch(self):
        patch_files = []
        try:
            patches_path = Path(self.patches_dir)
            if patches_path.exists():
                for f in patches_path.iterdir():
                    if f.suffix in ['.txt', '.lpzip']: patch_files.append(f.name)
        except: pass
        if patch_files:
            self.findings.append({
                'type': 'custom_patch', 'color': 'yellow',
                'title': 'Custom Patch Available',
                'description': f'{len(patch_files)} patch(es) found',
                'details': patch_files, 'action': 'apply_custom_patch'
            })
            self.available_patches.append('custom')
        else:
            self.findings.append({
                'type': 'no_custom_patch', 'color': None,
                'title': 'Custom Patch', 'description': 'Not available',
                'details': [f'No patches found in {self.patches_dir}'], 'action': None
            })

    def _check_system_app(self):
        pkg = self.apk.get_package()
        if pkg.startswith('com.android.') or pkg.startswith('com.google.android.'):
            has_boot = any('BOOT_COMPLETED' in str(r) for r in self.apk.get_receivers())
            if has_boot:
                self.findings.append({
                    'type': 'system_boot', 'color': 'purple',
                    'title': 'System Startup App', 'description': 'Starts at boot time',
                    'details': ['System application', 'Has BOOT_COMPLETED receiver'], 'action': None
                })
            else:
                self.findings.append({
                    'type': 'system', 'color': 'orange',
                    'title': 'System Application', 'description': 'Pre-installed system app',
                    'details': ['Part of system partition'], 'action': None
                })

    def _check_dangerous_permissions(self):
        dangerous = [
            'android.permission.READ_SMS', 'android.permission.SEND_SMS',
            'android.permission.RECEIVE_SMS', 'android.permission.READ_CONTACTS',
            'android.permission.ACCESS_FINE_LOCATION', 'android.permission.CAMERA',
            'android.permission.RECORD_AUDIO', 'android.permission.READ_PHONE_STATE',
            'android.permission.CALL_PHONE', 'android.permission.WRITE_EXTERNAL_STORAGE',
            'android.permission.READ_EXTERNAL_STORAGE',
        ]
        found = [p.split('.')[-1] for p in self.apk.get_permissions() if p in dangerous]
        if found:
            self.findings.append({
                'type': 'permissions', 'color': None,
                'title': 'Dangerous Permissions', 'description': f'{len(found)} dangerous permission(s)',
                'details': found, 'action': 'manage_permissions'
            })

    def _count_components(self):
        acts = len(self.apk.get_activities())
        srv = len(self.apk.get_services())
        recv = len(self.apk.get_receivers())
        prov = len(self.apk.get_providers())
        self.findings.append({
            'type': 'components', 'color': None,
            'title': 'App Components',
            'description': f'Activities: {acts}, Services: {srv}, Receivers: {recv}, Providers: {prov}',
            'details': [f'Activities: {acts}', f'Services: {srv}', f'Receivers: {recv}', f'Providers: {prov}'],
            'action': None
        })