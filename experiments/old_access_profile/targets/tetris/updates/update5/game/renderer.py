class Renderer:
    def install(self, bus):
        # UPDATE5での修正: on -> subscribe, off -> unsubscribeに変更
        # - UPDATE3,4を踏まえてまとめてトークンを用いた管理に移行
        # 削除
        # self._subscriptions = [
        #     ("piece_locked", self._on_piece_locked),
        #     ("line_cleared", self._on_line_cleared),
        # ]
        # for event_name, callback in self._subscriptions:
        #     bus.on(event_name, callback)
        # 追加
        self._subscriptions = [
            ("piece_locked", self._on_piece_locked, 0),
            ("line_cleared", self._on_line_cleared, 0),
        ]
        for index, (event_name, callback, _) in enumerate(self._subscriptions):
            token = bus.subscribe(event_name, callback)
            self._subscriptions[index] = (event_name, callback, token)

    def uninstall(self, bus):
        # 削除
        # for event_name, callback in self._subscriptions:
        #     bus.off(event_name, callback)
        # 追加
        for _, _, token in self._subscriptions:
            bus.unsubscribe(token)

    def _on_piece_locked(self, payload):
        print(f"render lock {payload['piece']} at ({payload['left']},{payload['top']})")
        self._print_board(payload["board_lines"])

    def _on_line_cleared(self, payload):
        print(f"render clear lines={payload['cleared']}")
        self._print_board(payload["board_lines"])

    def _print_board(self, board_lines):
        for line in board_lines:
            print(line)
