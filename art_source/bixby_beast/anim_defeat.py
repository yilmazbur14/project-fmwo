"""DEFEAT sequence for the beast Bixby: 10 frames of 192x160, feet anchor (96,151) on the ground.
 0 final blow: every head snaps back, glow flares
 1 collapse: belly flat, heads down, dizzy swirl eyes, glow dimming
 2 glow and cracks die, wing membranes crumble into embers
 3 poof: smoke burst hides the shrink
 4 normal Bixby (bixby.png) revealed, dizzy stars circling
 5 cough wind-up: cheeks puffed, side heads alarmed
 6 HACK: slimy Liam shoots out of the middle mouth, upside down
 7 Liam tumbles through the air to the right
 8 Liam lands on his rump beside Bixby (dust, slime splat)
 9 HOLD: Bixby sits sheepishly beside dazed Liam (stars over Liam)"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, BLACK
import anim_rig as AR
import beast_poses as BP
import beast_fx as BF
import fx2 as FX
import small_art as SA

W, H = 192, 160
DY = 2
BIX_X, BIX_Y = 64, 89          # bixby.png placement: middle head centred on x=96, paws (row 62) on y=151
LIAM_SIT_X, LIAM_SIT_Y = 126, 90

LAYERS = ['fx_back', 'wings', 'body', 'liam', 'fx_front']


def blank():
    lib.set_size(W, H)
    return Canvas(W, H)


# ------------------------------------------------------------------ effects specific to the defeat
def crumble(cv, t, seed=1, roots=((84, 101), (108, 101))):
    """burn a wing layer away from the tips inward in blobby chunks. Surviving pixels next to a hole become a
    glowing rim (F/o/O) with a charred band behind it. Returns the pixels removed (for ember placement)."""
    pts = [(x, y) for y in range(cv.h) for x in range(cv.w) if cv.px[y][x] is not None]
    if not pts:
        return []
    dist = {}
    maxd = 1.0
    for (x, y) in pts:
        d = min(math.hypot(x - rx, y - ry) for rx, ry in roots)
        dist[(x, y)] = d
        maxd = max(maxd, d)
    removed = []
    for (x, y) in pts:
        v = _noise(x * 0.09, y * 0.09, seed)
        if v * 0.7 + (dist[(x, y)] / maxd) * 0.85 > 1.36 - t * 1.15:
            cv.px[y][x] = None
            removed.append((x, y))
    rem = set(removed)
    keep = [(x, y) for (x, y) in pts if cv.px[y][x] is not None]
    rim = []
    for (x, y) in keep:
        if any((x + dx, y + dy) in rem for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            rim.append((x, y))
    for (x, y) in rim:
        h = (x * 7 + y * 3 + seed) % 5
        cv.px[y][x] = PALC['O'] if h == 0 else (PALC['o'] if h < 3 else PALC['F'])
    rims = set(rim)
    for (x, y) in keep:
        if (x, y) in rims or cv.px[y][x] == BLACK:
            continue
        if any((x + dx, y + dy) in rims for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            cv.px[y][x] = PALC['r'] if (x + y) % 3 == 0 else PALC['T']
    return removed


def _noise(x, y, seed):
    import fire
    return fire.fbm(x, y, seed)


def embers_from(cv, removed, n, seed=3, rise=6):
    R = FX.rng(seed)
    if not removed:
        return
    for k in range(n):
        x, y = removed[int(R() * len(removed)) % len(removed)]
        FX.ember(cv, x + (R() - 0.5) * 6, y - rise * R() - 2, size=1 if R() < 0.45 else (2 if R() < 0.8 else 3), hot=R() < 0.6)


def poof(cv, cx, cy, rx, ry, seed=5, n=16, rmin=9, rmax=16, holes=0.0):
    R = FX.rng(seed)
    items = []
    for k in range(n):
        a = 2 * math.pi * k / n + R() * 0.4
        d = 0.55 + 0.45 * R()
        items.append((math.sin(a), cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, rmin + (rmax - rmin) * R(), k))
    items.append((0, cx, cy, rmax + 3, n))
    for sn, x, y, r, k in sorted(items):
        m = FX.blob(x, y, r, lumps=6, seed=seed * 13 + k, squash=0.85)
        if holes:
            RR = FX.rng(seed * 7 + k)
            m = {q for q in m if RR() > holes}
            m = {q for q in m if sum(((q[0] + dx, q[1] + dy) in m) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2}
        FX.shade_cloud(cv, m, x, y, r, [PALC['W'], PALC['x'], PALC['X']], PALC['y'])


SPARK = """
..k..
.kWk.
kWWWk
.kWk.
..k..
"""
SPARK_S = """
.W.
WWW
.W.
"""


def dizzy_stars(cv, cx, cy, rx, ry, phase, n=3, big=True):
    for k in range(n):
        a = phase + 2 * math.pi * k / n
        x = cx + math.cos(a) * rx
        y = cy + math.sin(a) * ry
        grid = FX.STAR5 if (big and math.sin(a) > -0.2) else FX.STAR3
        rows = grid.strip('\n').split('\n')
        FX.stamp(cv, grid, int(round(x - len(rows[0]) / 2)), int(round(y - len(rows) / 2)))


def slime_drop(cv, x, y, big=False):
    g = """
.k.
kCk
kWk
.k.
""" if not big else """
.kk.
kCCk
kWCk
.kk.
"""
    FX.stamp(cv, g, int(x), int(y))


def paste(dst, src, ox, oy):
    for y in range(src.h):
        for x in range(src.w):
            c = src.px[y][x]
            if c is not None:
                dst.put(ox + x, oy + y, c)


# ------------------------------------------------------------------ beast frames
def beast_collapse(glow, eyes, **kw):
    P = BP.exhausted(k=4, mh=(96, 76), sh=(6, 92), sh_R=(144, 92), jaw=3, wing=8, tongue=(7, 8), sway=(1, -1),
                     eyes=eyes, mouth='pant', eyes_side=eyes, mouth_side='pant', glow=glow)
    P['sn_base'], P['sn_base_R'] = (60, 114), (132, 114)
    P.update(kw)
    return P


def frames():
    out = []
    # 0: final blow
    P = BP.exhausted(k=-5, mh=(96, 44), sh=(10, 56), sh_R=(140, 56), jaw=5, wing=0, wing_lift=14, tongue=(0, 0),
                     eyes='shut', mouth='yelp', eyes_side='shut', mouth_side='yelp', glow=2, tails=BP.TAILS_FLICK)
    P['sn_base'], P['sn_base_R'] = (64, 88), (128, 88)
    P['side_rot'] = (18, -18)
    wings, body = AR.render(P, dy=DY)
    back, front = blank(), blank()
    BF.burst(back, 96, 96, 70, 98, 20, offset=4, color='W')
    FX.embers(back, (4, 40, 188, 156), 26, seed=301, hot_ratio=0.7, sizes=(1, 2, 2, 3))
    FX.embers(front, (4, 120, 40, 156), 4, seed=302, hot_ratio=0.7, sizes=(1, 2))
    FX.embers(front, (152, 120, 188, 156), 4, seed=303, hot_ratio=0.7, sizes=(1, 2))
    ox, oy = P['mh']
    for k, (x, y) in enumerate(((ox - 30, oy + 4), (ox + 26, oy + 2), (ox - 22, oy - 10), (ox + 20, oy - 12), (10, 60), (178, 60))):
        FX.stamp(front, FX.SWEAT_BIG, int(x), int(y), flip=x > 96)
    out.append(dict(fx_back=back, wings=wings, body=body, liam=blank(), fx_front=front))
    # 1: collapse
    P = beast_collapse(1, 'dizzy')
    wings, body = AR.render(P, dy=DY)
    back, front = blank(), blank()
    FX.dust_ring(back, front, 96, 146, 80, 8, 5.6, seed=77, n=14, lift=0.9)
    ox, oy = P['mh']
    dizzy_stars(front, ox, oy - 8, 24, 5, 0.3)
    out.append(dict(fx_back=back, wings=wings, body=body, liam=blank(), fx_front=front))
    # 2: glow dies, wings crumble into embers
    P = beast_collapse(0, 'dizzy', tail_glow=0)
    wings, body = AR.render(P, dy=DY)
    removed = crumble(wings, 0.5, seed=11)
    back, front = blank(), blank()
    embers_from(front, removed, 46, seed=12, rise=14)
    dizzy_stars(front, ox, oy - 8, 24, 5, 1.4)
    out.append(dict(fx_back=back, wings=wings, body=body, liam=blank(), fx_front=front))
    # 3: poof (the beast is gone behind the cloud; wings nearly burnt away at the edges)
    wings2 = wings.copy()
    removed2 = crumble(wings2, 1.0, seed=11)
    back, front = blank(), blank()
    poof(front, 96, 122, 64, 16, seed=21, n=17, rmin=11, rmax=19)
    embers_from(front, removed + removed2, 30, seed=13, rise=26)
    for k, (x, y) in enumerate(((30, 70), (160, 66), (70, 58), (124, 54), (96, 44))):
        FX.stamp(front, SPARK if k % 2 == 0 else SPARK_S, x, y)
    out.append(dict(fx_back=back, wings=wings2, body=blank(), liam=blank(), fx_front=front))
    # 4: normal Bixby revealed, dizzy
    body = blank()
    paste(body, SA.bixby_variant('dizzy'), BIX_X, BIX_Y)
    back, front = blank(), blank()
    for k, (x, y, r) in enumerate(((50, 146, 5.5), (142, 146, 5.5), (68, 153, 4.0), (124, 153, 4.0), (34, 136, 3.4), (158, 136, 3.4), (96, 84, 2.6))):
        m = FX.blob(x, y, r, lumps=5, seed=600 + k, squash=0.85)
        FX.shade_cloud(back if y < 150 else front, m, x, y, r, [PALC['W'], PALC['x'], PALC['X']], PALC['y'])
    for k, (x, y) in enumerate(((40, 112), (150, 104), (78, 76), (120, 72))):
        FX.stamp(front, SPARK_S, x, y)
    dizzy_stars(front, 96, BIX_Y + 2, 20, 5, 0.2)
    FX.embers(front, (30, 110, 162, 150), 8, seed=41, hot_ratio=0.1, sizes=(1,))
    out.append(dict(fx_back=back, wings=blank(), body=body, liam=blank(), fx_front=front))
    # 5: cough wind-up (jolts up 1px)
    body = blank()
    paste(body, SA.bixby_variant('cough'), BIX_X, BIX_Y - 1)
    back, front = blank(), blank()
    dizzy_stars(front, 96, BIX_Y + 1, 20, 5, 1.3, n=2)
    for k, (x, y) in enumerate(((60, BIX_Y + 12), (130, BIX_Y + 11))):
        FX.stamp(front, FX.SWEAT, x, y, flip=x > 96)
    # "hic" shake lines beside the middle head
    BF.wind_streaks(front, [((78, BIX_Y + 6), (74, BIX_Y + 4)), ((114, BIX_Y + 6), (118, BIX_Y + 4)),
                            ((78, BIX_Y + 12), (73, BIX_Y + 12)), ((114, BIX_Y + 12), (119, BIX_Y + 12))], 'W')
    out.append(dict(fx_back=back, wings=blank(), body=body, liam=blank(), fx_front=front))
    # 6: HACK - Liam shoots out upside down
    body = blank()
    paste(body, SA.bixby_variant('hack'), BIX_X, BIX_Y)
    back, front = blank(), blank()
    lm = blank()
    paste(lm, SA.liam_tumble(2), 70, 12)
    for k, (x, y, big) in enumerate(((92, 100, True), (104, 96, False), (84, 92, False), (110, 86, True), (98, 84, False),
                                     (80, 80, False), (116, 76, False))):
        slime_drop(front, x, y, big)
    BF.wind_streaks(front, [((74, 70), (70, 50)), ((124, 70), (128, 50)), ((84, 74), (82, 62)), ((114, 74), (116, 62))], 'W')
    out.append(dict(fx_back=back, wings=blank(), body=body, liam=lm, fx_front=front))
    # 7: Liam tumbles to the right
    body = blank()
    paste(body, SA.bixby_variant('look'), BIX_X, BIX_Y)
    back, front = blank(), blank()
    lm = blank()
    paste(lm, SA.liam_tumble(1), 122, 26)
    for k, (x, y, big) in enumerate(((118, 70, True), (128, 98, False), (112, 56, False), (140, 100, True))):
        slime_drop(front, x, y, big)
    BF.wind_streaks(front, [((110, 40), (98, 52)), ((116, 30), (104, 42)), ((122, 22), (112, 32))], 'W')
    out.append(dict(fx_back=back, wings=blank(), body=body, liam=lm, fx_front=front))
    # 8: Liam lands on his rump beside Bixby
    body = blank()
    paste(body, SA.bixby_variant('look'), BIX_X, BIX_Y)
    back, front = blank(), blank()
    lm = blank()
    paste(lm, SA.liam_sit(squash=2), LIAM_SIT_X, LIAM_SIT_Y)
    for k, (x, y, r) in enumerate(((128, 150, 4.6), (183, 149, 4.4), (120, 153, 3.0), (186, 154, 2.4))):
        FX.puff(front, x, y, r, seed=500 + k, kind='dust')
    for k, (x, y, big) in enumerate(((140, 84, True), (174, 82, True), (130, 96, False), (184, 94, False), (158, 76, False))):
        slime_drop(front, x, y, big)
    out.append(dict(fx_back=back, wings=blank(), body=body, liam=lm, fx_front=front))
    # 9: HOLD
    body = blank()
    paste(body, SA.bixby_sit(), BIX_X, BIX_Y)
    back, front = blank(), blank()
    lm = blank()
    paste(lm, SA.liam_sit(), LIAM_SIT_X, LIAM_SIT_Y)
    dizzy_stars(front, LIAM_SIT_X + 31, LIAM_SIT_Y + 6, 16, 4, 0.9)
    out.append(dict(fx_back=back, wings=blank(), body=body, liam=lm, fx_front=front))
    return out


def flatten(fr):
    c = Canvas(W, H)
    for L in LAYERS:
        c.blit(fr[L], 0, 0)
    return c


if __name__ == '__main__':
    import anim_common as AC
    fr = frames()
    comps = [flatten(f) for f in fr]
    top = AC.strip_of(comps[:5])
    bot = AC.strip_of(comps[5:])
    sheet = Canvas(top.w, 320)
    sheet.blit(top, 0, 0)
    sheet.blit(bot, 0, 160)
    AC.preview(sheet, sys.argv[1] + '.png', 2)
    print('ok')
