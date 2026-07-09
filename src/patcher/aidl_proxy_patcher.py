import os
import shutil

class AIDLProxyPatcher:
    def __init__(self, decompiled_path, proxy_source_dir=None):
        self.decompiled_path = decompiled_path
        self.proxy_source = proxy_source_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', 'tools', 'proxy_service', 'smali'
        )

    def patch(self):
        print("[*] Injecting AIDL Proxy Service...")
        target_smali = None
        for d in os.listdir(self.decompiled_path):
            if d.startswith('smali'):
                target_smali = os.path.join(self.decompiled_path, d)
                break
        if not target_smali:
            target_smali = os.path.join(self.decompiled_path, 'smali')
            os.makedirs(target_smali, exist_ok=True)

        count = 0
        for root, dirs, files in os.walk(self.proxy_source):
            for file in files:
                src = os.path.join(root, file)
                rel = os.path.relpath(src, self.proxy_source)
                dest = os.path.join(target_smali, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src, dest)
                count += 1
        print(f"[+] Copied {count} proxy files")

        manifest_path = os.path.join(self.decompiled_path, "AndroidManifest.xml")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = f.read()

        service_decl = '''
        <service android:name="com.android.vending.billing.IInAppBillingServiceProxy"
                 android:exported="true"
                 android:permission="android.permission.BIND_GET_INSTALL_PACKAGES">
            <intent-filter>
                <action android:name="com.android.vending.billing.IInAppBillingService.BIND" />
            </intent-filter>
        </service>'''

        if 'IInAppBillingServiceProxy' not in manifest:
            manifest = manifest.replace('</application>', service_decl + '\n</application>')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(manifest)
            print("[+] Service declaration added to manifest")
        return True