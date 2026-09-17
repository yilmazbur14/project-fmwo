"""Effect art for beast Bixby's pound + spin attack.

  bixby_quake_crack.png   48 x 24,  4 frames   telegraph: a glowing crack opening in the floor
  bixby_quake_burst.png   64 x 64,  6 frames   the eruption that follows 1.2 s later
  bixby_quake_wave.png    32 x 32,  4 frames   the travelling ridge between bursts (tiles every 32 px)
  bixby_sonic_beam.png   128 x 48,  4 frames   one head's scream, pointing RIGHT, pivot at the mouth

Everything is opaque (alpha 0/255). The ground effects use Bixby's own fire/ember palette (lava ramp
over the dark stone and ear-brown ramps); the scream uses a cool DB32 blue ramp so it can never be
mistaken for his fire.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, RAMPC, BLACK, hexc
import fx2 as FX
from body import line_px

# ---- the scream's own ramp (DB32 blues; CBDBFC is already in the cast palette as 'C')
SONIC = {
    '#': hexc('FFFFFF'),
    '(': hexc('CBDBFC'),
    ')': hexc('5FCDE4'),
    '[': hexc('639BFF'),
    ']': hexc('5B6EE1'),
    '{': hexc('3F3F74'),
}
SONIC_RAMP = [SONIC['#'], SONIC['('], SONIC[')'], SONIC['['], SONIC[']'], SONIC['{']]

FX_PAL = dict(FX.FX_PAL)
FX_PAL.update(SONIC)

STONE = RAMPC['dark']          # G B D J Z
EARTH = RAMPC['ear']           # a b c d e
LAVA = ['W', 'L', 'O', 'o', 'F', 'r']


def rng(seed):
    return FX.rng(seed)


# ==================================================================== quake crack (telegraph)
CRACK_W, CRACK_H = 48, 24
CRACK_C = (24, 13)             # put this texel on the impact point


def _fissure(cv, cx, cy, half, hmax, hot, seed=11, squash=1.0):
    """a spindle-shaped split in the floor: black lips, molten core, hairline cracks running off it"""
    R = rng(seed)
    lip_top, lip_bot = {}, {}
    for x in range(cx - half, cx + half + 1):
        u = (x - cx) / max(1.0, half)
        h = hmax * max(0.0, 1.0 - u * u) ** 0.65
        h *= 0.82 + 0.36 * ((x * 7 + seed) % 5) / 4.0          # ragged, but deterministic
        yc = cy + 1.6 * u * u * squash + (((x * 5 + seed * 3) % 3) - 1) * 0.6 * squash
        lip_top[x], lip_bot[x] = yc - h, yc + h
        if h < 0.35:
            cv.put(x, int(round(yc)), BLACK)
            continue
        for y in range(int(math.floor(yc - h)), int(math.ceil(yc + h)) + 1):
            d = abs((y + 0.5 - yc) / max(0.4, h))
            if d > 1.0:
                continue
            if hot <= 0 or d > 0.80:
                c = BLACK
            elif d > 0.58:
                c = PALC['r']
            elif d > 0.40:
                c = PALC[LAVA[4]]
            else:
                lv = max(0, 3 - hot)
                c = PALC[LAVA[lv]] if abs(u) < 0.72 else PALC[LAVA[min(5, lv + 2)]]
                if hot >= 3 and abs(u) < 0.45 and (x + y) % 2 == 0:
                    c = PALC['W']
            cv.put(x, y, c)
    # hairline cracks spidering away from the split
    for i in range(5):
        sx = cx - half + int((i + 0.5) * 2 * half / 5)
        up = (i % 2 == 0)
        y0 = (lip_top.get(sx, cy) - 1) if up else (lip_bot.get(sx, cy) + 1)
        pts = [(sx, y0)]
        ang = (-math.pi / 2 if up else math.pi / 2) + (R() - 0.5) * 2.0
        x, y = sx, y0
        for st in range(2):
            ang += (R() - 0.5) * 1.6
            x += math.cos(ang) * 2.4
            y += math.sin(ang) * 2.4 * squash
            pts.append((x, y))
        for j, q in enumerate(line_px(pts)):
            if not (0 <= q[0] < cv.w and 0 <= q[1] < cv.h):
                continue
            cv.put(q[0], q[1], BLACK if (j > 1 or hot < 2) else PALC[LAVA[4]])
    return lip_top, lip_bot


def _chunk(cv, x, y, s, seed=1, ramp='dark', bias=0, spin=0.0):
    """a chunky piece of broken floor: irregular polygon, shaded, black outline"""
    R = rng(seed)
    n = 5
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + spin
        r = s * (0.72 + 0.5 * R())
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r * 0.86))
    m = poly(pts)
    if len(m) < 3:
        m = ell(x, y, max(1.0, s * 0.7), max(1.0, s * 0.6))
    cv.part(m, ramp, ('sphere', x - s * 0.45, y - s * 0.5, s + 1.6, s + 1.4, 0.18), TH_B4, bias=bias)
    return m


def crack_frame(k):
    """k 0..3: hairline -> splitting -> molten -> pulsing white (frames 2 and 3 loop as the throb)"""
    lib.set_size(CRACK_W, CRACK_H)
    cv = Canvas(CRACK_W, CRACK_H)
    cx, cy = CRACK_C
    half = [9, 15, 20, 20][k]
    hmax = [0.9, 2.0, 3.4, 3.7][k]
    hot = [0, 1, 2, 3][k]
    _fissure(cv, cx, cy, half, hmax, hot, seed=11, squash=1.0)
    if k >= 2:
        for j, (dx, dy, sz, rp) in enumerate(((-15, 5, 3.2, 'dark'), (-7, -5, 2.8, 'ear'),
                                              (5, 6, 3.4, 'dark'), (14, -4, 3.0, 'ear'),
                                              (-20, -3, 2.4, 'ear'), (19, 5, 2.6, 'dark'))):
            _chunk(cv, cx + dx, cy + dy, sz, seed=20 + j, ramp=rp, bias=-1, spin=j * 0.7)
    if hot >= 1:
        FX.embers(cv, (4, 2, 44, 20), 3 + hot * 4, seed=41 + k * 7, hot_ratio=0.25 + 0.2 * hot,
                  sizes=(1, 1, 2))
    return cv


# ==================================================================== quake burst (eruption)
BURST_W, BURST_H = 64, 64
BURST_C = (32, 52)             # ground contact

BURST_CHUNKS = [  # (angle deg, speed, size, ramp)
    (-90, 1.00, 4.2, 'dark'), (-64, 0.94, 3.4, 'ear'), (-114, 0.90, 3.6, 'dark'),
    (-44, 0.82, 2.8, 'ear'), (-138, 0.78, 2.6, 'dark'), (-76, 1.12, 2.8, 'ear'),
    (-104, 1.08, 2.4, 'dark'), (-28, 0.64, 2.2, 'dark'), (-152, 0.60, 2.0, 'ear'),
    (-54, 0.72, 1.8, 'ear'), (-126, 0.74, 1.9, 'dark'), (-94, 0.55, 1.7, 'dark'),
]


def burst_frame(k):
    """k 0..5: flash -> the floor bursts -> full eruption -> peak -> falling -> settling scar"""
    lib.set_size(BURST_W, BURST_H)
    cv = Canvas(BURST_W, BURST_H)
    cx, gy = BURST_C
    half = [8, 15, 21, 24, 25, 26][k]
    hmax = [1.4, 3.4, 4.6, 4.2, 3.2, 2.2][k]
    hot = [3, 3, 3, 2, 1, 1][k]
    # --- dome of light heaving out of the split, with ragged tongues licking up between the chunks
    dome_h = [5, 15, 21, 17, 9, 0][k]
    dome_w = [7, 15, 20, 22, 20, 0][k]
    if dome_h:
        for x in range(cx - dome_w, cx + dome_w + 1):
            u = (x - cx) / max(1.0, dome_w)
            jag = 0.70 + 0.55 * (((x * 3 + k * 7) % 5) / 4.0)
            h = dome_h * max(0.0, 1 - u * u) ** 0.55 * jag
            for j in range(int(h)):
                t = j / max(1.0, h)
                y = gy - 3 - j
                if y < 1:
                    break
                lv = (0 if (abs(u) < 0.34 and t < 0.45) else (1 if abs(u) < 0.62 else 2)) + int(t * 2.8)
                if k >= 3:
                    lv += 1
                cv.put(x, y, PALC[LAVA[min(5, lv)]])
        # a few tall tongues of light shooting higher than the dome
        for j, (dx, hh) in enumerate(((-9, 1.5), (0, 1.9), (8, 1.4), (-15, 1.0), (14, 1.1))):
            if k == 0 or k >= 4:
                break
            x = cx + dx
            for t in range(int(dome_h * hh * 0.55)):
                y = gy - 3 - int(dome_h * 0.55) - t
                if y < 1:
                    break
                lv = 1 + int(t / max(1.0, dome_h * 0.25))
                cv.put(x + (1 if t % 4 == 2 else 0), y, PALC[LAVA[min(5, lv + (1 if k >= 3 else 0))]])
    # --- the split itself
    _fissure(cv, cx, gy, half, hmax, hot, seed=23 + k, squash=0.55)
    if k >= 1:
        # rim slabs tipped up on both sides
        for sgn in (-1, 1):
            for j in range(3):
                px = cx + sgn * (half - 3 - j * 7)
                py = gy + 2 + j * 1.2
                _chunk(cv, px, py, 3.8 - j * 0.5, seed=60 + j + (0 if sgn < 0 else 7), ramp='dark',
                       bias=-1, spin=j * 0.5 + (0 if sgn < 0 else 1.1))
        # flung chunks
        rise = [0, 12, 27, 35, 33, 20][k]
        for j, (ang, sp, sz, ramp) in enumerate(BURST_CHUNKS):
            if k == 1 and j > 6:
                continue
            a_ = math.radians(ang)
            d = rise * sp
            x = cx + math.cos(a_) * d * 1.0
            y = gy - 4 + math.sin(a_) * d + (0 if k < 3 else (k - 2) ** 2 * 2.8 * sp)
            if not (3 <= x < BURST_W - 3 and 2 <= y < BURST_H - 2):
                continue
            _chunk(cv, x, y, sz * (1.0 if k < 4 else 0.9), seed=80 + j * 3 + k, ramp=ramp,
                   bias=-1 if k < 4 else 0, spin=(k * 0.9 + j * 1.3))
    puffs = [[(-6, -1, 2.6), (6, -1, 2.6)],
             [(-13, -3, 5.2), (13, -3, 5.2), (0, -15, 4.2)],
             [(-19, -4, 6.6), (19, -4, 6.6), (-10, -20, 5.6), (10, -20, 5.6)],
             [(-24, -3, 7.0), (24, -3, 7.0), (-14, -24, 6.6), (14, -24, 6.6), (0, -35, 5.4)],
             [(-27, -2, 6.4), (27, -2, 6.4), (-17, -26, 6.8), (17, -26, 6.8), (0, -38, 5.8)],
             [(-28, -1, 5.0), (28, -1, 5.0), (-19, -23, 5.4), (19, -23, 5.4), (0, -34, 4.6)]][k]
    for j, (dx, dy, r) in enumerate(puffs):
        FX.puff(cv, cx + dx, gy + dy, r, seed=91 + k * 13 + j, kind='dust', holes=0.06 * k)
    FX.embers(cv, (5, max(2, gy - 46), 59, gy + 6), [6, 12, 20, 22, 16, 9][k],
              seed=131 + k * 5, hot_ratio=0.65 - 0.09 * k, sizes=(1, 1, 2, 3))
    return cv


# ==================================================================== travelling ground wave
WAVE_W, WAVE_H = 32, 32
WAVE_GY = 24                   # ground line inside the tile
WAVE_PERIOD = 32               # space the tiles exactly this far apart


def wave_frame(k, n=4):
    """A rolling ridge of cracked, glowing earth. Every feature is a function of (x + phase) mod 32, so
    a row of tiles WAVE_PERIOD apart reads as one continuous wave and frames 0..3 roll it one period."""
    lib.set_size(WAVE_W, WAVE_H)
    cv = Canvas(WAVE_W, WAVE_H)
    ph = WAVE_PERIOD * k / n

    def crest(x):
        u = 2 * math.pi * (x - ph) / WAVE_PERIOD
        return 11.5 * (0.5 + 0.5 * math.cos(u)) + 2.2 * (0.5 + 0.5 * math.cos(2 * u + 1.1))

    def base(x):
        u = 2 * math.pi * (x - ph) / WAVE_PERIOD
        return WAVE_GY + 2.2 + 1.6 * math.cos(u + 0.9)

    top = {x: WAVE_GY - crest(x + 0.5) for x in range(WAVE_W)}
    ridge = set()
    for x in range(WAVE_W):
        for y in range(int(math.floor(top[x])), int(round(base(x + 0.5))) + 1):
            if 0 <= y < WAVE_H:
                ridge.add((x, y))
    cv.part(ridge, 'ear',
            ('func', lambda x, y: ((x - 16) / 26.0, (y - top.get(int(x), WAVE_GY) - 4) / 9.0, 1.0)),
            TH_B, outline=False)
    # rock plates riding the crest
    for i in range(4):
        px = (i * 8 + 4 - ph) % WAVE_PERIOD
        py = top.get(int(px) % WAVE_W, WAVE_GY) + 2.4
        w = 3.4
        m = poly([(px - w, py + 3), (px - w + 1.2, py - 2), (px + w - 1.2, py - 1.2), (px + w, py + 3)]) & ridge
        if m:
            cv.part(m, 'dark', ('sphere', px - 1, py - 2, w + 2, 5, 0.2), TH_B4)
    # glowing seams between the plates
    for i in range(4):
        sx = (i * 8 - ph) % WAVE_PERIOD
        pts = []
        for j in range(8):
            y = top.get(int(sx) % WAVE_W, WAVE_GY) + 1 + j
            pts.append((sx + math.sin(j * 1.1 + i) * 1.5, y))
        for j, q in enumerate(line_px(pts)):
            qq = (int(q[0]) % WAVE_W, q[1])
            if qq in ridge:
                cv.put(qq[0], qq[1], PALC[LAVA[1 if j < 3 else (2 if j < 6 else 4)]])
    # black lip along the crest and a lit rim under it; black underside where it meets the floor
    for x in range(WAVE_W):
        y = int(math.floor(top[x]))
        cv.put(x, y, BLACK)
        if (x, y + 1) in ridge:
            cv.put(x, y + 1, PALC['a'])
        yb = int(round(base(x + 0.5)))
        cv.put(x, yb, BLACK)
    # embers thrown off the crest, dust at the foot
    for i in range(5):
        x = (i * 6.4 + 2 + ph * 0.6) % WAVE_W
        y = top.get(int(x), WAVE_GY) - 2 - (i % 3) * 3
        if y > 1:
            FX.ember(cv, x, y, 1 + (i % 2), hot=(i % 3 != 2))
    for i in range(3):
        x = (i * 11 + 5 - ph * 0.4) % WAVE_W
        FX.puff(cv, x, WAVE_GY + 1.5, 1.7 + (i % 2) * 0.4, seed=71 + k * 5 + i, kind='dust', holes=0.35)
    # the tile must be flush at both seams: never let the outline close across the left/right edges
    for y in range(WAVE_H):
        for x in (0, WAVE_W - 1):
            inner = cv.get(1 if x == 0 else WAVE_W - 2, y)
            if cv.px[y][x] == BLACK and inner not in (None, BLACK) and (x, y) in ridge and (
                    (1 if x == 0 else WAVE_W - 2, y) in ridge):
                cv.px[y][x] = inner
    return cv


# ==================================================================== sonic scream
BEAM_W, BEAM_H = 128, 48
BEAM_PIVOT = (2, 24)           # the mouth: put this texel on the head's mouth, then rotate
RING_GAP = 22.0
RING_N = 6


def _cone_w(x):
    return 4.0 + 18.0 * max(0.0, x - 8.0) / 118.0


def _ring(cv, x0, bright):
    """one wavefront: a forward-bulging arc, white on its leading edge and cooling backwards"""
    w = _cone_w(x0)
    if w < 2:
        return
    sag = 0.45 * w
    thick = [4, 3, 3, 2][bright]
    lead = [0, 0, 1, 2][bright]          # index into SONIC_RAMP for the leading pixel
    for v in range(-int(w), int(w) + 1):
        f = v / w
        x = x0 + sag * (1 - f * f)
        y = BEAM_PIVOT[1] + v
        if not (0 <= y < BEAM_H):
            continue
        fade = 2 if abs(f) > 0.86 else (1 if abs(f) > 0.66 else 0)
        for t in range(thick):
            xx = int(round(x)) - t
            if not (0 <= xx < BEAM_W):
                continue
            idx = min(5, lead + fade + (0 if t == 0 else (1 if t < thick - 1 else 2)))
            cv.put(xx, y, SONIC_RAMP[idx])


def beam_frame(k, n=4):
    """k 0..3, a perfect loop: the wavefronts march one ring-gap outward over the four frames"""
    lib.set_size(BEAM_W, BEAM_H)
    cv = Canvas(BEAM_W, BEAM_H)
    off = RING_GAP * k / n
    # sparse sparkle inside the cone so it reads as one beam of sound, not floating arcs
    for x in range(8, BEAM_W):
        w = _cone_w(x)
        for v in range(-int(w) + 1, int(w)):
            y = BEAM_PIVOT[1] + v
            if not (0 <= y < BEAM_H):
                continue
            hsh = ((x * 73856093) ^ (y * 19349663) ^ ((k + 1) * 83492791)) & 0xFFFF
            if hsh % 9 == 0:
                cv.put(x, y, SONIC[')'] if x < 66 else SONIC['['])
    # the cone edges, dashed so they read as travelling
    for sgn in (-1, 1):
        for x in range(10, BEAM_W):
            w = _cone_w(x)
            y = int(round(BEAM_PIVOT[1] + sgn * w))
            if not (0 <= y < BEAM_H):
                continue
            ph = (x + int(off * 2)) % 9
            if ph < 5:
                cv.put(x, y, SONIC_RAMP[1 if x < 50 else 2])
            elif ph == 5:
                cv.put(x, y, SONIC_RAMP[3])
    # the wavefronts
    for i in range(RING_N + 1):
        x0 = 12.0 + RING_GAP * i + off
        if x0 > BEAM_W + 6:
            continue
        bright = 0 if x0 < 48 else (1 if x0 < 86 else 2)
        _ring(cv, x0, bright)
    # white-hot core at the mouth
    px, py = BEAM_PIVOT
    for q in ell(px + 5, py, 8.0, 5.6):
        d = math.hypot((q[0] + 0.5 - px - 5) / 8.0, (q[1] + 0.5 - py) / 5.6)
        cv.put(q[0], q[1], SONIC['#'] if d < 0.45 else (SONIC['('] if d < 0.74 else SONIC[')']))
    for q in ell(px + 3, py, 4.0, 2.8):
        cv.put(q[0], q[1], SONIC['#'])
    return cv


# ==================================================================== dizzy stars
def dizzy_stars(cv, cx, cy, k, n=3, rx=22, ry=7):
    """stars circling over his head during the dizzy recovery"""
    for j in range(n):
        a = math.radians(k * 30.0 + 360.0 * j / n)
        x = cx + rx * math.cos(a)
        y = cy + ry * math.sin(a) - 2
        grid = FX.STAR5 if j == 0 else FX.STAR3
        FX.stamp(cv, grid, int(x - 4), int(y - 4), flip=(j % 2 == 1))


SHEETS = {
    'bixby_quake_crack': (CRACK_W, CRACK_H, 4, crack_frame),
    'bixby_quake_burst': (BURST_W, BURST_H, 6, burst_frame),
    'bixby_quake_wave': (WAVE_W, WAVE_H, 4, wave_frame),
    'bixby_sonic_beam': (BEAM_W, BEAM_H, 4, beam_frame),
}


# ==================================================================== per-frame FX for the character sheets
FW, FH = 192, 160
GX, GY = 96, 151           # ground contact centre, frame space


def _blank():
    lib.set_size(FW, FH)
    return Canvas(FW, FH)


def _streaks(cv, pts, color='W'):
    for (a, b) in pts:
        for q in line_px([a, b]):
            cv.put(q[0], q[1], PALC[color])


def pound_fx(i, paws):
    """(fx_back, fx_front) for bixby_pound.png frame i. paws = ((lx, ly), (rx, ry)) in frame coords."""
    back, front = _blank(), _blank()
    (lx, ly), (rx, ry) = paws
    if i == 0:
        for j, (x, r) in enumerate(((lx + 4, 2.4), (rx - 4, 2.4), (74, 1.8), (118, 1.8))):
            FX.puff(front, x, GY - 1, r, seed=200 + j, kind='dust', holes=0.15)
        FX.embers(front, (40, 96, 152, 140), 5, seed=211, hot_ratio=0.4, sizes=(1,))
        return back, front
    if i == 1:
        FX.embers(front, (24, 40, 168, 140), 12, seed=221, hot_ratio=0.6, sizes=(1, 2))
        _streaks(front, [((lx - 2, ly + 10), (lx - 2, ly + 20)), ((rx + 2, ry + 10), (rx + 2, ry + 20)),
                         ((14, 128), (14, 138)), ((178, 128), (178, 138))], 'x')
        for j, (x, r) in enumerate(((46, 2.0), (146, 2.0))):
            FX.puff(front, x, GY, r, seed=230 + j, kind='dust', holes=0.3)
        return back, front
    if i == 2:
        # claws whipping down: hard speed lines behind each paw
        for (px_, py_) in ((lx, ly), (rx, ry)):
            _streaks(front, [((px_ - 5, py_ - 26), (px_ - 5, py_ - 8)), ((px_, py_ - 32), (px_, py_ - 10)),
                             ((px_ + 5, py_ - 24), (px_ + 5, py_ - 8))], 'W')
        FX.embers(front, (24, 50, 168, 140), 10, seed=241, hot_ratio=0.6, sizes=(1, 2))
        return back, front
    if i == 3:
        # IMPACT: floor cracks under each claw, a dust ring, debris, then a white-hot flash ON TOP
        for (px_, py_) in ((lx, ly), (rx, ry)):
            FX.ground_cracks(back, px_, GY - 1, spokes=8, length=54, seed=31 if px_ < 96 else 37,
                             glow=True, squash=0.30)
        FX.dust_ring(back, front, GX, GY - 5, 78, 9, 7.2, seed=4, n=18, lift=0.85)
        for j, (x, y, sz) in enumerate(((20, 124, 2), (172, 122, 2), (44, 112, 1), (148, 110, 1),
                                        (8, 136, 1), (184, 138, 1), (62, 120, 1), (130, 118, 1))):
            _chunk(front, x, y, sz + 1.4, seed=250 + j, ramp='dark', bias=-1, spin=j)
        for (px_, py_) in ((lx, ly), (rx, ry)):
            # the split the claws punch into the floor, then the flash over everything
            _fissure(front, int(px_), GY - 1, 13, 2.6, 3, seed=45 if px_ < 96 else 47, squash=0.45)
            for q in ell(px_, GY - 2, 11.0, 3.4):
                d = math.hypot((q[0] + 0.5 - px_) / 11.0, (q[1] + 0.5 - GY + 2) / 3.4)
                front.put(q[0], q[1], PALC['W' if d < 0.4 else ('L' if d < 0.7 else 'O')])
            for sgn in (-1, 1):
                for j in range(3):
                    y = GY - 4 + j * 3
                    for x in range(int(px_ + sgn * (12 + j * 4)), int(px_ + sgn * (26 + j * 7)), sgn):
                        if 2 <= x < FW - 2:
                            front.put(x, y, PALC['W' if j == 0 else 'L'])
        _streaks(front, [((3, 150), (18, 150)), ((174, 150), (189, 150)),
                         ((5, 156), (15, 156)), ((177, 156), (187, 156))], 'W')
        FX.embers(front, (10, 60, 182, 148), 26, seed=261, hot_ratio=0.65, sizes=(1, 2, 3))
        return back, front
    if i == 4:
        for (px_, py_) in ((lx, ly), (rx, ry)):
            FX.ground_cracks(back, px_, GY - 1, spokes=7, length=46, seed=31 if px_ < 96 else 37,
                             glow=False, squash=0.30)
        FX.dust_ring(back, front, GX, GY - 5, 82, 10, 6.0, seed=9, broken=0.35, n=16, lift=1.2)
        for j, (x, y, sz) in enumerate(((18, 138, 2), (176, 136, 2), (48, 130, 1), (146, 128, 1))):
            _chunk(front, x, y, sz + 1.2, seed=270 + j, ramp='ear', bias=-1, spin=j * 1.3)
        FX.embers(front, (14, 80, 178, 148), 14, seed=271, hot_ratio=0.4, sizes=(1, 2))
        return back, front
    for (px_, py_) in ((lx, ly), (rx, ry)):
        FX.ground_cracks(back, px_, GY - 1, spokes=6, length=40, seed=31 if px_ < 96 else 37,
                         glow=False, squash=0.30)
    for j, (x, r) in enumerate(((26, 4.0), (166, 4.0), (52, 2.6), (140, 2.6))):
        FX.puff(front, x, GY - 2, r, seed=280 + j, kind='dust', holes=0.35)
    FX.embers(front, (24, 60, 168, 144), 8, seed=281, hot_ratio=0.5, sizes=(1, 2))
    return back, front


def dizzy_fx(i, P):
    """(fx_back, fx_front) for bixby_dizzy.png frame i"""
    back, front = _blank(), _blank()
    ox, oy = P['mh']
    dizzy_stars(front, ox, oy + 2 - 12, i)
    FX.stamp(front, FX.SWEAT_BIG, int(ox + 22), int(oy + 6 + [0, 2, 4, 1][i]))
    FX.stamp(front, FX.SWEAT, int(ox - 27), int(oy + 10 + [3, 1, 0, 2][i]), flip=True)
    for j, (x, r) in enumerate(((36, 2.2), (156, 2.2))):
        FX.puff(front, x + [2, 0, -2, 0][i], GY - 1, r, seed=300 + j + i, kind='dust', holes=0.3)
    FX.embers(front, (40, 100, 152, 144), 4, seed=311 + i, hot_ratio=0.2, sizes=(1,))
    return back, front


if __name__ == '__main__':
    import anim_common as AC
    from pngio import write_png, scale
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'prev')
    for name, (w, h, n, fn) in SHEETS.items():
        strip = Canvas(w * n, h)
        for i in range(n):
            strip.blit(fn(i), w * i, 0)
        px = strip.rgba()
        px = [[(p if p[3] else (96, 128, 84, 255)) for p in r] for r in px]
        write_png(os.path.join(OUT, name + '_draft.png'), w * n * 5, h * 5, scale(px, 5))
        print(name, w * n, 'x', h)


