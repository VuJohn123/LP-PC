import json
import os
import time

class PatchHistory:
    """Lưu và quản lý lịch sử các lần patch."""
    def __init__(self, history_dir=None):
        if history_dir is None:
            history_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workspace', 'history')
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)
        self.history_file = os.path.join(self.history_dir, 'patch_history.json')
        self.history = self._load()

    def _load(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def add_record(self, apk_path, mode, success, output_path, patches_applied):
        record = {
            'apk': apk_path,
            'mode': mode,
            'success': success,
            'output': output_path,
            'patches': patches_applied,
            'timestamp': time.time()
        }
        self.history.insert(0, record)
        if len(self.history) > 100:
            self.history = self.history[:100]
        self._save()

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
        self._save()