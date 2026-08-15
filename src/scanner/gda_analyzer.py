import subprocess
import os
import tempfile
import re
import logging

logger = logging.getLogger(__name__)

class GDAAnalyzer:
    def __init__(self, gda_path=None):
        self.gda_exe = gda_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'tools', 'GDA', 'GDA.exe'
        )

    def analyze(self, apk_path, output_report=None):
        logger.debug(f"[*] [GDA] Analyzing {os.path.basename(apk_path)}...")
        findings = {'license_classes': [], 'iap_classes': [], 'ad_urls': []}
        if not os.path.exists(self.gda_exe):
            logger.warning("[!] GDA not found. Skipping.")
            return findings
        
        if not output_report:
            output_report = tempfile.mktemp(suffix='.txt')
        
        try:
            cmd = [self.gda_exe, '-a', apk_path, '-o', output_report]
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if os.path.exists(output_report):
                with open(output_report, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Tìm class dựa trên pattern thực tế từ GDA output
                license_pattern = r'L(?:com/google/android/vending/licensing/LicenseValidator;?)'
                findings['license_classes'] = re.findall(license_pattern, content)
                
                iap_pattern = r'L(?:com/android/vending/billing/IInAppBillingService\$Stub;?)'
                findings['iap_classes'] = re.findall(iap_pattern, content)
                
                ad_urls = re.findall(r'https?://[^"\'\s]+(?:doubleclick|admob|applovin|unityads|googlesyndication)[^"\'\s]*', content)
                findings['ad_urls'] = ad_urls[:20]
        except Exception as e:
            logger.error(f"[!] GDA analysis error: {e}")
        finally:
            if output_report and os.path.exists(output_report):
                try: os.remove(output_report)
                except Exception: pass
        
        return findings