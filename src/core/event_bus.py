class EventBus:
    """
    Mô phỏng cơ chế Intent/Event của Android.
    Cho phép các thành phần giao tiếp một cách lỏng lẻo.
    """
    def __init__(self):
        self._listeners = {}

    def subscribe(self, event_type, callback):
        """Đăng ký lắng nghe một loại sự kiện."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        print(f"[EventBus] {callback.__name__} subscribed to '{event_type}'")

    def emit(self, event_type, data=None):
        """Phát ra một sự kiện."""
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                callback(data)
            print(f"[EventBus] Emitted '{event_type}' with data: {str(data)[:100]}...")

# Singleton bus toàn cục
event_bus = EventBus()