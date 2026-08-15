import subprocess

def install_apk(apk_path):
    print("[*] [ADB] Installing APK...")
    cmd = ['adb', 'install', '-r', apk_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if 'Success' in proc.stdout:
        print("[+] [ADB] Install successful")
        return True
    else:
        raise RuntimeError(f"Install failed: {proc.stderr}")

def setup_reverse_port(remote_port, local_port):
    print(f"[*] [ADB] Setting up reverse port {remote_port} -> {local_port}...")
    cmd = ['adb', 'reverse', f'tcp:{remote_port}', f'tcp:{local_port}']
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0

def check_root():
    try:
        result = subprocess.run(['adb', 'shell', 'su', '-c', 'id'], capture_output=True, text=True, timeout=5)
        return 'uid=0' in result.stdout
    except Exception:
        return False