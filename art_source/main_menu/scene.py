"""Main-menu background: 'The Ladder'. 640x360, DB32 only.

A tower of stacked boxing-ring tiers at night. Each tier is one rank of the server; its
member stands on it as a role-lit silhouette. A red-carpet staircase climbs the middle to a
locked, glowing INVITE at the top. The newcomer (player) stands at the foot, back to camera.
Left ~250px stays calm for the logo / NEW GAME / VOLUME UI.
"""
import math, os, random
from lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

W, H = 640, 360
CX = 432
INV_CY = 36          # invite glow centre

# (strip_top, face_top, face_bot, half_width, role colour ramp (hi, base, lo))
ROLE = {
    1: (LG, GR, OG),        # green
    2: (WH2, CY, BL),       # cyan
    3: (SK, OR, BR),        # orange
    4: (WH2, MG, PU),       # pink
    5: (SK, PK, RD),        # red
    6: (WH, YL, TN),        # gold
}
TIERS = [
    (267, 272, 311, 186),
    (229, 234, 266, 158),
    (195, 199, 228, 130),
    (164, 168, 194, 104),
    (137, 140, 163, 80),
    (112, 115, 136, 58),
]
BASE_Y = 311


def stair_hw(y):
    return int(round(12 + (y - 112) * (22 - 12) / float(BASE_Y - 112)))


# ------------------------------------------------------------------ sky
def draw_sky(c):
    rnd = random.Random(7)
    for y in range(H):
        for x in range(W):
            col = N0
            # plum haze toward the horizon
            t = (y - 170) / 140.0
            if t > 0 and dith(x, y, min(1.0, t) * 0.75):
                col = P0
            # halo of the invite
            dx, dy = x - CX, (y - INV_CY) * 1.15
            r = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            ray = 0.5 + 0.5 * math.cos(ang * 9 + 0.6)
            ray = ray ** 3
            glow = max(0.0, 1.0 - r / 150.0)
            g2 = max(0.0, 1.0 - r / 78.0)
            dens = glow * 0.55 + ray * glow * 0.55
            if dens > 0 and dith(x, y, min(1.0, dens)):
                col = IN
            if g2 > 0 and dith(x, y, min(1.0, g2 * 1.1 + ray * g2 * 0.4)):
                col = IN if g2 < 0.45 else RB if dith(x + 1, y, (g2 - 0.45) * 1.6) else IN
            c.set(x, y, col)
    # stars (kept out of the brightest halo)
    for i in range(170):
        x, y = rnd.randrange(W), rnd.randrange(0, 250)
        if math.hypot(x - CX, (y - INV_CY) * 1.15) < 95:
            continue
        v = rnd.random()
        col = G5 if v < 0.55 else WH2 if v < 0.85 else WH
        if y > 190:
            col = G4 if v < 0.7 else G5
        c.set(x, y, col)
    for (x, y) in [(38, 132), (206, 20), (590, 150), (118, 250), (300, 60), (612, 30), (18, 40)]:
        c.set(x, y, WH)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.set(x + dx, y + dy, G5)


# ------------------------------------------------------------------ floor
def draw_floor(c):
    VPY = 150
    for y in range(BASE_Y + 1, H):
        for x in range(W):
            col = N0
            c.set(x, y, col)
    # perspective seams converging on the stairs
    for xb in range(-900, 1800, 48):
        for y in range(BASE_Y + 1, H):
            t = (y - VPY) / float(BASE_Y + 1 - VPY)
            x = int(round(CX + (xb - CX) * t))
            c.set(x, y, K)
    for y in [BASE_Y + 1, 316, 322, 331, 343, 358]:
        c.hline(0, W - 1, y, K)
    # faint reflected glow in front of the base
    for y in range(BASE_Y + 2, H):
        for x in range(W):
            d = math.hypot((x - CX) / 210.0, (y - BASE_Y) / 40.0)
            if d < 1 and c.get(x, y) == N0 and dith(x, y, (1 - d) * 0.6):
                c.set(x, y, P0)


# ------------------------------------------------------------------ tiers
def draw_tier(c, k):
    st, ft, fb, hw = TIERS[k - 1]
    hi, base, lo = ROLE[k]
    x0, x1 = CX - hw, CX + hw
    # canvas top surface
    for y in range(st, ft):
        for x in range(x0, x1 + 1):
            col = OG
            if y == st:
                col = G1
            if y == ft - 1:
                col = TE
            c.set(x, y, col)
    # apron face
    for y in range(ft, fb + 1):
        for x in range(x0, x1 + 1):
            col = N0
            yy = y - ft
            if yy == 0:
                col = TN
            elif yy == 1:
                col = GO
            elif yy == 2:
                col = K
            elif yy < 8 and dith(x, y, 0.55 - (yy - 3) * 0.12):
                col = IN
            if y == fb - 4:
                col = base
            if y == fb - 3:
                col = lo
            if y == fb:
                col = K
            c.set(x, y, col)
    for y in range(st, fb + 1):
        c.set(x0, y, K)
        c.set(x1, y, K)
    c.hline(x0, x1, st - 1, K)


def draw_post(c, px, st, k):
    hi, base, lo = ROLE[k]
    top = st - 16
    for y in range(top, st + 2):
        c.set(px - 1, y, K)
        c.set(px + 2, y, K)
        c.set(px, y, TN)
        c.set(px + 1, y, GO)
    # lantern: round server icon
    ly = top - 4
    icon = ['.###.', '#hbb#', '#bbl#', '#bll#', '.###.']
    # glow
    for yy in range(ly - 8, ly + 9):
        for xx in range(px - 8, px + 10):
            d = math.hypot(xx - (px + 0.5), yy - ly)
            if d < 8.5 and c.get(xx, yy) in (N0, P0) and dith(xx, yy, (1 - d / 8.5) * 0.9):
                c.set(xx, yy, IN)
    c.grid(px - 2, ly - 2, icon, {'#': K, 'h': hi, 'b': base, 'l': lo})


def draw_ropes(c, k):
    st, ft, fb, hw = TIERS[k - 1]
    pl, pr = CX - hw + 4, CX + hw - 5
    gap = stair_hw(st) + 3
    for i, ry in enumerate((st - 5, st - 10)):
        for x in range(pl + 2, pr):
            if abs(x - CX) <= gap:
                continue
            c.set(x, ry, G5 if abs(x - CX) > 90 else WH2)
    draw_post(c, pl, st, k)
    draw_post(c, pr, st, k)


def draw_stairs(c):
    for y in range(112, BASE_Y + 1):
        hw = stair_hw(y)
        for x in range(CX - hw, CX + hw + 1):
            e = abs(x - CX)
            ph = (y - 112) % 4
            if e >= hw - 2:
                col = K if e == hw else GO if e == hw - 1 else TN
            else:
                col = [PK, RD, RD, P0][ph]
                if e >= hw - 4 and ph != 0:
                    col = BR
            c.set(x, y, col)
        c.set(CX - hw - 1, y, K)
        c.set(CX + hw + 1, y, K)


def draw_carpet_runout(c):
    for y in range(BASE_Y + 1, H):
        t = (y - BASE_Y) / float(H - BASE_Y)
        hw = int(round(22 + 30 * t))
        for x in range(CX - hw, CX + hw + 1):
            e = abs(x - CX)
            col = RD
            if e >= hw - 1:
                col = K
            elif e >= hw - 3:
                col = TN if e == hw - 2 else GO
            elif dith(x, y, t * 0.5):
                col = BR
            c.set(x, y, col)


def build_stage1():
    c = Canvas(W, H)
    draw_sky(c)
    for k in range(6, 0, -1):
        draw_tier(c, k)
    for k in range(1, 7):
        draw_ropes(c, k)
    draw_floor(c)
    draw_stairs(c)
    draw_carpet_runout(c)
    return c


if __name__ == '__main__':
    c = build_stage1()
    p = c.save(os.path.join(OUT, 'stage1.png'))
    crop_zoom(p, os.path.join(OUT, 'stage1_2x.png'), 0, 0, 640, 360, 2)
    crop_zoom(p, os.path.join(OUT, 'stage1_top_4x.png'), 300, 0, 260, 200, 4)
    print('ok')
