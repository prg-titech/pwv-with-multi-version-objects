class Renderer:
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
        print(f"render lock {payload['piece']} at ({payload['left']},{payload['top']})")
        self._print_board(payload["board_lines"])

    def _on_line_cleared(self, payload):
        print(f"render clear lines={payload['cleared']}")
        self._print_board(payload["board_lines"])

    def _print_board(self, board_lines):
        for line in board_lines:
            print(line)
