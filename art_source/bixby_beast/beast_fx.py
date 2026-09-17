"""Per-frame effect layers for the beast Bixby combat sheets. Each builder returns (fx_back, fx_front):
fx_back sits under the wings (floor cracks, the far half of dust rings), fx_front sits over the body."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, BLACK
import fx2 as FX
from body import line_px

W, H = 192, 160
GX, GY = 96, 151          # ground contact centre (frame space)


def blank():
    lib.set_size(W, H)
    return Canvas(W, H)


def debris(cv, x, y, size=2, seed=1):
    """small floor chunk: dark stone with a lit top-left pixel, black outline"""
    R = FX.rng(seed)
    if size <= 1:
        cv.put(int(x), int(y), PALC['D'])
        return
    m = ell(x, y, size * 0.9, size * 0.75)
    m |= {(int(x + (R() - 0.5) * size), int(y + (R() - 0.5) * size))}
    cv.part(m, 'dark', ('sphere', x - 1, y - 1, size + 1, size + 1), TH_B4 if False else [0.9, 0.5, 0.1])


def wind_streaks(cv, pts, color='x'):
    for (a, b) in pts:
        for q in line_px([a, b]):
            cv.put(q[0], q[1], PALC[color])


# ================================================================== LAND
def land_fx(i):
    back, front = blank(), blank()
    if i == 0:
        # short speed lines trailing upward off the flared wing tips and heads while he drops
        wind_streaks(front, [((10, 104), (10, 94)), ((181, 104), (181, 94)), ((20, 124), (20, 116)), ((171, 124), (171, 116)),
                             ((46, 132), (46, 126)), ((145, 132), (145, 126))], 'x')
        return back, front
    if i == 1:
        FX.ground_cracks(back, GX, GY - 1, spokes=10, length=84, seed=21, glow=True, squash=0.30)
        FX.dust_ring(back, front, GX, GY - 5, 78, 8, 7.2, seed=4, n=16, lift=0.8)
        # debris kicked up
        for k, (x, y, s) in enumerate(((22, 124, 2), (170, 120, 2), (40, 110, 1), (152, 108, 1), (8, 134, 1), (184, 136, 1),
                                       (64, 118, 1), (128, 116, 1))):
            debris(front, x, y, s, seed=k + 3)
        # flat shock lines skimming the floor
        wind_streaks(front, [((3, 150), (12, 150)), ((179, 150), (188, 150)), ((5, 155), (11, 155)), ((180, 155), (186, 155))], 'W')
        return back, front
    # crouch: ring spreads wider and breaks up, cracks cool, debris falls back
    FX.ground_cracks(back, GX, GY - 1, spokes=10, length=84, seed=21, glow=False, squash=0.30)
    FX.dust_ring(back, front, GX, GY - 5, 82, 9, 6.0, seed=9, broken=0.4, n=16, lift=1.1)
    for k, (x, y, s) in enumerate(((16, 140, 2), (178, 138, 2), (46, 132, 1), (146, 130, 1))):
        debris(front, x, y, s, seed=k + 13)
    return back, front


# ================================================================== TAKEOFF
def takeoff_fx(i):
    back, front = blank(), blank()
    if i == 0:
        for k, (x, y, r) in enumerate(((40, 149, 2.4), (152, 149, 2.4), (74, 151, 1.8), (118, 151, 1.8))):
            FX.puff(front, x, y, r, seed=40 + k, kind='dust')
        for k, (x, y) in enumerate(((30, 144), (162, 143), (56, 147), (138, 146))):
            debris(front, x, y, 1, seed=k)
        return back, front
    if i == 1:
        # downbeat: dust blasted outward along the floor on both sides
        for k, (x, y, r) in enumerate(((30, 146, 7.0), (14, 140, 5.5), (52, 150, 5.0), (8, 131, 3.2), (70, 152, 3.2))):
            FX.puff(front, x, y, r, seed=60 + k, kind='dust')
            FX.puff(front, 192 - x, y, r, seed=80 + k, kind='dust')
        wind_streaks(front, [((60, 157), (22, 157)), ((132, 157), (170, 157)), ((40, 136), (8, 124)), ((152, 136), (184, 124))], 'W')
        for k, (x, y) in enumerate(((20, 120), (174, 118), (44, 126), (150, 124))):
            debris(front, x, y, 2 if k < 2 else 1, seed=k + 30)
        return back, front
    for k, (x, y, r) in enumerate(((20, 144, 4.0), (6, 136, 3.0), (40, 152, 3.2))):
        FX.puff(front, x, y, r, seed=100 + k, kind='dust', holes=0.3)
        FX.puff(front, 192 - x, y, r, seed=120 + k, kind='dust', holes=0.3)
    return back, front


# ================================================================== RECOVER (smoke from the nostrils, sweat)
def recover_fx(i, P):
    back, front = blank(), blank()
    ox, oy = P['mh']
    DY = 2
    nl, nr = (ox - 4.5, oy + 30 + DY), (ox + 4.5, oy + 30 + DY)
    # middle head: a puff curls out of each nostril, swells and drifts up past the cheeks, then thins out
    MID = [
        [(-19, -20, 2.4), (-14, -14, 1.6)],
        [(-5, 4, 2.6)],
        [(-10, 1, 3.8), (-5, 5, 1.8)],
        [(-15, -8, 4.4), (-11, -1, 2.0)],
    ]
    for j, (dx, dy, r) in enumerate(MID[i]):
        FX.puff(front, nl[0] + dx, nl[1] + dy, r, seed=100 + i * 7 + j)
        FX.puff(front, nr[0] - dx, nr[1] + dy, r, seed=200 + i * 7 + j)
    sx, sy = P['sh']
    rx, ry = P.get('sh_R', (150 - sx, sy))
    sl, sr = (sx + 1.5, sy + 21.5 + DY), (rx + 40.5, ry + 21.5 + DY)
    # side heads: small puffs rise off the nose tips (up and forward, clear of the snout)
    SIDE = [
        [(-3, -21, 1.8), (-1, -16, 1.3)],
        [(-2, -5, 1.8)],
        [(-4, -10, 2.8)],
        [(-4, -16, 3.2)],
    ]
    for j, (dx, dy, r) in enumerate(SIDE[i]):
        FX.puff(front, max(2, sl[0] + dx), sl[1] + dy, r, seed=300 + i * 7 + j)
        FX.puff(front, min(189, sr[0] - dx), sr[1] + dy, r, seed=400 + i * 7 + j)
    FX.stamp(front, FX.SWEAT_BIG, int(ox + 21), int(oy + DY + 1 + [0, 2, 4, 1][i]))
    return back, front


# ================================================================== HIT
def hit_fx(i, P):
    back, front = blank(), blank()
    ox, oy = P['mh']
    sx, sy = P['sh']
    rx, ry = P.get('sh_R', (150 - sx, sy))
    if i == 0:
        drops = [(ox - 26, oy + 6), (ox + 24, oy + 4), (ox - 20, oy - 6), (ox + 18, oy - 8),
                 (sx + 1, sy + 4), (sx + 8, sy - 6), (rx + 36, ry + 4), (rx + 28, ry - 6)]
        for k, (x, y) in enumerate(drops):
            FX.stamp(front, FX.SWEAT if k % 2 else FX.SWEAT_BIG, int(x), int(y), flip=(x > 96))
        # embers jarred loose from the cracks
        FX.embers(front, (40, 96, 152, 130), 10, seed=51, hot_ratio=0.5, sizes=(1, 1, 2))
        return back, front
    drops = [(ox - 30, oy + 14), (ox + 28, oy + 12), (sx + 1, sy + 14), (rx + 36, ry + 14)]
    for k, (x, y) in enumerate(drops):
        FX.stamp(front, FX.SWEAT, int(x), int(y), flip=(x > 96))
    FX.embers(front, (36, 110, 156, 146), 6, seed=77, hot_ratio=0.2, sizes=(1,))
    return back, front


# ================================================================== ROAR
def arc_ring(cv, cx, cy, r, a0, a1, color='L', squash=0.8):
    pts = []
    n = max(6, int(r * abs(a1 - a0) / 3))
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * squash))
    for q in line_px(pts):
        cv.put(q[0], q[1], PALC[color])


def burst(cv, cx, cy, r0, r1, n, offset=0.0, color='L', margin=2):
    """radial speed-line burst (anime roar) centred on (cx, cy); rays stop inside the frame margin"""
    for k in range(n):
        a = math.radians(offset + 360.0 * k / n)
        dx, dy = math.cos(a), math.sin(a) * 0.8
        tmax = r1
        for lim, d in ((margin - cx, dx), (cv.w - 1 - margin - cx, dx), (margin - cy, dy), (cv.h - 1 - margin - cy, dy)):
            if d != 0:
                t = lim / d
                if t > 0:
                    tmax = min(tmax, t)
        rr0 = r0 + (6 if k % 2 else 0)
        if tmax <= rr0 + 3:
            continue
        a0 = (cx + dx * rr0, cy + dy * rr0)
        a1 = (cx + dx * (tmax - 0.5), cy + dy * (tmax - 0.5))
        for q in line_px([a0, a1]):
            cv.put(q[0], q[1], PALC[color])


def roar_fx(i, P):
    back, front = blank(), blank()
    ox, oy = P['mh']
    DY = 2
    mx, my = ox, oy + 48 + DY
    if i == 0:
        FX.embers(front, (10, 40, 182, 140), 8, seed=5, hot_ratio=0.3, sizes=(1,))
        for k, (x, y, r) in enumerate(((44, 150, 2.2), (148, 150, 2.2))):
            FX.puff(front, x, y, r, seed=k + 7, kind='dust')
        return back, front
    burst(back, mx, my - 18, 62 if i == 1 else 70, 96, 22, offset=(0 if i == 1 else 7.5), color='L')
    FX.embers(front, (4, 4, 186, 148), 34 if i == 1 else 40, seed=31 + i * 13, hot_ratio=0.5, sizes=(1, 2, 2, 3))
    for k, (x, y, r) in enumerate(((22, 148, 4.6), (9, 142, 3.0), (46, 153, 3.2))):
        FX.puff(front, x - (2 if i == 2 else 0), y, r, seed=90 + k + i, kind='dust', holes=0.1 if i == 2 else 0)
        FX.puff(front, 192 - x + (2 if i == 2 else 0), y, r, seed=95 + k + i, kind='dust', holes=0.1 if i == 2 else 0)
    return back, front


# ================================================================== FLY
def fly_fx(i):
    back, front = blank(), blank()
    sets = [
        [((2, 58), (14, 58)), ((2, 118), (10, 118)), ((20, 150), (38, 150))],
        [((2, 70), (10, 70)), ((2, 112), (16, 112)), ((24, 154), (40, 154))],
        [((2, 64), (16, 64)), ((2, 124), (8, 124)), ((18, 146), (32, 146))],
    ]
    wind_streaks(back, sets[i], 'x')
    return back, front
