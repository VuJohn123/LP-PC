import os, tempfile, shutil, zipfile, subprocess

class AndroidSystemPatcher:
    def __init__(self):
        self.adb = 'adb'
        self.tools_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tools')

    def create_magisk_module(self, output_zip, android_version=None):
        print("[*] Creating Magisk module...")
        tmp_dir = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp_dir, 'system', 'framework'), exist_ok=True)
            if android_version:
                sample_jar = os.path.join(self.tools_dir, 'patched_services', f'services_{android_version}.jar')
                if os.path.exists(sample_jar):
                    shutil.copy(sample_jar, os.path.join(tmp_dir, 'system', 'framework', 'services.jar'))
                    print(f"[+] Copied patched services.jar for Android {android_version}")
                else:
                    print(f"[!] No pre-patched services.jar for Android {android_version}")
            with open(os.path.join(tmp_dir, 'module.prop'), 'w') as f:
                f.write("""id=lp_pc_signature_patch
name=LP-PC Signature Verification Disabler
version=v1.0
versionCode=1
author=LP-PC Suite
description=Disable APK signature verification for Lucky Patcher compatibility
template=1
""")
            with open(os.path.join(tmp_dir, 'post-fs-data.sh'), 'w') as f:
                f.write("""#!/system/bin/sh
MODDIR=${0%/*}
if [ -f "$MODDIR/system/framework/services.jar" ]; then
    mount -o bind "$MODDIR/system/framework/services.jar" /system/framework/services.jar
fi
""")
            os.chmod(os.path.join(tmp_dir, 'post-fs-data.sh'), 0o755)
            shutil.make_archive(output_zip.replace('.zip', ''), 'zip', tmp_dir)
            print(f"[+] Magisk module created: {output_zip}")
            return output_zip
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def push_and_flash(self, module_zip):
        print("[*] Pushing module to device...")
        try:
            dest = '/sdcard/lp_pc_signature_patch.zip'
            subprocess.run([self.adb, 'push', module_zip, dest], check=True)
            print(f"[+] Module pushed to {dest}. Please flash via Magisk Manager.")
            return True
        except Exception as e:
            print(f"[!] ADB push failed: {e}")
            return False