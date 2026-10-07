"""HOME RUN! in the approved popup recipe (art_source/defense_hype/lettering.py, the one PARRY!,
GUARD BREAK! and KNIGHT BREAKER! are built with): bold 11-row italic glyphs with 3 px strokes, an
8-neighbour black outline, colour bands with checker dither, a light top/left rim, a glint and an
extrusion under the fill. Frame 0 rests; frame 1 pops up a texel, brightens and deepens the
extrusion, exactly like the others.

Glyphs: H M E R U come from the kit, N is tier_stamps.py's (built for KNIGHT BREAKER!), and O is new,
drawn in the same construction as the kit's C, D and G.
Scheme: white into gold into orange over a red extrusion - KNIGHT BREAKER!'s gold family, pushed hot
(orange where it has tan), with the ball's red stitching under it.
"""
import os
import sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('DH_WORK', os.path.join(HERE, '_dh_work'))
sys.path.insert(0, HERE)
from dh_common import Canvas, C   # noqa: E402
import lettering as LT             # noqa: E402

GLYPHS = dict(LT.GLYPHS)
GLYPHS['N'] = ["XXXX...XXX",
               "XXXXX..XXX",
               "XXXXX..XXX",
               "XXX.XX.XXX",
               "XXX.XX.XXX",
               "XXX..XXXXX",
               "XXX..XXXXX",
               "XXX...XXXX",
               "XXX...XXXX",
               "XXX....XXX",
               "XXX....XXX"]
GLYPHS['O'] = [".XXXXXXXX.",
               "XXXXXXXXXX",
               "XXX....XXX",
               "XXX....XXX",
               "XXX....XXX",
               "XXX....XXX",
               "XXX....XXX",
               "XXX....XXX",
               "XXX....XXX",
               "XXXXXXXXXX",
               ".XXXXXXXX."]

S = LT._s
SCHEME = (S("WWW.YYYY.OO", {3: 'WY', 8: 'YO'}, 'Erp', 'W', 'W'),
          S("WWWWW.YYY.O", {5: 'WY', 9: 'YO'}, 'eErp', 'W', 'W'))
# the alternative: baseball white with red stitching under it
ALT_SCHEME = (S("WWWW.PPP.ss", {4: 'WP', 8: 'Ps'}, 'Erp', 'W', 'W'),
              S("WWWWWW.PP.s", {6: 'WP', 9: 'Ps'}, 'eErp', 'W', 'W'))

WORD = 'HOME RUN!'
TW, TH = 104, 20


def sparkle(c, x, y, size, core='W', tip='Y'):
    c.set(x, y, C[core])
    for k in range(1, size + 1):
        col = C[core] if k < size else C[tip]
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.set(x + dx, y + dy, col)


def frames(scheme=SCHEME):
    out = []
    for bright in (False, True):
        c = LT.word_canvas(WORD, scheme[1 if bright else 0], bright, TW, TH, glyphs=GLYPHS)
        spots = [(2, 4, 1), (101, 3, 1), (51, 1, 0)] if bright else [(2, 4, 0), (101, 3, 0)]
        for (x, y, s) in spots:
            if c.get(x, y) is None:
                sparkle(c, x, y, s)
        out.append(c)
    return out


if __name__ == '__main__':
    print('width', LT.word_width(WORD, GLYPHS), 'canvas', TW, TH)
