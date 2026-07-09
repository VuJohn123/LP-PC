# patcher/lpdiff_analyzer.py
import re
import zipfile
import os
import tempfile
import shutil

class LPDiffAnalyzer:
    """
    Công cụ tạo custom patch từ sự khác biệt giữa file gốc và file đã vá.
    Hỗ trợ mask toán hạng để pattern có thể sống sót qua các bản cập nhật nhỏ.
    """
    def __init__(self, original_smali, patched_smali):
        self.orig = original_smali
        self.patched = patched_smali

    def generate_pattern(self, mask_operands=True):
        """Trả về nội dung file patch."""
        with open(self.orig, 'r', encoding='utf-8', errors='ignore') as f:
            orig_lines = f.readlines()
        with open(self.patched, 'r', encoding='utf-8', errors='ignore') as f:
            patched_lines = f.readlines()

        instructions_orig = self._extract_instructions(orig_lines)
        instructions_patched = self._extract_instructions(patched_lines)

        patch_lines = []
        i = 0
        j = 0
        while i < len(instructions_orig) and j < len(instructions_patched):
            if instructions_orig[i] == instructions_patched[j]:
                i += 1
                j += 1
            else:
                # Tìm block thay đổi
                orig_block = self._get_change_block(instructions_orig, i)
                patch_block = self._get_change_block(instructions_patched, j)

                pattern = self._block_to_pattern(orig_block, mask_operands)
                replacement = '\n'.join(patch_block)

                patch_lines.append(f"{pattern} -> {replacement}")
                i += len(orig_block)
                j += len(patch_block)

        return '\n'.join(patch_lines)

    def _extract_instructions(self, lines):
        """Trích xuất danh sách các instruction, bỏ qua comment và label."""
        insts = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('.') and not line.startswith('#') and ':' not in line:
                insts.append(line)
        return insts

    def _get_change_block(self, insts, start, max_size=5):
        """Lấy block các dòng thay đổi liên tiếp."""
        return insts[start:start+max_size]

    def _block_to_pattern(self, block, mask_operands):
        """
        Chuyển block thành regex pattern.
        Nếu mask_operands=True, tự động mask các toán hạng có thể thay đổi.
        """
        pattern = ''
        for inst in block:
            if mask_operands:
                # Mask register (v0, v1, p0...)
                masked = re.sub(r'\bv\d+\b', r'v\\d+', inst)
                masked = re.sub(r'\bp\d+\b', r'p\\d+', masked)
                # Mask label (:cond_xx, :goto_xx...)
                masked = re.sub(r':\w+', r':\\w+', masked)
                # Mask string literals (giữ nguyên cấu trúc)
                masked = re.sub(r'"(.*?)"', r'"\\w*"', masked)
                # Mask các tham số invoke
                masked = re.sub(r'\{.*?\}', r'\\{.*?\\}', masked)
                # Escape regex đặc biệt
                pattern += re.escape(masked).replace(r'\{\.\*\?\}', r'\{.*?\}') + '\n'
            else:
                pattern += re.escape(inst) + '\n'
        return pattern.rstrip('\n')

    def save_patch(self, output_path, target_filename="classes.dex"):
        """Lưu patch ra file .txt."""
        content = f"[{target_filename}]\n{self.generate_pattern()}"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def save_lpzip(self, output_zip, target_filename="classes.dex"):
        """Lưu patch ra file .lpzip."""
        tmp_dir = tempfile.mkdtemp()
        txt_path = os.path.join(tmp_dir, "patch.txt")
        self.save_patch(txt_path, target_filename)
        with zipfile.ZipFile(output_zip, 'w') as zf:
            zf.write(txt_path, arcname=os.path.basename(txt_path))
        shutil.rmtree(tmp_dir)
        return output_zip