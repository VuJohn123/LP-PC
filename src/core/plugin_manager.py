import os
import importlib
import sys
from pathlib import Path

class PluginManager:
    """Quản lý plugin: tự động tải các file .py trong thư mục plugins/"""
    def __init__(self, plugin_dir=None):
        if plugin_dir is None:
            plugin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plugins')
        self.plugin_dir = Path(plugin_dir)
        self.plugins = {}
        self.load_plugins()

    def load_plugins(self):
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            init_file = self.plugin_dir / '__init__.py'
            if not init_file.exists():
                init_file.touch()
            return

        sys.path.insert(0, str(self.plugin_dir.parent))
        for file in self.plugin_dir.glob('*.py'):
            if file.name.startswith('_'):
                continue
            module_name = file.stem
            try:
                module = importlib.import_module(f'plugins.{module_name}')
                if hasattr(module, 'register'):
                    plugin_info = module.register()
                    self.plugins[module_name] = plugin_info
                    print(f"[PluginManager] Loaded plugin: {module_name} - {plugin_info.get('name', 'Unknown')}")
            except Exception as e:
                print(f"[PluginManager] Failed to load plugin {module_name}: {e}")

    def get_patcher(self, mode_name):
        """Tìm patcher từ plugin cho mode cụ thể"""
        for plugin_name, info in self.plugins.items():
            patchers = info.get('patchers', {})
            if mode_name in patchers:
                return patchers[mode_name]
        return None

    def get_all_modes(self):
        """Trả về tất cả mode từ plugin"""
        modes = {}
        for plugin_name, info in self.plugins.items():
            modes.update(info.get('patchers', {}))
        return modes