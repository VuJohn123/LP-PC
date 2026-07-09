import argparse
import os
import sys
import time
import shutil
import traceback
import tempfile
import gc

from core.mode_registry import MODE_MAP
from core.pipeline_executor import set_file_cache, execute_modes
from core.plugin_manager import PluginManager
from core.patch_history import PatchHistory
from core.apk_utils import decompile_apk, recompile_apk, sign_apk, merge_split_apks
from core.device_bridge import install_apk
from scanner.ad_scanner import AdScanner
from patcher.watermarker import Watermarker
from core.smali_utils import FileContentCache, APKCache

plugin_manager = PluginManager()
patch_history = PatchHistory()
apk_cache = APKCache()

try:
    from core.event_bus import event_bus
    REACTIVE_SYSTEM = True
except ImportError:
    REACTIVE_SYSTEM = False

def run_pipeline(apk_path, mode='all', log_callback=print, key_type='testkey',
                 forced_package_id=None, fast_mode=True, use_gda=False,
                 apktool_jobs=4, apktool_memory="4096m", keep_workspace=True,
                 clone_package=None, split_apk=False, signals=None, force_reanalyze=False, **kwargs):
    start_time = time.time()
    log_callback(f"[*] ========== LP-PC Suite v4 – Pipeline Start ==========")
    log_callback(f"[*] APK: {apk_path}")
    log_callback(f"[*] Raw mode: {mode}")

    if mode.startswith('multi:'):
        modes = mode[6:].split(',')
    else:
        modes = [m.strip() for m in mode.split(',') if m.strip()]

    all_modes = {}
    all_modes.update(MODE_MAP)
    all_modes.update(plugin_manager.get_all_modes())
    mapped_modes = [all_modes.get(m, m) for m in modes]
    log_callback(f"[*] Mapped modes: {mapped_modes}")

    if forced_package_id is not None and (not isinstance(forced_package_id, int) or forced_package_id <= 0 or forced_package_id > 127):
        forced_package_id = None

    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace')
    decompiled_dir = os.path.join(base_dir, 'decompiled')
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(decompiled_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Tắt garbage collection để tăng hiệu suất
    gc.disable()
    log_callback("[*] [GC] Garbage collection disabled for performance")

    try:
        if use_gda:
            log_callback("[*] [GDA] Analyzing APK...")
            try:
                from scanner.gda_analyzer import GDAAnalyzer
                gda = GDAAnalyzer()
                gda_findings = gda.analyze(apk_path)
                log_callback(f"[*] [GDA] License classes: {gda_findings.get('license_classes', [])}")
                log_callback(f"[*] [GDA] IAP classes: {gda_findings.get('iap_classes', [])}")
            except Exception as e:
                log_callback(f"[!] [GDA] Failed: {e}")

        if split_apk and os.path.isdir(apk_path):
            log_callback("[*] Split APK mode detected. Merging splits...")
            merged_apk = os.path.join(tempfile.mkdtemp(), "merged.apk")
            merge_split_apks(apk_path, merged_apk, log_callback)
            apk_path = merged_apk

        scanner = AdScanner(apk_path)
        ad_activities, _ = scanner.scan_manifest()
        log_callback(f"[*] [Scanner] Found {len(ad_activities)} ad activities")

        log_callback(f"[*] [Apktool] Decompiling to {decompiled_dir} ...")
        decompile_apk(apk_path, decompiled_dir, force=True, jobs=apktool_jobs,
                      max_memory=apktool_memory, log_callback=log_callback, max_retries=2, use_cache=True)
        log_callback("[*] [Apktool] Decompile completed.")

        # Tạo file cache để tối ưu hiệu suất
        file_cache = FileContentCache(decompiled_dir)
        set_file_cache(file_cache)

        patches_applied, patch_reports = execute_modes(
            mapped_modes, decompiled_dir, ad_activities, apk_path, log_callback, signals
        )

        # Ghi tất cả thay đổi từ cache ra đĩa
        file_cache.flush(log_callback)

        if patches_applied:
            Watermarker.add_watermark(decompiled_dir, patches_applied, apk_path)

        log_callback("[*] [Apktool] Recompiling APK...")
        patched_apk = os.path.join(output_dir, 'patched.apk')
        recompile_apk(decompiled_dir, patched_apk, forced_package_id=forced_package_id,
                      log_callback=log_callback, max_retries=1)
        log_callback("[*] [Apktool] Recompile completed.")

        signed_apk = sign_apk(patched_apk, key_type=key_type, log_callback=log_callback)
        final_apk = os.path.join(output_dir, os.path.basename(signed_apk))
        shutil.move(signed_apk, final_apk)
        log_callback(f"[✔] [Output] APK saved to: {final_apk}")

        try:
            install_apk(final_apk)
            log_callback("[✔] [ADB] Installed on device.")
        except Exception as e:
            log_callback(f"[i] [ADB] Install skipped: {e}")

        total_time = time.time() - start_time
        if patches_applied:
            log_callback(f"[✔] [Done] Patches applied: {', '.join(patches_applied)} in {total_time:.1f}s")
        else:
            log_callback(f"[✔] [Done] APK rebuilt without modifications in {total_time:.1f}s")

        patch_history.add_record(apk_path, mode, True, final_apk, patches_applied)

        if REACTIVE_SYSTEM:
            event_bus.emit('apk.patched', {'path': final_apk, 'original': apk_path})

        if signals:
            signals.finished.emit(True, final_apk)

        return True, final_apk, patch_reports

    except Exception as e:
        log_callback(f"[!] [Error] Pipeline failed: {e}")
        traceback.print_exc()
        patch_history.add_record(apk_path, mode, False, '', [])
        if signals:
            signals.finished.emit(False, '')
        return False, None, {}
    finally:
        # Bật lại garbage collection
        gc.enable()
        log_callback("[*] [GC] Garbage collection enabled")
        if not keep_workspace:
            shutil.rmtree(decompiled_dir, ignore_errors=True)
            log_callback("[*] Workspace decompiled directory cleaned up.")
        else:
            log_callback(f"[*] Workspace kept at: {decompiled_dir}")


def main():
    parser = argparse.ArgumentParser(description='LP-PC Suite v4 – Fast & Smart')
    parser.add_argument('apk', nargs='?', help='Path to APK file or folder (for split APK)')
    parser.add_argument('--mode', default='all', help='Comma-separated modes')
    parser.add_argument('--custom-patch', help='Path to custom patch file')
    parser.add_argument('--key-type', default='testkey', help='Key type')
    parser.add_argument('--forced-package-id', type=int, help='Forced package ID')
    parser.add_argument('--fast', action='store_true', help='Fast mode (only main classes)')
    parser.add_argument('--gda', action='store_true', help='Use GDA pre-analysis')
    parser.add_argument('--apktool-jobs', type=int, default=4, help='Threads for apktool')
    parser.add_argument('--apktool-memory', default='4096m', help='Java heap memory')
    parser.add_argument('--keep', action='store_true', default=True, help='Keep workspace (default)')
    parser.add_argument('--clean', action='store_true', help='Remove workspace after patching')
    parser.add_argument('--clone-package', help='New package name for clone mode')
    parser.add_argument('--split-apk', action='store_true', help='Treat input as folder of split APKs')
    parser.add_argument('--force-reanalyze', action='store_true', help='Force re-analysis even if cache exists')
    args = parser.parse_args()

    if args.custom_patch:
        os.environ['LP_CUSTOM_PATCH'] = args.custom_patch

    if not args.apk:
        print("Usage: python main.py <apk> --mode ...")
        sys.exit(1)

    keep = not args.clean

    success, _, _ = run_pipeline(
        args.apk, args.mode, key_type=args.key_type,
        forced_package_id=args.forced_package_id,
        fast_mode=args.fast, use_gda=args.gda,
        apktool_jobs=args.apktool_jobs, apktool_memory=args.apktool_memory,
        keep_workspace=keep, clone_package=args.clone_package, split_apk=args.split_apk,
        force_reanalyze=args.force_reanalyze
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()