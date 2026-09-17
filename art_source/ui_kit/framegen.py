"""Frame grid construction helpers (role grids, not colours)."""


def frame_grid(n, top, bot, left=None, right=None, fill='P'):
    """n x n role grid from edge profiles. top: outer->inner (top->down).
    bot: inner->outer (top->down). left: outer->inner, right: inner->outer.
    Nearest edge owns a pixel; ties go to the horizontal (top/bottom) band."""
    left = left or top
    right = right or bot
    g = [[fill] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            dt, db, dl, dr = y, n - 1 - y, x, n - 1 - x
            cand = []
            if dt < len(top):
                cand.append((dt, 0, top[dt]))
            if db < len(bot):
                cand.append((db, 0, bot[len(bot) - 1 - db]))
            if dl < len(left):
                cand.append((dl, 1, left[dl]))
            if dr < len(right):
                cand.append((dr, 1, right[len(right) - 1 - dr]))
            if cand:
                cand.sort()
                g[y][x] = cand[0][2]
    return g


CORNERS = [('TL', 1, 1), ('TR', -1, 1), ('BL', 1, -1), ('BR', -1, -1)]


def corner_origin(n, name):
    cx = 0 if name in ('TL', 'BL') else n - 1
    cy = 0 if name in ('TL', 'TR') else n - 1
    return cx, cy


def chamfer_at(g, cx, cy, sx, sy):
    g[cy][cx] = '.'
    g[cy][cx + sx] = '.'
    g[cy + sy][cx] = '.'
    g[cy + sy][cx + sx] = 'K'


def chamfer(g, n=None):
    n = n or len(g)
    for name, sx, sy in CORNERS:
        cx, cy = corner_origin(n, name)
        chamfer_at(g, cx, cy, sx, sy)
    return g


def inner_round(g, n, t):
    """Round the inner K line at inset t: its corner pixel takes the rim colour
    diagonally outward; the pixel diagonally inward becomes K."""
    for name, sx, sy in CORNERS:
        cx, cy = corner_origin(n, name)
        px, py = cx + sx * t, cy + sy * t
        g[py][px] = g[py - sy][px - sx]
        g[py + sy][px + sx] = 'K'
    return g


def stamp(g, n, plate):
    """Stamp a square plate (lit from upper-left, identical in every corner)
    into all four corners, chamfering the plate's outer corner."""
    s = len(plate)
    for name, sx, sy in CORNERS:
        ox = 0 if name in ('TL', 'BL') else n - s
        oy = 0 if name in ('TL', 'TR') else n - s
        for y in range(s):
            for x in range(s):
                if plate[y][x] != '~':
                    g[oy + y][ox + x] = plate[y][x]
        cx, cy = corner_origin(n, name)
        chamfer_at(g, cx, cy, sx, sy)
    return g


def to_rows(g):
    return ["".join(r) for r in g]
