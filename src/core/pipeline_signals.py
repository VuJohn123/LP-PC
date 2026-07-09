from PyQt6.QtCore import QObject, pyqtSignal

class PipelineSignals(QObject):
    """Tín hiệu để cập nhật GUI từ pipeline"""
    progress = pyqtSignal(int, int)        # current, total
    status = pyqtSignal(str)               # thông báo trạng thái
    patch_complete = pyqtSignal(str, str)  # mode, kết quả
    finished = pyqtSignal(bool, str)       # success, output_path