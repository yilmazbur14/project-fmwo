"""Head part (facing right). Local coords; later pasted at a frame offset."""


def grid_from_spans(w, h, rows):
    g = [['.'] * w for _ in range(h)]
    for y, spec in rows.items():
        for item in spec:
            if len(item) == 3:
                x0, x1, c = item
            else:
                x0, c = item
                x1 = x0
            for x in range(x0, x1 + 1):
                g[y][x] = c
    return [''.join(r) for r in g]


HEAD_ROWS = {
    # ---- black cap: rounded crown, light upper-left
    0:  [(6, 11, 'K')],
    1:  [(4, 5, 'K'), (6, 7, 'E'), (8, 9, 'T'), (10, 11, 'B'), (12, 13, 'K')],
    2:  [(3, 'K'), (4, 'T'), (5, 6, 'E'), (7, 8, 'T'), (9, 12, 'B'), (13, 'b'), (14, 'K')],
    3:  [(2, 'K'), (3, 'T'), (4, 'E'), (5, 6, 'T'), (7, 12, 'B'), (13, 14, 'b'), (15, 'K')],
    4:  [(1, 'K'), (2, 5, 'T'), (6, 12, 'B'), (13, 15, 'b'), (16, 'K')],
    5:  [(1, 'K'), (2, 3, 'T'), (4, 12, 'B'), (13, 15, 'b'), (16, 20, 'K')],
    # band + forward brim
    6:  [(1, 'K'), (2, 16, 'b'), (17, 'B'), (18, 20, 'T'), (21, 'K')],
    7:  [(1, 'K'), (2, 'h'), (3, 10, 'H'), (11, 13, 'd'), (14, 'D'), (15, 20, 'K')],
    # ---- head: short hair at back, ear, sideburn, profile face
    8:  [(1, 'K'), (2, 'h'), (3, 9, 'H'), (10, 'H'), (11, 14, 's'), (15, 'd'), (16, 'K')],
    9:  [(1, 'K'), (2, 'h'), (3, 4, 'H'), (5, 9, 'h'), (10, 'H'), (11, 12, 'S'),
         (13, 15, 'h'), (16, 'K')],                                   # neutral flat brow
    10: [(1, 'K'), (2, 'h'), (3, 4, 'H'), (5, 'd'), (6, 'd'), (7, 8, 's'), (9, 'H'),
         (10, 15, 'S'), (16, 'K')],                                   # ear top
    11: [(1, 'K'), (2, 'h'), (3, 4, 'H'), (5, 'd'), (6, 'd'), (7, 'S'), (8, 'D'), (9, 'H'),
         (10, 12, 'S'), (13, 14, 'K'), (15, 's'), (16, 'K')],         # heavy upper lid
    12: [(1, 'K'), (2, 'h'), (3, 4, 'H'), (5, 'd'), (6, 'd'), (7, 's'), (8, 'D'), (9, 's'),
         (10, 12, 'S'), (13, 'W'), (14, 'K'), (15, 16, 'S'), (17, 'K')],  # half-lidded eye
    13: [(2, 'K'), (3, 'h'), (4, 'H'), (5, 'd'), (6, 7, 'd'), (8, 'D'), (9, 'S'),
         (10, 12, 'S'), (13, 14, 's'), (15, 16, 'S'), (17, 's'), (18, 'K')],
    14: [(2, 'K'), (3, 'h'), (4, 'H'), (5, 's'), (6, 8, 's'), (9, 14, 'S'), (15, 's'),
         (16, 'd'), (17, 'K')],
    15: [(3, 'K'), (4, 'd'), (5, 8, 's'), (9, 14, 'S'), (15, 's'), (16, 'K')],
    16: [(4, 'K'), (5, 'd'), (6, 8, 's'), (9, 12, 'S'), (13, 'D'), (14, 16, 'K')],  # flat mouth
    17: [(5, 'K'), (6, 'd'), (7, 9, 's'), (10, 13, 'S'), (14, 's'), (15, 'd'), (16, 'K')],
    18: [(5, 'K'), (6, 'D'), (7, 8, 'd'), (9, 's'), (10, 15, 'K')],
    19: [(5, 'K'), (6, 'D'), (7, 8, 'd'), (9, 's'), (10, 'K')],
    20: [(5, 'K'), (6, 'D'), (7, 8, 'd'), (9, 's'), (10, 'K')],
}

HEAD = grid_from_spans(23, 21, HEAD_ROWS)

if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ulib
    f = ulib.new_frame()
    ulib.paste(f, HEAD, 20, 8)
    here = os.path.dirname(os.path.abspath(__file__))
    ulib.write_crop(os.path.join(here, 'head_crop.png'), [f], 18, 6, 45, 30, 16)
    print('\n'.join(HEAD))
