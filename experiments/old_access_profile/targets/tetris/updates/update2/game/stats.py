class Stats:
    def __init__(self):
        self.lock_count = 0
        self.total_lines = 0

    def install(self, bus):
        self._subscriptions = [
            ("piece_locked", self._on_piece_locked),
            ("line_cleared", self._on_line_cleared),
        ]
        for event_name, callback in self._subscriptions:
            bus.on(event_name, callback)

    def uninstall(self, bus):
        for event_name, callback in self._subscriptions:
            bus.off(event_name, callback)

    def _on_piece_locked(self, payload):
        self.lock_count += 1

    def _on_line_cleared(self, payload):
        self.total_lines = payload["total_lines"]
