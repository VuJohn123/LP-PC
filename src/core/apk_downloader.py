import requests
import zipfile
import os
import shutil
import tempfile
import re
import json
from urllib.parse import urlparse, unquote

class APKDownloader:
    """
    Tải APK từ nhiều nguồn: APKPure, APKMody, Uptodown, Google Play (qua scraper).
    Hỗ trợ chuyển đổi .xapk => .apk.
    """
    BASE_URLS = {
        'apkpure': 'https://d.apkpure.com/b/APK',
        'apkmody': 'https://apkmody.io',
        'uptodown': 'https://api.uptodown.com/v4',
    }

    def __init__(self, download_dir=None, log_callback=print):
        self.download_dir = download_dir or os.path.join(os.path.expanduser("~"), "Downloads", "LP_Downloads")
        self.log = log_callback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def search_google_play(self, query, n_hits=10):
        """Tìm kiếm ứng dụng trên Google Play (sử dụng google-play-scraper)."""
        try:
            from google_play_scraper import search
            results = search(query, n_hits=n_hits)
            apps = []
            for app in results:
                apps.append({
                    'title': app['title'],
                    'package': app['appId'],
                    'developer': app['developer'],
                    'score': app.get('score', 0),
                    'icon': app.get('icon', ''),
                    'url': f"https://play.google.com/store/apps/details?id={app['appId']}"
                })
            return apps
        except ImportError:
            self.log("[!] google-play-scraper not installed. Install with: pip install google-play-scraper")
            return []
        except Exception as e:
            self.log(f"[!] Google Play search error: {e}")
            return []

    def get_google_play_app_info(self, package_name):
        """Lấy thông tin chi tiết về ứng dụng từ Google Play."""
        try:
            from google_play_scraper import app
            info = app(package_name)
            return {
                'title': info['title'],
                'package': package_name,
                'developer': info['developer'],
                'version': info.get('version', ''),
                'size': info.get('size', ''),
                'installs': info.get('installs', ''),
                'score': info.get('score', 0),
                'icon': info.get('icon', ''),
                'description': info.get('description', '')[:200] + '...'
            }
        except Exception as e:
            self.log(f"[!] Google Play info error: {e}")
            return None

    def download_from_apkpure(self, package_name, output_path=None):
        """Tải APK từ APKPure dựa trên package name."""
        url = f"{self.BASE_URLS['apkpure']}/{package_name}?version=latest"
        return self._download_file(url, output_path or self._get_output_path(package_name, 'apkpure'))

    def download_from_apkmody(self, package_name, output_path=None):
        """Tải APK từ APKMody."""
        url = f"https://apkmody.io/download?package={package_name}"
        try:
            response = self.session.get(url, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            download_link = soup.find('a', {'class': 'download-btn'})
            if download_link and download_link.get('href'):
                return self._download_file(download_link['href'], output_path or self._get_output_path(package_name, 'apkmody'))
        except ImportError:
            self.log("[!] beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
        except Exception as e:
            self.log(f"[!] APKMody download error: {e}")
        return None

    def download_from_uptodown(self, package_name, output_path=None):
        """Tải APK từ Uptodown (bản gốc, không mod)."""
        try:
            url = f"https://api.uptodown.com/v4/apps/{package_name}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'latest_version' in data['data']:
                    version = data['data']['latest_version']
                    download_url = version.get('download_url', '')
                    if download_url:
                        return self._download_file(download_url, output_path or self._get_output_path(package_name, 'uptodown'))
        except Exception as e:
            self.log(f"[!] Uptodown download error: {e}")
        return None

    def download_from_direct_url(self, url, output_path=None):
        """Tải APK từ một URL trực tiếp (hỗ trợ cả .apk và .xapk)."""
        self.log(f"[*] [Downloader] Downloading from: {url}")
        try:
            response = self.session.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                raise RuntimeError(f"Download failed: HTTP {response.status_code}")

            filename = self._extract_filename(url, response)
            if output_path is None:
                output_path = os.path.join(self.download_dir, filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if int(progress) % 10 == 0:
                            self.log(f"[*] [Downloader] Progress: {progress:.0f}%")

            self.log(f"[*] [Downloader] Downloaded: {output_path} ({downloaded} bytes)")
            return output_path
        except Exception as e:
            self.log(f"[!] [Downloader] Direct download error: {e}")
            return None

    def process_xapk(self, xapk_path, output_dir=None):
        """Giải nén file .xapk và merge thành một APK duy nhất."""
        self.log(f"[*] [Downloader] Processing XAPK: {xapk_path}")
        if output_dir is None:
            output_dir = os.path.dirname(xapk_path)

        temp_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(xapk_path, 'r') as z:
                z.extractall(temp_dir)

            manifest_path = os.path.join(temp_dir, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                base_apk = manifest.get('package_name', '') + '.apk'
                base_apk_path = os.path.join(temp_dir, base_apk)
                if not os.path.exists(base_apk_path):
                    base_apk_path = None
                    for f in os.listdir(temp_dir):
                        if f.endswith('.apk') and not f.startswith('config.'):
                            base_apk_path = os.path.join(temp_dir, f)
                            break
            else:
                base_apk_path = None
                for f in os.listdir(temp_dir):
                    if f.endswith('.apk') and ('base' in f.lower() or 'master' in f.lower()):
                        base_apk_path = os.path.join(temp_dir, f)
                        break
                if not base_apk_path:
                    apks = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.apk')]
                    if not apks:
                        raise ValueError("No APK files found in XAPK")
                    base_apk_path = apks[0]

            merged_apk = os.path.join(output_dir, os.path.basename(xapk_path).replace('.xapk', '.apk'))
            self._merge_apks(base_apk_path, temp_dir, merged_apk)

            self.log(f"[*] [Downloader] XAPK merged to: {merged_apk}")
            return merged_apk
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _download_file(self, url, output_path):
        """Tải file từ URL về output_path."""
        self.log(f"[*] [Downloader] Downloading from: {url}")
        response = self.session.get(url, stream=True, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Download failed: HTTP {response.status_code}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        self.log(f"[*] [Downloader] Downloaded: {output_path}")
        return output_path

    def _get_output_path(self, package_name, source):
        """Tạo đường dẫn output dựa trên package name và nguồn."""
        return os.path.join(self.download_dir, f"{package_name}_{source}.apk")

    def _extract_filename(self, url, response):
        """Trích xuất tên file từ URL hoặc header Content-Disposition."""
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            if 'filename*=' in content_disposition:
                match = re.search(r"filename\*=UTF-8''(.+)", content_disposition)
                if match:
                    return unquote(match.group(1))
            match = re.search(r'filename="?(.+?)"?$', content_disposition)
            if match:
                return match.group(1).strip('"')

        path = urlparse(url).path
        filename = os.path.basename(path)
        if filename and '.' in filename:
            return unquote(filename)
        return 'downloaded.apk'

    def _merge_apks(self, base_apk_path, source_dir, output_apk):
        """Merge tất cả APK trong source_dir vào base APK."""
        with zipfile.ZipFile(output_apk, 'w') as zout:
            with zipfile.ZipFile(base_apk_path, 'r') as zin:
                for item in zin.namelist():
                    zout.writestr(item, zin.read(item))
            for f in os.listdir(source_dir):
                apk_path = os.path.join(source_dir, f)
                if f.endswith('.apk') and apk_path != base_apk_path:
                    with zipfile.ZipFile(apk_path, 'r') as zin:
                        for item in zin.namelist():
                            if item not in zout.namelist():
                                zout.writestr(item, zin.read(item))