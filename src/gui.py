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
                 apktool_jobs=None, apktool_memory="4096m", keep_workspace=True,
                 clone_package=None, split_apk=False, signals=None, force_reanalyze=False, **kwargs):
    t0 = time.time()
    log_callback(f"[*] ========== LP-PC Suite v4 — Pipeline Start ==========")
    log_callback(f"[*] APK: {os.path.basename(apk_path)}")
    log_callback(f"[*] Raw mode: {mode}")

    if mode.startswith('multi:'):
        modes = mode[6:].split(',')
    else:
        modes = [m.strip() for m in mode.split(',') if m.strip()]

    all_modes = {**MODE_MAP, **plugin_manager.get_all_modes()}
    mapped_modes = [all_modes.get(m, m) for m in modes]
    log_callback(f"[*] Mapped modes: {mapped_modes}")

    if forced_package_id is not None and (not isinstance(forced_package_id, int) or forced_package_id <= 0 or forced_package_id > 127):
        forced_package_id = None

    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace')
    decompiled_dir = os.path.join(base_dir, 'decompiled')
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(decompiled_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    if apktool_jobs is None:
        apktool_jobs = min(os.cpu_count() or 4, 8)

    gc.disable()
    log_callback("[*] [GC] Disabled for performance")

    try:
        if use_gda:
            try:
                from scanner.gda_analyzer import GDAAnalyzer
                GDAAnalyzer().analyze(apk_path)
            except Exception as e:
                log_callback(f"[!] [GDA] Failed: {e}")

        if split_apk and os.path.isdir(apk_path):
            merged_apk = os.path.join(tempfile.mkdtemp(), "merged.apk")
            merge_split_apks(apk_path, merged_apk, log_callback)
            apk_path = merged_apk

        ad_activities, _ = AdScanner(apk_path).scan_manifest()
        log_callback(f"[*] [Scanner] Found {len(ad_activities)} ad activities")

        needs_resources = any(m in mapped_modes for m in ['change_perms', 'resign'])
        log_callback(f"[*] [Apktool] Decompiling (no_res={not needs_resources})...")
        decompile_apk(apk_path, decompiled_dir, force=True, no_res=not needs_resources,
                      jobs=apktool_jobs, max_memory=apktool_memory, log_callback=log_callback)
        log_callback("[*] [Apktool] Decompile completed.")

        file_cache = FileContentCache(decompiled_dir)
        set_file_cache(file_cache)

        patches_applied, patch_reports = execute_modes(
            mapped_modes, decompiled_dir, ad_activities, apk_path, log_callback, signals
        )
        file_cache.flush(log_callback)

        if patches_applied:
            Watermarker.add_watermark(decompiled_dir, patches_applied, apk_path)

        log_callback("[*] [Apktool] Recompiling...")
        patched_apk = os.path.join(output_dir, 'patched.apk')
        recompile_apk(decompiled_dir, patched_apk, forced_package_id=forced_package_id, log_callback=log_callback)
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

        elapsed = time.time() - t0
        if patches_applied:
            log_callback(f"[✔] [Done] Patches applied: {', '.join(patches_applied)} in {elapsed:.1f}s")
        else:
            log_callback(f"[✔] [Done] APK rebuilt without modifications in {elapsed:.1f}s")

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
        gc.enable()
        log_callback("[*] [GC] Enabled")
        if not keep_workspace:
            shutil.rmtree(decompiled_dir, ignore_errors=True)
        else:
            log_callback(f"[*] Workspace kept at: {decompiled_dir}")


def main():
    parser = argparse.ArgumentParser(description='LP-PC Suite v4 — Ultra Fast')
    parser.add_argument('apk', nargs='?', help='Path to APK file or folder (for split APK)')
    parser.add_argument('--mode', default='all', help='Comma-separated modes')
    parser.add_argument('--custom-patch', help='Path to custom patch file')
    parser.add_argument('--key-type', default='testkey', help='Key type')
    parser.add_argument('--forced-package-id', type=int, help='Forced package ID')
    parser.add_argument('--fast', action='store_true', help='Fast mode')
    parser.add_argument('--gda', action='store_true', help='Use GDA pre-analysis')
    parser.add_argument('--apktool-jobs', type=int, help='Threads for apktool')
    parser.add_argument('--apktool-memory', default='4096m', help='Java heap memory')
    parser.add_argument('--keep', action='store_true', default=True, help='Keep workspace')
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

    success, _, _ = run_pipeline(
        args.apk, args.mode, key_type=args.key_type,
        forced_package_id=args.forced_package_id,
        fast_mode=args.fast, use_gda=args.gda,
        apktool_jobs=args.apktool_jobs, apktool_memory=args.apktool_memory,
        keep_workspace=not args.clean, clone_package=args.clone_package,
        split_apk=args.split_apk, force_reanalyze=args.force_reanalyze
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()