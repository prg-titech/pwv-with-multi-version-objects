from .pieces import get_cells

class Board:
    def __init__(self, width=6, height=6):
        self.width = width
        self.height = height
        self._grid = []
        for _ in range(height):
            self._grid.append(["."] * width)

    def drop_piece(self, piece_name, left):
        cells = get_cells(piece_name)
        top = self._find_drop_row(cells, left)
        if top is None:
            raise ValueError(f"cannot place piece {piece_name} at x={left}")

        for dx, dy in cells:
            self._grid[top + dy][left + dx] = "#"
        return top

    def clear_full_rows(self):
        kept_rows = []
        cleared = 0
        for row in self._grid:
            if all(cell == "#" for cell in row):
                cleared += 1
            else:
                kept_rows.append(row)

        while len(kept_rows) < self.height:
            kept_rows.insert(0, ["."] * self.width)

        self._grid = kept_rows
        return cleared

    def snapshot(self):
        lines = []
        for row in self._grid:
            lines.append("".join(row))
        return lines

    def can_drop_piece(self, piece_name, left):
        cells = get_cells(piece_name)
        return self._find_drop_row(cells, left) is not None

    def preview_drop(self, piece_name, left):
        cells = get_cells(piece_name)
        top = self._find_drop_row(cells, left)
        board_copy = []
        for row in self._grid:
            board_copy.append(list(row))

        if top is not None:
            for dx, dy in cells:
                board_copy[top + dy][left + dx] = "@"

        lines = []
        for row in board_copy:
            lines.append("".join(row))
        return lines

    def _find_drop_row(self, cells, left):
        max_dy = max(dy for _, dy in cells)
        best_top = None
        for top in range(self.height - max_dy):
            if not self._can_place(cells, left, top):
                break
            best_top = top
        return best_top

    def _can_place(self, cells, left, top):
        for dx, dy in cells:
            x = left + dx
            y = top + dy
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                return False
            if self._grid[y][x] != ".":
                return False
        return True
