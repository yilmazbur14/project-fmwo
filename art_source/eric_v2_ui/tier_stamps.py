"""Tier stamps for the tiered mash, in the MASH!/PARRY! recipe (art_source/defense_hype/lettering.py):
italic glyphs, an 8-neighbour black outline, colour bands with checker dither, a light top/left rim, a
glint and an extrusion under the fill. Frame 0 rests; frame 1 pops up a texel, brightens and deepens
the extrusion.

  qte_tier_1        2 x 40x22   "1!"    bar 1's blue
  qte_tier_2        2 x 40x22   "2!!"   bar 2's cyan-white
  qte_tier_3        2 x 40x22   "3!!!"  bar 3's gold, sparks on the pop
  knight_breaker    2 x 160x20  "KNIGHT BREAKER!"  the tier-3 special's name

The numerals use a taller 15-row set with 4-texel strokes: at the words' 11 rows "1!" would be 45 px
wide on screen, too small to register mid-mash. KNIGHT BREAKER! uses the words' own 11-row glyphs,
plus N and I drawn in the same construction."""
import sys
sys.dont_write_bytecode = True
from ev2_common import *

# ---------------------------------------------------------------- 11-row glyphs: the kit's, plus N and I
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
GLYPHS['I'] = ["XXX"] * 11

# ---------------------------------------------------------------- 15-row numerals, 4-texel strokes
BIG = {
    'H': ["X"] * 15,          # word_canvas reads the glyph height off 'H'
    '1': ["...XXXX...",
          "..XXXXX...",
          ".XXXXXX...",
          "XXXXXXX...",
          "XX.XXXX...",
          "...XXXX...",
          "...XXXX...",
          "...XXXX...",
          "...XXXX...",
          "...XXXX...",
          "...XXXX...",
          "...XXXX...",
          "...XXXX...",
          "XXXXXXXXXX",
          "XXXXXXXXXX"],
    '2': [".XXXXXXXXXX.",
          "XXXXXXXXXXXX",
          "XXXX....XXXX",
          "XXXX....XXXX",
          "........XXXX",
          "........XXXX",
          "......XXXXX.",
          "....XXXXXX..",
          "..XXXXXX....",
          ".XXXXX......",
          "XXXXX.......",
          "XXXX........",
          "XXXX........",
          "XXXXXXXXXXXX",
          "XXXXXXXXXXXX"],
    '3': ["XXXXXXXXXXXX",
          "XXXXXXXXXXXX",
          "........XXXX",
          ".......XXXX.",
          "......XXXX..",
          ".....XXXXX..",
          ".....XXXXXX.",
          "........XXXX",
          "........XXXX",
          "........XXXX",
          "........XXXX",
          "XXXX....XXXX",
          "XXXX....XXXX",
          "XXXXXXXXXXXX",
          ".XXXXXXXXXX."],
    '!': ["XXXX"] * 9 + [".XX.", "....", "....", "XXXX", "XXXX", "XXXX"],
}
BIG_SLANT = [3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0]

S = LT._s
# bar 1 blue, bar 2 cyan into white, bar 3 gold: the same colours as the meter's three windows
SCHEMES = {
    'tier1': (S("WWW.bbbb.BB", {3: 'Wb', 8: 'bB'}, 'In', 'W', 'P'),
              S("WWWWW.bb.bb", {5: 'Wb', 8: 'bb'}, 'BIn', 'W', 'W')),
    'tier2': (S("WWWW.CCC.bb", {4: 'WC', 8: 'Cb'}, 'Bn', 'W', 'W'),
              S("WWWWWW.CC.C", {6: 'WC', 9: 'CC'}, 'bBn', 'W', 'W')),
    'tier3': (S("WWW.YYYY.OO", {3: 'WY', 8: 'YO'}, 'rp', 'W', 'W'),
              S("WWWWW.YYY.O", {5: 'WY', 9: 'YO'}, 'Erp', 'W', 'W')),
    # Knight Breaker: gold with a crimson extrusion, Eric's own red cross under the player's gold
    'knight': (S("WWW.YYYY.TT", {3: 'WY', 8: 'YT'}, 'Erp', 'W', 'W'),
               S("WWWWW.YYY.T", {5: 'WY', 9: 'YT'}, 'eErp', 'W', 'W')),
}

TIER_W, TIER_H = 40, 22
KB_W, KB_H = 160, 20
TIER_MS = [90, 90]
KB_MS = [80, 80]
TIER_WORDS = {1: '1!', 2: '2!!', 3: '3!!!'}


def tier_frames(tier):
    out = []
    for bright in (False, True):
        c = LT.word_canvas(TIER_WORDS[tier], SCHEMES['tier%d' % tier][1 if bright else 0], bright,
                           TIER_W, TIER_H, glyphs=BIG, slant=BIG_SLANT, gap=2, oy_rest=2)
        if tier == 3 and bright:
            for (x, y, s) in [(1, 3, 1), (38, 2, 1), (2, 20, 0), (37, 21, 0)]:
                if c.get(x, y) is None:
                    sparkle(c, x, y, s, 'W', 'Y')
        out.append(c)
    return out


def knight_breaker_frames():
    out = []
    for bright in (False, True):
        c = LT.word_canvas('KNIGHT BREAKER!', SCHEMES['knight'][1 if bright else 0], bright, KB_W, KB_H,
                           glyphs=GLYPHS)
        spots = [(3, 4, 1), (156, 3, 1), (79, 1, 0)] if bright else [(3, 4, 0), (156, 3, 0)]
        for (x, y, s) in spots:
            if c.get(x, y) is None:
                sparkle(c, x, y, s, 'W', 'Y')
        out.append(c)
    return out


def build():
    out = {'qte_tier_%d' % t: tier_frames(t) for t in (1, 2, 3)}
    out['knight_breaker'] = knight_breaker_frames()
    return out


if __name__ == '__main__':
    print('KNIGHT BREAKER! width', LT.word_width('KNIGHT BREAKER!', GLYPHS))
    for t in (1, 2, 3):
        print(TIER_WORDS[t], LT.word_width(TIER_WORDS[t], BIG, BIG_SLANT, 2))
    for name, frames in build().items():
        s = strip(frames)
        check_db32(s, name)
        print(name, len(frames), frames[0].w, frames[0].h, 'bbox', bbox(frames[0]), bbox(frames[1]))
