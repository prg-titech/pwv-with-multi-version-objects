class Audio:
    def install(self, bus):
        self._subscriptions = [
            ("line_cleared", self._on_line_cleared),
            ("game_finished", self._on_game_finished),
        ]
        for event_name, callback in self._subscriptions:
            bus.on(event_name, callback)

    def uninstall(self, bus):
        for event_name, callback in self._subscriptions:
            bus.off(event_name, callback)

    def _on_line_cleared(self, payload):
        print(f"audio clear lines={payload['cleared']}")

    def _on_game_finished(self, payload):
        print("audio finish")
