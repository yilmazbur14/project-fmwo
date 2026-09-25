"""Greyson's delayed eruption (the barbell slam's pay-off, in the manner of Bixby's quake crack and burst), and
the barbell's own impact at his end. Three sheets:
  greyson_erupt_mark   8 frames of 336x260, the pending area on the floor, aimed at the player:
                         f0-1  PLANTED: the ring snaps in with a flash, the first cracks split from the middle
                         f2-3  STAGE 1, throbbing at 0.3 s: a dim dashed violet ring, short cracks faintly lit
                         f4-5  STAGE 2, at 0.22 s: the ring solid, cracks across most of the area, glowing, embers
                         f6-7  STAGE 3, at 0.17 s (the rush; every throb stays at or under 3 a second for
                               photosensitivity): the ring doubled and pulsing, the cracks white-hot
                               across the whole area, a violet glow filling it, sparks leaping
                       Three pending at once read at a glance: dim-and-short, lit-and-long, white-and-flashing.
                       PIVOT: the area's centre on the floor (168, 134). The area is an ellipse rx 160, ry 116.67
                       texels: rx 480, ry 350 px at scale 3 (the user's call after playtesting the plan's 380 x 280);
                       that is the hurt area. The arena's mat
                       is drawn top-down (its centre circle and corner arcs are true circles), so the oval sits on
                       it as drawn: no perspective correction is needed.
  greyson_erupt_burst  7 frames of 360x304 at 0.05 s, once: the area flashes, then the whole of it erupts:
                       flame-shaped pillars of violet energy all over it (white-hot cores, their tops thinning in
                       stepped alpha) over a pool of violet light, chunks of mat thrown up; it peaks, breaks into
                       flares and a rolling band of chalk dust, and leaves the cracks scorched. It hurts on f1-f3. PIVOT: the area's centre on
                       the floor (180, 174).
  greyson_slam         6 frames of 112x60 at 0.05 s, once: the barbell's plate hitting the floor at Greyson's end:
                       a white flash, a violet shock ring along the floor, chalk dust, the canvas split under it.
                       PIVOT: the point the plate hits (56, 40).
The cannon's violets (V v U u X) with white-hot hearts (W w) for his power, the mat's greens (n m q Q) for the
canvas it splits, chalk white (W w E e f) for the dust. No keyline.
"""
import math
import random

import gfx_pal as pal
import gfx_floor as fl

ZONE_PX = (480, 350)          # the hurt oval on screen, rx x ry, at scale 3
RX, RY = ZONE_PX[0] / 3.0, ZONE_PX[1] / 3.0
MW, MH = 336, 260
MCX, MCY = 168.0, 134.0
BW, BH = 360, 304
BCX, BCY = 180.0, 174.0
# counts were tuned at 380 x 280 px; they grow with the area (K_AREA) or the rim (K_RIM) to keep that density
K_AREA = (ZONE_PX[0] * ZONE_PX[1]) / (380.0 * 280.0)
K_RIM = (ZONE_PX[0] + ZONE_PX[1]) / (380.0 + 280.0)


def scaled(n, factor):
    return int(round(n * factor))
SW, SH = 112, 60
SCX, SCY = 56.0, 40.0

# the cracks from the area's middle: (angle, share of the radius it reaches), the order they appear in
CRACKS = [(12, 0.95), (200, 0.9), (95, 0.85), (300, 0.92), (150, 0.8), (40, 0.75), (250, 0.85), (340, 0.7),
          (120, 0.65), (220, 0.7), (70, 0.6), (180, 0.95), (272, 0.8), (28, 0.55), (162, 0.6), (322, 0.75)]


def ring(g, cx, cy, rx, ry, keys, dash=None, width=1.0, only=None, yk=None):
    """An ellipse ring on the floor, `width` texels thick (`yk` of that vertically; the oval's own ry/rx by default),
    dashed (period, duty) along its angle if asked."""
    n = int(2 * math.pi * max(rx, ry) * 2.2)
    for i in range(n):
        a = 2 * math.pi * i / n
        if dash and ((a / (2 * math.pi) * dash[0]) % 1.0) > dash[1]:
            continue
        for w in [j * 0.5 for j in range(int(width * 2) + 1)]:
            x = int(cx + (rx + w) * math.cos(a))
            y = int(cy + (ry + w * (ry / rx if yk is None else yk)) * math.sin(a))
            if 0 <= x < len(g[0]) and 0 <= y < len(g):
                if only is None or g[y][x] in only:
                    g[y][x] = keys[0] if math.sin(a) < 0.15 else keys[1]


def mark_cracks(g, cx, cy, reach, glow, seed_off=0):
    """The area's cracks, each reaching `reach` of its length; glow 0 dark, 1 violet, 2 white-hot."""
    core = ['X', 'U', 'W'][glow]
    lip = [None, ('v', 'u'), ('V', 'v')][glow]
    count = [7, 12, 16][glow]
    for n, (ang, share) in enumerate(CRACKS[:count]):
        a = math.radians(ang)
        ln = share * reach
        x1, y1 = cx + math.cos(a) * RX * ln, cy + math.sin(a) * RY * ln
        pts = fl.zigzag(cx + math.cos(a) * 2, cy + math.sin(a) * 1.5, x1, y1, seed=n + seed_off, jag=1.6, step=3.2)
        fl.crack(g, pts, core=core, lip=lip, wide=(glow == 2 and n < 6), only_empty_lip=False)
        if glow >= 1 and n % 2 == 0 and ln > 0.4:
            for j, (share_at, turn) in enumerate(((0.45, 0.55), (0.75, -0.5))):
                m = pts[int(len(pts) * share_at)]
                b = a + (turn if n % 4 else -turn)
                fl.crack(g, fl.zigzag(m[0], m[1], m[0] + math.cos(b) * RX * ln * 0.28, m[1] + math.sin(b) * RY * ln * 0.28,
                                      seed=n * 3 + j + 50, jag=1.0), core=core, lip=None)


def mark_frame(f):
    g = pal.blank(MW, MH)
    local = {}
    stage = [0, 0, 1, 1, 2, 2, 3, 3][f]
    beat = f % 2
    if stage == 3:
        # a violet glow filling the area, in stepped alpha, brighter on the beat
        a_in, a_mid, a_out = (112, 88, 64) if beat == 0 else (80, 62, 44)
        local = {'1': pal.hx('A063DC', a_in), '2': pal.hx('7C3BB4', a_mid), '3': pal.hx('7C3BB4', a_out)}
        for y in range(MH):
            for x in range(MW):
                d = math.hypot((x + 0.5 - MCX) / RX, (y + 0.5 - MCY) / RY)
                if d <= 1.0:
                    g[y][x] = '1' if d < 0.45 else ('2' if d < 0.78 else '3')
    if stage == 0:
        if f == 0:
            ring(g, MCX, MCY, RX, RY, 'WV', width=2.0)
            ring(g, MCX, MCY, RX - 4, RY - 4 * RY / RX, 'VU')
        else:
            ring(g, MCX, MCY, RX, RY, 'uX', dash=(scaled(44, K_RIM), 0.6))
        mark_cracks(g, MCX, MCY, 0.25 if f == 0 else 0.35, 0)
    elif stage == 1:
        ring(g, MCX, MCY, RX, RY, ('U' if beat == 0 else 'u') + 'X', dash=(scaled(44, K_RIM), 0.6), width=1.0)
        mark_cracks(g, MCX, MCY, 0.42, 1 if beat == 0 else 0)
    elif stage == 2:
        ring(g, MCX, MCY, RX, RY, ('V' if beat == 0 else 'v') + 'U', width=1.5)
        mark_cracks(g, MCX, MCY, 0.78, 1)
        rnd = random.Random(9 + beat)
        for i in range(scaled(20, K_AREA)):
            a = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(0.2, 0.85)
            x, y = MCX + math.cos(a) * RX * r, MCY + math.sin(a) * RY * r - rnd.uniform(3, 12) - beat * 2
            pal.put(g, int(x), int(y), 'V' if i % 2 else 'v')
            pal.put(g, int(x), int(y) + 1, 'U')
    else:
        ring(g, MCX, MCY, RX, RY, ('W' if beat == 0 else 'V') + 'v', width=2.0)
        ring(g, MCX, MCY, RX + 5, RY + 5 * RY / RX, 'Vv' if beat == 0 else 'vU', dash=(scaled(64, K_RIM), 0.5), width=1.0)
        mark_cracks(g, MCX, MCY, 1.0, 2)
        rnd = random.Random(19 + beat)
        for i in range(scaled(40, K_AREA)):
            a = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(0.1, 0.9)
            x, y = MCX + math.cos(a) * RX * r, MCY + math.sin(a) * RY * r - rnd.uniform(4, 22) - beat * 3
            for dy in range(2 if i % 3 else 3):
                pal.put(g, int(x), int(y) + dy, 'W' if dy == 0 else 'V')
    return pal.Frame(pal.rows(g), local)


PILLARS = None


def pillars():
    """The energy pillars the eruption is made of: (base x, base y on the area's floor, half-width, height share,
    wobble phase), spread over the whole area, the middle ones the tallest."""
    global PILLARS
    if PILLARS is None:
        rnd = random.Random(11)
        out = []
        for i in range(scaled(64, K_AREA)):
            a = rnd.uniform(0, 2 * math.pi)
            r = math.sqrt(rnd.uniform(0.0, 1.0)) * 0.92
            x = BCX + math.cos(a) * RX * r
            y = BCY + math.sin(a) * RY * r
            out.append((x, y, rnd.uniform(5.0, 10.0), (1.0 - 0.55 * r) * rnd.uniform(0.7, 1.0), rnd.uniform(0, 6.28)))
        PILLARS = sorted(out, key=lambda p: p[1])          # back to front
    return PILLARS


def eruption(g, height, heat, broken=0.0):
    """The whole area erupting: flame-shaped pillars of violet energy standing all over it, overlapping back to
    front, each white-hot down its middle and violet to its flanks, tapering to a ragged point; their tops thin
    out in stepped alpha. `broken` (0..1) shortens a growing share of them as it breaks up. Returns the frame's
    local stepped-alpha keys."""
    H, W = len(g), len(g[0])
    local = {'5': pal.hx('C892F2', 176), '6': pal.hx('A063DC', 176), '7': pal.hx('C892F2', 112),
             '8': pal.hx('A063DC', 112)}
    for n, (bx, by, hw, share, ph) in enumerate(pillars()):
        h = height * share
        if broken and ((n * 7) % 10) / 10.0 < broken:
            h *= 0.3
        if h < 2:
            continue
        for y in range(max(0, int(by - h)), min(H, int(by) + 1)):
            t = (by - y) / h                                 # 0 at the foot .. 1 at the tip
            half = hw * (1.0 - t ** 1.6) * (0.85 + 0.15 * math.sin(ph + y * 0.45))
            cx = bx + 1.2 * math.sin(ph + y * 0.21)
            for x in range(int(cx - half) - 1, int(cx + half) + 2):
                if not (0 <= x < W):
                    continue
                d = abs(x + 0.5 - cx) / max(0.6, half)
                if d > 1.0:
                    continue
                if d < 0.4 * heat and t < 0.8:
                    k = 'W'
                elif d < 0.72:
                    k = 'V'
                else:
                    k = 'v'
                if t > 0.82:
                    k = '7' if k in 'WV' else '8'
                elif t > 0.62:
                    k = '5' if k in 'WV' else '6'
                g[y][x] = k
    return local


def burst_frame(f):
    g = pal.blank(BW, BH)
    local = {}
    rnd = random.Random(3)
    if f == 0:
        # the whole area flashes, a low dome of white rising off it
        for y in range(BH):
            for x in range(BW):
                d = math.hypot((x + 0.5 - BCX) / RX, (y + 0.5 - BCY) / RY)
                dome = math.hypot((x + 0.5 - BCX) / (RX * 0.8), (y + 0.5 - (BCY - 10)) / 30)
                if d <= 1.0 or dome <= 1.0:
                    g[y][x] = 'W' if (d < 0.55 or dome < 0.7) else ('V' if d < 0.85 or dome < 0.9 else 'v')
        return pal.rows(g)
    # scorch under everything from f1: the cracks burnt dark violet
    mark_cracks(g, BCX, BCY, 1.0, 0)
    spec = {1: (66, 1.0, 0.0), 2: (124, 1.0, 0.0), 3: (110, 0.8, 0.45), 4: (66, 0.5, 0.75), 5: (28, 0.3, 0.9)}
    if f in spec:
        h, heat, broken = spec[f]
        if f <= 3:
            # a pool of violet light on the floor under the pillars
            for y in range(BH):
                for x in range(BW):
                    d = math.hypot((x + 0.5 - BCX) / RX, (y + 0.5 - BCY) / RY)
                    if d <= 1.0:
                        g[y][x] = 'V' if d < 0.5 else ('v' if d < 0.85 else 'U')
        local = eruption(g, h, heat, broken)
    # chunks of mat thrown up and falling
    t = f * 0.05
    for i in range(scaled(28, K_AREA)):
        a = math.radians(rnd.uniform(-160, -20))
        v = rnd.uniform(170, 320)
        x = BCX + rnd.uniform(-RX * 0.7, RX * 0.7) + math.cos(a) * v * t * 0.8
        y = min(BCY + 6, BCY - 10 + math.sin(a) * v * t + 0.5 * 900 * t * t)
        if 1 <= f <= 5 and 2 <= x < BW - 3 and 1 <= y < BH - 2:
            fl.chip(g, x, y, big=(i % 2 == 0))
    # sparks flung off the flares
    if 2 <= f <= 5:
        for i in range(scaled(40, K_AREA)):
            x = BCX + rnd.uniform(-RX, RX)
            y = BCY - rnd.uniform(10, 40 + 10 * f)
            if 0 <= int(x) < BW and 0 <= int(y) < BH and g[int(y)][int(x)] == '.':
                pal.put(g, int(x), int(y), 'W' if i % 2 else 'V')
    if f >= 3:
        # chalk dust rolling out along the area's rim as one cloud band, thinning in stepped alpha
        dust = pal.blank(BW, BH)
        grow = f - 3
        pts = []
        n_puffs = scaled(44, K_RIM)
        for i in range(n_puffs):
            a = 2 * math.pi * i / n_puffs + 0.05 * math.sin(i * 1.7)
            x = BCX + math.cos(a) * RX * (0.86 + 0.05 * grow)
            y = BCY + math.sin(a) * RY * (0.86 + 0.05 * grow) - 3 - grow
            r = (7.5 + 1.5 * grow) * (0.8 + 0.4 * ((i * 7) % 5) / 4.0)
            pts.append((y, x, r))
        for (y, x, r) in sorted(pts):
            x = max(r + 1, min(BW - r - 2, x))
            fl.puff(dust, x, y, r, shade=min(2, grow), squash=0.72)
        if f >= 5:
            m, dl = pal.alpha_keys('WwEef', 168 if f == 5 else 96, 'ghjlp')
            local = dict(local, **dl)
            for row in dust:
                for x, k in enumerate(row):
                    if k in m:
                        row[x] = m[k]
        for y in range(BH):
            for x in range(BW):
                if dust[y][x] != '.' and (g[y][x] == '.' or g[y][x] in 'Qqnm' or y > BCY):
                    g[y][x] = dust[y][x]
    return pal.Frame(pal.rows(g), local)


def slam_frame(f):
    g = pal.blank(SW, SH)
    local = {}
    grow = [0.45, 0.8, 1.0, 1.0, 1.0, 1.0][f]
    for n, ang in enumerate((10, 60, 110, 165, 200, 250, 300, 345)):
        a = math.radians(ang)
        ln = 20 * grow * (0.7 + 0.3 * (n % 3) / 2)
        pts = fl.zigzag(SCX + math.cos(a) * 2, SCY + math.sin(a), SCX + math.cos(a) * ln, SCY + math.sin(a) * ln * 0.36,
                        seed=n + 70, jag=0.9)
        fl.crack(g, pts, core='Q' if f > 1 else 'U', lip=('n', 'm'))
    if f <= 3:
        # a violet shock ring racing out along the floor
        rr = [8, 20, 32, 42][f]
        ring(g, SCX, SCY, rr, rr * 0.36, 'Vv' if f < 2 else 'vU', width=1.0, yk=0.4)
    if f == 0:
        for y in range(SH):
            for x in range(SW):
                d = math.hypot((x + 0.5 - SCX) / 12, (y + 0.5 - SCY) / 5)
                if d <= 1.0:
                    g[y][x] = 'W' if d < 0.6 else 'V'
    if 1 <= f <= 5:
        dust = pal.blank(SW, SH)
        rnd = random.Random(5)
        for i in range(8):
            a = math.pi + math.pi * i / 7 + rnd.uniform(-0.2, 0.2)
            spread = [0, 10, 18, 24, 28, 30][f]
            x = SCX + math.cos(a) * spread
            y = SCY + math.sin(a) * spread * 0.35 - 3 - (f - 1)
            fl.puff(dust, x, y, [0, 5, 6.5, 7, 7, 6.5][f] * rnd.uniform(0.85, 1.1), shade=min(2, max(0, f - 2)), squash=0.75)
        if f >= 4:
            m, local = pal.alpha_keys('WwEef', 168 if f == 4 else 96, 'ghjlp')
            for row in dust:
                for x, k in enumerate(row):
                    if k in m:
                        row[x] = m[k]
        for y in range(SH):
            for x in range(SW):
                if dust[y][x] != '.':
                    g[y][x] = dust[y][x]
    return pal.Frame(pal.rows(g), local)


def mark_frames():
    return [mark_frame(f) for f in range(8)]


def burst_frames():
    return [burst_frame(f) for f in range(7)]


def slam_frames():
    return [slam_frame(f) for f in range(6)]


SHEETS = {'greyson_erupt_mark': (mark_frames, (MW, MH)), 'greyson_erupt_burst': (burst_frames, (BW, BH)),
          'greyson_slam': (slam_frames, (SW, SH))}
