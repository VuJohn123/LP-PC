import threading
import time
import socket
from core.device_bridge import setup_reverse_port
from patcher.iap_proxy_server import IAPProxyServer
from patcher.iap_smali_patcher import IAPSmaliPatcher
from patcher.signature_patcher import SignatureVerifyPatcher
from patcher.iap_dex_patcher import IAPDexPatcher

class IAPBypass:
    def __init__(self, decompiled_path: str, mode: str = 'proxy', proxy_port: int = 8888,
                 log_callback=print, file_cache=None):
        self.decompiled_path = decompiled_path
        self.mode = mode
        self.proxy_port = proxy_port
        self.log = log_callback
        self.file_cache = file_cache
        if mode == 'dex':
            self.dex_patcher = IAPDexPatcher(decompiled_path, log_callback=log_callback, file_cache=file_cache)
        else:
            self.proxy_server = IAPProxyServer(port=proxy_port)
            self.smali_patcher = IAPSmaliPatcher(decompiled_path)
            self.signature_patcher = SignatureVerifyPatcher(decompiled_path, file_cache=file_cache)
            self.proxy_thread = None

    def _wait_for_proxy(self, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            try:
                sock = socket.create_connection(('localhost', self.proxy_port), timeout=1)
                sock.close()
                return True
            except:
                time.sleep(0.5)
        return False

    def execute(self) -> bool:
        if self.mode == 'dex':
            return self.dex_patcher.patch() > 0
        else:
            sig_patched = self.signature_patcher.patch()
            self.proxy_thread = threading.Thread(target=self.proxy_server.start, daemon=True)
            self.proxy_thread.start()
            if not self._wait_for_proxy():
                self.log("[!] Proxy server did not start in time")
                return False
            if not setup_reverse_port(self.proxy_port, self.proxy_port):
                self.log("[!] ADB reverse failed")
            patched_smali = self.smali_patcher.patch_billing_calls(
                proxy_host='localhost', proxy_port=self.proxy_port
            )
            return (sig_patched + patched_smali) > 0

    def execute_with_report(self):
        report = {'patterns': {}, 'total_patched': 0}
        if self.mode == 'dex':
            return self.dex_patcher.patch_with_report()
        else:
            sig_patched = self.signature_patcher.patch()
            report['patterns']['Signature checks'] = sig_patched > 0
            self.proxy_thread = threading.Thread(target=self.proxy_server.start, daemon=True)
            self.proxy_thread.start()
            if not self._wait_for_proxy():
                report['patterns']['Proxy server'] = False
                return report
            report['patterns']['Proxy server'] = True
            setup_reverse_port(self.proxy_port, self.proxy_port)
            patched_smali = self.smali_patcher.patch_billing_calls(
                proxy_host='localhost', proxy_port=self.proxy_port
            )
            report['patterns']['Smali billing intent'] = patched_smali > 0
            report['total_patched'] = sig_patched + patched_smali
            return report