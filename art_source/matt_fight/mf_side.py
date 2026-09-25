"""matt_trueshot_charge_side.png and matt_trueshot_fire_side.png: the megaphone in a three-quarter
side view for the LEFT and RIGHT stations, drawn facing screen-right (the code mirrors it).

About a 40 degree turn, well past the walk's 20: the face's features gather on the right half of
the head with the chin swung toward the turn, the near ear comes in off the silhouette with the back
of the head behind it, the far ear goes out of sight, the crest's fan narrows (its near spikes in
front), the torso and collar turn, and the cupped hands stand in front of his mouth pointing right,
the near hand in profile, the far one behind it. Light stays upper left.
"""
import math

import mf_base as M
from mf_base import B, A, G, F, H, L, PZ
from mi_base import sh, details, poly, moved, matt
from shapes import tuft_frames

# ------------------------------------------------------------------ the 40 degree head
BASE40 = B.rows_of([
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65      y
    ".kiii iiiii iiikk kkkkk kkkkk kkkkk kiik.",       # 29  hairline
    ".kiii iiiii iiik1 11122 22222 22222 3kik.",       # 30
    ".kiii iiiii iik11 22222 22222 22233 3kik.",       # 31
    ".kiii iiiii ik112 22222 22222 22233 3kik.",       # 32
    ".kiii iiiii ik122 22222 22222 22233 3kik.",       # 33
    ".kiii iiiii k1222 22222 22222 22233 3k...",       # 34
    ".kiii ikkik 12222 22222 22222 22233 3k...",       # 35  near ear's top
    ".kiii k323k 12222 22222 22221 22333 3k...",       # 36  near ear; nose bridge
    ".kiii k343k 12222 22222 22221 23333 3k...",       # 37
    ".kiii k343k 12222 22222 22221 23333 3k...",       # 38
    ".kiii k353k 12222 22222 22221 23333 3k...",       # 39
    ".kiii k333k 12222 22222 22221 13333 3k...",       # 40
    "..kkk .k44k 12222 22222 22223 21133 3k...",       # 41  nose tip
    "..... ..kkk 12222 22222 22224 63433 3k...",       # 42  near nostril
    "..... ....k 12222 22222 22223 33333 3k...",       # 43
    "..... ....k 12222 22222 22222 22333 3k...",       # 44
    "..... ..... k1222 22222 22222 22333 3k...",       # 45
    "..... ..... k1222 22222 22222 22333 3k...",       # 46
    "..... ..... .k122 22222 22222 22333 3k...",       # 47
    "..... ..... ..k12 22222 22222 23333 k....",       # 48
    "..... ..... ...k1 22222 22223 33344 k....",       # 49
    "..... ..... ....k k2222 22233 3344k .....",       # 50
    "..... ..... ..... .kkk3 33334 44kk. .....",       # 51
    "..... ..... ..... ....k kkkkk kk... .....",       # 52  chin, swung right
])


def face40(*groups):
    edits = []
    for g in groups:
        edits += g
    return G.patched(BASE40, edits)


# features: near (screen-left) side full, far side foreshortened toward the right contour
BR40_ANGRY = [(32, 45, 'hhh'), (33, 46, 'hhhhh'), (34, 49, 'hhhh'), (32, 60, 'h'), (33, 58, 'hhh'),
              (34, 57, 'hh'), (33, 54, '3'), (34, 54, '4')]
EY40_ANGRY = [(35, 46, 'kkkkk'), (36, 47, 'kWhhk'), (37, 48, 'kkk'), (35, 58, 'kkk'), (36, 58, 'khk'),
              (37, 59, 'k')]
EY40_SQUEEZE = [(35, 47, 'kk'), (36, 49, 'kkk'), (37, 47, 'kk'), (35, 60, 'k'), (36, 58, 'kk'), (37, 60, 'k')]
EY40_WIDE = [(34, 47, 'kkkk'), (35, 46, 'kWWWXk'), (36, 46, 'kWWhWk'), (37, 47, 'kkkk'),
             (34, 58, 'kkk'), (35, 58, 'kWh'), (36, 58, 'kkh')]
M40_AAH = [(45, 52, 'kkkkk'), (46, 51, 'kmmnnk'), (47, 51, 'kmnqnk'), (48, 52, 'kkkk')]

# ------------------------------------------------------------------ the crest, turned
SQ = 0.85                 # the fan's width at the turn (a touch wider than cos 40 keeps the crest's read)


def crest_specs(spikes):
    """The rig's five spikes with the fan narrowed about the crown, ordered far (right) to near
    (left) so the near spikes overlap the far ones."""
    centre, inner, outer = spikes
    specs = {}
    for name, (ang, r0, r1, w0, w1, bend) in (('outer', outer), ('inner', inner)):
        for sgn, sidename in ((1, 'L'), (-1, 'R')):
            base, tip = matt.radial(48, 30, ang * sgn, r0, r1)
            base = (48 + (base[0] - 48) * SQ, base[1])
            tip = (48 + (tip[0] - 48) * SQ, tip[1])
            specs[name + sidename] = (base, tip, w0, w1, bend * sgn)
    ang, r0, r1, w0, w1, bend = centre
    base, tip = matt.radial(48, 30, ang, r0, r1)
    specs['centre'] = (base, tip, w0, w1, bend)
    return [specs[n] for n in ('outerR', 'innerR', 'centre', 'innerL', 'outerL')]


def crest(spikes):
    """matt.hair() line for line, on the turned specs."""
    dome = poly(matt.DOME)
    tufts = [tuft_frames(b, t, w0, w1, bd) for (b, t, w0, w1, bd) in crest_specs(spikes)]
    part = {}
    for (x, y) in dome:
        u = (x - 48) / 15.0
        v = (y - 22) / 7.0
        lit = -(u * 0.75 + v * 0.65)
        part[(x, y)] = 'j' if lit > 0.55 else ('h' if lit < -0.55 else 'i')
    owner = {}
    for idx, (px, fr) in enumerate(tufts):
        for p in px:
            t, s_, nx, ny = fr[p]
            t = min(1.0, t)
            lit = s_ * (nx * matt.LIGHT[0] + ny * matt.LIGHT[1])
            if t >= 0.64 - 0.06 * lit and p not in dome:
                k = 'c'
                if lit > 0.15:
                    k = 'b'
                if lit > 0.45 and t < 0.93:
                    k = 'a'
                if lit < -0.3:
                    k = 'd'
                if lit < -0.75:
                    k = 'e'
            else:
                k = 'i'
                if lit > 0.2:
                    k = 'j'
                if lit > 0.5 and 0.3 < t < 0.62:
                    k = 'l'
                if lit < -0.35:
                    k = 'h'
            part[p] = k
            owner[p] = idx
    for idx, (px, fr) in enumerate(tufts):
        for p in px:
            if owner.get(p) != idx:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + dx, p[1] + dy)
                if q in owner and owner[q] < idx and q not in dome:
                    part[p] = 'k' if fr[p][0] > 0.42 else 'h'
                    break
    return part


# ------------------------------------------------------------------ the turned torso
TURN = 0.88               # the torso's width at the turn
SHIFT = 1


def tx(x):
    return 48 + (x - 48) * TURN + SHIFT


def sweatshirt_side():
    """matt.sweatshirt() on turned points, its chest shadow slid round with the collar."""
    half = [(48, 48.5), (41, 49), (36, 50.5), (31.5, 52.5), (30.5, 56), (31, 61), (32, 65), (32.5, 68.5),
            (33, 71), (48, 71)]
    pts = [(tx(x), y) for (x, y) in half] + [(tx(96 - x), y) for (x, y) in reversed(half) if x != 48]
    part = {p: 'C' for p in poly(pts)}
    sh.ellipsoid(part, tx(47), 58, 19 * TURN, 15, 'ABCDE', (0.93, 0.76, 0.36, 0.0))
    rows = {}
    for (x, y) in part:
        rows.setdefault(y, []).append(x)
    for (x, y) in list(part):
        edge = min(x - min(rows[y]), max(rows[y]) - x)
        if 57 <= y <= 70 and edge <= 1:
            part[(x, y)] = B.DARKER[part[(x, y)]]
        if 57 <= y <= 58 and 43 <= x <= 58:
            part[(x, y)] = B.DARKER[part[(x, y)]]
    return part


def hem_side():
    half = [(48, 68.5), (33.5, 68.5), (32.5, 70.5), (33.5, 72.5), (48, 72.5)]
    pts = [(tx(x), y) for (x, y) in half] + [(tx(96 - x), y) for (x, y) in reversed(half) if x != 48]
    part = {p: 'c' for p in poly(pts)}
    sh.ellipsoid(part, tx(46), 66, 17 * TURN, 8, 'abcde', (0.9, 0.62, 0.28, -0.1))
    return part


def collar_side():
    """The crew collar slid round toward the turn; the chin covers its middle, its far end turns
    out of sight."""
    return {(x + 3, y): k for (x, y), k in details.collar().items() if x + 3 <= 63}


# ------------------------------------------------------------------ feet: both trainers pointing right
# The approved left trainer's toe claws point out to screen-left and its mirror, the approved right
# trainer, points right; turned to face right, both feet are that right trainer, shaded as
# matt.feet() shades it.
def side_feet(near_dx=-22, far_dx=2):
    out = []
    for dx in (far_dx, near_dx):
        f = moved(details.foot_structure(1), dx, 0)
        sock = {p: 'W' for p, k in f.items() if k == 'S'}
        upper = {p: 'C' for p, k in f.items() if k == 'U'}
        rubber = {p: 'W' for p, k in f.items() if k == 'W'}
        laces = {p: 'b' for p, k in f.items() if k == 'Y'}
        cx = 96 - 35.5 + dx
        ux = 96 - 35 + dx
        sh.cylinder(sock, (cx, 80), (cx, 95), 7.0, 'WXx', (0.35, -0.2))
        sh.ellipsoid(upper, ux, 92, 11, 5, 'BCDE', (0.8, 0.45, 0.05))
        sh.ellipsoid(rubber, ux, 90, 11, 5, 'WXx', (0.2, -0.45))
        sh.ellipsoid(laces, ux, 89, 5, 3, 'abc', (0.7, 0.3))
        for d in (sock, upper, rubber, laces):
            f.update(d)
        out.append(f)
    return out


def side_legs(f):
    """The far leg and foot first, then the near ones; the trousers are the rig's legs moved over
    their feet."""
    far_ft, near_ft = side_feet()
    return [(far_ft, False), (L.leg(1, 0, 2, 0, 0.0, screen=True), True),
            (near_ft, False), (L.leg(0, 0, 2, 0, 0.0, screen=True), True)]


# ------------------------------------------------------------------ the open jaw, behind the cone
YELL40_ROWS = [
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65      y
    "..... ....k 12222 22222 22223 33333 3k...",       # 43
    "..... ....k 1222k kkkkk kkkkk kkkk3 3k...",       # 44  upper lip
    "..... ..... k12kW WWWWW WWWWW WWk33 3k...",       # 45  upper teeth
    "..... ..... k12kn mmmmm mmmmm mnk33 3k...",       # 46  throat
    "..... ..... k12kn mmkkk kkkkm mnk33 3k...",       # 47
    "..... ..... .k1kq nmqrr rrrqm nqk33 3k...",       # 48  tongue
    "..... ..... ..kkq qrRRr rrrrq qk333 k....",       # 49
    "..... ..... ...kW WWWWW WWWWW Wk33k .....",       # 50  lower teeth
    "..... ..... ...k1 kkkkk kkkkk k333k .....",       # 51  lower lip
    "..... ..... ....k k2222 22333 344k. .....",       # 52
    "..... ..... ..... .kkk3 33334 44kk. .....",       # 53
    "..... ..... ..... ....k kkkkk kk... .....",       # 54  chin, two rows down
]


# ------------------------------------------------------------------ the frames
import mf_hands as MH


def side_arms(dx=0, dy=0, push=0):
    """The near arm across his chest, the cupped hand in profile at his lips pointing right; the far
    arm bent up behind his head. push slides the hand forward (the recoil)."""
    near = A.bent(0, (29, 57 + dy), (28, 60 + dy), (41 + dx, 64 + dy), (51 + dx + push, 52 + dy),
                  hand=MH.MEGA_CONE, fore_layer='front', hand_layer='front')
    far = A.bent(1, (69, 57 + dy), (69, 60 + dy), (73, 66 + dy), (63, 55 + dy), hand=None, cuff=False)
    return [far, near]


def side_fig(face, arms, spikes=PZ.SP_IDLE, head=(0, 0), body=(0, 0)):
    return F.Fig(arms=arms, face=(face, G.X0, G.Y0), torso_fn=sweatshirt_side, hem_fn=hem_side,
                 collar_fn=collar_side, hair_fn=lambda P: crest(P.spikes), comb=False, legs=side_legs,
                 spikes=spikes, head=head, body=body)


def charge_figs():
    face = face40(BR40_ANGRY, EY40_ANGRY, M40_AAH)
    out = []
    for body, t in ((0, 0.0), (-1, 0.35), (-1, 0.6), (0, 0.3)):
        out.append(side_fig(face, side_arms(dy=body), spikes=PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_PERK, t),
                            body=(0, body)))
    return out


def fire_figs():
    blast = G.with_jaw(face40(BR40_ANGRY, EY40_SQUEEZE), YELL40_ROWS)
    wide = G.with_jaw(face40(BR40_ANGRY, EY40_WIDE), YELL40_ROWS)
    return [
        side_fig(blast, side_arms(dx=1, dy=1), spikes=PZ.SP_ROAR, head=(1, 1), body=(1, 1)),
        side_fig(wide, side_arms(dx=-1, dy=-1, push=3), spikes=PZ.SP_BRISTLE, head=(-1, 0), body=(-1, -1)),
        side_fig(wide, side_arms(push=2), spikes=PZ.lerp_spikes(PZ.SP_BRISTLE, PZ.SP_ROAR, 0.5), head=(0, 1)),
    ]


class ChargeSide:
    NAME = 'matt_trueshot_charge_side'

    @staticmethod
    def figs():
        return charge_figs()


class FireSide:
    NAME = 'matt_trueshot_fire_side'

    @staticmethod
    def figs():
        return fire_figs()


if __name__ == '__main__':
    import mi_view as V
    print(B.check_map(BASE40, 35, 'BASE40'))
    ims = []
    for name, rows in (('BASE34 (walk)', G.BASE34), ('BASE40', BASE40),
                       ('charge face', face40(BR40_ANGRY, EY40_ANGRY, M40_AAH))):
        px = F.px_of(F.Fig(face=(rows, G.X0, G.Y0)))
        ims.append(V.label(V.up(B.image(px).crop((22, 18, 74, 60)), 8), name))
    print(V.save(V.row(ims), 'side_head.png'))
