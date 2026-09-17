"""daze_stars: 6-frame loop of 48x24. Two stars and two little birds orbit an ellipse centred (24, 13).
Stars reuse the approved defeat-screen star sprites (big yellow in front, small tan behind).
30 degrees per frame; stars sit 180 apart and birds 180 apart, so the 6-frame loop is seamless."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import Canvas, strip, save_zoom, FX
from paths import work

FW, FH = 48, 24
CX, CY = 24, 13
RX, RY = 17, 5

PAL = {'K': '000000', 'Y': 'fbf236', 'T': 'd9a066', 'g': '8a6f30', 'W': 'ffffff',
       'B': '639bff', 'b': '5b6ee1', 'P': 'cbdbfc', 'O': 'df7126', 'n': '3f3f74'}

# approved defeat_stars.png sprites
STAR_BIG = [
    "....K....",
    "...KYK...",
    "KKKKYKKKK",
    "KYYWYYTTK",
    ".KYYYTTK.",
    "..KYYTK..",
    ".KYYKYTK.",
    ".KYK.KTK.",
    ".KK...KK.",
]
STAR_SMALL = [
    "...K...",
    "..KTK..",
    "KKKTKKK",
    "KTTTggK",
    ".KTTgK.",
    ".KTKTK.",
    ".KK.KK.",
]
# little bluebird facing LEFT, two wing poses (big = front of the orbit, small = back)
BIRD_UP = [
    "......KK.",
    ".....KBBK",
    "..KKKBBK.",
    ".KBWWKK..",
    "KOKKWBBKK",
    ".KPPBBBBK",
    "..KPPBBK.",
    "...KKKK..",
]
BIRD_DN = [
    ".........",
    "..KKKK...",
    ".KBWWBK..",
    "KOKKWBBKK",
    ".KPPBBBBK",
    "..KPPBPBK",
    "...KKKPK.",
    "......K..",
]
BIRD_SMALL_UP = [
    "...KK.",
    ".KKBK.",
    "KOWBBK",
    ".KPBBK",
    "..KKK.",
]
BIRD_SMALL_DN = [
    "......",
    ".KKKK.",
    "KOWBBK",
    ".KPBBK",
    "..KBK.",
    "...K..",
]


def flip(rows):
    return [r[::-1] for r in rows]


def stamp(c, rows, cx, cy, recolor=None):
    h, w = len(rows), len(rows[0])
    x0 = int(round(cx - w / 2.0))
    y0 = int(round(cy - h / 2.0))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            col = PAL[ch]
            if recolor and ch in recolor:
                col = PAL[recolor[ch]]
            c.set(x0 + i, y0 + j, col)


def frame(f):
    c = Canvas(FW, FH)
    items = []
    for k, kind in enumerate(['star', 'bird', 'star', 'bird']):
        a = math.radians(90 * k + 30 * f + 15)
        x = CX + RX * math.cos(a)
        y = CY + RY * math.sin(a)
        depth = math.sin(a)            # +1 front (lower), -1 back (higher)
        vx = -math.sin(a)              # direction of travel along x
        items.append((depth, kind, x, y, vx, k))
    items.sort()                       # back first
    for depth, kind, x, y, vx, k in items:
        big = depth > -0.35
        if kind == 'star':
            stamp(c, STAR_BIG if big else STAR_SMALL, x, y)
        else:
            wing_up = (f + k) % 2 == 0
            if big:
                spr = BIRD_UP if wing_up else BIRD_DN
            else:
                spr = BIRD_SMALL_UP if wing_up else BIRD_SMALL_DN
            if vx > 0:
                spr = flip(spr)
            if not big:
                stamp(c, spr, x, y, recolor={'B': 'b', 'P': 'B'})
            else:
                stamp(c, spr, x, y)
    return c


def build():
    return [frame(f) for f in range(6)]


if __name__ == '__main__':
    frames = build()
    s = strip(frames)
    s.save(work('daze_strip.png'))
    save_zoom(s, work('daze_8x.png'), 8, bg=(136, 180, 99), grid=(48, 24))
    print('ok')
