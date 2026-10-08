"""Jordan at his computer, seen from behind: the desk idle (4 frames, looping).

He sits hunched in his gaming chair with his headset on, elbows out at the keyboard and mouse,
nodding along to the game. The chair turns its back to the camera (yaw 0), so the backrest hides
his back below the shoulders; above it are his greasy quiff (seen from behind for the first time:
v2's hair vocabulary, the dark oily clumps, the wet shine band, the dandruff, the rat-tail, the
quiff's crest peeking over the crown), the headset, a thin neck, and the Peach tee's back and
drooping sleeves. His hands are on the desk beyond him, hidden by his own body from this angle;
the elbows and the head carry the motion.

  0  base
  1  a nod: head and headset a pixel down; the mouse elbow flicks out; the headset's light pulses
  2  back up; the keyboard elbow twitches (typing)
  3  a nod; the mouse elbow draws back in; the light pulses

Jordan's parts are drawn in the approved rig's 96-frame space and moved by jfc_base.OFF into the
128x128 frame; the chair is rendered straight into it (its floor contact on the anchor (64, 127)).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfc_base as B  # noqa: E402
import jfc_chair as C  # noqa: E402

NAME = 'jordan_desk_idle'
TIMES = [0.18, 0.14, 0.18, 0.14]
LOOP = True


#HAIR, FROM BEHIND (hand-authored; '.' transparent, the map carries its own keyline)

HX0, HY0 = 35, 6
HAIR = [
    # x: 35-39 40-44 45-49 50-54 55-59 60-61      y
    "..... ..... ..... ..... kk... ..",   # 6   the quiff's crest, peeking over the crown
    "..... ..... ..... ....k ljk.. ..",   # 7
    "..... ..... ..... ...kA ijk.. ..",   # 8   its wet shine, as on the approved quiff
    "..... ..... ..... .kkAY ihk.. ..",   # 9
    "..... ..... ...kk kAYli jhk.. ..",   # 10
    "..... ..... .kkjl AYlji hhk.. ..",   # 11
    "..... ...kk kjlAY ljhij hihk. ..",   # 12
    "..... .kkjl lAjhi jhijh ihhk. ..",   # 13  the crown: clumps fanning out from the whorl
    "....k kjlAl hljhi jhihh ihhik ..",   # 14
    "...kj lAljh ljhij hijhh ihhhk ..",   # 15
    "..kjl Alhjl jhijh ijhhi hhihk ..",   # 16
    "..kjA ljhlj hijhl ihhij hhihh k.",   # 17
    ".kjlA jhljh ijhli hjhij hihhh k.",   # 18  the wet shine runs round the lit side
    ".kjAY lhjlh ijlih jhijh ihhih k.",   # 19
    ".kjlA jhjlh ijlih jhWjh ihhih k.",   # 20  dandruff (W)
    ".kijl Ahjlh jilih jhijh hhhih k.",   # 21
    ".kijl jhAlh jilhh jhijh hhhih k.",   # 22
    ".kijj lhjAh jihjh ihijh hihhh k.",   # 23
    ".kiij lhjlh WihjA hhijh hihhh k.",   # 24
    ".khij jhjlh jihjl hhihh hihhh k.",   # 25
    ".khij jhilh jihjl hhihh hhhhh k.",   # 26
    ".khii jhilh jhhjl hhihh Whhhh k.",   # 27
    ".khii jhijh jhhil hhihh hhhhh k.",   # 28
    ".khii jhijh jhhil hhihh hhhhh k.",   # 29
    ".khii ihijh ihhil hhihh hhhhh k.",   # 30
    ".khii ihiWh ihhij hhihh hhhhh k.",   # 31
    ".khhi ihihh ihhij hhhhh hhhhh k.",   # 32
    "..khi ihihh ihhij hhhhh hhhhk ..",   # 33
    "..khi ihihh ihhij hhhhh hhhhk ..",   # 34
    "...kh ihihh ihhih hhhhh hhhk. ..",   # 35
    "...kh iiihh ihhih hhhhh hhhk. ..",   # 36
    "....k hiihh ihhih hhhhh hhk.. ..",   # 37
    "..... khihk hihkh hhkhk kk... ..",   # 38  the nape frays into greasy points
    "..... .kik. khk.k hk.k. ..... ..",   # 39
    "..... .kik. .k... k.... ..... ..",   # 40  the rat-tail hangs off the back, over the neck
    "..... ..kik ..... ..... ..... ..",   # 41
    "..... ..kik ..... ..... ..... ..",   # 42
    "..... ...k. ..... ..... ..... ..",   # 43
]


def hair(dy=0):
    rows = B.rows_of(HAIR)
    for i, r in enumerate(rows):
        if len(r) != 27:
            raise ValueError('back hair row %d is %d wide' % (HY0 + i, len(r)))
    return B.shift(B.amap(rows, HX0, HY0), 0, dy)


#THE HEADSET (charcoal, pink light rings: the chair's colours)

def band(dy=0, cx=48.0, cy=28.5, rx=12.3, ry=14.2, a0=196, a1=344):
    """The headband over the crown: a 2px arc, its top edge lit toward the light."""
    import math
    outer, inner = set(), set()
    for i in range(1000):
        t = math.radians(a0 + (a1 - a0) * i / 999.0)
        for r, s in ((1.0, outer), (0.9, inner)):
            outer_x = cx + rx * r * math.cos(t)
            outer_y = cy + ry * r * math.sin(t)
            s.add((int(math.floor(outer_x)), int(math.floor(outer_y))))
    part = {q: '1' for q in inner}
    for q in outer:
        part[q] = '3' if q[0] < cx + 3 else '2'
    return B.shift(part, 0, dy)


CUP = [
    ".2222.",
    "233322",
    "232221",
    "232221",
    "232221",
    "232221",
    "232221",
    "232221",
    "222221",
    "222211",
    ".1111.",
]


def cup(side, dy=0, pulse=False):
    """An ear cup seen from behind: a rounded block, its pink light ring showing as a strip down
    the outer rim (lit on the left cup, in shade low on the right one). `pulse` brightens the ring a
    step (the headset's light breathing with the game)."""
    x0, y0 = (31, 24) if side < 0 else (60, 24)
    rows = B.rows_of(CUP)
    part = B.amap(rows, x0, y0)
    if side > 0:
        part = {(2 * x0 + 5 - x, y): k for (x, y), k in part.items()}
    edge = x0 if side < 0 else x0 + 5
    for y in range(y0 + 1, y0 + 10):
        if side < 0:
            part[(edge, y)] = 'Q' if (y < y0 + 4 or pulse) else 'P'
        else:
            part[(edge, y)] = ('Q' if y < y0 + 4 else 'P') if pulse else ('P' if y < y0 + 7 else 'q')
    return B.shift(part, 0, dy)


#NECK, TEE AND ARMS

def neck(dy=0):
    """The back of a thin neck in the hair's shadow, the knob of his spine at its base."""
    n = B.fill(B.poly([(45.4, 36), (50.4, 36), (50.8, 45), (45.2, 45)]), 'b')
    B.rim(n, 'c', -1, 0)
    B.rim(n, 'a', 1, 0)
    for (x, y) in list(n):
        if y <= 41:
            n[(x, y)] = 'a' if (x + 1, y) not in n else 'b'
    n[(48, 44)] = 'd'
    n[(48, 43)] = 'c'
    return B.shift(n, 0, dy)


# The tee's back above the chair, SKINNY (the user, 2026-09-28: approved "the skinnier one"; the FITTED
# tee before it, the same day): narrow sloped shoulders down to the sleeves, then in to the same 15px
# chest as the fight sheets (build x 42..56, i.e. frame 41..55, centred on his column 48), the collar
# trim round the neck; short sleeves hugging the tops of his thinner stick arms. The fitted back was a
# 19px column (frame 39..57): git history.
TEE = [(43.0, 43.6), (53.0, 43.6), (56.0, 44.6), (57.0, 46.6), (55.5, 49.6), (55.4, 53), (40.6, 53),
       (40.5, 49.6), (39.0, 46.6), (40.0, 44.6)]
COLLAR = {44: 44, 45: 45, 46: 45, 47: 45, 48: 45, 49: 45, 50: 45, 51: 45, 52: 44}
DANDRUFF = {(41, 47): 'W', (45, 46): '9', (55, 47): 'W', (51, 48): 'W'}
SHOULDER = {-1: (38.6, 47.6), 1: (57.4, 47.6)}       # where each upper arm leaves the tee


def tee():
    part = B.fill(B.poly(TEE), 'R')
    for x, yc in COLLAR.items():
        for y in range(40, yc):
            part.pop((x, y), None)
    for (x, y) in list(part):
        lo, hi = B.span(part, y)
        t = (x - lo) / max(1, hi - lo)
        k = 'R'
        if t <= 0.08:
            k = 'T'
        elif t >= 0.9:
            k = 'v'
        elif t >= 0.7:
            k = 'V'
        elif 0.14 <= t <= 0.3 and y <= 48:
            k = 'T'
        part[(x, y)] = k
    for x, yc in COLLAR.items():
        part[(x, yc)] = '1'
    # fitted, the thin cloth shows his shoulder blades and the knobs of his spine
    for q in ((42, 49), (43, 50), (53, 49), (52, 50), (48, 47), (48, 49), (48, 51)):
        if q in part:
            part[q] = 'V'
    for q, k in DANDRUFF.items():
        if q in part:
            part[q] = k
    return part


def sleeve(side):
    """A short fitted sleeve round the top of the upper arm, the black trim at its hem (skinny: half a
    pixel tighter and shorter, as the fight sheets' sleeves)."""
    sx, sy = SHOULDER[side]
    if side < 0:
        pts = [(sx + 1.6, sy - 3.2), (sx - 1.6, sy - 1.6), (sx - 2.9, sy + 1.2), (sx - 2.6, sy + 3.8),
               (sx - 0.4, sy + 4.3), (sx + 1.0, sy + 2.0)]
        hem = [(sx - 2.8, sy + 3.3), (sx - 0.6, sy + 3.9)]
    else:
        pts = [(sx - 1.6, sy - 3.2), (sx + 1.6, sy - 1.6), (sx + 2.9, sy + 1.2), (sx + 2.6, sy + 3.8),
               (sx + 0.4, sy + 4.3), (sx - 1.0, sy + 2.0)]
        hem = [(sx + 2.8, sy + 3.3), (sx + 0.6, sy + 3.9)]
    s = B.fill(B.poly(pts), 'R')
    B.rim(s, 'T', -1, 0)
    B.rim(s, 'V', 1, 0)
    B.rim(s, 'v', 0, 1, only='RV')
    B.stroke(s, [(int(round(x)), int(round(y))) for (x, y) in hem], '1')
    return s


def arm(side, elbow_dx=0, elbow_dy=0):
    """A stick arm out of the sleeve, down and out to a bony elbow; the forearm turns forward (up the
    screen) toward the desk and goes behind the sleeve."""
    if side < 0:
        sh, el, fw = (36.4, 50.6), (30.4 + elbow_dx, 57.6 + elbow_dy), (34.0 + elbow_dx, 51.8)
        base, lit, shade = 'd', 'e', 'c'
    else:
        sh, el, fw = (59.6, 50.6), (65.6 + elbow_dx, 57.6 + elbow_dy), (62.0 + elbow_dx, 51.8)
        base, lit, shade = 'c', 'd', 'b'
    return B.limb([(sh, el, 1.5, 1.4), (el, fw, 1.4, 1.25)], knobs=((el[0], el[1], 1.8),),
                  base=base, lit=lit, shade=shade)


#THE FRAMES

def chair_parts(yaw=0):
    """The chair's solids, padded, as {name: (part, depth)}; and its painted decals."""
    out = {}
    for n, p, d in C.solids(yaw):
        if n in ('back', 'seat', 'pad-1', 'pad+1', 'bolster-1', 'bolster+1'):
            C.pad(p)
        out[n] = (p, d)
    return out, C.decals(yaw)


# Seated with his back to us he sits over the seat's back edge, hunched: his collar sits this much
# higher than the approved standing sprite's, which lines his head up with the talk poses' through the
# swivel (and rests his elbows on the armrest pads).
LIFT = -4


def _at(part):
    """Parts here are drawn in the approved rig's 96-frame space; move them into the 128 frame."""
    return B.shift(part, B.OFF[0], B.OFF[1] + LIFT)


def build(nod=0, elbow_l=(0, 0), elbow_r=(0, 0), pulse=False):
    cv = B.Canvas(B.FW, B.FH)
    parts, decals = chair_parts(0)
    for n in sorted(parts, key=lambda n: -parts[n][1]):
        if n != 'back':
            cv.stamp(parts[n][0])
    cv.stamp(_at(arm(-1, *elbow_l)))
    cv.stamp(_at(arm(1, *elbow_r)))
    cv.stamp(_at(neck(nod)))
    cv.stamp(_at(tee()))
    cv.stamp(_at(sleeve(-1)))
    cv.stamp(_at(sleeve(1)))
    cv.stamp(_at(hair(nod)), outline=False)
    cv.stamp(_at(band(nod)))
    cv.stamp(_at(cup(-1, nod, pulse)))
    cv.stamp(_at(cup(1, nod, pulse)))
    back = parts['back'][0]
    cv.stamp(back)
    for q, k in decals.items():
        if q in back and cv.px.get(q) not in (None, 'k'):
            cv.px[q] = k
    fill_holes(cv.px)
    return cv, set()


def fill_holes(px):
    """A single transparent pixel boxed in by two parts' keylines is a gap in the ink: close it
    (janim_defeat.fill_holes)."""
    for q in B.audit(px)['holes']:
        px[q] = 'k'
    return px


def builders():
    return [lambda: build(0, (0, 0), (0, 0)),
            lambda: build(1, (0, 0), (1, 0), pulse=True),
            lambda: build(0, (-1, 0), (0, 0)),
            lambda: build(1, (0, 0), (-1, 0), pulse=True)]


def frames():
    return [(cv.px, fx) for cv, fx in (b() for b in builders())]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.image(px))
        a = B.audit(px, fx)
        print(i, {k: round(v, 4) if isinstance(v, float) else v for k, v in st.items()},
              {k: (len(v) if isinstance(v, list) else v) for k, v in a.items()})
