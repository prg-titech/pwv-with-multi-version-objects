from .board import Board
from .pieces import get_cells

DEMO_SCRIPT = [
    {"piece": "O", "x": 0},
    {"piece": "O", "x": 2},
    {"piece": "O", "x": 4},
    {"piece": "I", "x": 3},
]

class TetrisEngine:
    def __init__(self, bus):
        self.bus = bus
        self.board = Board()
        self.total_lines = 0
        self.locked_pieces = 0
        self.turn = 0

    def run_demo(self):
        for step in DEMO_SCRIPT:
            self._run_turn(step["piece"], step["x"])

        self._emit_game_finished()

    def run_playable(self):
        piece_cycle = ["O", "I", "O", "I", "O", "O"]
        cycle_index = 0

        while True:
            piece_name = piece_cycle[cycle_index % len(piece_cycle)]
            cycle_index += 1
            left = self._default_left(piece_name)

            if not self.board.can_drop_piece(piece_name, left):
                print("これ以上ピースを置けません。ゲームを終了します。")
                break

            placed = False
            while not placed:
                self._print_playable_state(piece_name, left)
                try:
                    command = input("操作 [a:left d:right s:drop q:quit] > ").strip().lower()
                except EOFError:
                    self._emit_game_finished()
                    return
                if command == "q":
                    self._emit_game_finished()
                    return
                if command == "a":
                    next_left = max(0, left - 1)
                    if self.board.can_drop_piece(piece_name, next_left):
                        left = next_left
                    continue
                if command == "d":
                    next_left = min(self.board.width - self._piece_width(piece_name), left + 1)
                    if self.board.can_drop_piece(piece_name, next_left):
                        left = next_left
                    continue
                if command in {"", "s"}:
                    if not self.board.can_drop_piece(piece_name, left):
                        print("その位置には置けません。")
                        continue
                    self._run_turn(piece_name, left)
                    placed = True
                    continue
                print("不正な入力です。a / d / s / q を使ってください。")

        self._emit_game_finished()

    def _run_turn(self, piece_name, left):
        self.turn += 1
        # self.bus.emit("turn_started", {
        #     "turn": self.turn,
        #     "piece": piece_name,
        #     "left": left,
        #     "total_lines": self.total_lines,
        # })
        self.bus.publish("turn_started", {
            "turn": self.turn,
            "piece": piece_name,
            "left": left,
            "total_lines": self.total_lines,
        })

        top = self.board.drop_piece(piece_name, left)
        self.locked_pieces += 1
        # UPDATE2での修正: emit -> publishに変更
        # 削除
        # self.bus.emit("piece_locked", {
        #     "turn": self.turn,
        #     "piece": piece_name,
        #     "left": left,
        #     "top": top,
        #     "board_lines": self.board.snapshot(),
        # })
        # 追加
        self.bus.publish("piece_locked", {
            "turn": self.turn,
            "piece": piece_name,
            "left": left,
            "top": top,
            "board_lines": self.board.snapshot(),
        })

        cleared = self.board.clear_full_rows()
        if cleared:
            self.total_lines += cleared
            self.bus.emit("line_cleared", {
                "turn": self.turn,
                "cleared": cleared,
                "total_lines": self.total_lines,
                "board_lines": self.board.snapshot(),
            })

    def _emit_game_finished(self):
        self.bus.emit("game_finished", {
            "turns": self.turn,
            "locked_pieces": self.locked_pieces,
            "total_lines": self.total_lines,
            "board_lines": self.board.snapshot(),
        })

    def _default_left(self, piece_name):
        return (self.board.width - self._piece_width(piece_name)) // 2

    def _piece_width(self, piece_name):
        return max(dx for dx, _ in get_cells(piece_name)) + 1

    def _print_playable_state(self, piece_name, left):
        print(f"turn={self.turn + 1} next={piece_name} left={left}")
        for line in self.board.preview_drop(piece_name, left):
            print(line)
