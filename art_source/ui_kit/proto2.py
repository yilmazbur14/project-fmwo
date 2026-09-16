"""Prototype pass 2: rim profile + corner plate treatments, steel vs brass."""
from kitlib import *
import os

P = "C:/Users/theyi/OneDrive/Documents/new-game-project/"
OUT = "proto2/"
os.makedirs(OUT, exist_ok=True)


def frame_grid(n, m, top, bot, left=None, right=None, fill='P'):
    """Build an n x n role grid from edge profiles.
    top: roles for rows 0..len-1 (outer -> inner) on the top side
    bot: roles for the last rows, listed INNER -> OUTER (top->bottom order)
    left/right analogous (left outer->inner, right inner->outer).
    Corners get a rounded (chamfered) outline and mitred bevels; the result is
    then refined by explicit overrides."""
    left = left or top
    right = right or bot
    T, B = len(top), len(bot)
    g = [[fill] * n for _ in range(n)]
    for y in range(n):
        for x in range(n):
            # distance-based: which side owns this pixel (nearest edge wins,
            # ties -> top/bottom go to the horizontal bands)
            dt, db, dl, dr = y, n - 1 - y, x, n - 1 - x
            cand = []
            if dt < T:
                cand.append((dt, 0, top[dt]))
            if db < B:
                cand.append((db, 0, bot[B - 1 - db]))
            if dl < len(left):
                cand.append((dl, 1, left[dl]))
            if dr < len(right):
                cand.append((dr, 1, right[len(right) - 1 - dr]))
            if cand:
                cand.sort()
                g[y][x] = cand[0][2]
    return g


def chamfer(g, n):
    # outer rounded corners
    for (cx, cy, sx, sy) in [(0, 0, 1, 1), (n - 1, 0, -1, 1), (0, n - 1, 1, -1), (n - 1, n - 1, -1, -1)]:
        g[cy][cx] = '.'
        g[cy][cx + sx] = '.'
        g[cy + sy][cx] = '.'
        g[cy + sy][cx + sx] = 'K'
    return g


def show(g):
    return "\n".join("".join(r) for r in g)


# ---- corner plate stamps (lit from upper-left in every corner) ----
PLATE7 = [
    "KKKKKKK",
    "K11112K",
    "K1ab34K",
    "K1bc34K",
    "K13334K",
    "K24445K",
    "KKKKKKK",
]
PLATE9 = [
    "KKKKKKKKK",
    "K1111112K",
    "K1333334K",
    "K13ab334K",
    "K13bcd34K",
    "K133dd34K",
    "K1333334K",
    "K2444445K",
    "KKKKKKKKK",
]


def stamp_plate(g, n, plate):
    s = len(plate)
    for corner in ['TL', 'TR', 'BL', 'BR']:
        ox = 0 if corner in ('TL', 'BL') else n - s
        oy = 0 if corner in ('TL', 'TR') else n - s
        for y in range(s):
            for x in range(s):
                g[oy + y][ox + x] = plate[y][x]
        # chamfer the plate's outer corner
        cx = ox if corner in ('TL', 'BL') else ox + s - 1
        cy = oy if corner in ('TL', 'TR') else oy + s - 1
        sx = 1 if corner in ('TL', 'BL') else -1
        sy = 1 if corner in ('TL', 'TR') else -1
        g[cy][cx] = '.'
        g[cy][cx + sx] = '.'
        g[cy + sy][cx] = '.'
        g[cy + sy][cx + sx] = 'K'
    return g


def inner_round(g, n, t):
    """round the inner black line corners (t = index of the inner K line):
    the corner pixel of the K line takes the rim colour diagonally outward,
    and the panel pixel diagonally inward becomes K."""
    for (cx, cy, sx, sy) in [(t, t, 1, 1), (n - 1 - t, t, -1, 1), (t, n - 1 - t, 1, -1), (n - 1 - t, n - 1 - t, -1, -1)]:
        g[cy][cx] = g[cy - sy][cx - sx]
        g[cy + sy][cx + sx] = 'K'
    return g


N, M = 32, 10
FLAT_TOP = list("K1334K") + ['p']
FLAT_BOT = ['q'] + list("K2335K")
TUBE_TOP = list("K1234K") + ['p']
TUBE_BOT = ['q'] + list("K2345K")

variants = {}
# A: v1-like flat chamfer rim, no plates
g = inner_round(chamfer(frame_grid(N, M, FLAT_TOP, FLAT_BOT), N), N, 5)
variants['A_flat'] = g
# B: tube rim, no plates
g = inner_round(chamfer(frame_grid(N, M, TUBE_TOP, TUBE_BOT), N), N, 5)
variants['B_tube'] = g
# C: flat rim + 7px plates
g = stamp_plate(inner_round(chamfer(frame_grid(N, M, FLAT_TOP, FLAT_BOT), N), N, 5), N, PLATE7)
variants['C_flat_p7'] = g
# D: tube rim + 9px plates
g = stamp_plate(inner_round(chamfer(frame_grid(N, M, TUBE_TOP, TUBE_BOT), N), N, 5), N, PLATE9)
variants['D_tube_p9'] = g
# E: flat rim + 9px plates
g = stamp_plate(inner_round(chamfer(frame_grid(N, M, FLAT_TOP, FLAT_BOT), N), N, 5), N, PLATE9)
variants['E_flat_p9'] = g

PALS = {
    'steel': {'K': '000000', '1': 'ffffff', '2': 'cbdbfc', '3': '9badb7', '4': '847e87', '5': '595652',
              'a': 'ffffff', 'b': 'cbdbfc', 'c': '595652', 'd': '222034',
              'P': '222034', 'p': '000000', 'q': '3f3f74'},
    'brass': {'K': '000000', '1': 'fbf236', '2': 'eec39a', '3': 'd9a066', '4': '8a6f30', '5': '524b24',
              'a': 'ffffff', 'b': 'fbf236', 'c': '8f563b', 'd': '45283c',
              'P': '222034', 'p': '000000', 'q': '3f3f74'},
}

tiles = []
for vname, g in variants.items():
    grid = ["".join(r) for r in g]
    with open(OUT + f"{vname}.txt", "w") as f:
        f.write("\n".join(grid))
    for pname, pal in PALS.items():
        w, h, pix = grid_to_pix(grid, pal)
        probs = check_nine_slice(w, h, pix, M)
        print(f"{vname:10s} {pname:6s} 9-slice:", "OK" if not probs else probs[:3])
        write_png(OUT + f"{vname}_{pname}_1x.png", w, h, pix)
        tiles.append((vname, pname, w, h, pix))

# contact sheet: each variant at 8x, steel row then brass row
S = 8
cols = len(variants)
sheet_w = cols * (32 * S + 16) + 16
sheet_h = 2 * (32 * S + 16) + 16
sheet = solid(sheet_w, sheet_h, (96, 96, 110, 255))
for i, (vname, pname, w, h, pix) in enumerate(tiles):
    col = i // 2
    row = 0 if pname == 'steel' else 1
    _, _, z = upscale(w, h, pix, S, bg=(128, 126, 135, 255))
    blit(sheet, z, 16 + col * (32 * S + 16), 16 + row * (32 * S + 16))
write_png(OUT + "sheet_8x.png", sheet_w, sheet_h, sheet)

# game-scale mocks: a 1860x234 box, cropped to the left 700px, all variants stacked
bw, bh, bg = read_png(P + "Assets/Characters/Danny/DannyIntro.png")
rows = []
for (vname, pname, w, h, pix) in tiles:
    W3, H3, pix3 = scale_nn(w, h, pix, 3)
    box = nine_slice(W3, H3, pix3, 30, 1860, 234)
    strip = crop([list(r) for r in bg], 0, 1080 - 270, 700, 270)
    blit(strip, crop(box, 0, 0, 700 - 30, 234), 30, 18)
    rows += strip
    rows += [[(255, 0, 255, 255)] * 700 for _ in range(3)]
write_png(OUT + "game_scale.png", 700, len(rows), rows)
print("done")
