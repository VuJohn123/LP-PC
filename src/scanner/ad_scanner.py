import re
from androguard.core.apk import APK

class AdScanner:
    def __init__(self, apk_path):
        self.apk = APK(apk_path)
        self.ad_activities = []
        self.ad_providers = []

    def scan_manifest(self):
        print("[*] [AdScanner] Scanning for ad activities...")
        ad_patterns = [
            r'com\.google\.android\.gms\.ads\..*', r'com\.facebook\.ads\..*',
            r'com\.unity3d\.ads\..*', r'com\.applovin\..*', r'com\.ironsource\..*',
            r'com\.mopub\..*', r'com\.inmobi\..*', r'com\.vungle\..*', r'com\.chartboost\..*',
            r'com\.adcolony\..*', r'com\.startapp\..*', r'.*\.AdActivity$', r'.*\.InterstitialAd.*',
            r'.*\.RewardedVideo.*', r'.*\.RewardedAd.*'
        ]
        for activity in self.apk.get_activities():
            for pat in ad_patterns:
                if re.match(pat, activity):
                    self.ad_activities.append(activity)
                    break
        print(f"[*] [AdScanner] Found {len(self.ad_activities)} ad activities")
        return self.ad_activities, self.ad_providers