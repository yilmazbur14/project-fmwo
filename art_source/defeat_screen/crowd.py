"""Emoji-face crowd for the defeat screen (mocking / laughing reactions)."""
import math
import random
from lib import *

TONES = {
    # base, shade, highlight, feature
    'night': (PLUM, NAVY, PLUM, K),
    'deep': (BROWN_D, PLUM, BROWN_D, K),
    'dim': (BROWN, BROWN_D, BROWN, K),
    'mid': (BROWN, BROWN_D, TAN, K),
    'lit': (TAN, BROWN, SKIN_L, K),
}
SKULL_TONES = {
    'night': (NAVY, K, NAVY, K),
    'deep': (PLUM, NAVY, PLUM, K),
    'dim': (GREY_D, PLUM, GREY_D, K),
    'mid': (GREY, GREY_D, GREY_L, K),
    'lit': (GREY_L, GREY, ICE, K),
}
TEETH = {'night': BROWN_D, 'deep': BROWN, 'dim': GREY_D, 'mid': GREY, 'lit': WHITE}
TEARS = {'night': NAVY, 'deep': INDIGO, 'dim': BLUE_D, 'mid': BLUE_L, 'lit': BLUE_L}
TONGUE = {'night': NAVY, 'deep': PLUM, 'dim': BROWN_D, 'mid': RED, 'lit': RED}


def face_mask(cx, cy, r):
    return ellipse_mask(cx, cy, r, r * 0.92)


def paint_body(img, m, cx, cy, r, tone):
    base, shade, hi, feat = tone
    for (x, y) in m:
        dx = (x + 0.5 - cx) / r
        dy = (y + 0.5 - cy) / r
        # light from upper left / front
        nz = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
        l = -0.45 * dx - 0.55 * dy + 0.7 * nz
        if l < 0.28:
            c = shade
        elif l > 0.86 and r >= 6:
            c = hi
        else:
            c = base
        img.set(x, y, c)
    for p in outline_of(m):
        img.set(p[0], p[1], K)


def eyes_laugh(img, cx, cy, r, feat):
    ey = int(round(cy - 0.22 * r))
    for sgn in (-1, 1):
        ex = int(round(cx + sgn * 0.4 * r - 0.5))
        if r >= 8:
            pts = [(-2, 1), (-1, 0), (0, -1), (1, 0), (2, 1)]
        else:
            pts = [(-1, 1), (0, 0), (1, 1)]
        for dx, dy in pts:
            img.set(ex + dx, ey + dy, feat)


def eyes_xd(img, cx, cy, r, feat):
    """> <  squeezed eyes"""
    ey = int(round(cy - 0.22 * r))
    for sgn in (-1, 1):
        ex = int(round(cx + sgn * 0.4 * r - 0.5))
        s = -sgn
        if r >= 8:
            pts = [(-s * 1, -2), (0, -1), (s * 1, 0), (0, 1), (-s * 1, 2)]
        else:
            pts = [(-s * 1, -1), (0, 0), (-s * 1, 1)]
        for dx, dy in pts:
            img.set(ex + dx, ey + dy, feat)


def eyes_smug(img, cx, cy, r, feat):
    """half-lidded: flat lid line with pupil under"""
    ey = int(round(cy - 0.22 * r))
    for sgn in (-1, 1):
        ex = int(round(cx + sgn * 0.4 * r - 0.5))
        w = 2 if r >= 8 else 1
        for dx in range(-w, w + 1):
            img.set(ex + dx, ey, feat)
        img.set(ex + (1 if r >= 8 else 0), ey + 1, feat)


def mouth_open(img, cx, cy, r, feat, tone='mid', teeth=True):
    top = int(round(cy + 0.12 * r))
    hw = max(2, int(round(0.55 * r)))
    depth = max(2, int(round(0.5 * r)))
    for i in range(depth):
        w = int(round(hw * math.sqrt(max(0.0, 1 - (i / depth) ** 2))))
        for dx in range(-w, w + 1):
            x = int(round(cx - 0.5)) + dx
            img.set(x, top + i, feat)
    if r >= 8 and teeth:
        for dx in range(-hw + 1, hw):
            img.set(int(round(cx - 0.5)) + dx, top, TEETH[tone])
    if r >= 7:
        # tongue
        ty = top + depth - 2
        for dx in (-1, 0, 1):
            img.set(int(round(cx - 0.5)) + dx, ty, TONGUE[tone])
        img.set(int(round(cx - 0.5)), ty - 1, TONGUE[tone])


def mouth_smirk(img, cx, cy, r, feat):
    y = int(round(cy + 0.35 * r))
    x0 = int(round(cx - 0.35 * r))
    x1 = int(round(cx + 0.4 * r))
    for x in range(x0, x1):
        img.set(x, y, feat)
    img.set(x1, y - 1, feat)
    if r >= 8:
        img.set(x1 + 1, y - 2, feat)


def tears(img, cx, cy, r, tone='mid'):
    ey = int(round(cy - 0.05 * r))
    for sgn in (-1, 1):
        ex = int(round(cx + sgn * 0.62 * r - 0.5))
        img.set(ex, ey, TEARS[tone])
        img.set(ex, ey + 1, TEARS[tone])
        if r >= 8:
            img.set(ex + sgn, ey + 2, TEARS[tone])


def skull(img, cx, cy, r, tone):
    base, shade, hi, feat = SKULL_TONES[tone]
    m = ellipse_mask(cx, cy - 0.1 * r, r * 0.95, r * 0.8)
    jaw = set()
    for (x, y) in list(m):
        pass
    jy = int(round(cy + 0.45 * r))
    jw = int(round(0.5 * r))
    for y in range(jy, jy + max(2, int(round(0.4 * r)))):
        for x in range(int(round(cx - 0.5)) - jw, int(round(cx - 0.5)) + jw + 1):
            jaw.add((x, y))
    m |= jaw
    paint_body(img, m, cx, cy, r, (base, shade, hi, feat))
    ey = int(round(cy - 0.12 * r))
    s = 2 if r >= 8 else 1
    for sgn in (-1, 1):
        ex = int(round(cx + sgn * 0.42 * r - 0.5))
        for dy in range(0, s + 1):
            for dx in range(-s + 1, s):
                img.set(ex + dx, ey + dy, feat)
        if s == 1:
            img.set(ex, ey, feat)
    # nose
    img.set(int(round(cx - 0.5)), int(round(cy + 0.25 * r)), feat)
    # teeth line
    ty = jy + 1
    for x in range(int(round(cx - 0.5)) - jw + 1, int(round(cx - 0.5)) + jw, 2):
        img.set(x, ty, feat)


def face(img, cx, cy, r, expr, tone):
    if expr == 'skull':
        skull(img, cx, cy, r, tone)
        return
    t = TONES[tone]
    m = face_mask(cx, cy, r)
    paint_body(img, m, cx, cy, r, t)
    feat = t[3]
    if expr == 'laugh':
        eyes_laugh(img, cx, cy, r, feat)
        mouth_open(img, cx, cy, r, feat, tone)
    elif expr == 'cry':
        eyes_xd(img, cx, cy, r, feat)
        mouth_open(img, cx, cy, r, feat, tone)
        tears(img, cx, cy, r, tone)
    elif expr == 'xd':
        eyes_xd(img, cx, cy, r, feat)
        mouth_open(img, cx, cy, r, feat, tone)
    elif expr == 'smug':
        eyes_smug(img, cx, cy, r, feat)
        mouth_smirk(img, cx, cy, r, feat)


EXPRS = ['laugh', 'cry', 'xd', 'smug', 'laugh', 'cry', 'laugh', 'xd', 'smug', 'laugh', 'skull', 'cry', 'xd']


TONE_ORDER = ['night', 'deep', 'dim', 'mid', 'lit']


def crowd_rows(img, rows, seed=7, x0=-8, x1=648, clip=None, spill=None):
    """rows: list of (y, r, tone, spacing). drawn back to front.
    spill: (cx, half_width) -> faces within half_width of cx are one tone lighter,
    faces beyond 2*half_width one tone darker (spotlight spill)."""
    rnd = random.Random(seed)
    placed = []
    for (y, r, tone0, sp) in rows:
        x = x0 + rnd.uniform(0, sp)
        while x < x1:
            rr = r + rnd.choice([-1, 0, 0, 1])
            yy = y + rnd.choice([-2, -1, 0, 1, 2])
            e = rnd.choice(EXPRS)
            tone = tone0
            if spill is not None:
                i = TONE_ORDER.index(tone0)
                d = abs(x - spill[0])
                if d < spill[1]:
                    i = min(i + 1, TONE_ORDER.index('mid'))
                elif d > 2 * spill[1]:
                    i = max(i - 1, 0)
                tone = TONE_ORDER[i]
            if clip is None or clip(x, yy):
                face(img, x, yy, rr, e, tone)
                placed.append((x, yy, rr, e, tone))
            x += sp + rnd.uniform(-1.5, 2.5)
    return placed
