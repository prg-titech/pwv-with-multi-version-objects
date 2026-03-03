LINE_CLEAR_SCORES = {
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}

class Score:
    def __init__(self):
        self.total_score = 0

    def install(self, bus):
        self._subscriptions = [("line_cleared", self._on_line_cleared)]
        for event_name, callback in self._subscriptions:
            bus.on(event_name, callback)

    def uninstall(self, bus):
        for event_name, callback in self._subscriptions:
            bus.off(event_name, callback)

    def _on_line_cleared(self, payload):
        cleared = payload["cleared"]
        self.total_score += LINE_CLEAR_SCORES.get(cleared, cleared * 200)
