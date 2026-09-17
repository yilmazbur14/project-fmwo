"""Consecutive-parry streak art.
  popup_parry_x2     : 2 frames of 96x20  "PARRY x2"  - the x1 popup pushed hotter (white -> gold -> orange)
  popup_parry_x3     : 2 frames of 112x20 "PARRY x3+" - gold into magenta, deeper extrusion, spark ticks
  streak_badge       : 4 frames x 3 tier rows of 46x22 - the HUD badge (brass plate, flame, "x", digit slot)
  streak_digits      : 10 cells of 8x13 (0-9) - white digits dropped into the badge's slot, so any count works
  parry_flash_strong : 7 frames of 96x96, pivot (48, 48) - the x3+ parry burst, bigger and hotter
  parry_shatter      : 4 frames of 32x32, pivot (16, 16) - a parried projectile breaking apart
DB32 only, alpha 0/255."""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *
import lettering as LT
import fx_defense as FD

# ------------------------------------------------------------------ popups
POPUPS = {'popup_parry_x2': ('PARRY x2', 'parry_x2', 96),
          'popup_parry_x3': ('PARRY x3+', 'parry_x3', 112)}
POPUP_DURATIONS_MS = {'popup_parry_x2': [80, 80], 'popup_parry_x3': [70, 70]}
# spark ticks around the x3+ word (x, y, size); the pop frame gets all of them
X3_SPARKS = [(6, 3, 1), (104, 4, 1), (16, 17, 0), (95, 17, 0), (54, 1, 0)]


def sparkle(c, x, y, size, core='W', tip='Y'):
    c.set(x, y, C[core])
    for k in range(1, size + 1):
        col = core if k < size else tip
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.set(x + dx, y + dy, C[col])


def popup(name, bright):
    word, scheme, tw = POPUPS[name]
    c = LT.word_canvas(word, scheme, bright, tw, 20)
    if name == 'popup_parry_x3':
        for i, (x, y, s) in enumerate(X3_SPARKS):
            if bright or i % 2 == 0:
                sparkle(c, x, y, s + (1 if bright else 0), 'W', 'm' if i % 2 else 'Y')
    return c


def popups():
    return {n: [popup(n, False), popup(n, True)] for n in POPUPS}


# ------------------------------------------------------------------ HUD streak badge
BW, BH = 50, 22
BADGE_DURATIONS_MS = [90, 90, 90, 90]
# digit cells (8x13) drop into the badge: one digit at (30, 4), two at (26, 4) and (35, 4)
DIGIT_CELL = (8, 13)
DIGIT_ONE = (30, 4)
DIGIT_TWO = ((26, 4), (35, 4))

# flame in tier colours: 'a' white core, 'b' mid, 'c' outer, 'd' ember
FLAME = [
    "....KK....",
    "...KbaK...",
    "..KbaaK...",
    "..KbaabK..",
    ".KbaaabK..",
    ".KbaaabK..",
    "KcbaaabbK.",
    "KcbaaabbK.",
    "KcbbaabbK.",
    "KcbbbbbdK.",
    ".KcbbbddK.",
    ".KccbddK..",
    "..KcddK...",
    "...KKK....",
]
FLAME_XY = (4, 4)
XGLYPH = [
    ".K...K.",
    "KcK.KcK",
    ".KcKcK.",
    "..KcK..",
    ".KcKcK.",
    "KcK.KcK",
    ".K...K.",
]
XGLYPH_XY = (16, 8)

TIERS = [                                     # flame ramp, x colour, lit rim, glow
    {'a': 'W', 'b': 'Y', 'c': 'T', 'd': 'O', 'x': 'Y', 'glow': None},         # x1 gold
    {'a': 'W', 'b': 'Y', 'c': 'O', 'd': 'E', 'x': 'O', 'glow': 'O'},          # x2 hot gold
    {'a': 'W', 'b': 'Y', 'c': 'm', 'd': 'V', 'x': 'm', 'glow': 'm'},          # x3+ magenta-gold
]


def plate(lit):
    """brass HUD chip in the kit's profile: black outline, 2 px brass bevel, inner outline, navy face"""
    c = Canvas(BW, BH)
    P = {'hi': 'Y', 'lo': 'S', 'sh': 'D', 'dk': 'o', 'face': 'n', 'ref': 'I'}
    if lit:
        P.update({'hi': 'W', 'lo': 'W', 'sh': 'T', 'dk': 'D', 'ref': 'm'})
    for y in range(BH):
        for x in range(BW):
            edge = min(x, y, BW - 1 - x, BH - 1 - y)
            top_left = (y <= x) and (y <= BW - 1 - x)
            bottom_right = (BH - 1 - y < x) and (BH - 1 - y <= BW - 1 - x)
            if edge == 0:
                col = 'K'
            elif edge == 1:
                col = P['hi'] if top_left else (P['dk'] if bottom_right else P['lo'])
            elif edge == 2:
                col = P['lo'] if top_left else (P['sh'] if bottom_right else P['sh'])
            elif edge == 3:
                col = 'K'
            else:
                col = P['face']
                if edge == 4 and (y == BH - 5 or x == BW - 5):
                    col = P['ref']          # reflected light on the inner bottom and right edges only
            c.p[y][x] = C[col]
    for (x, y) in [(0, 0), (BW - 1, 0), (0, BH - 1), (BW - 1, BH - 1)]:
        c.p[y][x] = None
    return c


def badge_frame(tier, f):
    t = TIERS[tier]
    lit = f in (0, 1) and tier > 0
    c = plate(lit)
    flick = [0, 1, 0, 0][f]
    pal = {'K': C['K'], 'a': C[t['a']], 'b': C[t['b']], 'c': C[t['c']], 'd': C[t['d']]}
    rows = FLAME if f % 2 == 0 else [r.replace('a', 'b').replace('b', 'b') for r in FLAME]
    stamp(c, rows, FLAME_XY[0], FLAME_XY[1] - flick, pal)
    stamp(c, XGLYPH, XGLYPH_XY[0], XGLYPH_XY[1], {'K': C['K'], 'c': C[t['x'] if f % 2 == 0 else 'W']})
    if t['glow'] and f == 0:
        solid = {(x, y) for y in range(c.h) for x in range(c.w) if c.p[y][x]}
        for (x, y) in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in solid and c.inb(*q) and c.get(*q) is None:
                    c.set(q[0], q[1], C[t['glow']])
    return c


def streak_badge():
    return [[badge_frame(t, f) for f in range(4)] for t in range(3)]


def badge_with_count(tier, f, count):
    """preview helper: the badge with its digits dropped in"""
    c = badge_frame(tier, f)
    d = streak_digits()
    text = str(count)
    if len(text) == 1:
        c.blit(d[int(text)], *DIGIT_ONE)
    else:
        for k, ch in enumerate(text[-2:]):
            c.blit(d[int(ch)], *DIGIT_TWO[k])
    return c


# ------------------------------------------------------------------ digits for the badge slot
DIGITS = {
    '0': [".XXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    '1': ["..XX..", ".XXX..", "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", "..XX..", "XXXXXX"],
    '2': [".XXXX.", "XX..XX", "....XX", "...XX.", "..XX..", ".XX...", "XX....", "XX....", "XXXXXX"],
    '3': ["XXXXXX", "....XX", "...XX.", "..XXX.", "....XX", "....XX", "XX..XX", "XX..XX", ".XXXX."],
    '4': ["...XX.", "..XXX.", ".XXXX.", "XX.XX.", "XXXXXX", "...XX.", "...XX.", "...XX.", "...XX."],
    '5': ["XXXXXX", "XX....", "XX....", "XXXXX.", "....XX", "....XX", "XX..XX", "XX..XX", ".XXXX."],
    '6': ["..XXX.", ".XX...", "XX....", "XXXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    '7': ["XXXXXX", "....XX", "....XX", "...XX.", "...XX.", "..XX..", "..XX..", ".XX...", ".XX..."],
    '8': [".XXXX.", "XX..XX", "XX..XX", ".XXXX.", "XX..XX", "XX..XX", "XX..XX", "XX..XX", ".XXXX."],
    '9': [".XXXX.", "XX..XX", "XX..XX", "XX..XX", ".XXXXX", "....XX", "....XX", ".XX.XX", "..XXX."],
}


def digit_cell(d):
    """8x13 cell: white digit, cream bottom shade, 1 px black outline - reads on every tier"""
    c = Canvas(*DIGIT_CELL)
    rows = DIGITS[d]
    pts = {(x + 1, y + 2) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == 'X'}
    for (x, y) in pts:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in pts and c.inb(*q):
                    c.set(q[0], q[1], C['K'])
    for (x, y) in pts:
        c.set(x, y, C['S'] if (x, y + 1) not in pts else C['W'])
    return c


def streak_digits():
    return [digit_cell(str(d)) for d in range(10)]


# ------------------------------------------------------------------ x3+ parry flash (96x96)
FS_, FC_ = 96, 48
FLASH_DURATIONS_MS = [30, 50, 60, 70, 80, 90, 100]


def flash_frame(i):
    cx = cy = FC_
    c = Canvas(FS_, FS_)
    if i == 0:
        for ang, ln in ((0, 26), (180, 26), (-90, 22), (90, 19)):
            FD.needle(c, cx, cy, ang, 9, ln, ['W', 'W', 'Y'])
        body = Canvas(FS_, FS_)
        FD.astroid(body, cx, cy, 12, 11, 0.55, 'W', 'Y')
        FD.disc(body, cx, cy, 2.2, 'W')
        FD.outline(body)
        c.blit(body, 0, 0)
    elif i == 1:
        for ang in (30, 60, 120, 150, 210, 240, 300, 330):
            FD.needle(c, cx, cy, ang, 16, 42, ['Y', 'O', 'm', 'm'])
        for ang, ln in ((0, 46), (180, 46), (-90, 42), (90, 36)):
            FD.needle(c, cx, cy, ang, 22, ln, ['W', 'W', 'Y', 'O'])
        for ang in (45, 135, 225, 315):
            FD.needle(c, cx, cy, ang, 8, 20, ['W', 'Y', 'm'])
        body = Canvas(FS_, FS_)
        FD.astroid(body, cx, cy, 24, 22, 0.55, 'W', 'Y')
        FD.astroid(body, cx, cy, 14, 13, 0.55, 'W', 'W')
        FD.disc(body, cx, cy, 5.0, 'W')
        FD.outline(body)
        c.blit(body, 0, 0)
    elif i == 2:
        FD.ring(c, cx, cy, 34, ['m', 'V'])
        FD.ring(c, cx, cy, 25, ['W', 'Y', 'O'])
        body = Canvas(FS_, FS_)
        FD.astroid(body, cx, cy, 13, 12, 0.55, 'W', 'Y')
        FD.outline(body)
        c.blit(body, 0, 0)
        for k in range(8):
            FD.needle(c, cx, cy, 22.5 + 45 * k, 29, 33, ['W', 'Y', 'O'])
    elif i == 3:
        FD.ring(c, cx, cy, 41, ['m'], gaps=[(35, 55), (125, 145), (215, 235), (305, 325)])
        FD.ring(c, cx, cy, 32, ['Y', 'O'], gaps=[(80, 100), (170, 190), (260, 280), (350, 10)])
        FD.sparkle(c, cx, cy, 4, 'W', 'Y')
        for k in range(8):
            FD.needle(c, cx, cy, 22.5 + 45 * k, 36, 39, ['Y', 'm'])
    elif i == 4:
        FD.ring(c, cx, cy, 44, ['m', 'V'], gaps=[(20, 70), (110, 160), (200, 250), (290, 340)])
        FD.ring(c, cx, cy, 37, ['O'], gaps=[(60, 120), (150, 210), (240, 300), (330, 30)])
        FD.sparkle(c, cx, cy, 2, 'Y', 'O')
        for (x, y, s) in ((cx - 26, cy - 30, 1), (cx + 28, cy + 24, 1), (cx + 30, cy - 26, 2)):
            FD.sparkle(c, x, y, s, 'W', 'm')
    elif i == 5:
        for k in range(4):
            for da in range(-12, 13, 2):
                aa = math.radians(90 * k + da)
                c.set(int(round(cx + 44 * math.cos(aa))), int(round(cy + 44 * math.sin(aa))),
                      C['V' if abs(da) > 7 else 'm'])
        for (x, y, s) in ((cx - 20, cy - 24, 1), (cx + 22, cy + 20, 1), (cx + 24, cy - 21, 2), (cx - 26, cy + 24, 1)):
            FD.sparkle(c, x, y, s, 'W', 'Y')
    else:
        for (x, y, s) in ((cx - 14, cy - 18, 1), (cx + 16, cy + 14, 0), (cx + 18, cy - 15, 1),
                          (cx - 18, cy + 17, 0), (cx, cy - 26, 0)):
            FD.sparkle(c, x, y, s, 'Y', 'm')
    return c


def parry_flash_strong():
    return [flash_frame(i) for i in range(7)]


# ------------------------------------------------------------------ parried projectile shatter (32x32)
SHW, SHC = 32, 16
SHATTER_DURATIONS_MS = [40, 50, 60, 70]
SHARD = ["KK.", "KTK", ".KK"]
SHARD_BIG = [".KK.", "KTrK", "KrpK", ".KK."]
SHARD_ANGLES = [-20, 35, 80, 125, 160, 215, 250, 305]


def shatter_frame(f):
    c = Canvas(SHW, SHW)
    cx = cy = SHC
    if f == 0:
        body = Canvas(SHW, SHW)
        FD.astroid(body, cx, cy, 9, 8, 0.55, 'W', 'Y')
        FD.disc(body, cx, cy, 2.0, 'W')
        FD.outline(body)
        c.blit(body, 0, 0)
        for ang in SHARD_ANGLES[::2]:
            FD.needle(c, cx, cy, ang, 9, 12, ['Y', 'O'])
    else:
        r = [0, 7.5, 11.5, 14.5][f]
        for k, ang in enumerate(SHARD_ANGLES):
            a = math.radians(ang)
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a) + [0, 0.5, 2.0, 4.0][f]))
            spal = {'K': C['K'], 'T': C['T'], 'r': C['r'], 'p': C['p']}
            if f == 1:
                stamp(c, SHARD_BIG if k % 2 == 0 else SHARD, x - 2, y - 2, spal)
            elif f == 2:
                stamp(c, SHARD, x - 1, y - 1, spal)
            else:
                c.set(x, y, C['r'])
                c.set(x + 1, y, C['p'])
        if f == 1:
            body = Canvas(SHW, SHW)
            FD.astroid(body, cx, cy, 5, 4.5, 0.55, 'W', 'Y')
            FD.outline(body)
            c.blit(body, 0, 0)
            for ang in SHARD_ANGLES[1::2]:
                FD.needle(c, cx, cy, ang, 4, 6, ['W', 'Y'])
        elif f == 2:
            FD.sparkle(c, cx, cy, 2, 'Y', 'O')
        else:
            FD.sparkle(c, cx, cy - 1, 1, 'O', 'r')
    return c


def parry_shatter():
    return [shatter_frame(f) for f in range(4)]


def build():
    out = dict(popups())
    out['streak_digits'] = streak_digits()
    return out


if __name__ == '__main__':
    A = build()
    for name, frames in A.items():
        s = strip(frames)
        print(name, s.w, s.h, 'non-DB32', s.colours() - DB32)
        save_zoom(s, work('%s_8x.png' % name), 8, bg=(70, 70, 90), grid=(frames[0].w, frames[0].h))
    badge = streak_badge()
    sheet = grid_sheet(badge)
    print('streak_badge', sheet.w, sheet.h, 'non-DB32', sheet.colours() - DB32)
    save_zoom(sheet, work('streak_badge_8x.png'), 8, bg=(70, 70, 90), grid=(BW, BH))
    for n, fr, z in (('parry_flash_strong', parry_flash_strong(), 4), ('parry_shatter', parry_shatter(), 8)):
        s = strip(fr)
        print(n, s.w, s.h, 'non-DB32', s.colours() - DB32)
        save_zoom(s, work('%s_z.png' % n), z, bg=(136, 180, 99), grid=(fr[0].w, fr[0].h))
