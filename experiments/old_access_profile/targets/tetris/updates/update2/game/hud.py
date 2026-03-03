class Hud:
    def install(self, bus):
        self._subscriptions = [
            ("turn_started", self._on_turn_started),
            ("line_cleared", self._on_line_cleared),
            ("game_finished", self._on_game_finished),
        ]
        for event_name, callback in self._subscriptions:
            bus.on(event_name, callback)

    def uninstall(self, bus):
        for event_name, callback in self._subscriptions:
            bus.off(event_name, callback)

    def _on_turn_started(self, payload):
        print(f"turn={payload['turn']} piece={payload['piece']} x={payload['left']}")

    def _on_line_cleared(self, payload):
        print(f"hud total_lines={payload['total_lines']}")

    def _on_game_finished(self, payload):
        print(f"hud finished pieces={payload['locked_pieces']} lines={payload['total_lines']}")
