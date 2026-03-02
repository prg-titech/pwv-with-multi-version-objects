PIECES = {
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "I": [(0, 0), (0, 1), (0, 2), (0, 3)],
}

def get_cells(piece_name):
    return PIECES[piece_name]
