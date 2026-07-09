import subprocess
import os
import shutil
import tempfile
import zipfile

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))

def aab_to_apk(aab_path, output_dir=None, keystore=None, log_callback=print):
    """
    Chuyển đổi file .aab sang .apk sử dụng bundletool.
    Yêu cầu: bundletool.jar trong thư mục tools/.
    """
    bundletool_jar = os.path.join(TOOLS_DIR, 'bundletool.jar')
    if not os.path.exists(bundletool_jar):
        raise FileNotFoundError("bundletool.jar not found. Please download it to tools/")

    if output_dir is None:
        output_dir = os.path.dirname(aab_path)

    # Tạo file APK set từ AAB
    apks_output = os.path.join(output_dir, 'app.apks')
    cmd_build = [
        'java', '-jar', bundletool_jar,
        'build-apks',
        f'--bundle={aab_path}',
        f'--output={apks_output}',
        '--mode=universal'
    ]
    if keystore:
        cmd_build.append(f'--ks={keystore}')
        cmd_build.append('--ks-pass=pass:android')
        cmd_build.append('--ks-key-alias=androiddebugkey')
    else:
        cmd_build.append('--overwrite')

    log_callback(f"[*] [Bundletool] Building APK from AAB...")
    proc = subprocess.run(cmd_build, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Bundletool build failed: {proc.stderr}")

    # Giải nén APK từ file .apks (thực chất là zip)
    apk_output = os.path.join(output_dir, os.path.basename(aab_path).replace('.aab', '.apk'))
    with zipfile.ZipFile(apks_output, 'r') as z:
        # Tìm file universal.apk hoặc standalones/universal.apk
        universal_apk = None
        for name in z.namelist():
            if 'universal' in name and name.endswith('.apk'):
                universal_apk = name
                break
        if not universal_apk:
            for name in z.namelist():
                if name.startswith('standalones/') and name.endswith('.apk'):
                    universal_apk = name
                    break
        if universal_apk:
            with z.open(universal_apk) as src, open(apk_output, 'wb') as dst:
                dst.write(src.read())
            log_callback(f"[*] [Bundletool] Universal APK extracted: {apk_output}")
        else:
            raise RuntimeError("No universal APK found in bundle")

    os.remove(apks_output)
    return apk_output