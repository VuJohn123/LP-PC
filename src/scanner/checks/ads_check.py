import re

def check_ads(apk, findings, available_patches):
    ad_networks = {
        'AdMob': [r'com\.google\.android\.gms\.ads', r'AdActivity', r'AdMob'],
        'Facebook Ads': [r'com\.facebook\.ads'],
        'Unity Ads': [r'com\.unity3d\.ads'],
        'AppLovin': [r'com\.applovin'],
        'IronSource': [r'com\.ironsource'],
        'Vungle': [r'com\.vungle'],
        'Chartboost': [r'com\.chartboost'],
        'AdColony': [r'com\.adcolony'],
        'MoPub': [r'com\.mopub'],
        'InMobi': [r'com\.inmobi'],
        'StartApp': [r'com\.startapp'],
    }
    found_networks = []
    for activity in apk.get_activities():
        for name, patterns in ad_networks.items():
            for pat in patterns:
                if re.search(pat, activity):
                    if name not in found_networks:
                        found_networks.append(name)
    if found_networks:
        findings.append({
            'type': 'ads', 'color': 'blue',
            'title': 'Google Ads Detected',
            'description': f'Ad networks: {", ".join(found_networks)}',
            'details': found_networks, 'action': 'remove_ads'
        })
        available_patches.append('ads')
    else:
        findings.append({
            'type': 'no_ads', 'color': None,
            'title': 'Google Ads', 'description': 'Not detected',
            'details': ['No ad networks found'], 'action': None
        })