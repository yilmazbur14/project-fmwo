"""Jordan's room - room_furniture, part 1: the desk, its monitors and the PC.

Every builder draws one piece of furniture onto a full-size transparent Canvas
at its place in the room. Furniture is complete without anything that sits on
it (that is room_props), so the props can fall away first. `under` is the room
so far (floor + walls); builders read it to lay their contact shadows, which
belong to the piece.

The chair spot in front of the desk is left empty on purpose: the gaming chair
is drawn on Jordan's seated sheet (CHAIR_POINT in jr_geom).
"""
import numpy as np

from jr_lib import Canvas, W, H, IDX, KEYS, T, DARKER, border, poly_mask, rect_mask, \
    ellipse_mask, bayer
from jr_geom import (FLOOR_Y, DESK_X0, DESK_X1, DESK_FRONT_Y, DESK_TOP_Y, DESK_LIP_Y,
                     PC_X0, PC_X1)


# ---------------------------------------------------------------- helpers
def shade_under(c, under, mask, steps=1, p=1.0):
    """Contact shadow: copy what's underneath, darkened, into the piece."""
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        if c.a[y, x] != T:
            continue
        if p < 1.0 and bayer(x, y) >= p:
            continue
        v = under.a[y, x]
        if v == T:
            continue
        k = KEYS[v]
        for _ in range(steps):
            k = DARKER[k]
        c.a[y, x] = IDX[k]


def outline(c, mask, k='K'):
    c.a[border(mask)] = IDX[k]


def fill_shaded(c, mask, hi, base, lo, light='tl'):
    """Flat fill with a lit edge and a shadow edge (one pixel each)."""
    up = np.zeros_like(mask)
    up[1:, :] = mask[1:, :] & ~mask[:-1, :]
    up[0, :] = mask[0, :]
    dn = np.zeros_like(mask)
    dn[:-1, :] = mask[:-1, :] & ~mask[1:, :]
    lf = np.zeros_like(mask)
    lf[:, 1:] = mask[:, 1:] & ~mask[:, :-1]
    rt = np.zeros_like(mask)
    rt[:, :-1] = mask[:, :-1] & ~mask[:, 1:]
    c.fill(mask, base)
    if light == 'tl':
        c.fill(rt | dn, lo)
        c.fill((up | lf) & ~(rt | dn), hi)
    elif light == 'tr':
        c.fill(lf | dn, lo)
        c.fill((up | rt) & ~(lf | dn), hi)
    elif light == 'top':
        c.fill(dn, lo)
        c.fill(up & ~dn, hi)


# ================================================================ desk
DX0, DX1 = DESK_X0, DESK_X1


def desk(under):
    """Black gaming desk: 18-row top, RGB underglow, two leg panels, open kneehole."""
    c = Canvas()
    top0, lip = DESK_TOP_Y, DESK_LIP_Y                    # 114, 132
    # kneehole: the wall and boards under the desk, deep in shadow
    knee = rect_mask(DX0 + 9, lip + 3, DX1 - 9, DESK_FRONT_Y - 1)
    shade_under(c, under, knee, steps=1)
    shade_under(c, under, rect_mask(DX0 - 1, DESK_FRONT_Y, DX1 + 2, DESK_FRONT_Y + 1), 1)
    # top surface, with a faint sheen near the back
    c.rect(DX0, top0, DX1, lip - 1, 'N')
    for x in range(DX0, DX1 + 1):
        if bayer(x, top0 + 3) < 0.5:
            c.set(x, top0 + 1, '6')
    # front lip (3 rows) and the RGB underglow strip below it
    c.rect(DX0, lip, DX1, lip + 2, '6')
    c.hline(DX0, DX1, lip, 'E')
    for x in range(DX0 + 9, DX1 - 8):
        c.set(x, lip + 3, ['c', '8', 'U'][((x - DX0) // 12) % 3])
    # underglow washing the top of the kneehole
    for y in range(lip + 4, lip + 12):
        for x in range(DX0 + 9, DX1 - 8):
            if bayer(x, y) < 0.62 - (y - lip - 4) * 0.08:
                c.set(x, y, 'I' if y > lip + 5 else 'V')
    # leg panels, their inner faces lit by the underglow
    for (a, b, inner) in ((DX0, DX0 + 8, DX0 + 8), (DX1 - 8, DX1, DX1 - 8)):
        c.rect(a, lip + 3, b, DESK_FRONT_Y - 1, 'N')
        c.vline(inner, lip + 3, DESK_FRONT_Y - 1, 'I')
        c.vline((a + b) // 2, lip + 5, DESK_FRONT_Y - 3, '6')
        c.hline(a, b, DESK_FRONT_Y - 1, 'K')
    m = rect_mask(DX0, top0, DX1, lip + 2) | rect_mask(DX0, lip + 3, DX0 + 8, DESK_FRONT_Y - 1) \
        | rect_mask(DX1 - 8, lip + 3, DX1, DESK_FRONT_Y - 1)
    outline(c, m)
    c.hline(DX0 - 1, DX1 + 1, lip - 1, 'K')
    c.hline(DX0, DX1, lip, 'E')
    return c


# ---------------------------------------------------------------- monitors
GAME_SCREEN = [
    # 52x22: a boss fight in whatever Jordan is playing
    "IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
    "IKKKKKKKKKKKKKKKKKKKKKKIIIIIIIIIIIIIIIIIIIIIIIIIIIPI",
    "IKRRRRRRRRRRRRRRRRRRNNKIIIIIIIIUIIIIIIIIIIIIIIIIIIII",
    "IKKKKKKKKKKKKKKKKKKKKKKIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
    "IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIVVVVIIIIIIIIIUIIIIII",
    "IIIIIUIIIIIIIIIIIIIIIIIIIIIIIIVV88VVIIIIIIIIIIIIIIII",
    "IIIIIIIIIIIIIIIIIIIIIIIIIIIIIV8888VVVIIIIIIIIIIIIIII",
    "IIIIIIIIIIIIIIIIIIIIIIIIRRIIIVRR88RRVIIRRIIIIIIIIIII",
    "IIIIIIIIIIIIIIIIIIIIIIIIRrRIIVYRRRRYVIRrRIIIIIIIIIII",
    "IIIIIIIIIIIIIIIIIIIIIIIIIRrRRRRRRRRRRRrRIIIIIIIIIIII",
    "IIIIIIIIIIIIIIIIIIIIIIIIIIRRRRWRRWRRRRRIIIIIIIIIIIII",
    "IIIIIIIIIIIIIIIIIIIIIIIIIIIRRRRRRRRRRRIIIIIIIIIIIIII",
    "IIIIIIIIIIIYIIIIIIIIIIIIIIIIRRrrrrRRIIIIIIIIIIIIIIII",
    "IIIIIIIIIIYOYIIIIIIIIIIIIIIIRRRRRRRRIIIIIIIIIIIIIIII",
    "IIIIIIIIIIIYIIIIIIIIIIIIIIIRRIIIIIRRIIIIIIIIIIIIIIII",
    "IIIIIIsIIIIIIIIIIIIIIIIIIIRRRIIIIIRRRIIIIIIIIIIIIIII",
    "IIIIIUuUIWWWWWWIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
    "IIIIIIUIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
    "IIIIIUIUIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
    "UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU",
    "7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U7U",
    "7777777777777777777777777777777777777777777777777777",
]

CHAT_SCREEN = [
    # 28x18: the server's chat on the second screen
    "IIIIINNNNNNNNNNNNNNNNNNNNNNN",
    "IWWIINUUUUUUUUNNNNNNNNNNNNNN",
    "IWUWINNNNNNNNNNNNNNNNNNNNNNN",
    "IIIIINNNNNNNNNNNNNNNNNNNNNNN",
    "IUUIINrNNggggggNNNNNNNNNNNNN",
    "IUUIINNNNPPPPPPPPPPPNNNNNNNN",
    "IIIIINNNNPPPPPPNNNNNNNNNNNNN",
    "I88IINcNNggggggggNNNNNNNNNNN",
    "I88IINNNNPPPPPPPPPPPPPPNNNNN",
    "IIIIINNNNNNNNNNNNNNNNNNNNNNN",
    "I22IIN8NNgggggNNNNNNNNNNNNNN",
    "I22IINNNNPPPPPPPPPNNNNNNNNNN",
    "IIIIINNNNPPPPPPPPPPPPPNNNNNN",
    "IccIINUNNggggggggNNNNNNNNNNN",
    "IccIINNNNPPPPPNNNNNNNNNNNNNN",
    "IIIIINNNNNNNNNNNNNNNNNNNNNNN",
    "IIIIINIIIIIIIIIIIIIIIIIIIIIN",
    "IIIIINIFFFFFFFFFFFFFFFFFFFIN",
]

MAIN_SX0, MAIN_SY0 = 386, 86          # main screen, 52x22
CHAT_SX0, CHAT_SY0 = 352, 90          # second screen, 28x18


def monitors():
    c = Canvas()
    foot_y = DESK_TOP_Y + 4                              # stands sit near the back of the top
    sx0, sy0 = MAIN_SX0, MAIN_SY0
    sw, sh = len(GAME_SCREEN[0]), len(GAME_SCREEN)
    c.stamp(GAME_SCREEN, sx0, sy0)
    c.box(sx0 - 1, sy0 - 1, sx0 + sw, sy0 + sh, 'N')
    c.hline(sx0 - 1, sx0 + sw, sy0 + sh + 1, 'N')        # thick bottom bezel
    c.set(sx0 + sw // 2, sy0 + sh + 1, 'E')
    c.box(sx0 - 2, sy0 - 2, sx0 + sw + 1, sy0 + sh + 2, 'K')
    for i in range(3):
        c.set(sx0 + sw - 3 - i, sy0 + 1 + i, 'P')        # glare
    nx = sx0 + sw // 2 - 2
    c.rect(nx, sy0 + sh + 3, nx + 3, foot_y, 'E')
    c.vline(nx, sy0 + sh + 3, foot_y, 'F')
    c.box(nx - 1, sy0 + sh + 3, nx + 4, foot_y, 'K')
    c.rect(nx - 9, foot_y + 1, nx + 12, foot_y + 2, 'E')
    c.hline(nx - 9, nx + 12, foot_y + 1, 'F')
    c.box(nx - 10, foot_y, nx + 13, foot_y + 3, 'K')
    c.rect(nx - 1, foot_y, nx + 4, foot_y, 'E')
    # second screen: the server's chat
    tx0, ty0 = CHAT_SX0, CHAT_SY0
    tw, th = len(CHAT_SCREEN[0]), len(CHAT_SCREEN)
    c.stamp(CHAT_SCREEN, tx0, ty0)
    c.box(tx0 - 1, ty0 - 1, tx0 + tw, ty0 + th, 'N')
    c.hline(tx0 - 1, tx0 + tw, ty0 + th + 1, 'N')
    c.box(tx0 - 2, ty0 - 2, tx0 + tw + 1, ty0 + th + 2, 'K')
    c.set(tx0 + tw - 2, ty0 + 1, 'P')
    c.set(tx0 + tw - 3, ty0 + 2, 'P')
    mx = tx0 + tw // 2 - 1
    c.rect(mx, ty0 + th + 3, mx + 2, foot_y, 'E')
    c.box(mx - 1, ty0 + th + 3, mx + 3, foot_y, 'K')
    c.rect(mx - 6, foot_y + 1, mx + 8, foot_y + 2, 'E')
    c.box(mx - 7, foot_y, mx + 9, foot_y + 3, 'K')
    return c


# ---------------------------------------------------------------- PC tower
def pc_tower(under):
    c = Canvas()
    x0, x1 = PC_X0, PC_X1
    base = FLOOR_Y + 16
    front0 = base - 34
    top0 = front0 - 16
    shade_under(c, under, rect_mask(x0 - 1, base + 1, x1 + 2, base + 2), 1)
    shade_under(c, under, rect_mask(x1 + 1, front0, x1 + 3, base), 1, 0.5)
    c.rect(x0, top0, x1, front0 - 1, '6')
    for y in range(top0 + 2, front0 - 2, 2):
        c.hline(x0 + 3, x1 - 3, y, 'N')
    c.rect(x0, front0, x1, base, 'N')
    c.hline(x0, x1, front0, 'E')
    c.vline(x0, front0, base, 'I')
    for i, (ring, hub) in enumerate((('c', 'U'), ('8', 'V'), ('U', 'I'))):
        cy = front0 + 7 + i * 10
        cx = (x0 + x1) // 2
        for y in range(cy - 4, cy + 5):
            for x in range(cx - 5, cx + 6):
                d = ((x - cx) / 5.2) ** 2 + ((y - cy) / 4.2) ** 2
                if 0.55 <= d <= 1.0:
                    c.set(x, y, ring)
                elif d < 0.55:
                    c.set(x, y, hub if (x + y) % 2 else 'N')
        c.set(cx, cy, 'K')
        c.set(cx - 4, cy - 2, 'W')
    c.set(x1 - 2, front0 + 2, 'c')
    c.vline(x1 - 1, front0 + 2, base - 2, 'U')
    outline(c, rect_mask(x0, top0, x1, base))
    c.hline(x0, x1, front0 - 1, 'K')
    return c
