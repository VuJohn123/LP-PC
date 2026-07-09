import os
import zipfile
import tempfile
import shutil
from pathlib import Path
import subprocess

class APKSigner:
    """Ký APK với nhiều loại key khác nhau."""
    
    KEY_TYPES = {
        'testkey': 'testkey',
        'platform': 'platform',
        'media': 'media',
        'shared': 'shared',
        'release': 'release'  # tự tạo key mới
    }
    
    def __init__(self, tools_dir=None):
        if tools_dir:
            self.keys_dir = os.path.join(tools_dir, 'keys')
        else:
            self.keys_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'keys')
    
    def sign_apk(self, apk_path, key_type='testkey'):
        """
        Ký APK với loại key chỉ định.
        Nếu key không tồn tại, tự động tạo key mới.
        """
        if key_type not in self.KEY_TYPES:
            raise ValueError(f"Unknown key type: {key_type}")
        
        # Nếu dùng testkey mặc định, dùng uber-apk-signer
        if key_type == 'testkey':
            return self._sign_with_uber(apk_path)
        
        # Dùng key có sẵn hoặc tự tạo
        key_path = os.path.join(self.keys_dir, key_type)
        pk8_file = os.path.join(key_path, f'{key_type}.pk8')
        pem_file = os.path.join(key_path, f'{key_type}.x509.pem')
        
        if not os.path.exists(pk8_file) or not os.path.exists(pem_file):
            # Tự tạo key mới
            os.makedirs(key_path, exist_ok=True)
            self._generate_key(key_type, pk8_file, pem_file)
        
        return self._sign_with_jarsigner(apk_path, pk8_file, pem_file, key_type)
    
    def _sign_with_uber(self, apk_path):
        """Dùng uber-apk-signer với testkey mặc định."""
        from core.apk_utils import sign_apk as uber_sign
        return uber_sign(apk_path)
    
    def _sign_with_jarsigner(self, apk_path, pk8_file, pem_file, alias):
        """Dùng jarsigner với key đã có."""
        # Chuyển đổi pk8 + pem thành keystore JKS
        keystore = self._pk8_to_jks(pk8_file, pem_file, alias)
        
        # Ký bằng jarsigner
        signed_apk = apk_path.replace('.apk', '_signed.apk')
        cmd = [
            'jarsigner',
            '-keystore', keystore,
            '-storepass', 'android',
            '-keypass', 'android',
            '-signedjar', signed_apk,
            apk_path,
            alias
        ]
        subprocess.run(cmd, check=True)
        return signed_apk
    
    def _pk8_to_jks(self, pk8_file, pem_file, alias):
        """Chuyển đổi PK8 + PEM thành Java Keystore (JKS)."""
        keystore_path = os.path.join(tempfile.gettempdir(), f'{alias}.keystore')
        
        # Sử dụng openssl để chuyển đổi
        p12_file = os.path.join(tempfile.gettempdir(), f'{alias}.p12')
        
        # Bước 1: Tạo PKCS12 từ PEM và key
        cmd1 = [
            'openssl', 'pkcs12', '-export',
            '-in', pem_file,
            '-inkey', pk8_file,
            '-out', p12_file,
            '-name', alias,
            '-passout', 'pass:android'
        ]
        subprocess.run(cmd1, check=True, capture_output=True)
        
        # Bước 2: Import vào keystore JKS
        cmd2 = [
            'keytool', '-importkeystore',
            '-destkeystore', keystore_path,
            '-deststorepass', 'android',
            '-srckeystore', p12_file,
            '-srcstoretype', 'PKCS12',
            '-srcstorepass', 'android',
            '-alias', alias
        ]
        subprocess.run(cmd2, check=True, capture_output=True)
        
        # Dọn dẹp
        os.remove(p12_file)
        return keystore_path
    
    def _generate_key(self, key_type, pk8_file, pem_file):
        """Tạo cặp key mới."""
        # Tạo private key
        subprocess.run([
            'openssl', 'genrsa', '-out', os.path.join(os.path.dirname(pk8_file), f'{key_type}.key'), '2048'
        ], check=True)
        
        # Tạo certificate
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-key',
            os.path.join(os.path.dirname(pk8_file), f'{key_type}.key'),
            '-out', pem_file, '-days', '36500',
            '-subj', f'/CN={key_type}'
        ], check=True)
        
        # Chuyển sang PK8
        subprocess.run([
            'openssl', 'pkcs8', '-topk8', '-inform', 'PEM', '-outform', 'DER',
            '-in', os.path.join(os.path.dirname(pk8_file), f'{key_type}.key'),
            '-out', pk8_file, '-nocrypt'
        ], check=True)