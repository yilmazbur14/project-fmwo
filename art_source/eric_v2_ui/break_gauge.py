"""Eric's Break gauge: a slim brass rail under his health bar, drawn at 3x like the rest of the HUD kit.
It is exactly as tall as the ring's top rope (7 texels = 21 px), so at its slot it replaces a stretch
of rope: rivet plates clamp its ends and brass lips frame the fill, which keeps the fill from reading
as more rope.

  break_gauge_frame     128x7      rivet plates, brass lips, navy channel
  break_gauge_fill      114x3      steel-white -> white -> yellow -> gold, revealed left to right at (7, 2);
                                   the gold band starts at 80%, where the gauge starts to pulse
  break_gauge_pulse     4 x 140x7  overlay from 80% up, looped: rest, warm, hot, warm. Lights the brass only
                                   (the bottom lip warms, the plates flare with sparks on the hot frame),
                                   never the channel. Drawn at (-6, 0), over frame and fill.
  break_gauge_fill_hot  4 x 114x3  the fill while pulsing, frame for frame with the overlay: stress cracks
                                   open in the gold end, and the fill warms to white-hot and back
  break_gauge_shatter   6 x 144x31 played once on a Break, at (-8, -12): flash, split, burst, tumble,
                                   embers. The frame underneath already shows the empty channel.
  break_text            2 x 72x20  "BREAK!" in the MASH!/PARRY! recipe (rest, pop)

PALETTE.  This family has left DB32.  What ships in Assets/UI is no longer what
build() returns: the approved gothic direction restyled the boss health bar and
its daze meter together, and hud_bars/export_gothic.py writes these same shapes
through a colour remap sampled from the direction reference, which is
deliberately not DawnBringer-32.  The frames here are still the brass originals
and are still the shapes of record - the remap keeps every pixel of shape and
every frame boundary - so this file stays as the source of the geometry, and
__main__ no longer asserts a palette the shipped set does not have.
"""
import math
import random
import sys
sys.dont_write_bytecode = True
from ev2_common import *

GW, GH = 128, 7
PLATE_W = 7
FILL_X, FILL_Y, FILL_W, FILL_H = 7, 2, 114, 3

# cross-section between the plates: outline, brass lip, channel (navy, navy, reflected light), lip, outline
RAIL = ['K', 'Y', 'n', 'n', 'I', 'D', 'K']

PLATE = [".KKKKK.",
         "KYYYYSK",
         "KYSWYDK",
         "KYWRpDK",
         "KYYppDK",
         "KSDDDoK",
         ".KKKKK."]


def frame_canvas(pal_over=None):
    P = dict(C)
    if pal_over:
        P.update(pal_over)
    c = Canvas(GW, GH)
    for x in range(PLATE_W, GW - PLATE_W):
        for y, ch in enumerate(RAIL):
            c.p[y][x] = P[ch]
    # the channel's ends, as in qte_meter_frame: an inner shadow on the left, reflected light on the right
    for y in (2, 3):
        c.p[y][PLATE_W] = P['K']
        c.p[y][GW - PLATE_W - 1] = P['I']
    stamp(c, PLATE, 0, 0, P)
    stamp(c, PLATE, GW - PLATE_W, 0, P)
    return c


def fill_canvas(ramps, edges, w=FILL_W, h=FILL_H):
    """(highlight, base, shade) per band; a 2-column checker dither before each edge"""
    c = Canvas(w, h)
    for x in range(w):
        band = sum(1 for e in edges if x >= e)
        nb = band + 1 if (band < len(edges) and x in (edges[band] - 2, edges[band] - 1)) else band
        for y in range(h):
            b = nb if (nb != band and (x + y) % 2 == 0) else band
            hi, base, sh = ramps[b]
            c.p[y][x] = C[hi if y == 0 else (sh if y == h - 1 else base)]
    return c


# steel-white, white, yellow, gold. The gold band starts at 80% of the fill, the share where the gauge
# starts to pulse, so "gold" and "about to break" are the same read.
WHITE_GOLD = [('W', 'P', 's'),
              ('W', 'W', 'S'),
              ('W', 'Y', 'T'),
              ('Y', 'Y', 'O')]
PULSE_FROM = 0.8
WHITE_GOLD_EDGES = [32, 62, int(round(FILL_W * PULSE_FROM))]


def gauge_fill():
    return fill_canvas(WHITE_GOLD, WHITE_GOLD_EDGES)


# ------------------------------------------------------------------ near full
# A four-step throb (rest, warm, hot, warm) rather than a two-frame strobe: the gauge can sit above 80%
# for several seconds, and a hard blink that long gets tuned out. The overlay lights only the brass,
# never the channel, so the fill level always shows through; the fill itself is swapped for the
# matching fill_hot frame. Stress cracks open in the gold end, the gauge's shatter foreshadowed.
LIT = {'Y': C['W'], 'S': C['W'], 'T': C['Y'], 'D': C['T'], 'o': C['D'], 'R': C['T'], 'p': C['D']}
# (x, column offset per row) zigzags across the fill's three rows
CRACKS = [(93, [1, 0, 1]), (99, [0, 1, 0]), (105, [1, 1, 0]), (110, [0, 1, 1])]
PULSE_PAD = 6
PULSE_MS = [100, 90, 110, 90]


def pulse_frames():
    """The top lip stays gold on every frame: lit white, the whole gauge would melt into the white
    stripe of the rope it sits on. The bottom lip warms, and the plates flare on the hot frame."""
    out = []
    for f in range(4):
        c = Canvas(GW + 2 * PULSE_PAD, GH)
        if f in (1, 2, 3):
            for x in range(PLATE_W, GW - PLATE_W):
                c.p[5][x + PULSE_PAD] = C['T']
        if f == 2:
            lit = frame_canvas(LIT)
            for side in (0, GW - PLATE_W):
                for y in range(GH):
                    for x in range(side, side + PLATE_W):
                        if lit.p[y][x] is not None:
                            c.p[y][x + PULSE_PAD] = lit.p[y][x]
            for (x, y, s) in [(2, 1, 1), (3, 5, 0), (c.w - 3, 1, 1), (c.w - 4, 5, 0)]:
                sparkle(c, x, y, s, 'W', 'Y')
        elif f in (1, 3):
            for (x, y) in ([(3, 2), (c.w - 4, 4)] if f == 1 else [(2, 4), (c.w - 3, 2)]):
                put(c, x, y, 'Y')
        out.append(c)
    return out


def _cracked(fill, col):
    for (x, rows) in CRACKS:
        for y, dx in enumerate(rows):
            put(fill, x + dx, y, col)
    return fill


def fill_hot_frames():
    rest = _cracked(gauge_fill(), 'D')
    warm = _cracked(fill_canvas([('W', 'W', 'P'), ('W', 'W', 'S'), ('W', 'Y', 'Y'), ('W', 'Y', 'O')],
                                WHITE_GOLD_EDGES), 'O')
    hot = _cracked(fill_canvas([('W', 'W', 'Y')], []), 'O')
    return [rest, warm, hot, warm.copy()]


# ------------------------------------------------------------------ shatter
SH_PAD_X, SH_PAD_Y = 8, 12
SW_, SH_ = GW + 2 * SH_PAD_X, GH + 2 * SH_PAD_Y
SHATTER_MS = [50, 50, 60, 60, 70, 70]
# where the fill splits, in fill texels: 13 shards of uneven width
SPLITS = [0, 7, 17, 25, 34, 43, 52, 60, 70, 79, 88, 97, 106, 114]


def _shard_colour(x):
    band = sum(1 for e in WHITE_GOLD_EDGES if x >= e)
    return WHITE_GOLD[band]


def _poly_cells(pts):
    """cells whose centres fall inside a small polygon"""
    ys = [p[1] for p in pts]
    cells = set()
    for y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 1):
        yc = y + 0.5
        xs = []
        n = len(pts)
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(int(math.floor(a + 0.5)), int(math.floor(b + 0.5))):
                cells.add((x, y))
    return cells


def _shards():
    rnd = random.Random(7)
    shards = []
    for i in range(len(SPLITS) - 1):
        a, b = SPLITS[i], SPLITS[i + 1]
        mid = (a + b) / 2.0
        up = -1 if i % 2 == 0 else 1
        # outward from the bar's middle a little, mostly straight up or down
        vx = (mid - FILL_W / 2.0) / (FILL_W / 2.0) * rnd.uniform(1.6, 2.6)
        vy = up * rnd.uniform(4.8, 6.0)
        spin = rnd.uniform(0.25, 0.5) * (1 if rnd.random() < 0.5 else -1)
        # a slanted top edge so the pieces read as broken, not cut
        jag = rnd.choice([-0.6, 0.0, 0.6])
        shards.append({'a': a, 'b': b, 'vx': vx, 'vy': vy, 'spin': spin, 'jag': jag, 'mid': mid})
    return shards


DRAG = 1.8      # steps: the pieces burst out fast and slow down, instead of sailing off the canvas
FALL = 0.15     # texels per step squared


def _travel(v, t):
    return v * DRAG * (1.0 - math.exp(-t / DRAG))


def _shard_poly(s, t, shrink):
    """the shard's quad after t steps, in shatter-canvas texels"""
    a, b = s['a'] + shrink, s['b'] - shrink
    if b - a < 1.0:
        a, b = s['mid'] - 0.5, s['mid'] + 0.5
    cx = SH_PAD_X + FILL_X + (a + b) / 2.0 + _travel(s['vx'], t)
    cy = SH_PAD_Y + FILL_Y + 1.5 + _travel(s['vy'], t) + FALL * t * t
    hw, hh = (b - a) / 2.0, 1.5
    ang = s['spin'] * t
    ca, sa = math.cos(ang), math.sin(ang)
    corners = [(-hw, -hh + s['jag']), (hw, -hh - s['jag']), (hw, hh), (-hw, hh)]
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for (x, y) in corners]


def _paint_shard(c, cells, hi, base, sh):
    outline(c, cells, K, diag=False)
    ys = sorted({y for _, y in cells})
    for (x, y) in cells:
        c.set(x, y, C[hi] if y == ys[0] else (C[sh] if y == ys[-1] else C[base]))


def shatter_frames():
    frames = []
    shards = _shards()
    ox, oy = SH_PAD_X, SH_PAD_Y
    lit = frame_canvas(LIT)
    # 0: flash. The whole rail white-hot with the split lines already in it, a glow round it.
    c = Canvas(SW_, SH_)
    c.blit(lit, ox, oy)
    for y in range(FILL_Y, FILL_Y + FILL_H):
        for x in range(FILL_X, FILL_X + FILL_W):
            put(c, ox + x, oy + y, 'W')
    for sx in SPLITS[1:-1]:
        for j, dy in enumerate((0, 1, 0)):
            put(c, ox + FILL_X + sx + dy, oy + FILL_Y + j, 'Y')
    halo(c, C['Y'])
    halo(c, C['O'])
    frames.append(c)
    # 1: split. The pieces lift apart, white-hot sparks at the breaks.
    c = Canvas(SW_, SH_)
    for s in shards:
        _paint_shard(c, _poly_cells(_shard_poly(s, 0.35, 0.5)), *_shard_colour(s['mid']))
    for sx in SPLITS[1:-1]:
        x = ox + FILL_X + sx
        for (dx, dy, col) in [(0, -2, 'W'), (0, 6, 'W'), (-1, -3, 'Y'), (1, 7, 'Y')]:
            if c.get(x + dx, oy + FILL_Y + dy) is None:
                put(c, x + dx, oy + FILL_Y + dy, col)
    frames.append(c)
    # 2-5: the pieces fly, turn and shrink, cooling from their own colours to embers
    for f, (t, shrink, cool) in enumerate([(1.0, 0.8, 0), (1.9, 1.6, 1), (2.9, 2.6, 2), (4.0, 3.6, 3)]):
        c = Canvas(SW_, SH_)
        rnd = random.Random(20 + f)
        for i, s in enumerate(shards):
            if cool == 3 and i % 2:
                continue
            hi, base, sh = _shard_colour(s['mid'])
            if cool == 1:
                base, sh = ('Y' if base in 'WPY' else base), 'T'
            elif cool == 2:
                hi, base, sh = 'Y', 'T', 'D'
            elif cool == 3:
                hi, base, sh = 'T', 'O', 'D'
            cells = _poly_cells(_shard_poly(s, t, shrink))
            if len(cells) >= 6:
                _paint_shard(c, cells, hi, base, sh)
            else:
                for (x, y) in cells:
                    c.set(x, y, C[base])
        n = [18, 14, 9, 5][f]
        for k in range(n):
            x = rnd.randint(ox + 2, ox + GW - 3)
            spread = [4, 7, 9, 11][f]
            y = oy + 3 + rnd.choice([-1, 1]) * rnd.randint(2, spread)
            if c.get(x, y) is None:
                put(c, x, y, ['W', 'Y', 'Y', 'O'][f] if k % 3 else ['Y', 'T', 'O', 'D'][f])
        frames.append(c)
    return frames


# ------------------------------------------------------------------ BREAK!
TW, TH = 72, 20
# The gauge's own colours, steel-white into a gold underside, over a deep indigo extrusion: it reads
# as steel giving way, and it stays clear of every other word. GUARD BREAK! is red (the player's bad
# news), PARRY! white-gold on brown, PERFECT! cyan, KNIGHT BREAKER! hot gold on crimson.
BREAK_SCHEME = (LT._s("WWWW.PPP.YY", {4: 'WP', 8: 'PY'}, 'Ipn', 'W', 'W'),
                LT._s("WWWWWW.PP.Y", {6: 'WP', 9: 'PY'}, 'BIpn', 'W', 'W'))
TEXT_MS = [80, 80]


def break_text_frames():
    out = []
    for bright in (False, True):
        c = LT.word_canvas('BREAK!', BREAK_SCHEME[1 if bright else 0], bright, TW, TH)
        if bright:
            for (x, y, s) in [(2, 3, 1), (69, 2, 1), (5, 16, 0), (66, 17, 0)]:
                if c.get(x, y) is None:
                    sparkle(c, x, y, s, 'W', 'Y')
        out.append(c)
    return out


def build():
    return {
        'break_gauge_frame': [frame_canvas()],
        'break_gauge_fill': [gauge_fill()],
        'break_gauge_pulse': pulse_frames(),
        'break_gauge_fill_hot': fill_hot_frames(),
        'break_gauge_shatter': shatter_frames(),
        'break_text': break_text_frames(),
    }


def composite(frac, frame=None, fill=None):
    c = (frame or frame_canvas()).copy()
    f = fill or gauge_fill()
    n = int(round(FILL_W * frac))
    if n:
        c.blit(crop(f, 0, 0, n, FILL_H), FILL_X, FILL_Y)
    return c


if __name__ == '__main__':
    A = build()
    for name, frames in A.items():
        s = strip(frames)
        bad = s.colours() - DB32
        zoom(s, name + '_8x.png', 8, grid_wh=(frames[0].w, frames[0].h))
        print(name, len(frames), frames[0].w, frames[0].h,
              '' if not bad else 'off-DB32: %s' % sorted(bad))
