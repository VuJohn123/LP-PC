import subprocess
import re

def get_installed_apps():
    try:
        proc = subprocess.run(['adb', 'shell', 'pm', 'list', 'packages', '-3'], capture_output=True, text=True)
        packages = []
        for line in proc.stdout.split('\n'):
            m = re.search(r'package:(.+)', line)
            if m:
                pkg = m.group(1)
                packages.append({'name': pkg.split('.')[-1].capitalize(), 'package': pkg})
        return packages
    except FileNotFoundError:
        return []
    except Exception:
        return []