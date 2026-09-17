"""victory_banner: chat-embed notification frame, built as the SAME component as the defeat
screen's banner (42x40, accent bar on the left, round mascot avatar with a status badge) in
victory colours: navy panel, gold accent bar, green 'online' badge.
9-slice margins (1x): L=32 T=30 R=4 B=4. Centre is flat navy.
python banner.py outdir"""
import sys, math
from cv import *

W, H = 42, 40
ML, MT, MR, MB = 32, 30, 4, 4

GRID = [
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "abccadddddddddddddddddddddddddddddddddddda",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeaaaaaaaaeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeaaffffffffaaeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeaffffffffffffaeeeeeeeeeeeeeeea",
    "abccaeeeeeeaffffffffffffffaeeeeeeeeeeeeeea",
    "abccaeeeeeaffffffffffffffffaeeeeeeeeeeeeea",
    "abccaeeeeafffffffffffffffffgaeeeeeeeeeeeea",
    "abccaeeeeafffffffffffffffffgaeeeeeeeeeeeea",
    "abccaeeeafffffhhhfffffhhhfffgaeeeeeeeeeeea",
    "abccaeeeaffffhhhhhhhhhhhhhffgaeeeeeeeeeeea",
    "abccaeeeafffhhhhhhhhhhhhhhhfgaeeeeeeeeeeea",
    "abccaeeaffffhhhhhhhhhhhhhhhfggaeeeeeeeeeea",
    "abccaeeaffffhhhhiihhhiihhhhgggaeeeeeeeeeea",
    "abccaeeaffffhhhhiihhhiihhhhgggaeeeeeeeeeea",
    "abccaeeaffffhhhhiihhhiihhhhgggaeeeeeeeeeea",
    "abccaeeeafffhhhhhhhhhhhhhhhggaeeeeeeeeeeea",
    "abccaeeeafffhhhhhhhhhhhhhhhggaeeeeeeeeeeea",
    "abccaeeeaffffhhhhhhhhhhhhheeeeeeeeeeeeeeea",
    "abccaeeeeaffffhhhhfffhhheeaaaaeeeeeeeeeeea",
    "abccaeeeeafffffffffffffeeaMMMMaeeeeeeeeeea",
    "abccaeeeeeafffffffffffgeaMLLMMMaeeeeeeeeea",
    "abccaeeeeeeaffffffffgggeaMLMMMTaeeeeeeeeea",
    "abccaeeeeeeeaggggggggggeaMMMMTTaeeeeeeeeea",
    "abccaeeeeeeeeaaggggggggeaTMMTTTaeeeeeeeeea",
    "abccaeeeeeeeeeeaaaaaaaaeeaTTTTaeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeaaaaeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "abccaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeea",
    "aBCCajjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjja",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
]

PAL = {
    'a': K,
    'b': YEL, 'c': TAN, 'B': TAN, 'C': BRASS,         # gold accent bar (defeat uses pink/red)
    'd': INDIGO,                                        # panel top highlight
    'e': NAVY,                                          # panel
    'j': K,                                             # panel bottom shade
    'f': WHITE, 'g': PALE, 'h': BLURPLE, 'i': WHITE,   # server icon house rule: WHITE circle, BLURPLE mascot
    'M': GREEN, 'L': LIME, 'T': TEAL,                   # online badge (defeat uses a red 'do not disturb')
}


def build():
    cv = Canvas(W, H)
    for y, row in enumerate(GRID):
        assert len(row) == W, (y, len(row))
        for x, ch in enumerate(row):
            if ch != '.':
                cv.set(x, y, PAL[ch])
    return cv


def check_nine(cv):
    probs = []
    ref = cv.get(ML, MT)
    for y in range(MT, H - MB):
        for x in range(ML, W - MR):
            if cv.get(x, y) != ref:
                probs.append(('centre', x, y))
    for y in list(range(0, MT)) + list(range(H - MB, H)):
        for x in range(ML, W - MR):
            if cv.get(x, y) != cv.get(ML, y):
                probs.append(('hband', x, y))
                break
    for x in list(range(0, ML)) + list(range(W - MR, W)):
        for y in range(MT, H - MB):
            if cv.get(x, y) != cv.get(x, MT):
                probs.append(('vband', x, y))
                break
    return probs


def nine(cv, WW, HH):
    out = Canvas(WW, HH)
    cw, ch = W - ML - MR, H - MT - MB
    CW, CH = WW - ML - MR, HH - MT - MB

    def mp(D, m0, sc, dc):
        if D < m0:
            return D
        if D >= m0 + dc:
            return D - (m0 + dc) + (m0 + sc)
        return m0 + min(sc - 1, (D - m0) * sc // dc)

    for Y in range(HH):
        for X in range(WW):
            out.set(X, Y, cv.get(mp(X, ML, cw, CW), mp(Y, MT, ch, CH)))
    return out


def x3(cv):
    out = Canvas(cv.w * 3, cv.h * 3)
    for y in range(cv.h):
        for x in range(cv.w):
            c = cv.get(x, y)
            for j in range(3):
                for i in range(3):
                    out.p[y * 3 + j][x * 3 + i] = c
    return out


if __name__ == '__main__':
    od = sys.argv[1].rstrip('/') + '/'
    cv = build()
    print('nine-slice problems:', check_nine(cv)[:10])
    cv.save(od + 'victory_banner.png')
    x3(cv).save(od + 'victory_banner_3x.png')
    nine(cv, 320, 46).save(od + 'victory_banner_320x46.png')
    print('ok')
