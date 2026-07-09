import os, shutil, tempfile

def create_magisk_module(services_jar_path, output_zip):
    tmp = tempfile.mkdtemp()
    framework_dir = os.path.join(tmp, 'system', 'framework')
    os.makedirs(framework_dir, exist_ok=True)
    shutil.copy(services_jar_path, os.path.join(framework_dir, 'services.jar'))

    with open(os.path.join(tmp, 'module.prop'), 'w') as f:
        f.write("id=lp_pc_signature_patch\nname=LP-PC Signature Patch\nversion=v1\nversionCode=1\nauthor=LP-PC Suite\ndescription=Disable APK signature verification\n")

    with open(os.path.join(tmp, 'post-fs-data.sh'), 'w') as f:
        f.write("#!/system/bin/sh\nmount -o bind $MODDIR/system/framework/services.jar /system/framework/services.jar\n")
    os.chmod(os.path.join(tmp, 'post-fs-data.sh'), 0o755)

    shutil.make_archive(output_zip.replace('.zip', ''), 'zip', tmp)
    shutil.rmtree(tmp)
    return output_zip