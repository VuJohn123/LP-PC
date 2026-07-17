import subprocess
import os
import shutil
import zipfile
import hashlib

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
NAILGUN = shutil.which('ng')


def get_apk_hash(apk_path):
    hasher = hashlib.md5()
    with open(apk_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_cache_dir(apk_path, base_cache_dir=None):
    if base_cache_dir is None:
        base_cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace', 'cache')
    apk_hash = get_apk_hash(apk_path)
    cache_dir = os.path.join(base_cache_dir, apk_hash)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def decompile_apk(apk_path, output_dir, force=True, no_res=True,
                  jobs=None, max_memory="4096m", log_callback=print, max_retries=2, use_cache=True):
    if jobs is None:
        jobs = min(os.cpu_count() or 4, 8)

    if use_cache and not force:
        cache_dir = get_cache_dir(apk_path)
        if os.path.exists(os.path.join(cache_dir, 'apktool.yml')):
            log_callback("[*] Cache hit — using cached decompiled APK")
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir, ignore_errors=True)
            shutil.copytree(cache_dir, output_dir)
            return output_dir

    current_jobs = jobs
    current_memory = max_memory
    use_no_res = no_res

    for attempt in range(max_retries + 1):
        if NAILGUN:
            cmd = [NAILGUN, os.path.join(TOOLS_DIR, 'apktool.jar')]
        else:
            cmd = ['java', f'-Xmx{current_memory}', '-jar', os.path.join(TOOLS_DIR, 'apktool.jar')]

        cmd += ['d', apk_path, '-o', output_dir, '-f', '--jobs', str(current_jobs)]
        if use_no_res:
            cmd.append('--no-res')

        log_callback(f"[*] [Apktool] Attempt {attempt+1}/{max_retries+1}: jobs={current_jobs}, no_res={use_no_res}")
        proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.stdout:
            log_callback(proc.stdout[-500:])
        if proc.stderr:
            log_callback(proc.stderr[-500:])

        if proc.returncode == 0:
            if use_cache:
                cache_dir = get_cache_dir(apk_path)
                if os.path.exists(cache_dir):
                    shutil.rmtree(cache_dir, ignore_errors=True)
                shutil.copytree(output_dir, cache_dir)
            return output_dir

        if attempt == 0:
            use_no_res = True
        elif attempt == 1:
            current_jobs = 1
            current_memory = "8192m"

    raise RuntimeError(f"Decompile failed after {max_retries + 1} attempts")


def recompile_apk(decompiled_path, output_apk, forced_package_id=None,
                  log_callback=print, max_retries=1):
    for attempt in range(max_retries + 1):
        if NAILGUN:
            cmd = [NAILGUN, os.path.join(TOOLS_DIR, 'apktool.jar')]
        else:
            cmd = ['java', '-Xmx4096m', '-jar', os.path.join(TOOLS_DIR, 'apktool.jar')]

        cmd += ['b', decompiled_path, '-o', output_apk]
        if forced_package_id is not None:
            cmd += ['--forced-package-id', str(forced_package_id)]

        log_callback(f"[*] [Apktool] Recompile attempt {attempt+1}")
        proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.stdout:
            log_callback(proc.stdout[-500:])

        if proc.returncode == 0:
            return output_apk

        if attempt == 0:
            cmd.append('--use-aapt2')

    raise RuntimeError(f"Recompile failed after {max_retries + 1} attempts")


def sign_apk(apk_path, key_type='testkey', log_callback=print):
    log_callback(f"[*] [Signer] Signing with {key_type}...")
    if key_type == 'testkey':
        if NAILGUN:
            cmd = [NAILGUN, os.path.join(TOOLS_DIR, 'uber-apk-signer.jar'), '--apks', apk_path]
        else:
            cmd = ['java', '-jar', os.path.join(TOOLS_DIR, 'uber-apk-signer.jar'), '--apks', apk_path]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Signing failed: {proc.stderr}")
        return apk_path.replace('.apk', '-aligned-debugSigned.apk')
    else:
        from core.sign_with_key import APKSigner
        return APKSigner(TOOLS_DIR).sign_apk(apk_path, key_type)


def merge_split_apks(input_dir, output_apk, log_callback=print):
    apk_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.apk')])
    if not apk_files:
        raise ValueError("No APK files found")
    base_apk = next((f for f in apk_files if 'base' in f.lower() or 'master' in f.lower()), apk_files[0])
    shutil.copy2(os.path.join(input_dir, base_apk), output_apk)
    with zipfile.ZipFile(output_apk, 'a') as zout:
        for f in apk_files:
            if f == base_apk:
                continue
            with zipfile.ZipFile(os.path.join(input_dir, f), 'r') as zin:
                for item in zin.namelist():
                    if item not in zout.namelist():
                        zout.writestr(item, zin.read(item))
    return output_apk