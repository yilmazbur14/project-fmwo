"""Full-screen celebration overlays in the arena's 640x360 texel space (drawn at 3x, from the
screen origin, like Ringside / RingsideCrowd). Effects carry no keyline.

  confetti_burst.png   one-shot, 28 frames: the trophy pops a confetti burst and the four ring
                       corners fire cannons with streamers; everything slows, flutters and falls.
  confetti_rain.png    4-frame loop for the hold (0.12 s a frame, the victory screen's rhythm),
                       the same two-tone 3x2 flutter pieces as victory_confetti.png, denser + gold.
  spot_sweep.png       10 frames: two warm spotlights sweep in from the top corners and lock on
                       Burak (frames 0-7 one-shot), then a 2-frame shimmer loop (8-9).
  lift_flash.png       3 frames: the anime impact flash on the drop - light rays out of the cup.
"""
import math
import random
from PIL import Image, ImageDraw

W, H = 640, 360

# the victory screen's confetti pairs (light, dark) + the trophy's gold
PAIRS = [
    ((99, 155, 255), (91, 110, 225)),     # sky / blurple
    ((153, 229, 80), (106, 190, 48)),     # lime / green
    ((251, 242, 54), (217, 160, 102)),    # yellow / tan
    ((215, 123, 186), (118, 66, 138)),    # mauve / purple
    ((217, 87, 99), (172, 50, 50)),       # pink / red
    ((95, 205, 228), (48, 96, 130)),      # cyan / steel
    ((255, 255, 255), (155, 173, 183)),   # white / grey
    ((251, 210, 60), (184, 104, 27)),     # gold / gold shade  (x3 weight: it's the champion's)
    ((251, 210, 60), (184, 104, 27)),
    ((251, 210, 60), (184, 104, 27)),
]
# the flutter: flat, S, edge-on, reverse S (victory_confetti.png's four piece shapes)
SHAPES = [
    [(0, 0, 'L'), (1, 0, 'L'), (2, 0, 'L'), (0, 1, 'D'), (1, 1, 'D'), (2, 1, 'D')],
    [(1, 0, 'L'), (2, 0, 'L'), (0, 1, 'D'), (1, 1, 'D')],
    [(0, 0, 'L'), (0, 1, 'D'), (0, 2, 'D')],
    [(0, 0, 'L'), (1, 0, 'L'), (1, 1, 'D'), (2, 1, 'D')],
]

TROPHY_POP = (319, 140)      # texel point the burst leaves from: the cup overhead
CORNERS = [(38, 40, 1, 1), (601, 40, -1, 1), (38, 318, 1, -1), (601, 318, -1, -1)]


def put_piece(px, x, y, pair, phase):
    for dx, dy, t in SHAPES[phase % 4]:
        X, Y = int(round(x)) + dx, int(round(y)) + dy
        if 0 <= X < W and 0 <= Y < H:
            px[X, Y] = (pair[0] if t == 'L' else pair[1]) + (255,)


class Piece:
    def __init__(self, x, y, vx, vy, pair, phase, flutter):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.pair, self.phase, self.flutter = pair, phase, flutter
        self.t = 0
        self.sway = random.random() * 6.28
        self.drag = random.uniform(0.86, 0.91)

    def step(self):
        self.t += 1
        self.vx *= self.drag
        self.vy = self.vy * self.drag + 0.26
        if self.vy > 1.7:
            self.vy = 1.7
        drift = math.sin(self.t * 0.45 + self.sway) * 0.6 if abs(self.vx) < 1 else 0
        self.x += self.vx + drift
        self.y += self.vy
        if self.t % self.flutter == 0:
            self.phase += 1


class Streamer:
    """A serpentine paper streamer: its head flies a ballistic arc, the tail follows its path
    with a wiggle; drawn as a 1-px two-tone ribbon."""
    def __init__(self, x, y, vx, vy, pair, length):
        self.pts = [(x, y)]
        self.vx, self.vy, self.pair, self.length = vx, vy, pair, length
        self.t = 0

    def step(self):
        self.t += 1
        x, y = self.pts[-1]
        self.vx *= 0.92
        self.vy = self.vy * 0.92 + 0.30
        self.vy = min(self.vy, 1.4)
        for s in range(3):                              # sub-steps keep the ribbon unbroken
            x += self.vx / 3
            y += self.vy / 3
            self.pts.append((x, y))
        self.pts = self.pts[-self.length:]

    def draw(self, px):
        n = len(self.pts)
        for i, (x, y) in enumerate(self.pts):
            w = math.sin(i * 0.55 + self.t * 0.5) * 2.2
            # wiggle perpendicular-ish: horizontal while falling, vertical while flying
            X, Y = int(round(x + w)), int(round(y))
            c = (self.pair[0] if (i // 3) % 2 == 0 else self.pair[1]) + (255,)
            for dx in (0, 1):                           # 2 px wide: reads at 3x
                if 0 <= X + dx < W and 0 <= Y < H:
                    px[X + dx, Y] = c


def confetti_burst(n_frames=28, seed=9):
    random.seed(seed)
    pieces, streamers = [], []
    for _ in range(230):                                # the cup's own pop
        a = random.uniform(-math.pi * 0.98, -math.pi * 0.02)
        sp = random.uniform(6.0, 21.0)
        r0 = random.uniform(11, 17)                     # leaves from a ring round the cup, so
        pieces.append(Piece(TROPHY_POP[0] + r0 * math.cos(a),   # the cup itself stays clear
                            TROPHY_POP[1] + r0 * math.sin(a) * 0.8,
                            sp * math.cos(a), sp * math.sin(a) * 0.85, random.choice(PAIRS),
                            random.randrange(4), random.choice((1, 2, 2, 3))))
    for cx, cy, sx, sy in CORNERS:                      # four corner cannons, aimed up and in
        for _ in range(55):
            a = math.atan2(-1.0 if sy < 0 else 0.25, sx) + random.uniform(-0.35, 0.35)
            sp = random.uniform(10.0, 26.0)
            pieces.append(Piece(cx, cy, sp * math.cos(a), sp * math.sin(a), random.choice(PAIRS),
                                random.randrange(4), random.choice((1, 2, 3))))
        for k in range(2):
            a = math.atan2(-1.0 if sy < 0 else 0.05, sx) + (k - 0.5) * 0.5
            sp = random.uniform(22, 28)
            streamers.append(Streamer(cx, cy, sp * math.cos(a), sp * math.sin(a),
                                      random.choice(PAIRS[:8]), 60))
    frames = []
    for f in range(n_frames):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        px = im.load()
        for s in streamers:
            s.step()
            s.draw(px)
        for p in pieces:
            p.step()
            put_piece(px, p.x, p.y, p.pair, p.phase)
        frames.append(im)
    return frames


def confetti_rain(n=240, seed=21):
    """4-frame loop: each piece sinks 2 px a frame and turns through its flutter, and returns to
    its start on the wrap - the victory screen's approved flicker-fall."""
    rng = random.Random(seed)
    pieces = [(rng.uniform(0, W), rng.uniform(0, H), rng.choice(PAIRS), rng.randrange(4),
               rng.choice((-1, 0, 1))) for _ in range(n)]
    frames = []
    for f in range(4):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        px = im.load()
        for x, y, pair, ph, sway in pieces:
            put_piece(px, x + sway * (f % 2), y + 2 * f, pair, ph + f)
        frames.append(im)
    return frames


SPOT = (255, 240, 196)


def _beam_poly(origin, aim, half_w):
    ox, oy = origin
    ax, ay = aim
    dx, dy = ax - ox, ay - oy
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    return [(ox + nx * 3, oy + ny * 3), (ox - nx * 3, oy - ny * 3),
            (ax - nx * half_w, ay - ny * half_w), (ax + nx * half_w, ay + ny * half_w)]


SPOT_ALPHA = [0, 30, 56, 80, 100]     # light stacks in a few fixed steps: crisp, no gradients


def spot_frame(aims, pool=None, shimmer=0):
    """Two beams from above the corner stands to their aim points; a light pool on the mat.
    Overlaps add up a step each (beam edge, beam core, pool, pool core)."""
    acc = Image.new('L', (W, H), 0)
    shapes = []
    for origin, aim in zip(((-30, -50), (670, -50)), aims):
        shapes.append(('poly', _beam_poly(origin, aim, 30 + shimmer)))
        shapes.append(('poly', _beam_poly(origin, aim, 17 + shimmer)))
    if pool:
        cx, cy = pool
        shapes.append(('ell', (cx - 46, cy - 15, cx + 46, cy + 15)))
        shapes.append(('ell', (cx - 30, cy - 10, cx + 30, cy + 10)))
    for kind, geo in shapes:
        m = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(m)
        (d.polygon if kind == 'poly' else d.ellipse)(geo, fill=1)
        acc = Image.eval(Image.merge('L', [acc]), lambda v: v)  # keep as L
        acc = Image.fromarray(__import__('numpy').minimum(
            __import__('numpy').asarray(acc, dtype='uint8') + __import__('numpy').asarray(m, dtype='uint8'), 4))
    import numpy as np
    a = np.asarray(acc)
    lut = np.array(SPOT_ALPHA + [SPOT_ALPHA[-1]] * 251, dtype='uint8')
    alpha = lut[a]
    rgba = np.zeros((H, W, 4), dtype='uint8')
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = SPOT
    rgba[..., 3] = alpha
    return Image.fromarray(rgba, 'RGBA')


def spot_sweep(target=(320, 165)):
    tx, ty = target
    starts = ((120, 300), (520, 300))
    frames = []
    for f in range(8):
        t = 1 - (1 - f / 7) ** 2.2                       # ease out: fast sweep, soft landing
        aims = [(sx + (tx - sx) * t, sy + (ty + 15 - sy) * t) for sx, sy in starts]
        frames.append(spot_frame(aims, pool=(tx, ty + 15) if f >= 6 else None))
    for k in range(2):
        frames.append(spot_frame([(tx - 1 + k, ty + 15), (tx + 1 - k, ty + 15)],
                                 pool=(tx, ty + 15), shimmer=k))
    return frames


def lift_flash(center=TROPHY_POP):
    cx, cy = center
    frames = []
    for f, (n, core, reach, width) in enumerate(((18, 26, 420, 7), (18, 15, 420, 4), (12, 7, 330, 2))):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for k in range(n):
            a = k * 2 * math.pi / n + (0.09 if f % 2 else 0)
            w = width * (1.0 if k % 2 == 0 else 0.55)
            p0 = (cx + core * 0.6 * math.cos(a), cy + core * 0.6 * math.sin(a))
            p1 = (cx + reach * math.cos(a - w / 400), cy + reach * math.sin(a - w / 400))
            p2 = (cx + reach * math.cos(a + w / 400), cy + reach * math.sin(a + w / 400))
            d.polygon([p0, p1, p2], fill=(255, 244, 163, 255) if k % 2 else (255, 255, 255, 255))
        d.ellipse((cx - core, cy - core * 0.85, cx + core, cy + core * 0.85), fill=(255, 255, 255, 255))
        frames.append(im)
    return frames


def strip(frames):
    s = Image.new('RGBA', (W * len(frames), H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * W, 0))
    return s
