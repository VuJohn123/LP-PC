import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.smali_utils import FileContentCache
from core.mode_registry import get_mode_group

from patcher.license_patcher import LicensePatcher
from patcher.license_extreme import LicenseExtremePatcher
from patcher.ad_remover import AdRemover
from patcher.ads_blocklist import AdsBlocklistPatcher
from patcher.iap_bypass import IAPBypass
from patcher.permission_changer import PermissionChanger
from patcher.custom_patch import CustomPatchParser, CustomPatchApplier
from patcher.signature_integrity_patcher import SignatureIntegrityPatcher
from patcher.signature_fake_archive_patcher import SignatureFakeArchivePatcher
from patcher.iap_manager import IAPManager
from patcher.gms_spoofer import GMSSpoofer
from patcher.event_logger import EventLogger

file_cache = None

def set_file_cache(cache):
    global file_cache
    file_cache = cache

def process_mode(mode_name, decompiled_dir, ad_activities, apk_path, log_callback):
    """Xử lý một mode duy nhất, trả về dict kết quả."""
    global file_cache
    result = {'patched': False, 'label': '', 'report': None}
    try:
        if mode_name == 'license':
            lp = LicensePatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            cnt = lp.patch_license_check()
            if cnt > 0: result['patched'] = True; result['label'] = "License (auto)"
        elif mode_name == 'license_reverse':
            lp = LicensePatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            cnt = lp.patch_reverse_auto()
            if cnt > 0: result['patched'] = True; result['label'] = "License (reverse)"
        elif mode_name == 'license_extreme':
            le = LicenseExtremePatcher(decompiled_dir, file_cache=file_cache)
            cnt = le.patch_extreme()
            if cnt > 0: result['patched'] = True; result['label'] = "License (extreme)"
        elif mode_name == 'license_amazon':
            le = LicenseExtremePatcher(decompiled_dir, file_cache=file_cache)
            cnt = le.patch_amazon_market()
            if cnt > 0: result['patched'] = True; result['label'] = "License (Amazon)"
        elif mode_name == 'license_samsung':
            le = LicenseExtremePatcher(decompiled_dir, file_cache=file_cache)
            cnt = le.patch_samsung_apps()
            if cnt > 0: result['patched'] = True; result['label'] = "License (Samsung)"
        elif mode_name == 'ads':
            remover = AdRemover(decompiled_dir, file_cache=file_cache)
            if remover.remove_activities(ad_activities): result['patched'] = True; result['label'] = "Ads removed"
        elif mode_name == 'ads_break':
            ap = AdsBlocklistPatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            n = ap.make_ads_offline()
            if n > 0: result['patched'] = True; result['label'] = "Ads receiver broken"
        elif mode_name == 'ads_offline':
            ap = AdsBlocklistPatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            n = ap.make_ads_offline()
            if n > 0: result['patched'] = True; result['label'] = "Ads offline"
        elif mode_name == 'ads_other':
            ap = AdsBlocklistPatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            n = ap.remove_ad_urls_from_smali()
            if n > 0: result['patched'] = True; result['label'] = "Ads other"
        elif mode_name == 'ads_full_offline':
            ap = AdsBlocklistPatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            n1 = ap.make_ads_offline(); n2 = ap.remove_ad_urls_from_smali()
            if n1 > 0 or n2 > 0: result['patched'] = True; result['label'] = "Ads full offline"
        elif mode_name == 'iap_dex':
            bypass = IAPBypass(decompiled_dir, mode='dex', log_callback=log_callback, file_cache=file_cache)
            report = bypass.execute_with_report()
            if report['total_patched'] > 0: result['patched'] = True; result['label'] = "IAP (dex)"
            result['report'] = report
        elif mode_name == 'iap_proxy':
            bypass = IAPBypass(decompiled_dir, mode='proxy', log_callback=log_callback, file_cache=file_cache)
            report = bypass.execute_with_report()
            if report['total_patched'] > 0: result['patched'] = True; result['label'] = "IAP (proxy)"
            result['report'] = report
        elif mode_name == 'sig_disable':
            from patcher.signature_patcher import SignatureVerifyPatcher
            sp = SignatureVerifyPatcher(decompiled_dir, file_cache=file_cache)
            cnt = sp.patch()
            if cnt > 0: result['patched'] = True; result['label'] = "Signature verification disabled"
        elif mode_name == 'sig_integrity':
            sip = SignatureIntegrityPatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            cnt = sip.patch()
            if cnt > 0: result['patched'] = True; result['label'] = "Signature integrity patched"
        elif mode_name == 'sig_fake_archive':
            sfp = SignatureFakeArchivePatcher(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            cnt = sfp.patch()
            if cnt > 0: result['patched'] = True; result['label'] = "Signature fake archive patched"
        elif mode_name == 'change_perms':
            pc = PermissionChanger(decompiled_dir, file_cache=file_cache)
            if pc.remove_permissions(): result['patched'] = True; result['label'] = "Permissions changed"
        elif mode_name == 'custom':
            custom_file = os.environ.get('LP_CUSTOM_PATCH')
            if custom_file:
                parser = CustomPatchParser(custom_file)
                instructions = parser.parse()
                applier = CustomPatchApplier(decompiled_dir, file_cache=file_cache)
                n = applier.apply(instructions)
                if n > 0: result['patched'] = True; result['label'] = f"Custom patch ({n} files)"
        elif mode_name == 'save_purchase':
            IAPManager().save_for_restore_enabled = True
            result['patched'] = True; result['label'] = "Save purchase enabled"
        elif mode_name == 'auto_repeat':
            IAPManager().auto_repeat_enabled = True
            result['patched'] = True; result['label'] = "Auto-repeat enabled"
        elif mode_name == 'clone':
            from patcher.app_cloner import AppCloner
            new_package = os.path.basename(apk_path).replace('.apk', '.clone') if apk_path else 'cloned.app'
            cloner = AppCloner(apk_path, new_package)
            cloner.clone()
            result['patched'] = True; result['label'] = f"Cloned to {new_package}"
        elif mode_name == 'backup':
            import shutil
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace', 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            shutil.copy2(apk_path, os.path.join(backup_dir, os.path.basename(apk_path)))
            result['patched'] = True; result['label'] = "Backup created"
        elif mode_name == 'gms_spoof':
            spoofer = GMSSpoofer(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            cnt = spoofer.patch()
            if cnt > 0: result['patched'] = True; result['label'] = "GMS Spoofed"
        elif mode_name == 'event_logger':
            logger = EventLogger(decompiled_dir, log_callback=log_callback, file_cache=file_cache)
            cnt = logger.inject_logging()
            if cnt > 0: result['patched'] = True; result['label'] = "Event logger injected"
    except Exception as e:
        log_callback(f"[!] [{mode_name}] Error: {e}")
    return result


def execute_modes(mapped_modes, decompiled_dir, ad_activities, apk_path, log_callback, signals=None):
    """Thực thi tất cả các mode, trả về (patches_applied, patch_reports)."""
    global file_cache
    patches_applied = []
    patch_reports = {}
    total_modes = len(mapped_modes)
    completed_modes = 0

    parallel_modes, sequential_modes = _classify_modes(mapped_modes)

    if parallel_modes:
        with ThreadPoolExecutor(max_workers=min(4, len(parallel_modes))) as executor:
            futures = {executor.submit(process_mode, m, decompiled_dir, ad_activities, apk_path, log_callback): m
                       for m in parallel_modes}
            for future in as_completed(futures):
                mode_name = futures[future]
                try:
                    result = future.result()
                    if result['patched']: patches_applied.append(result['label'])
                    if 'report' in result and result['report']: patch_reports[mode_name] = result['report']
                    completed_modes += 1
                    if signals:
                        signals.progress.emit(completed_modes, total_modes)
                        signals.status.emit(f"Đã hoàn thành {mode_name}")
                except Exception as e:
                    log_callback(f"[!] [{mode_name}] Failed: {e}")
                    completed_modes += 1

    for m in sequential_modes:
        try:
            result = process_mode(m, decompiled_dir, ad_activities, apk_path, log_callback)
            if result['patched']: patches_applied.append(result['label'])
            if 'report' in result and result['report']: patch_reports[m] = result['report']
            completed_modes += 1
            if signals:
                signals.progress.emit(completed_modes, total_modes)
                signals.status.emit(f"Đã hoàn thành {m}")
        except Exception as e:
            log_callback(f"[!] [{m}] Failed: {e}")
            completed_modes += 1

    return patches_applied, patch_reports


def _classify_modes(mapped_modes):
    """Phân loại mode thành song song và tuần tự."""
    parallel_modes = []
    sequential_modes = []
    used_groups = set()
    for m in mapped_modes:
        group = get_mode_group(m)
        if group and group not in used_groups:
            parallel_modes.append(m)
            used_groups.add(group)
        elif not group:
            parallel_modes.append(m)
        else:
            sequential_modes.append(m)
    return parallel_modes, sequential_modes