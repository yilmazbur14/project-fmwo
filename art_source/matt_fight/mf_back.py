"""matt_trueshot_charge_back.png and matt_trueshot_fire_back.png: the megaphone from behind, for the
BOTTOM station, where he faces up the ring, away from the camera.

What carries the read from behind: the crest (the fan of five spikes reads the same both ways),
the back of his head all hair with the backs of his ears, the ribbed back of the crewneck under
the nape, the speaker ports on his shoulders, and the forearms rising from out-flung elbows into
the sides of his head: his hands are cupped at his mouth, out of sight in front of his face.

Built on the approved rig like everything else: the rig's crest, sweatshirt, hem band, sleeves,
ports and trousers; the back of the head, the collar's back and the trainers' heels are new maps.
Light stays upper left.
"""
import math

import mf_base as M
from mf_base import B, A, G, F, H, L, PZ
from mi_base import sh, details, poly, moved, matt

# ------------------------------------------------------------------ the back of the head
# The head's silhouette is the approved one (the dome, and the idle face map's outline down to the
# nape); from behind it is all hair, lit on the upper left, with partings raying down from the crown
# and a lit strand beside each. Rows 44-47 round off into the nape.
CROWN = (48, 16)


def head_mask():
    rows = G.IDLE
    mask = set()
    for i, r in enumerate(rows):
        y = G.Y0 + i
        for j, ch in enumerate(r):
            x = G.X0 + j
            if ch == '.':
                continue
            if 36 <= y <= 42 and (x <= 35 or x >= 61):
                continue                         # the ears, drawn on their own
            if y >= 44:
                continue                         # the nape is rounded off below
            mask.add((x, y))
    for y, (x0, x1) in ((44, (37, 59)), (45, (38, 58)), (46, (39, 57)), (47, (41, 55))):
        for x in range(x0, x1 + 1):
            mask.add((x, y))
    return mask


def back_head():
    part = {}
    for (x, y) in head_mask():
        u = (x - 48) / 15.0
        v = (y - 26) / 12.0
        lit = -(u * 0.75 + v * 0.65)
        part[(x, y)] = 'j' if lit > 0.45 else ('h' if lit < -0.45 else 'i')
    # the locks: black partings raying down from the crown (the portrait's treatment of his hair),
    # each with a lit strand along the next lock's edge toward the light, on its left
    for ang in (-44, -22, -1, 20, 42):
        a = math.radians(ang)
        for r in range(14, 34):
            x = int(round(CROWN[0] + math.sin(a) * r * 0.62))
            y = int(round(CROWN[1] + math.cos(a) * r))
            if (x, y) in part and y >= 29:
                part[(x, y)] = 'k' if r >= 17 else 'h'
                if (x - 1, y) in part and part[(x - 1, y)] not in 'hk':
                    part[(x - 1, y)] = 'l' if part[(x - 1, y)] == 'j' else 'j'
    return part


# the backs of the ears: the approved ear outlines, their backs turned to us, in shade
EAR_BACK = [
    # x: 31-35 ... 61-65    (y 36-42)
    (36, 31, 'k323k'), (37, 31, 'k343k'), (38, 31, 'k344k'), (39, 31, 'k344k'), (40, 31, 'k344k'),
    (41, 31, '.k44k'), (42, 31, '..kkk'),
    (36, 61, 'k434k'), (37, 61, 'k454k'), (38, 61, 'k454k'), (39, 61, 'k454k'), (40, 61, 'k454k'),
    (41, 61, 'k55k.'), (42, 61, 'kkk..'),
]

# the nape: skin in the head's shadow between the hair and the collar
NAPE = [(y, 42, '4' * 13) for y in range(46, 50)]

# the collar's back: the ribbed yellow band straight across the top of his back, lit upper left
COLLAR_BACK = [
    # x: 36-60    y 48-53
    (48, 36, '..kkkkkkkkkkkkkkkkkkkkk..'),
    (49, 36, '.kbbbbbbbbbbbbbbbcccccdk.'),
    (50, 36, 'kbbccccccccccccccccccddek'),
    (51, 36, 'kcddddddddddddddddddddeek'),
    (52, 36, '.keeeeeeeeeeeeeeeeeeeeek.'),
    (53, 36, '..kkkkkkkkkkkkkkkkkkkkk..'),
]


def spans(edits):
    part = {}
    for y, x0, keys in edits:
        for j, ch in enumerate(keys):
            if ch != '.':
                part[(x0 + j, y)] = ch
    return part


def collar_back():
    part = spans(COLLAR_BACK)
    for (x, y), k in list(part.items()):
        if k in 'bcde' and x % 2 == 0 and 49 <= y <= 52:
            part[(x, y)] = B.DARKER[k]            # the ribbing
    return part


# ------------------------------------------------------------------ the trainers from behind
# The heel counter in lavender (no laces, no toe claws from this side), a pull tab at the top of the
# heel, the white sole across the bottom; the striped socks as from the front.
FOOT_BACK = [
    # x: 25-29 30-34 35-39 40-44 45       y
    "....k SSSSS SSSSS SSk.. .",          # 85
    "....k kkkkk kkkkk kkk.. .",          # 86  stripe
    "....k SSSSS SSSSS SSk.. .",          # 87
    "....k kkkkk kkkkk kkk.. .",          # 88  stripe
    "...kk SSSSS SSSSS SSkk. .",          # 89
    "..kUU UUUUU kkkUU UUUUk .",          # 90  heel tab
    ".kUUU UUUUU kUkUU UUUUU k",          # 91
    "kUUUU UUUUU UUUUU UUUUU k",          # 92
    "kWWWW WWWWW WWWWW WWWWW k",          # 93  sole
    "kWWWW WWWWW WWWWW WWWWW k",          # 94
    ".kkkk kkkkk kkkkk kkkkk .",          # 95
]


def back_feet(stance=0, hip=0):
    out = []
    for side in (0, 1):
        f = B.amap(FOOT_BACK, 25, 85)
        if side:
            f = {(96 - x, y): k for (x, y), k in f.items()}
        f = moved(f, stance if side else -stance, 0)
        sock = {p: 'W' for p, k in f.items() if k == 'S'}
        upper = {p: 'C' for p, k in f.items() if k == 'U'}
        rubber = {p: 'W' for p, k in f.items() if k == 'W'}
        cx = (96 - 35.5 + stance) if side else (35.5 - stance)
        sh.cylinder(sock, (cx, 80), (cx, 95), 7.0, 'WXx', (0.35, -0.2))
        sh.ellipsoid(upper, cx, 92, 11, 5, 'BCDE', (0.8, 0.45, 0.05))
        sh.ellipsoid(rubber, cx, 91, 11, 5, 'WXx', (0.2, -0.45))
        for d in (sock, upper, rubber):
            f.update(d)
        out.append(f)
    return out


def back_legs(stance=0, hip=0):
    def fn(f):
        parts = []
        for ft in back_feet(stance, hip):
            parts.append((ft, False))
        for side in (0, 1):
            parts.append((L.leg(side, hip, (stance if side else -stance), 0, 0.0, screen=True), True))
        return parts
    return fn


# ------------------------------------------------------------------ his back
# The back pockets of his trousers (Hong's pocket), outlined over the trousers' own shading, and the
# folds the sweatshirt pulls up from each armpit when his elbows go up.
POCKET = [
    "kkkkkkk",
    "k.....k",
    "k.....k",
    "k.....k",
    ".k...k.",
    "..kkk..",
]


def pockets():
    part = {}
    for x0 in (33, 57):
        for (x, y), k in B.amap(POCKET, x0, 74).items():
            part[(x, y)] = k
    return part


def armpit_folds():
    """Short black folds from each armpit in toward the shoulder blades, a lit lip above each."""
    part = {}
    for (x, y) in ((33, 59), (34, 60), (35, 61), (33, 63), (34, 64)):
        part[(x, y)] = 'k'
        part[(96 - x, y)] = 'k'
    for (x, y) in ((33, 58), (34, 59), (35, 60)):
        part[(x, y)] = 'B'
    for (x, y) in ((63, 58), (62, 59), (61, 60)):
        part[(x, y)] = 'D'
    return part


# ------------------------------------------------------------------ the arms from behind
def back_arms(dy=0, spread=0, lift=0):
    """Elbows out at his sides, forearms rising into the sides of his head: the hands are at his
    mouth, hidden in front of his face. Drawn before the head, which covers the hands."""
    el = (16 - spread, 63 + dy)
    wl = (37 - spread // 2, 42 + dy - lift)    # the wrists end behind his head: no cuff to show
    return [A.bent(0, (25, 57 + dy), (24, 60 + dy), el, wl, hand=None, cuff=False),
            A.bent(1, (71, 57 + dy), (72, 60 + dy), (96 - el[0], el[1]), (96 - wl[0], wl[1]),
                   hand=None, cuff=False)]


class BackFig:
    """A back-view frame: the approved rig's body (no face), then the back of the head over the
    dome, then the ears' backs. Parts that ride on the body (nape, collar) move with it."""

    def __init__(self, arms, body=0, head=0, spikes=PZ.SP_IDLE, hip=0, stance=0):
        nape = moved(spans(NAPE), 0, body)
        collar = moved(collar_back(), 0, body)
        folds = moved(armpit_folds(), 0, body)
        self.fig = F.Fig(arms=arms, body=(0, body), head=(0, head), spikes=spikes, collar=False,
                         comb=False, face=([], G.X0, G.Y0), legs=back_legs(stance, hip),
                         parts=[(moved(pockets(), 0, 0), False, 'back2x'),
                                (folds, False, 'mid'), (nape, False, 'mid'), (collar, False, 'mid')])
        self.pockets = pockets()
        self.fx = set()
        self.anchors = {}

    def px(self):
        f = self.fig
        cv = F.build(f)
        # the pockets go on the trousers where they still show under the hem band
        for q, k in self.pockets.items():
            if cv.px.get(q) in ('K', 'L', 'M', 'N'):
                cv.px[q] = k
        P = f.pose()
        hx, hy = f.head
        dy = hy + P.head_dy
        head = moved(back_head(), hx, dy)
        cv.stamp(head, outline=False)
        # keyline only the silhouette: where the back of the head meets empty space
        edge = set()
        for (x, y) in head:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q not in cv.px:
                    edge.add(q)
        for q in edge:
            cv.px[q] = 'k'
        cv.stamp(moved(spans(EAR_BACK), hx, dy), outline=False)
        return F.close_pinholes(B.clip(cv.px), self.fx)

    def crown(self):
        P = self.fig.pose()
        return (48 + self.fig.head[0], 16 + self.fig.head[1] + P.head_dy)


def charge_figs():
    out = []
    for body, sh_, t in ((0, 0, 0.0), (-1, -1, 0.35), (-1, -2, 0.6), (0, -1, 0.3)):
        out.append(BackFig(back_arms(dy=sh_), body=body, spikes=PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_PERK, t)))
    return out


def fire_figs():
    return [
        # the blast: he pitches forward up the ring, knees giving, crest flaring
        BackFig(back_arms(dy=1), body=2, head=1, hip=2, spikes=PZ.SP_ROAR),
        # the recoil throws his head back toward us and his elbows out
        BackFig(back_arms(dy=-1, spread=4, lift=-1), body=-1, head=2, spikes=PZ.SP_BRISTLE),
        BackFig(back_arms(spread=3), body=0, head=1, spikes=PZ.lerp_spikes(PZ.SP_BRISTLE, PZ.SP_ROAR, 0.5)),
    ]


class ChargeBack:
    NAME = 'matt_trueshot_charge_back'

    @staticmethod
    def figs():
        return charge_figs()


class FireBack:
    NAME = 'matt_trueshot_fire_back'

    @staticmethod
    def figs():
        return fire_figs()
