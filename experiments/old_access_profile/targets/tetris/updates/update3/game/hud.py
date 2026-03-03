class Hud:
    def install(self, bus):
        # UPDATE3での修正: on -> subscribeに変更
        # - それに伴って、_subscriptionsがトークンも格納するように変更
        #  - 0はトークンのプレースホルダ
        # - subscribeが返すトークンをevent_nameとともに格納
        self._subscriptions = [
            ("turn_started", self._on_turn_started, 0),
            ("line_cleared", self._on_line_cleared, 0),
            ("game_finished", self._on_game_finished, 0),
        ]
        # 削除
        # for event_name, callback in self._subscriptions:
        #     bus.on(event_name, callback)
        # 追加
        for index, (event_name, callback, _) in enumerate(self._subscriptions):
            token = bus.subscribe(event_name, callback)
            self._subscriptions[index] = (event_name, callback, token)


    def uninstall(self, bus):
        # UPDATE3での修正: _subscriptionsの構造変化に追従する
        # - まだtokenを使った削除はしない
        # 削除
        # for event_name, callback in self._subscriptions:
        #     bus.off(event_name, callback)
        # 追加
        for event_name, callback, _ in self._subscriptions:
            bus.off(event_name, callback)

    def _on_turn_started(self, payload):
        print(f"turn={payload['turn']} piece={payload['piece']} x={payload['left']}")

    def _on_line_cleared(self, payload):
        print(f"hud total_lines={payload['total_lines']}")

    def _on_game_finished(self, payload):
        print(f"hud finished pieces={payload['locked_pieces']} lines={payload['total_lines']}")
