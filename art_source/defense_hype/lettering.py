"""Popup words and the HYPE label, in the approved qte_mash_text / qte_full_text recipe:
bold 11-row italic glyphs (3 px strokes), 8-neighbour black outline, colour bands with checker dither,
a light top/left rim, a short glint, and a 2-3 px extrusion attached under the fill.
Frame 0 rests, frame 1 pops up 1 px, brightens and deepens the extrusion (exactly like MASH!/FULL!)."""
import sys
sys.dont_write_bytecode = True
from dh_common import *

K = C['K']

GLYPHS = {
    # --- copied from the approved qte text (MASH! / FULL!) ---
    'M': ["XXX.....XXX", "XXXX...XXXX", "XXXXX.XXXXX", "XXXXXXXXXXX", "XXX.XXX.XXX", "XXX..X..XXX",
          "XXX.....XXX", "XXX.....XXX", "XXX.....XXX", "XXX.....XXX", "XXX.....XXX"],
    'A': ["...XXXX...", "..XXXXXX..", ".XXX..XXX.", "XXX....XXX", "XXX....XXX", "XXXXXXXXXX",
          "XXXXXXXXXX", "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXX....XXX"],
    'S': [".XXXXXXXX.", "XXXXXXXXXX", "XXX.......", "XXX.......", "XXXXXXXXX.", ".XXXXXXXXX",
          ".......XXX", ".......XXX", "XXX....XXX", "XXXXXXXXXX", ".XXXXXXXX."],
    'H': ["XXX....XXX", "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXXXXXXXXX", "XXXXXXXXXX",
          "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXX....XXX"],
    '!': ["XXX", "XXX", "XXX", "XXX", "XXX", "XXX", ".X.", "...", "...", "XXX", "XXX"],
    'F': ["XXXXXXXXX", "XXXXXXXXX", "XXX......", "XXX......", "XXXXXXX..", "XXXXXXX..", "XXX......",
          "XXX......", "XXX......", "XXX......", "XXX......"],
    'U': ["XXX....XXX", "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXX....XXX",
          "XXX....XXX", "XXX....XXX", "XXXX..XXXX", "XXXXXXXXXX", ".XXXXXXXX."],
    'L': ["XXX......", "XXX......", "XXX......", "XXX......", "XXX......", "XXX......", "XXX......",
          "XXX......", "XXX......", "XXXXXXXXX", "XXXXXXXXX"],
    # --- new glyphs in the same construction ---
    'P': ["XXXXXXXXX.", "XXXXXXXXXX", "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXXXXXXXXX",
          "XXXXXXXXX.", "XXX.......", "XXX.......", "XXX.......", "XXX......."],
    'R': ["XXXXXXXXX.", "XXXXXXXXXX", "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXXXXXXXXX",
          "XXXXXXXXX.", "XXX..XXX..", "XXX...XXX.", "XXX....XXX", "XXX....XXX"],
    'Y': ["XXX....XXX", "XXX....XXX", "XXX....XXX", "XXXX..XXXX", ".XXXXXXXX.", "..XXXXXX..",
          "...XXXX...", "...XXXX...", "...XXXX...", "...XXXX...", "...XXXX..."],
    'E': ["XXXXXXXXX", "XXXXXXXXX", "XXX......", "XXX......", "XXXXXXX..", "XXXXXXX..", "XXX......",
          "XXX......", "XXX......", "XXXXXXXXX", "XXXXXXXXX"],
    'C': [".XXXXXXXX.", "XXXXXXXXXX", "XXX....XXX", "XXX.......", "XXX.......", "XXX.......",
          "XXX.......", "XXX.......", "XXX....XXX", "XXXXXXXXXX", ".XXXXXXXX."],
    'T': ["XXXXXXXXX", "XXXXXXXXX", "...XXX...", "...XXX...", "...XXX...", "...XXX...", "...XXX...",
          "...XXX...", "...XXX...", "...XXX...", "...XXX..."],
    'G': [".XXXXXXXX.", "XXXXXXXXXX", "XXX....XXX", "XXX.......", "XXX.......", "XXX..XXXXX",
          "XXX..XXXXX", "XXX....XXX", "XXX....XXX", "XXXXXXXXXX", ".XXXXXXXX."],
    'D': ["XXXXXXXX..", "XXXXXXXXX.", "XXX...XXXX", "XXX....XXX", "XXX....XXX", "XXX....XXX",
          "XXX....XXX", "XXX....XXX", "XXX...XXXX", "XXXXXXXXX.", "XXXXXXXX.."],
    'B': ["XXXXXXXXX.", "XXXXXXXXXX", "XXX....XXX", "XXX....XXX", "XXXXXXXXX.", "XXXXXXXXX.",
          "XXX....XXX", "XXX....XXX", "XXX....XXX", "XXXXXXXXXX", "XXXXXXXXX."],
    'K': ["XXX....XXX", "XXX...XXX.", "XXX..XXX..", "XXX.XXX...", "XXXXXX....", "XXXXXX....",
          "XXX.XXX...", "XXX..XXX..", "XXX...XXX.", "XXX....XXX", "XXX....XXX"],
    ' ': ["..", "..", "..", "..", "..", "..", "..", "..", "..", "..", ".."],
}
SLANT = [2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0]

# small 7-row glyphs (2 px strokes) for the HUD label
SMALL = {
    'H': ["XX..XX", "XX..XX", "XX..XX", "XXXXXX", "XX..XX", "XX..XX", "XX..XX"],
    'Y': ["XX..XX", "XX..XX", "XXXXXX", ".XXXX.", "..XX..", "..XX..", "..XX.."],
    'P': ["XXXXX.", "XX..XX", "XX..XX", "XXXXX.", "XX....", "XX....", "XX...."],
    'E': ["XXXXX", "XX...", "XX...", "XXXX.", "XX...", "XX...", "XXXXX"],
}
SMALL_SLANT = [1, 1, 1, 1, 0, 0, 0]


# colour schemes: (bands, dither rows, extrusion by depth, rim colour rows<=5, rim colour rows 6-7)
def _s(bands, dith, ext, rim_hi, rim_lo, glint='W'):
    return {'bands': [C[b] if b != '.' else None for b in bands],
            'dith': {k: (C[a], C[b]) for k, (a, b) in dith.items()},
            'ext': [C[e] for e in ext], 'rim_hi': C[rim_hi], 'rim_lo': C[rim_lo], 'glint': C[glint]}


SCHEMES = {
    # approved MASH!/FULL! look, kept for side-by-side checks
    'gold': (_s("YYYY.TTT.DD", {4: 'YT', 8: 'TD'}, 'or', 'W', 'S'),
             _s("WWW.YYYY.TT", {3: 'WY', 8: 'YT'}, 'orp', 'W', 'S')),
    # PARRY! bright white-gold (MASH!'s olive/brown extrusion so it sits in the same family)
    'parry': (_s("WWWW.YYY.TT", {4: 'WY', 8: 'YT'}, 'or', 'W', 'W'),
              _s("WWWWWW.YYYY", {6: 'WY'}, 'Tor', 'W', 'W')),
    # PERFECT! cyan, teal/navy extrusion
    'perfect': (_s("WWW.CCCC.bb", {3: 'WC', 8: 'Cb'}, 'un', 'W', 'P'),
                _s("WWWWW.CC.CC", {5: 'WC', 8: 'CC'}, 'bun', 'W', 'W')),
    # GUARD BREAK! red, flashing hot
    'guard': (_s("eee.EEEE.EE", {3: 'eE', 8: 'EE'}, 'rp', 'S', 'e'),
              _s("YYY.OOOO.ee", {3: 'YO', 8: 'Oe'}, 'Erp', 'W', 'Y')),
    # HYPE! gold into magenta, purple extrusion
    'hype': (_s("YYYY.mmm.VV", {4: 'Ym', 8: 'mV'}, 'pn', 'W', 'W'),
             _s("WWWW.YYY.mm", {4: 'WY', 8: 'Ym'}, 'Vpn', 'W', 'W')),
}


def word_canvas(word, scheme, bright, tw, th, glyphs=GLYPHS, slant=SLANT, gap=2, dx=0, oy_rest=2):
    """renders one frame of a word, centred in a tw x th canvas"""
    sc = SCHEMES[scheme][1 if bright else 0] if isinstance(scheme, str) else scheme
    gh = len(glyphs['H'])
    fill = set()
    x = 0
    for ch in word:
        g = glyphs[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == 'X':
                    fill.add((x + i + slant[j], j))
        x += len(g[0]) + gap
    width = max(p[0] for p in fill) + 1
    ox = (tw - width) // 2 + dx
    oy = oy_rest - (1 if bright else 0)
    pts = {(fx + ox, fy + oy) for (fx, fy) in fill}
    c = Canvas(tw, th)
    ext = {}
    for k in range(1, len(sc['ext']) + 1):
        col = sc['ext'][k - 1]
        for (px_, py_) in pts:
            q = (px_, py_ + k)
            if q not in pts and q not in ext:
                ext[q] = col
    body = pts | set(ext)
    for (px_, py_) in body:
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                q = (px_ + ddx, py_ + ddy)
                if q not in body:
                    c.set(q[0], q[1], K)
    for q, col in ext.items():
        c.set(q[0], q[1], col)
    bands, dith = sc['bands'], sc['dith']
    # bands are authored for 11 rows; small glyphs sample them proportionally
    for (px_, py_) in pts:
        gy = py_ - oy
        by = gy if gh == 11 else min(10, int(round(gy * 10.0 / (gh - 1))))
        if by in dith:
            a, b = dith[by]
            col = a if (px_ + py_) % 2 == 0 else b
        else:
            col = bands[by]
        up = (px_, py_ - 1) not in pts
        left = (px_ - 1, py_) not in pts
        if (up or left) and by <= 7:
            col = sc['rim_hi'] if by <= 5 else sc['rim_lo']
        c.set(px_, py_, col)
    for (px_, py_) in pts:
        gy = py_ - oy
        glint_row = 2 if gh == 11 else 1
        if gy == glint_row and (px_ + 1, py_ - 1) in pts and (px_ - 1, py_) in pts and (px_ - 2, py_) not in pts:
            c.set(px_, py_, sc['glint'])
            c.set(px_ + 1, py_ - 1, sc['glint'])
    return c


def word_width(word, glyphs=GLYPHS, slant=SLANT, gap=2):
    x = 0
    for ch in word:
        x += len(glyphs[ch][0]) + gap
    return x - gap + max(slant)


if __name__ == '__main__':
    for w in ['PARRY!', 'PERFECT!', 'GUARD BREAK!', 'HYPE!', 'MASH!']:
        print(w, word_width(w))
    print('HYPE small', word_width('HYPE', SMALL, SMALL_SLANT, 1))
