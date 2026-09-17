"""QTE mash-prompt UI art (DB32 only, alpha 0/255).
  qte_key_q / qte_key_w : 2 frames of 32x32 (0 normal = the approved controls keycap, 1 pressed + lit)
  qte_mash_text         : 2 frames of 64x20 ("MASH!", pulse)
  qte_full_text         : 2 frames of 64x20 ("FULL!", flash)
  qte_meter_frame       : 72x16 brass bar, 9-slice margins L8 T6 R8 B6
  qte_meter_fill        : 58x6 heat gradient (blue -> cyan -> white -> gold), sits at (7, 5) inside the frame
  qte_meter_full        : 2 frames of 72x16, the whole meter flashing when full
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import Canvas, from_png, strip, save_zoom, DB32
from paths import PROJ, work

K = '000000'; N0 = '222034'; P0 = '45283c'; BR = '663931'; BR2 = '8f563b'
TN = 'd9a066'; SK = 'eec39a'; YL = 'fbf236'; GO = '8a6f30'; OL = '524b24'
IN = '3f3f74'; RB = '5b6ee1'; SB = '639bff'; CY = '5fcde4'; WH2 = 'cbdbfc'; WH = 'ffffff'
G5 = '9badb7'; G4 = '847e87'; G3 = '696a6a'; G2 = '595652'


# ------------------------------------------------------------------ keycaps
def keycap_frames(name):
    base = from_png(PROJ + 'Assets/UI/%s.png' % name)
    f0 = base.copy()
    f1 = Canvas(32, 32)
    # top part (outline top .. face bottom shade row 23) moves down 2px
    for y in range(1, 24):
        for x in range(32):
            f1.p[y + 2][x] = base.p[y][x]
    # front skirt compressed from 6 rows (24..29) to 4 rows (26..29)
    for ny, oy in ((26, 25), (27, 27), (28, 28), (29, 29), (30, 30)):
        for x in range(32):
            f1.p[ny][x] = base.p[oy][x]
    # light the top face (rows 4..24 after the shift, columns 4..27)
    lit = {WH: WH, WH2: YL, G5: TN}
    for y in range(4, 26):
        for x in range(4, 28):
            v = f1.p[y][x]
            if v in lit:
                f1.p[y][x] = lit[v]
    # face corner/rim: keep the white rim, glyph stays navy
    # press flash rays in the freed rows above the cap
    for (x, y) in [(8, 2), (7, 1), (15, 0), (16, 0), (15, 1), (16, 1), (23, 2), (24, 1)]:
        f1.set(x, y, YL)
    return [f0, f1]


# ------------------------------------------------------------------ text
GLYPHS = {
    'M': ["XXX.....XXX",
          "XXXX...XXXX",
          "XXXXX.XXXXX",
          "XXXXXXXXXXX",
          "XXX.XXX.XXX",
          "XXX..X..XXX",
          "XXX.....XXX",
          "XXX.....XXX",
          "XXX.....XXX",
          "XXX.....XXX",
          "XXX.....XXX"],
    'A': ["...XXXX...",
          "..XXXXXX..",
          ".XXX..XXX.",
          "XXX....XXX",
          "XXX....XXX",
          "XXXXXXXXXX",
          "XXXXXXXXXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX"],
    'S': [".XXXXXXXX.",
          "XXXXXXXXXX",
          "XXX.......",
          "XXX.......",
          "XXXXXXXXX.",
          ".XXXXXXXXX",
          ".......XXX",
          ".......XXX",
          "XXX....XXX",
          "XXXXXXXXXX",
          ".XXXXXXXX."],
    'H': ["XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXXXXXXXXX",
          "XXXXXXXXXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX"],
    '!': ["XXX",
          "XXX",
          "XXX",
          "XXX",
          "XXX",
          "XXX",
          ".X.",
          "...",
          "...",
          "XXX",
          "XXX"],
    'F': ["XXXXXXXXX",
          "XXXXXXXXX",
          "XXX......",
          "XXX......",
          "XXXXXXX..",
          "XXXXXXX..",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXX......"],
    'U': ["XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXX....XXX",
          "XXXX..XXXX",
          "XXXXXXXXXX",
          ".XXXXXXXX."],
    'L': ["XXX......",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXX......",
          "XXXXXXXXX",
          "XXXXXXXXX"],
}
SLANT = [2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0]   # per glyph row x shift (italic lean)
TW, TH = 64, 20


def text_canvas(word, bright):
    """menu-title recipe: black outline, white top/left rim, yellow -> tan -> dark gold bands with
    checker dither, white glint, and a two-step extrusion attached directly under the fill."""
    fill = set()
    x = 0
    for ch in word:
        g = GLYPHS[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == 'X':
                    fill.add((x + i + SLANT[j], j))
        x += len(g[0]) + 2
    width = max(p[0] for p in fill) + 1
    ox = (TW - width) // 2
    oy = 2 if not bright else 1
    depth = 2 if not bright else 3
    pts = {(fx + ox, fy + oy) for (fx, fy) in fill}
    c = Canvas(TW, TH)
    ext = {}
    for k in range(1, depth + 1):
        col = [OL, BR, P0][min(k - 1, 2)]
        for (px_, py_) in pts:
            q = (px_, py_ + k)
            if q not in pts and q not in ext:
                ext[q] = col
    body = pts | set(ext)
    for (px_, py_) in body:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (px_ + dx, py_ + dy)
                if q not in body:
                    c.set(q[0], q[1], K)
    for q, col in ext.items():
        c.set(q[0], q[1], col)
    if bright:
        bands = [WH, WH, WH, None, YL, YL, YL, YL, None, TN, TN]
        dith = {3: (WH, YL), 8: (YL, TN)}
    else:
        bands = [YL, YL, YL, YL, None, TN, TN, TN, None, GO, GO]
        dith = {4: (YL, TN), 8: (TN, GO)}
    for (px_, py_) in pts:
        gy = py_ - oy
        if gy in dith:
            a, b = dith[gy]
            col = a if (px_ + py_) % 2 == 0 else b
        else:
            col = bands[gy]
        up = (px_, py_ - 1) not in pts
        left = (px_ - 1, py_) not in pts
        if (up or left) and gy <= 7:
            col = WH if gy <= 5 else SK
        c.set(px_, py_, col)
    # short diagonal glint on the upper-left of each glyph stroke
    for (px_, py_) in pts:
        gy = py_ - oy
        if gy == 2 and (px_ + 1, py_ - 1) in pts and (px_ - 1, py_) in pts and (px_ - 2, py_) not in pts:
            c.set(px_, py_, WH)
            c.set(px_ + 1, py_ - 1, WH)
    return c


def word_frames(word):
    """frame 0: resting; frame 1: popped up 1px, brighter, deeper extrusion"""
    return [text_canvas(word, False), text_canvas(word, True)]


# ------------------------------------------------------------------ meter
MW, MH = 72, 16
ML, MT, MR, MB = 8, 6, 8, 6


def meter_frame(lit=False):
    c = Canvas(MW, MH)
    y_hi, tn, go, ol, sk = (WH, YL, TN, GO, WH) if lit else (YL, TN, GO, OL, SK)
    top = [K, y_hi, tn, go, K, K]                 # rows 0..5 (5 = inner shadow)
    bot = [IN, K, tn, go, ol, K]                  # rows 10..15 (10 = inner reflected light)
    left = [K, y_hi, sk, tn, tn, go, K, K]        # cols 0..7 (7 = inner shadow)
    right = [IN, K, sk, tn, tn, go, ol, K]        # cols 64..71
    for y in range(MH):
        for x in range(MW):
            col = N0
            if y < MT:
                col = top[y]
            elif y >= MH - MB:
                col = bot[y - (MH - MB)]
            if x < ML and MT <= y < MH - MB:
                col = left[x]
            elif x >= MW - MR and MT <= y < MH - MB:
                col = right[x - (MW - MR)]
            c.p[y][x] = col
    # corners: caps overlap the tube rows; build end caps explicitly (constant along y inside margins
    # is already guaranteed above; corners are free-form)
    for y in range(MT):
        for x in range(ML):
            c.p[y][x] = top[y] if x > y else left[x]
        for x in range(MW - MR, MW):
            k = x - (MW - MR)
            c.p[y][x] = top[y] if (MR - 1 - k) > y else right[k]
    for yy in range(MB):
        y = MH - MB + yy
        for x in range(ML):
            c.p[y][x] = bot[yy] if x > (MB - 1 - yy) else left[x]
        for x in range(MW - MR, MW):
            k = x - (MW - MR)
            c.p[y][x] = bot[yy] if (MR - 1 - k) > (MB - 1 - yy) else right[k]
    # inner corner consistency: inner outline ring
    for x in range(6, MW - 6):
        c.p[4][x] = K
        c.p[11][x] = K
    for y in range(4, 12):
        c.p[y][6] = K
        c.p[y][MW - 7] = K
    # chamfer outer corners (transparent + outline step)
    for (x, y) in [(0, 0), (1, 0), (0, 1), (MW - 1, 0), (MW - 2, 0), (MW - 1, 1),
                   (0, MH - 1), (1, MH - 1), (0, MH - 2), (MW - 1, MH - 1), (MW - 2, MH - 1), (MW - 1, MH - 2)]:
        c.p[y][x] = None
    for (x, y) in [(1, 1), (MW - 2, 1), (1, MH - 2), (MW - 2, MH - 2)]:
        c.p[y][x] = K
    # rivets on the end caps (inside the margin columns, rows 6..9 -> must stay constant along y for
    # 9-slice: rivets are placed in the corner zones instead, on the cap faces at rows 1..4 / 11..14)
    plate = [
        "KKKKKK",
        "K1112K",
        "K1ab4K",
        "K1cd4K",
        "K2445K",
        "KKKKKK",
    ]
    pal = {'K': K, '1': YL, '2': SK, '4': GO, '5': OL, 'a': WH, 'b': YL, 'c': BR2, 'd': P0}
    if lit:
        pal.update({'1': WH, '2': WH, '4': TN, '5': GO, 'c': TN})
    for (px0, py0) in [(0, 0), (MW - 6, 0), (0, MH - 6), (MW - 6, MH - 6)]:
        for j, row in enumerate(plate):
            for i, ch in enumerate(row):
                c.p[py0 + j][px0 + i] = pal[ch]
    for (x, y) in [(0, 0), (MW - 1, 0), (0, MH - 1), (MW - 1, MH - 1)]:
        c.p[y][x] = None
    return c


def meter_fill(mode='gradient', w=58, h=6):
    """mode: 'gradient' (heat ramp), 'hot' (all white-hot), 'gold' (all gold)"""
    c = Canvas(w, h)
    ramps = [  # (highlight, base, shade) per band
        (SB, RB, IN),
        (CY, SB, RB),
        (WH2, CY, SB),
        (WH, WH2, CY),
        (WH, YL, TN),
    ]
    edges = [11, 22, 34, 46]
    for x in range(w):
        band = sum(1 for e in edges if x >= e)
        # 2-column checker dither into the next band
        if band < 4 and x in (edges[band] - 2, edges[band] - 1):
            nb = band + 1
        else:
            nb = band
        for y in range(h):
            b = band
            if nb != band and (x + y) % 2 == 0:
                b = nb
            hi, base, sh = ramps[b]
            if mode == 'hot':
                hi, base, sh = WH, WH, WH2
            elif mode == 'gold':
                hi, base, sh = WH, YL, TN
            col = hi if y == 0 else (sh if y == h - 1 else base)
            c.p[y][x] = col
    return c


def meter_full_frames():
    f0 = meter_frame(lit=True)
    hot = meter_fill('hot')
    f0.blit(hot, ML - 1, MT - 1)
    for (x, y) in [(12, 7), (30, 6), (51, 8)]:
        f0.set(x, y, YL)
    f1 = meter_frame(lit=False)
    f1.blit(meter_fill('gold'), ML - 1, MT - 1)
    return [f0, f1]


def check_nine_slice(c, l, t, r, b):
    probs = []
    for y in range(c.h):
        vals = set(c.p[y][x] for x in range(l, c.w - r))
        if len(vals) != 1:
            probs.append('row %d not uniform across centre' % y)
    for x in range(c.w):
        vals = set(c.p[y][x] for y in range(t, c.h - b))
        if len(vals) != 1:
            probs.append('col %d not uniform down centre' % x)
    return probs


def build():
    out = {}
    out['qte_key_q'] = keycap_frames('key_q')
    out['qte_key_w'] = keycap_frames('key_w')
    out['qte_mash_text'] = word_frames('MASH!')
    out['qte_full_text'] = word_frames('FULL!')
    out['qte_meter_frame'] = [meter_frame()]
    out['qte_meter_fill'] = [meter_fill()]
    out['qte_meter_full'] = meter_full_frames()
    return out


if __name__ == '__main__':
    A = build()
    print('9-slice probs:', check_nine_slice(A['qte_meter_frame'][0], ML, MT, MR, MB))
    for name, frames in A.items():
        s = strip(frames)
        s.save(work('ui_%s.png' % name))
        save_zoom(s, work('ui_%s_8x.png' % name), 8, bg=(70, 70, 90), grid=(frames[0].w, frames[0].h))
        cols = s.colours()
        bad = [v for v in cols if v not in DB32]
        print(name, s.w, s.h, 'non-DB32:', bad)
