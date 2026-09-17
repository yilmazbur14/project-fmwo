"""Approved frames + reusable sprites (head groups) extracted from them."""
from auto import *
import build as B  # re-runs the approved build (idempotent; rewrites the approved strip identically)

IDLE = load_grid(os.path.join(HERE, 'idle_final.txt'))
CHARGE = load_grid(os.path.join(HERE, 'charge_final.txt'))

# idle head group (enlarged), exactly as composited in the approved idle
_hi = blank()
for y, spans in B.IDLE_HEAD.items():
    for a, b in spans:
        for x in range(a, b + 1):
            _hi[y][x] = 'X'
HEAD_MASK_IDLE = B.enlarge(_hi, dup_row=9)
HEAD_FRONT = mask_grid(IDLE, lambda x, y, c: HEAD_MASK_IDLE[y][x] != '.')

# ---- idle label/z maps (block-in labels, head group overrides) ----
import idle_block as _ib
_ib.cv.render()
_Z = {name: z for name, z, fill, pix, ol in _ib.cv.parts}
IDLE_LABEL = [[None] * 64 for _ in range(64)]
for y in range(64):
    for x in range(64):
        if IDLE[y][x] == '.':
            continue
        if HEAD_MASK_IDLE[y][x] != '.':
            IDLE_LABEL[y][x] = 'beard' if y >= 19 else 'head'
        else:
            IDLE_LABEL[y][x] = _ib.cv.label[y][x] or 'torso'
ZOF = dict(_Z)


def shifted(grid, label, groups, dx, dy):
    """Move pixels whose label is in groups by (dx,dy); z-aware composite with the rest."""
    out = blank(); zb = [[-1] * 64 for _ in range(64)]
    for pass_moving in (False, True):
        for y in range(64):
            for x in range(64):
                L = label[y][x]
                if L is None or ((L in groups) != pass_moving):
                    continue
                X, Y = (x + dx, y + dy) if pass_moving else (x, y)
                if not (0 <= X < 64 and 0 <= Y < 64):
                    continue
                z = ZOF.get(L, 0)
                if z >= zb[Y][X]:
                    out[Y][X] = grid[y][x]; zb[Y][X] = z
    return out


UPPER = {'head', 'earL', 'earR', 'beard', 'torso', 'armL', 'armR'}
HEADG = {'head', 'earL', 'earR', 'beard'}

HEAD_TUCK = B.enlarge(B.gh, dup_row=17)      # charge head group: top y9, beard tip y39
TORSO_FRONT = mask_grid(IDLE, lambda x, y, c: IDLE_LABEL[y][x] == 'torso')


def tint(pix):
    return [[(min(255, int(p[0] * 1.35)), min(255, int(p[1] * 1.5)), min(255, int(p[2] * 1.9)), p[3]) for p in row] for row in pix]
