"""
Arena redesign - design-pass generator.

Authors the ring mat and the ringside surround as pixel art on a 3x grid
(1 art pixel = 3 screen pixels), matching the crowd band (crowd_v2.png is
640x40 per frame drawn at scale 3) and the bosses (scale 3).

  full screen  = 640 x 360 art px  -> 1920 x 1080
  mat          = 564 x 284 art px  -> 1692 x  852, anchored at screen (111,114)

Nothing here writes into the project's Assets folder or touches any scene.

    python gen_arena.py --render <dir-with-arena00000015.png> --out <dir>
"""

import argparse
import math
import os
import random

from PIL import Image, ImageDraw

# --------------------------------------------------------------------------
# screen geometry, measured off the real ArenaScene render (do not guess)
# --------------------------------------------------------------------------
SCREEN = (1920, 1080)
SCALE = 3
ART = (SCREEN[0] // SCALE, SCREEN[1] // SCALE)          # 640 x 360

MAT_ANCHOR = (111, 114)                 # snapped to the 3x grid
MAT_ART = (564, 284)
CROWD_BOTTOM = 119                      # crowd band owns screen y 0..119
CROWD_Y = (CROWD_BOTTOM + 1) // SCALE   # 40 in art px

# the ring, in art px: everything inside is mat, everything outside is ringside
RING_X0, RING_X1 = 31, ART[0] - 32      # 31 .. 608
RING_Y1 = 328

MAT_GREEN = (136, 180, 99)
APRON_GREEN = (113, 152, 79)
CLEAR_GREY = (76, 76, 76)               # 3px sliver the root ColorRect misses

# --------------------------------------------------------------------------
# ringside bands, keyed by Chebyshev distance in art px from the ring edge.
# One table drives the left, right and bottom sides, so the corners mitre.
# --------------------------------------------------------------------------
# There are only 31 art px (93 screen px) of room outside the ropes on every
# open side, so this is four bold bands rather than six thin ones - six read
# as stripes at this size.
D_APRON = (1, 3)        # canvas continuing past the ropes
D_SKIRT = (4, 12)       # fabric skirt hanging off the apron
D_FLOOR = (13, 20)      # venue floor: skirt shadow, cables, light, dressing
D_RAIL = (21, 22)       # steel crowd barrier, read as a simple lit rail
D_CROWD = 23            # standing spectators behind it (8 art px = 24 screen)

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
BAYER8 = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def smoothstep(a, b, x):
    t = clamp((x - a) / (b - a) if b != a else 0.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def _hash2(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def ramp_pick(t, ramp, x, y, jitter=0.55):
    """Map t in [0,1] onto a colour ramp.

    The dither threshold is a blend of an ordered Bayer matrix and white
    noise. Pure Bayer at 3x screen scale reads as a printed halftone screen;
    jittering it breaks the grid so the transitions read as canvas grain.
    """
    n = len(ramp) - 1
    v = clamp(t) * n
    i = int(v)
    if i >= n:
        return ramp[n]
    thr = lerp((BAYER8[y & 7][x & 7] + 0.5) / 64.0, _hash2(x, y, 991), jitter)
    return ramp[i + 1] if (v - i) > thr else ramp[i]


def vnoise(x, y, period, seed):
    """Bilinear value noise on a lattice, smoothstep-interpolated."""
    fx, fy = x / period, y / period
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = smoothstep(0, 1, fx - ix), smoothstep(0, 1, fy - iy)
    a = lerp(_hash2(ix, iy, seed), _hash2(ix + 1, iy, seed), tx)
    b = lerp(_hash2(ix, iy + 1, seed), _hash2(ix + 1, iy + 1, seed), tx)
    return lerp(a, b, ty)


def fbm(x, y, seed, octaves=((52, 0.55), (19, 0.30), (7, 0.15))):
    return sum(vnoise(x, y, p, seed + i * 37) * w for i, (p, w) in enumerate(octaves))


def paint_mask(img, mask, colour, alpha):
    """Blend colour over img everywhere mask (an 'L' image) is non-zero."""
    layer = Image.new("RGBA", img.size, colour + (255,))
    m = mask.point(lambda v: int(v * alpha))
    img.paste(Image.composite(layer, img.convert("RGBA"), mask).convert(img.mode),
              (0, 0), m)


def newmask(size):
    return Image.new("L", size, 0)


def ring_dist(x, y):
    """Chebyshev distance out of the ring; <=0 means inside. The top edge is
    excluded because the crowd band already covers it."""
    return max(RING_X0 - x, x - RING_X1, y - RING_Y1)


# --------------------------------------------------------------------------
# palettes - three directions
# --------------------------------------------------------------------------
DIRECTIONS = {
    # A: keeps today's exact green as the base tone. Worn wrestling canvas.
    "a": dict(
        name="A - Worn Canvas",
        mat_ramp=[(106, 142, 75), (117, 156, 84), (126, 168, 91),
                  (136, 180, 99), (146, 190, 110)],
        paint_col=(238, 240, 226), paint_a=0.26,
        crest="hash", crest_col=(238, 240, 226), crest_a=0.17,
        accent=(172, 50, 50),                     # DB32 #ac3232
        skirt=[(34, 32, 52), (44, 42, 66), (24, 23, 38)],
        skirt_trim=(138, 111, 48),                # dull gold
        floor=[(17, 17, 23), (26, 26, 34), (36, 36, 46)],
        barrier=(13, 13, 18), barrier_hi=(52, 52, 66),
        banner=(56, 33, 48),
        lamp=(217, 160, 102), lamp_a=0.13,
    ),
    # B: cooler, deeper mat. Discord/"server stage" flavour, blurple markings.
    "b": dict(
        name="B - Server Stage",
        mat_ramp=[(70, 104, 72), (80, 117, 79), (89, 129, 85),
                  (99, 142, 92), (110, 154, 101)],
        paint_col=(203, 219, 252), paint_a=0.22,
        crest="bubble", crest_col=(140, 146, 226), crest_a=0.30,
        accent=(91, 110, 225),                    # DB32 #5b6ee1
        skirt=[(26, 27, 45), (36, 37, 60), (18, 19, 32)],
        skirt_trim=(91, 110, 225),
        floor=[(15, 17, 26), (23, 26, 37), (32, 36, 50)],
        barrier=(11, 12, 19), barrier_hi=(55, 56, 102),
        banner=(36, 36, 68),
        lamp=(99, 155, 255), lamp_a=0.12,
    ),
    # C: warm olive tournament canvas, painted corner quadrants, crest+banner.
    "c": dict(
        name="C - Tournament Olive",
        mat_ramp=[(104, 112, 63), (116, 126, 71), (128, 139, 79),
                  (140, 152, 88), (151, 163, 99)],
        paint_col=(244, 238, 214), paint_a=0.28,
        crest="shield", crest_col=(244, 238, 214), crest_a=0.20,
        accent=(172, 50, 50),
        skirt=[(45, 30, 29), (60, 41, 38), (32, 21, 21)],
        skirt_trim=(217, 160, 102),
        floor=[(20, 18, 20), (29, 27, 28), (39, 36, 37)],
        barrier=(16, 15, 16), barrier_hi=(58, 53, 52),
        banner=(62, 36, 32),
        lamp=(223, 113, 38), lamp_a=0.14,
    ),
}


# ==========================================================================
# THE MAT
# ==========================================================================
def build_mat(cfg, seed=7):
    """564x284 art px. Tight value range: texture must sit UNDER the fight."""
    w, h = MAT_ART
    img = Image.new("RGB", (w, h), cfg["mat_ramp"][3])
    px = img.load()
    cx, cy = w / 2.0, h / 2.0
    ramp = cfg["mat_ramp"]

    # --- base field: centre-bright vignette + gentle top light + wear noise
    for y in range(h):
        ny = (y - cy) / cy
        top_light = 1.0 - (y / h) * 0.16
        for x in range(w):
            nx = (x - cx) / cx
            r = math.sqrt(nx * nx * 0.72 + ny * ny)
            vig = 1.0 - smoothstep(0.34, 1.20, r)
            n = fbm(x, y, seed)
            # a broad, slightly more worn patch through the middle of the ring
            traffic = smoothstep(1.05, 0.40, math.sqrt(nx * nx * 1.5 + ny * ny)) * 0.08
            t = (0.26 + vig * 0.52 + (n - 0.5) * 0.26
                 + (top_light - 1.0) * 0.6 + traffic)
            px[x, y] = ramp_pick(t, ramp, x, y)

    # --- canvas weave: a very faint 2px cross-hatch, only in the mid tones
    for y in range(h):
        for x in range(w):
            if (x + y) % 4 == 0 and _hash2(x, y, 55) < 0.35:
                px[x, y] = mix(px[x, y], ramp[0], 0.22)

    # --- scuffs and skid marks: short streaks, never longer than a boss
    rnd = random.Random(seed + 101)
    for _ in range(80):
        sx, sy = rnd.randrange(14, w - 14), rnd.randrange(14, h - 14)
        ln, ang = rnd.randrange(6, 30), rnd.uniform(0, math.pi)
        dark = rnd.random() < 0.6
        for i in range(ln):
            x = int(sx + math.cos(ang) * i)
            y = int(sy + math.sin(ang) * i * 0.4)
            if 0 <= x < w and 0 <= y < h and _hash2(x, y, 7) < 0.6:
                px[x, y] = mix(px[x, y], ramp[0] if dark else ramp[4], 0.45)

    # --- painted markings (faded, low alpha so they read as paint not lines)
    d = ImageDraw.Draw(img)
    m = newmask((w, h))
    md = ImageDraw.Draw(m)
    md.rectangle([8, 8, w - 9, h - 9], outline=255, width=1)
    md.rectangle([13, 13, w - 14, h - 14], outline=255, width=1)
    for (ax, ay, a0, a1) in ((13, 13, 0, 90), (w - 14, 13, 90, 180),
                             (w - 14, h - 14, 180, 270), (13, h - 14, 270, 360)):
        md.arc([ax - 52, ay - 52, ax + 52, ay + 52], a0, a1, fill=255, width=1)
    paint_mask(img, m, cfg["paint_col"], cfg["paint_a"])

    # accent pinstripe between the two border lines
    m = newmask((w, h))
    ImageDraw.Draw(m).rectangle([10, 10, w - 11, h - 11], outline=255, width=1)
    paint_mask(img, m, cfg["accent"], 0.20)

    draw_crest(img, cfg, w // 2, h // 2)

    if cfg["crest"] == "shield":
        m = newmask((w, h))
        md = ImageDraw.Draw(m)
        for (ax, ay, a0, a1) in ((13, 13, 0, 90), (w - 14, 13, 90, 180),
                                 (w - 14, h - 14, 180, 270), (13, h - 14, 270, 360)):
            md.pieslice([ax - 50, ay - 50, ax + 50, ay + 50], a0, a1, fill=255)
        paint_mask(img, m, cfg["accent"], 0.09)

    return img


def draw_crest(img, cfg, cx, cy):
    w, h = img.size
    kind = cfg["crest"]
    R = 72

    # double ring, so the crest reads as a mat logo rather than a stain
    m = newmask((w, h))
    md = ImageDraw.Draw(m)
    md.ellipse([cx - R, cy - R, cx + R, cy + R], outline=255, width=1)
    md.ellipse([cx - R + 5, cy - R + 5, cx + R - 5, cy + R - 5], outline=255, width=1)
    paint_mask(img, m, cfg["paint_col"], cfg["paint_a"] * 0.75)

    # faint lighter disc: the centre is the brightest point on the mat
    m = newmask((w, h))
    ImageDraw.Draw(m).ellipse([cx - R + 6, cy - R + 6, cx + R - 6, cy + R - 6], fill=255)
    paint_mask(img, m, cfg["mat_ramp"][4], 0.16)

    m = newmask((w, h))
    md = ImageDraw.Draw(m)

    if kind == "hash":
        # a channel hash - generic, iconic, reads instantly at 3x
        s, th, sl = 44, 8, 9
        for off in (-14, 10):
            md.polygon([(cx + off + sl, cy - s // 2), (cx + off + sl + th, cy - s // 2),
                        (cx + off - sl + th, cy + s // 2), (cx + off - sl, cy + s // 2)],
                       fill=255)
        for off in (-13, 7):
            md.rectangle([cx - s // 2 - 4, cy + off, cx + s // 2 + 4, cy + off + th],
                         fill=255)

    elif kind == "bubble":
        md.rounded_rectangle([cx - 42, cy - 32, cx + 42, cy + 12], radius=11,
                             outline=255, width=4)
        md.polygon([(cx - 21, cy + 10), (cx - 6, cy + 10), (cx - 19, cy + 31)], fill=255)
        for ox in (-20, 0, 20):
            md.ellipse([cx + ox - 5, cy - 15, cx + ox + 4, cy - 6], fill=255)

    elif kind == "shield":
        md.polygon([(cx - 40, cy - 46), (cx + 40, cy - 46), (cx + 40, cy - 2),
                    (cx, cy + 32), (cx - 40, cy - 2)], outline=255, width=4)
        for off in (-10, 8):
            md.rectangle([cx + off, cy - 34, cx + off + 5, cy + 10], fill=255)
        for off in (-22, -4):
            md.rectangle([cx - 24, cy + off, cx + 24, cy + off + 5], fill=255)
        # banner ribbon below the shield point, not across it
        md.rectangle([cx - 52, cy + 34, cx + 52, cy + 44], outline=255, width=3)

    paint_mask(img, m, cfg["crest_col"], cfg["crest_a"])


# ==========================================================================
# THE RINGSIDE SURROUND
# ==========================================================================
def build_ringside(cfg, seed=19):
    """640x360 art px RGBA; transparent over the mat and the crowd band."""
    W, H = ART
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    rnd = random.Random(seed)
    floor, skirt = cfg["floor"], cfg["skirt"]

    # ---- pass 1: floor everywhere, with light spilling off the ring
    for y in range(CROWD_Y, H):
        for x in range(W):
            d = ring_dist(x, y)
            if d < 1:
                continue
            spill = smoothstep(float(D_RAIL[1]), float(D_FLOOR[0]), float(d))
            n = fbm(x * 1.7, y * 1.7, seed + 3, ((26, 0.6), (9, 0.4)))
            t = 0.18 + spill * 0.46 + (n - 0.5) * 0.38
            px[x, y] = ramp_pick(t, floor, x, y) + (255,)

    # ---- floor tile seams, one tone up, dithered so they stay quiet
    seam = floor[2]
    for y in range(CROWD_Y, H):
        for x in range(W):
            if ring_dist(x, y) < D_FLOOR[0]:
                continue
            if ring_dist(x, y) > D_FLOOR[1]:
                continue
            if (x % 18 == 0 or y % 18 == 0) and _hash2(x, y, 12) < 0.55:
                px[x, y] = seam + (255,)

    # ---- warm pools where the ring lighting hits the floor. Long and thin,
    #      running with the ring, so they read as spill and not as stains.
    lamp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lamp)
    a = int(255 * cfg["lamp_a"])
    for (lx, ly, rx, ry) in ((16, 120, 4, 62), (16, 268, 4, 62),
                             (W - 17, 120, 4, 62), (W - 17, 268, 4, 62),
                             (200, 343, 62, 4), (440, 343, 62, 4)):
        ld.ellipse([lx - rx, ly - ry, lx + rx, ly + ry], fill=cfg["lamp"] + (a,))
    lampmask = Image.new("L", (W, H), 0)
    lm = lampmask.load()
    for y in range(CROWD_Y, H):
        for x in range(W):
            if D_FLOOR[0] <= ring_dist(x, y) <= D_FLOOR[1]:
                lm[x, y] = 255
    img.alpha_composite(Image.composite(lamp, Image.new("RGBA", (W, H), (0, 0, 0, 0)),
                                        lampmask))

    draw_cables(img, cfg, rnd)
    draw_crowd(img, cfg, rnd)
    draw_rail(img, cfg)
    draw_skirt(img, cfg, rnd)
    draw_cases(img, cfg)          # objects standing on the floor: drawn last,
    draw_apron(img, cfg)          # and allowed to overlap the skirt hem

    ImageDraw.Draw(img).rectangle([0, 0, W - 1, CROWD_Y - 1], fill=(0, 0, 0, 0))
    return img


def draw_cables(img, cfg, rnd):
    W, H = img.size
    px = img.load()
    dark = mix(cfg["floor"][0], (0, 0, 0), 0.5)
    hi = cfg["floor"][2]

    def run(pts):
        for (x, y) in pts:
            if 0 <= x < W and 0 <= y < H and D_FLOOR[0] <= ring_dist(x, y) <= D_FLOOR[1]:
                px[x, y] = dark + (255,)
                if 0 <= y + 1 < H and D_FLOOR[0] <= ring_dist(x, y + 1) <= D_FLOOR[1]:
                    px[x, y + 1] = hi + (255,)

    for base_x in (15, W - 16):
        for k in range(2):
            x0 = base_x + k * 4 - 2
            pts = [(x0 + int(math.sin(y / 34.0 + k * 2) * 1.6), y)
                   for y in range(CROWD_Y, H)]
            run(pts)
    # short segments only - a cable run spanning the full width reads as a
    # scanline across the bottom of the screen
    for (x0, x1, y, k) in ((40, 250, 343, 0), (200, 300, 347, 1),
                           (392, 600, 344, 0), (360, 470, 347, 1)):
        run([(x, y + int(math.sin(x / 26.0 + k) * 1.6)) for x in range(x0, x1)])


def draw_cases(img, cfg):
    """Flight cases and a commentary desk. Centre of the bottom band only -
    the HUD owns screen x<270 and x>1545 down there."""
    d = ImageDraw.Draw(img)
    base = mix(cfg["floor"][2], (0, 0, 0), 0.25)
    hi = mix(cfg["floor"][2], (255, 255, 255), 0.22)
    lo = mix(base, (0, 0, 0), 0.5)
    trim = mix(cfg["skirt_trim"], (0, 0, 0), 0.55)

    shadow = mix(cfg["floor"][0], (0, 0, 0), 0.6)

    def crate(cx, cw, ch, y1):
        y0 = y1 - ch
        d.rectangle([cx - 1, y1 + 1, cx + cw + 1, y1 + 2], fill=shadow + (255,))
        d.rectangle([cx, y0, cx + cw, y1], fill=base + (255,))
        d.rectangle([cx, y0, cx + cw, y0], fill=hi + (255,))
        d.rectangle([cx, y1, cx + cw, y1], fill=lo + (255,))
        for bx in (cx + 3, cx + cw - 3):          # corner ribs
            d.line([(bx, y0), (bx, y1)], fill=trim + (255,))

    for (cx, cw, ch) in ((110, 30, 7), (147, 20, 5), (448, 28, 7), (485, 19, 5)):
        crate(cx, cw, ch, 348)

    # commentary desk: kept inside the floor band so it does not swallow the
    # skirt; only its monitors break the hem line, which reads as depth
    dx0, dx1, dy0, dy1 = 282, 358, 341, 348
    d.rectangle([dx0 - 1, dy1 + 1, dx1 + 1, dy1 + 2], fill=shadow + (255,))
    d.rectangle([dx0, dy0, dx1, dy1], fill=base + (255,))
    d.rectangle([dx0, dy0, dx1, dy0], fill=hi + (255,))
    d.rectangle([dx0, dy1, dx1, dy1], fill=lo + (255,))
    d.line([(dx0, dy0 + 3), (dx1, dy0 + 3)], fill=trim + (255,))
    for mx in (dx0 + 10, dx0 + 44):               # two dim monitors on the desk
        d.rectangle([mx, dy0 - 5, mx + 22, dy0 - 1], fill=lo + (255,))
        d.rectangle([mx + 1, dy0 - 4, mx + 21, dy0 - 2],
                    fill=mix(cfg["lamp"], (0, 0, 0), 0.62) + (255,))


def draw_crowd(img, cfg, rnd):
    """Standing spectators behind the barrier. Same blob language as
    crowd_v2.png, but knocked back so they never pull the eye.

    They need a flat dark backdrop first - drawn over the floor noise the
    silhouettes disappear entirely."""
    W, H = img.size
    px = img.load()
    d = ImageDraw.Draw(img)
    back = mix(cfg["barrier"], (34, 32, 52), 0.55)      # DB32 #222034, knocked back
    for y in range(CROWD_Y, H):
        for x in range(W):
            if ring_dist(x, y) >= D_CROWD:
                px[x, y] = (back if _hash2(x, y, 71) > 0.18
                            else mix(back, (0, 0, 0), 0.4)) + (255,)

    SKINS = [(143, 86, 59), (217, 160, 102), (102, 57, 49), (89, 86, 82)]
    SHIRTS = [(63, 63, 116), (69, 40, 60), (48, 96, 130), (82, 75, 36),
              (50, 60, 57), (76, 66, 138)]

    def figure(cx, feet_y):
        """Head over shoulders, 3 wide x 8 tall, with a clear dark gap either
        side. Separation is what made crowd_v2 read - butted-up figures turn
        into a mosaic of coloured squares at this size."""
        k = rnd.uniform(0.56, 0.68)
        skin = mix(rnd.choice(SKINS), (0, 0, 0), k)
        shirt = mix(rnd.choice(SHIRTS), (0, 0, 0), k + 0.08)
        top = feet_y - 7
        d.rectangle([cx - 1, top + 3, cx + 1, feet_y], fill=shirt + (255,))
        d.rectangle([cx - 1, top, cx + 1, top + 2], fill=skin + (255,))

    def ok(x, y):
        return 0 <= x < W and 0 <= y < H and ring_dist(x, y) >= D_CROWD

    # sides: two columns of upright figures, staggered, 3px gaps between them
    for col, x in enumerate((25, 31)):
        for y in range(CROWD_Y + 9 + col * 5, H, 11):
            if ok(x - 24, y) and ok(x - 24, y - 7):
                figure(x - 24, y)
            if ok(W - 1 - (x - 24), y) and ok(W - 1 - (x - 24), y - 7):
                figure(W - 1 - (x - 24), y)
    # bottom: one clean row along the rail
    for i, x in enumerate(range(6, W - 6, 5)):
        y = H - 1 - (i % 2)
        if ok(x, y) and ok(x, y - 7):
            figure(x, y)


def draw_rail(img, cfg):
    """Crowd barrier, reduced to what reads at 2 art px: a lit top rail with
    banner colour under it and a post tick every 14."""
    W, H = img.size
    px = img.load()
    bar, hi, ban = cfg["barrier"], cfg["barrier_hi"], cfg["banner"]
    for y in range(CROWD_Y, H):
        for x in range(W):
            d = ring_dist(x, y)
            if not (D_RAIL[0] <= d <= D_RAIL[1]):
                continue
            along = y if (x < RING_X0 or x > RING_X1) else x
            post = along % 14 < 2
            # d grows outward: D_RAIL[0] is the face turned toward the ring
            if d == D_RAIL[0]:
                c = hi if post else mix(ban, hi, 0.45)
            else:
                c = bar if post else ban
            px[x, y] = c + (255,)


def draw_skirt(img, cfg, rnd):
    """Hanging ring skirt: soft vertical folds + a repeating diamond motif."""
    W, H = img.size
    px = img.load()
    base, hi, lo = cfg["skirt"]
    trim = mix(cfg["skirt_trim"], (0, 0, 0), 0.30)

    for y in range(CROWD_Y, H):
        for x in range(W):
            d = ring_dist(x, y)
            if not (D_SKIRT[0] <= d <= D_SKIRT[1] + 2):
                continue
            if d > D_SKIRT[1]:
                # shadow the skirt throws onto the floor, fading outward
                c = px[x, y][:3]
                px[x, y] = mix(c, (0, 0, 0), 0.6 - (d - D_SKIRT[1] - 1) * 0.25) + (255,)
                continue
            along = y if (x < RING_X0 or x > RING_X1) else x
            f = math.sin(along * math.pi / 9.0)
            c = hi if f > 0.72 else (lo if f < -0.72 else base)
            if d == D_SKIRT[0]:
                c = trim                      # trim stripe along the top hem
            elif d == D_SKIRT[1]:
                c = mix(lo, (0, 0, 0), 0.45)  # dark hem at the bottom
            px[x, y] = c + (255,)

    # diamond motif repeating down the skirt, barely above the fold shading
    motif = mix(cfg["skirt_trim"], base, 0.5)

    def diamond(cx, cy):
        for dy in range(-2, 3):
            wdt = 2 - abs(dy)
            for dx in range(-wdt, wdt + 1):
                x, y = cx + dx, cy + dy
                if 0 <= x < W and 0 <= y < H and \
                        D_SKIRT[0] + 1 <= ring_dist(x, y) <= D_SKIRT[1] - 1:
                    px[x, y] = motif + (255,)

    mid = (D_SKIRT[0] + D_SKIRT[1]) // 2
    for y in range(CROWD_Y + 14, RING_Y1, 27):
        diamond(RING_X0 - mid, y)
        diamond(RING_X1 + mid, y)
    for x in range(56, W - 56, 27):
        diamond(x, RING_Y1 + mid)


def draw_apron(img, cfg):
    """Canvas continuing past the ropes, a step darker than the mat."""
    W, H = img.size
    px = img.load()
    ap, lip = cfg["mat_ramp"][1], cfg["mat_ramp"][0]
    for y in range(CROWD_Y, H):
        for x in range(W):
            d = ring_dist(x, y)
            if D_APRON[0] <= d <= D_APRON[1]:
                px[x, y] = (lip if d == D_APRON[1] else ap) + (255,)


# ==========================================================================
# COMPOSITING OVER THE REAL RENDER
# ==========================================================================
def build_background(mat_img, ring_img):
    W, H = SCREEN
    up = ring_img.resize((W, H), Image.NEAREST)
    bg = Image.new("RGB", (W, H), (0, 0, 0))
    bg.paste(up.convert("RGB"), (0, 0), up.split()[3])
    bg.paste(mat_img.resize((mat_img.width * SCALE, mat_img.height * SCALE),
                            Image.NEAREST), MAT_ANCHOR)
    return bg


def composite(render, bg):
    """Replace only the flat green and the black margins; keep crowd, ropes,
    poles, HUD and anything else the engine drew (plus a 2px dilation so the
    black outlines of those sprites survive)."""
    out = render.convert("RGB").copy()
    W, H = out.size
    src = render.convert("RGB").load()
    dst = out.load()
    bgp = bg.load()

    keep = [[False] * W for _ in range(H)]
    for y in range(CROWD_BOTTOM + 1, H):
        row = keep[y]
        for x in range(W):
            c = src[x, y]
            if c in (MAT_GREEN, APRON_GREEN, CLEAR_GREY):
                continue
            if c[0] < 12 and c[1] < 12 and c[2] < 12:
                continue
            row[x] = True
    dil = [[False] * W for _ in range(H)]
    for y in range(CROWD_BOTTOM + 1, H):
        for x in range(W):
            if not keep[y][x]:
                continue
            for dy in (-2, -1, 0, 1, 2):
                yy = y + dy
                if not (CROWD_BOTTOM + 1 <= yy < H):
                    continue
                r = dil[yy]
                for dx in (-2, -1, 0, 1, 2):
                    xx = x + dx
                    if 0 <= xx < W:
                        r[xx] = True

    for y in range(CROWD_BOTTOM + 1, H):
        for x in range(W):
            if not dil[y][x]:
                dst[x, y] = bgp[x, y]
    return out


def report_range(name, img):
    px = img.convert("RGB").load()
    lo, hi = 999, -1
    for y in range(0, img.height, 3):
        for x in range(0, img.width, 3):
            r, g, b = px[x, y]
            L = 0.299 * r + 0.587 * g + 0.114 * b
            lo, hi = min(lo, L), max(hi, L)
    print(f"    {name}: luma {lo:.0f}..{hi:.0f}  (spread {hi - lo:.0f})")


# ==========================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True, help="dir holding arena000000NN.png")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frame", default="arena00000015.png")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    render = Image.open(os.path.join(args.render, args.frame)).convert("RGB")

    for key, cfg in DIRECTIONS.items():
        mat = build_mat(cfg)
        ring = build_ringside(cfg)
        mat.save(os.path.join(args.out, f"mat_{key}.png"))
        ring.save(os.path.join(args.out, f"ringside_{key}.png"))
        bg = build_background(mat, ring)
        composite(render, bg).save(os.path.join(args.out, f"mockup_{key}.png"))
        print("built", cfg["name"])
        report_range("mat", mat)


if __name__ == "__main__":
    main()
