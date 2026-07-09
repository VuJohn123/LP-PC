import os
import re
import zipfile
import tempfile
import shutil
from core.smali_utils import get_all_smali_files

class CustomPatchParser:
    def __init__(self, patch_file_path):
        self.path = patch_file_path

    def parse(self):
        if self.path.endswith('.lpzip'):
            return self._parse_lpzip()
        else:
            return self._parse_txt()

    def _parse_txt(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        instructions = []
        current_target = None
        current_ops = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if line.startswith('[') and ']' in line:
                if current_target:
                    instructions.append({'target_file': current_target, 'operations': current_ops})
                current_target = line[1:line.index(']')].strip()
                current_ops = []
                remaining = line[line.index(']')+1:].strip()
                if remaining and '->' in remaining:
                    pattern, replacement = remaining.split('->', 1)
                    current_ops.append({'type': 'replace', 'pattern': pattern.strip(), 'replacement': replacement.strip()})
            elif '->' in line:
                pattern, replacement = line.split('->', 1)
                current_ops.append({'type': 'replace', 'pattern': pattern.strip(), 'replacement': replacement.strip()})
        if current_target:
            instructions.append({'target_file': current_target, 'operations': current_ops})
        return instructions

    def _parse_lpzip(self):
        with zipfile.ZipFile(self.path, 'r') as zf:
            txt_files = [f for f in zf.namelist() if f.endswith('.txt')]
            if not txt_files:
                raise ValueError("No .txt found in lpzip")
            content = zf.read(txt_files[0]).decode('utf-8')
        tmp = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp, 'patch.txt')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.path = tmp_path
        instructions = self._parse_txt()
        shutil.rmtree(tmp)
        return instructions

class CustomPatchApplier:
    def __init__(self, decompiled_path, file_cache=None):
        self.decompiled_path = decompiled_path
        self.file_cache = file_cache

    def _read_file(self, path):
        if self.file_cache:
            return self.file_cache.read(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _write_file(self, path, content):
        if self.file_cache:
            self.file_cache.write(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

    def apply(self, instructions):
        patched = 0
        for instr in instructions:
            target_pattern = instr['target_file']
            matched = self._find_files(target_pattern)
            if not matched:
                print(f"[!] [CustomPatch] Target not found: {target_pattern}")
                continue
            for path in matched:
                content = self._read_file(path)
                original = content
                for op in instr['operations']:
                    if op['type'] == 'replace':
                        content = re.sub(op['pattern'], op['replacement'], content, flags=re.DOTALL)
                if content != original:
                    self._write_file(path, content)
                    patched += 1
        return patched

    def _find_files(self, target_pattern):
        matched = []
        for filepath in get_all_smali_files(self.decompiled_path):
            full = filepath
            rel = os.path.relpath(full, self.decompiled_path)
            if re.search(target_pattern, rel):
                matched.append(full)
        return matched