"""danny_regen.png: green heal sparkles and plus signs rising off Danny while he sleeps and regenerates. 8 frames
of 176x144, looping at 0.08 s, one strip: his own body frame, on his own pivot.
THE PIVOT IS HIS FEET, the frame's bottom-centre (88, 144): the same frame and feet as his sumo sheets (176x144,
feet on row 143, centre column 88), so as a centred Sprite2D it takes the body's offset, (0, -72). Draw it OVER the
body. Never flipped.
Plus signs and four-point sparkles in a lime heal ramp with white hearts (J j, W) and a dark teal edge (i) so
they hold against the green mat as well as on his skin, each rising a stretch and thinning out in stepped
alpha (255, 176, 96) before it goes. The loop is seamless: every particle's phase wraps.
"""
import math
import random

import dfx_pal as pal

W, H = 176, 144
PX, PY = 88.0, 143.0
FRAME_SIZE = (W, H)
NOTE = '8 frames of 176x144 looping at 0.08 s; pivot = his feet (88,144) like his body sheets, offset (0,-72); draw over him'
FADE = {176: {'A': 'FFFFFF', 'C': 'E4FFB8', 'D': '99E550', 'E': '37946E'},
        96: {'F': 'FFFFFF', 'H': 'E4FFB8', 'I': '99E550', 'T': '37946E'}}

PLUS_S = ["..iii..", "..iJi..", "iiijiii", "iJjWjJi", "iiijiii", "..iJi..", "..iii.."]
PLUS_L = ["...iiii...", "...iJJi...", "...ijji...", "iiiijjiiii", "iJJjWWjJJi", "ijjjWWjjji", "iiiijjiiii",
          "...ijji...", "...iJJi...", "...iiii..."]
SPARK_S = ["..i..", "..J..", "iJWJi", "..J..", "..i.."]
SPARK_L = ["...i...", "...J...", "..iJi..", "iJJWJJi", "..iJi..", "...J...", "...i..."]


def particles():
    rnd = random.Random(12)
    out = []
    for i in range(20):
        shape = [PLUS_L, SPARK_L, PLUS_S, SPARK_S, PLUS_L][i % 5]
        x = rnd.uniform(22, 154)
        y = rnd.uniform(44, 130)
        out.append((shape, x, y, (i * 0.37 + rnd.uniform(0, 0.2)) % 1.0, rnd.uniform(18, 30)))
    return out


def frame(f):
    g = pal.blank(W, H)
    local = {}
    for lvl, keys in FADE.items():
        local.update({k: pal.hx(v, lvl) for k, v in keys.items()})
    for (shape, x, y, ph, rise) in particles():
        u = (f / 8.0 + ph) % 1.0
        yy0 = y - rise * u
        xx0 = x + 1.5 * math.sin(6.28 * u + x)
        fade = 0 if u < 0.6 else (176 if u < 0.82 else 96)
        remap = {} if not fade else dict(zip('WJji', FADE[fade].keys()))
        for j, row in enumerate(shape):
            for i, k in enumerate(row):
                if k == '.':
                    continue
                px, py = int(xx0 + i - len(row) // 2), int(yy0 + j - len(shape) // 2)
                if 0 <= px < W and 0 <= py < H:
                    g[py][px] = remap.get(k, k)
    return pal.Frame(pal.rows(g), local)


def frames():
    return [frame(f) for f in range(8)]
