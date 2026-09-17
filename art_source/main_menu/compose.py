"""Compose the main-menu background from layers. 640x360, DB32 only."""
import math, os, random
from lib import *
import scene
from scene import W, H, CX, TIERS, ROLE, BASE_Y, stair_hw
import invite
import player2
from mprev import load as load_masks

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')

CARD_X, CARD_Y = CX - 38, 4          # invite canvas origin (card rect is +3..+72, +4..+44)
GLOW = (CX, 30)


# ------------------------------------------------------------------ sky
def layer_sky():
    c = Canvas(W, H)
    rnd = random.Random(11)
    gx, gy = GLOW
    for y in range(H):
        for x in range(W):
            col = N0
            t = (y - 150) / 170.0
            if t > 0 and dith(x, y, min(1.0, t) * 0.8):
                col = P0
            dx, dy = x - gx, (y - gy) * 1.2
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            ray = max(0.0, math.cos(ang * 5 + 0.3)) ** 6          # few, soft, broad rays
            outer = max(0.0, 1.0 - r / 170.0)
            v = outer ** 1.6 * 0.9 + ray * outer ** 1.2 * 0.35
            if v > 0 and dith(x, y, min(1.0, v)):
                col = IN
            inner = max(0.0, 1.0 - r / 62.0)
            if inner > 0 and dith(x, y, min(1.0, inner ** 0.9 * 1.25)):
                col = RB if dith(x + 2, y + 1, inner * 0.9) else IN
            core = max(0.0, 1.0 - r / 40.0)
            if core > 0 and dith(x, y, min(1.0, core * 1.3)):
                col = SB if core < 0.75 else WH2
            c.set(x, y, col)
    # stars, kept out of the glow
    for i in range(190):
        x, y = rnd.randrange(W), rnd.randrange(0, 260)
        if math.hypot(x - gx, (y - gy) * 1.2) < 120:
            continue
        v = rnd.random()
        col = G5 if v < 0.55 else WH2 if v < 0.85 else WH
        if y > 180:
            col = G4 if v < 0.7 else G5
        c.set(x, y, col)
    for (x, y) in [(38, 136), (212, 22), (598, 150), (122, 238), (286, 88), (618, 34), (20, 44), (168, 170)]:
        c.set(x, y, WH)
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.set(x + ddx, y + ddy, G5)
    return c


# ------------------------------------------------------------------ tower
def draw_tier(c, k):
    st, ft, fb, hw = TIERS[k - 1]
    hi, base, lo = ROLE[k]
    x0, x1 = CX - hw, CX + hw
    for y in range(st, ft):
        for x in range(x0, x1 + 1):
            col = OG
            if y == st:
                col = G1
            if y == ft - 1:
                col = TE
            c.set(x, y, col)
    for y in range(ft, fb + 1):
        yy = y - ft
        for x in range(x0, x1 + 1):
            col = N0
            if yy == 0:
                col = TN
            elif yy == 1:
                col = GO
            elif yy == 2:
                col = K
            elif yy == 3:
                col = base
            elif yy == 4:
                col = lo
            elif yy == 5:
                col = K
            elif yy < 10 and dith(x, y, 0.5 - (yy - 6) * 0.14):
                col = IN
            # apron folds: faint vertical creases
            elif yy >= 6 and (x - CX) % 22 == 0 and y < fb - 1:
                col = K if dith(x, y, 0.5) else N0
            if y == fb:
                col = K
            c.set(x, y, col)
    for y in range(st, fb + 1):
        c.set(x0, y, K)
        c.set(x1, y, K)
    c.hline(x0, x1, st - 1, K)


LANTERN = ['..KKK..', '.KhbbK.', 'KhbbbbK', 'KbbbblK', 'KbbbllK', '.KbllK.', '..KKK..']


def draw_post(c, px, st, k):
    hi, base, lo = ROLE[k]
    top = st - 15
    for y in range(top, st + 2):
        c.set(px - 1, y, K)
        c.set(px + 2, y, K)
        c.set(px, y, TN)
        c.set(px + 1, y, GO)
    c.hline(px - 1, px + 2, top - 1, K)
    ly = top - 5
    for yy in range(ly - 10, ly + 11):
        for xx in range(px - 10, px + 12):
            d = math.hypot(xx - (px + 0.5), yy - ly)
            if d < 10.5 and c.get(xx, yy) is None and dith(xx, yy, (1 - d / 10.5) ** 1.3 * 0.9):
                c.set(xx, yy, IN)
    c.grid(px - 3 + 1, ly - 3, LANTERN, {'K': K, 'h': hi, 'b': base, 'l': lo}, skip='.')


def draw_ropes(c, k):
    st, ft, fb, hw = TIERS[k - 1]
    pl, pr = CX - hw + 4, CX + hw - 5
    gap = stair_hw(st) + 3
    for ry in (st - 5, st - 10):
        for x in range(pl + 2, pr):
            if abs(x - CX) <= gap:
                continue
            c.set(x, ry, WH2 if abs(x - CX) < 70 else G5)
    draw_post(c, pl, st, k)
    draw_post(c, pr, st, k)


def draw_stairs(c):
    for y in range(112, BASE_Y + 1):
        hw = stair_hw(y)
        ph = (y - 112) % 4
        for x in range(CX - hw, CX + hw + 1):
            e = abs(x - CX)
            if e == hw:
                col = K
            elif e == hw - 1:
                col = GO if ph else TN
            elif e == hw - 2:
                col = TN if ph != 3 else GO
            else:
                col = [PK, RD, RD, BR][ph]
                if ph == 0 and e >= hw - 4:
                    col = RD
                if ph in (1, 2) and e >= hw - 4:
                    col = BR
            c.set(x, y, col)
        c.set(CX - hw - 1, y, K)
        c.set(CX + hw + 1, y, K)


def draw_floor(c):
    VPY = 150
    for y in range(BASE_Y + 1, H):
        for x in range(W):
            c.set(x, y, N0)
    for xb in range(-900, 1800, 48):
        for y in range(BASE_Y + 1, H):
            t = (y - VPY) / float(BASE_Y + 1 - VPY)
            x = int(round(CX + (xb - CX) * t))
            c.set(x, y, K)
    for y in [BASE_Y + 1, 316, 322, 331, 343, 358]:
        c.hline(0, W - 1, y, K)
    for y in range(BASE_Y + 2, H):
        for x in range(W):
            d = math.hypot((x - CX) / 230.0, (y - BASE_Y) / 46.0)
            if d < 1 and c.get(x, y) == N0 and dith(x, y, (1 - d) * 0.7):
                c.set(x, y, P0)


def draw_carpet_runout(c):
    for y in range(BASE_Y + 1, H):
        t = (y - BASE_Y) / float(H - BASE_Y)
        hw = int(round(22 + 30 * t))
        for x in range(CX - hw, CX + hw + 1):
            e = abs(x - CX)
            col = RD
            if e >= hw:
                col = K
            elif e >= hw - 2:
                col = TN if e == hw - 1 else GO
            elif dith(x, y, 0.25 + t * 0.35):
                col = BR
            c.set(x, y, col)


def layer_tower():
    c = Canvas(W, H)
    for k in range(6, 0, -1):
        draw_tier(c, k)
    draw_floor(c)
    draw_stairs(c)
    draw_carpet_runout(c)
    for k in range(1, 7):
        draw_ropes(c, k)
    return c


# ------------------------------------------------------------------ members
MASKS = load_masks(os.path.join(HERE, 'masks_clean.txt'))
PLACE = [  # name, tier, x of the mask's anchor column, anchor column
    ('eric', 1, CX, 23),
    ('computah', 2, CX - 44, 7),
    ('greyson', 2, CX + 44, 11),
    ('carter', 3, CX - 42, 11),
    ('josh', 3, CX + 42, 14),
    ('mason', 4, CX, 14),
    ('liam', 5, CX - 38, 14),
    ('bixby', 5, CX + 38, 14),
    ('jordan', 6, CX, 7),
]


def put_member(c, rows, ax, feet, k, anchor):
    h, w = len(rows), len(rows[0])
    x0, y0 = ax - anchor, feet - h + 1
    hi, base, lo = ROLE[k]
    S = lambda x, y: 0 <= y < h and 0 <= x < w and rows[y][x] != '.'
    for y in range(h):
        for x in range(w):
            ch = rows[y][x]
            if ch == '.':
                continue
            col = K
            if ch == '+':
                col = N0
            elif ch == 'o':
                col = WH2
            elif ch == 'R':
                col = PK
            elif not S(x, y - 1):
                col = hi
            elif not S(x - 1, y) or not S(x + 1, y):
                col = base
            c.set(x0 + x, y0 + y, col)


def layer_members():
    c = Canvas(W, H)
    for name, k, ax, anchor in PLACE:
        st = TIERS[k - 1][0]
        feet = st + 2
        put_member(c, MASKS[name], ax, feet, k, anchor)
    return c


# ------------------------------------------------------------------ invite + player
def layer_invite():
    c = Canvas(W, H)
    c.blit(invite.card(), CARD_X, CARD_Y)
    return c


def layer_player():
    c = Canvas(W, H)
    rows = player2.rows()
    c.grid(CX - 16, H - len(rows) - 2, rows, player2.CMAP, skip='.')
    return c


LAYERS = [('sky', layer_sky), ('tower', layer_tower), ('members', layer_members), ('invite', layer_invite),
          ('player', layer_player)]


def build(layers=None):
    out = Canvas(W, H)
    parts = []
    for name, fn in LAYERS:
        lc = fn()
        parts.append((name, lc))
        out.blit(lc, 0, 0)
    return out, parts


if __name__ == '__main__':
    out, parts = build()
    p = out.save(os.path.join(OUT, 'bg_v1.png'))
    crop_zoom(p, os.path.join(OUT, 'bg_v1_2x.png'), 0, 0, W, H, 2)
    crop_zoom(p, os.path.join(OUT, 'bg_v1_top_4x.png'), 300, 0, 264, 180, 4)
    crop_zoom(p, os.path.join(OUT, 'bg_v1_bot_4x.png'), 250, 180, 370, 180, 3)
    print('ok')
