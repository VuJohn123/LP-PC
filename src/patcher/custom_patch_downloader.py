import requests, os, zipfile

class CustomPatchDownloader:
    BASE_URL = "https://patch.chelpus.com"

    def __init__(self, download_dir=None):
        self.download_dir = download_dir or os.path.join(
            os.path.expanduser("~"), "Documents", "LP_PC_Suite", "patches"
        )

    def download_patch(self, patch_name):
        url = f"{self.BASE_URL}/{patch_name}"
        os.makedirs(self.download_dir, exist_ok=True)
        dest = os.path.join(self.download_dir, patch_name)
        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(dest, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[+] Downloaded: {dest}")
                return dest
            else:
                print(f"[!] Failed to download {patch_name}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"[!] Download error: {e}")
            return None

    def extract_lpzip(self, lpzip_path, output_dir=None):
        if not output_dir:
            output_dir = os.path.dirname(lpzip_path)
        with zipfile.ZipFile(lpzip_path, 'r') as zf:
            zf.extractall(output_dir)
        return output_dir