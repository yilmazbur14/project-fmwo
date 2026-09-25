"""Captain Burak's posable rig for his fight body set.

Everything is built from the approved rig (art_source/burak_boss): the same parts, stamped in the
same order as burak.build(), so the default Pose IS the approved idle frame pixel for pixel and the
shot Pose IS the approved shot frame without its baked-in effects (both checked by atest.py).

A Pose moves what an animation needs to move and nothing else:
  bob      the whole body, whole pixels (breathing, crouches, bounces)
  head     the head on top of that (a nod, a lean, snapped back)
  expr     the face: the approved 'idle' smirk and 'shot' grin, or one of AFACES
  hat      its tilt, an extra offset, or None when it is off his head
  arm_l    his sword arm (screen left), arm_r his pistol arm (screen right): the approved ones by
           name, or a function that draws a posed arm and whatever it holds
  legs     None for the approved stance, or a function that draws posed legs (walk, run)
Posed arms, legs and props are drawn straight into the frame with the rig's own shading, which
uses the cast's fixed upper-left light, so any pose is lit like the approved frames.

Frames are 96 wide unless a sheet needs reach (slash, run: 128); `ox` slides the whole body so
its centre column is FW // 2 either way.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.join(os.path.dirname(HERE), 'burak_boss')
JUG = os.path.join(os.path.dirname(HERE), 'burak_boss_juggle')
for _p in (RIG, JUG, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import burak as B  # noqa: E402
import head as H  # noqa: E402
import kit  # noqa: E402
from kit import amap, capsule, cylinder, ellipse, fill, line, poly, rim  # noqa: E402,F401

MERGE = B.MERGE
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Pose:
    def __init__(self, **kw):
        self.bob = kw.get('bob', (0, 0))
        self.head = kw.get('head', (0, 0))
        self.expr = kw.get('expr', 'idle')
        self.hat = kw.get('hat', 0.0)              # tilt, or None: no hat on his head
        self.hat_off = kw.get('hat_off', (0, 0))
        self.tails = kw.get('tails', 0.0)          # the bandana tails' flutter
        self.flare = kw.get('flare', False)        # the coat's right skirt kicked out
        self.sweep = kw.get('sweep', 0.0)          # the coat's skirt blown back (px at the hem), for the run
        self.arm_l = kw.get('arm_l', 'sword_shoulder')
        self.arm_r = kw.get('arm_r', 'pistol_hang')
        self.legs = kw.get('legs', None)
        self.legs_off = kw.get('legs_off', (0, 0))     # the stance's own offset: feet stay planted under a bob
        self.sparkle = kw.get('sparkle', False)
        self.hair = kw.get('hair', 'approved')          # or 'tossed': the juggle's rounded crown with the
                                                        # brow lock tossed up, so both eyes read and a
                                                        # hopping hat shows hair, not a flat cut, under it
        self.hat_clip = kw.get('hat_clip', False)       # a hat pulled down low: no hair above its crown
        self.part_skirt = kw.get('part_skirt', 0.0)     # the front panels' hems pushed apart (px each)
        self.skirt_to = kw.get('skirt_to', None)        # the coat's hem row (approved terms) when he kneels
                                                        # and the skirt meets the ground: rows from the
                                                        # waist down are resampled, the gold hem kept
        self.before_head = kw.get('before_head', [])    # extra drawers under the head (behind it)
        self.extra = kw.get('extra', [])                # extra drawers on top of everything
        self.fw = kw.get('fw', 96)
        self.fh = kw.get('fh', 96)
        self.crop = kw.get('crop', None)                # (x0, y0): a window on the approved frame, for
                                                        # the portrait (a bust, cut by its frame's edges)

    @property
    def ox(self):
        if self.crop is not None:
            return -self.crop[0]
        return (self.fw - 96) // 2

    @property
    def oy(self):
        """Taller frames (headroom for the overhead swing) keep his feet on their own bottom row."""
        if self.crop is not None:
            return -self.crop[1]
        return self.fh - 96

    def at(self, p):
        """A point written in the approved frame's coordinates, moved by the bob and the frame offset."""
        return (p[0] + self.bob[0] + self.ox, p[1] + self.bob[1] + self.oy)

    def at_head(self, p):
        return (p[0] + self.bob[0] + self.head[0] + self.ox, p[1] + self.bob[1] + self.head[1] + self.oy)


class Frame:
    """A canvas plus the put() that shifts parts by whole pixels, as burak.build() does."""

    def __init__(self, P):
        self.P = P
        self.cv = kit.Canvas(P.fw, P.fh)

    def put(self, part, dx=0, dy=0, outline=True, owner=None):
        dx += self.P.ox
        dy += self.P.oy
        self.cv.stamp({(x + dx, y + dy): k for (x, y), k in part.items()} if (dx or dy) else part,
                      outline, owner)

    def body(self, part, outline=True, owner=None, extra=(0, 0)):
        bx, by = self.P.bob
        self.put(part, bx + extra[0], by + extra[1], outline, owner)

    def headpart(self, part, outline=True, owner=None):
        bx, by = self.P.bob
        hx, hy = self.P.head
        self.put(part, bx + hx, by + hy, outline, owner)


# ------------------------------------------------------------------ the approved arms, by name
def sword_shoulder(F):
    """The approved sword arm: elbow down and out, the cutlass resting on his shoulder."""
    F.body(B.sleeve((31.5, 53), (28.5, 63), 4.6, 3.9))
    F.body(B.cuff((28.5, 64), 3.8, 1.5))
    F.body(B.limb([((29, 66), (34, 58), 2.8, 2.6)], '3', '2', '4', '5'))
    F.body(B.cutlass((31.5, 49.5), (9, 25), bow=2.4))
    F.body(amap(B.FIST_SWORD, 29, 50), outline=False)


def pistol_hang(F):
    """The approved pistol arm: hanging at his side, the big flintlock dangling barrel-down."""
    F.body(B.sleeve((64.5, 53), (68, 62), 4.6, 3.9, lit_side=False))
    F.body(B.cuff((68.5, 63.5), 3.8, 1.5, lit=False))
    F.body(B.limb([((69, 65.5), (69.5, 68), 2.7, 2.5)], '4', '3', '5', '6'))
    for part in B.pistol_parts((71.5, 70.5), (0.66, 1.0), (-1.0, 0.3), barrel_len=12.5, grip_len=5.0,
                               bell_len=6.5, r_bar=2.2, r_bell=5.2, mouth_tip=0.5):
        F.body(part)
    F.body(B.hammer(70, 66))
    F.body(B.hand_pistol(), outline=False)


def shot_arm(F, fire=False):
    """The approved shot arm (frame 1), without the flash, smoke or ball: the bell mouth's bore dark."""
    F.body(B.sleeve((64, 53), (70, 57.5), 4.5, 4.0, lit_side=False))
    F.body(B.cuff_d((71.8, 59), (0.8, 0.6), 1.5, 4.0))
    F.body(B.limb([((73.3, 60.5), (75, 61.8), 2.9, 2.8)], '4', '3', '5', '6'))
    exit_, mouth = (81, 63.5), B.MUZZLE
    F.body(B.bell_wedge(exit_, mouth, 2.3, 5.4))
    F.body(B.FIST_GUN, extra=(0, 4), outline=False)
    F.body(B.hammer(79, 54))
    F.body(B.bell_mouth(exit_, mouth, 6.2, 3.9, fire=fire))


def gun_arm(elbow, wrist, fist_at, exit_, mouth, hammer_at, fire=False):
    """The shot arm re-aimed: the same sleeve, cuff, forearm, gun fist and forced-perspective bell,
    with the elbow, wrist, fist, barrel exit and mouth moved. Returns a drawer."""
    def draw(F):
        F.body(B.sleeve((64, 53), elbow, 4.5, 4.0, lit_side=False))
        ux, uy = (wrist[0] - elbow[0], wrist[1] - elbow[1])
        L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L
        F.body(B.cuff_d((elbow[0] + ux * 1.8, elbow[1] + uy * 1.8), (ux, uy), 1.5, 4.0))
        F.body(B.limb([((elbow[0] + ux * 3.3, elbow[1] + uy * 3.3), wrist, 2.9, 2.8)], '4', '3', '5', '6'))
        F.body(B.bell_wedge(exit_, mouth, 2.3, 5.4))
        F.body(B.FIST_GUN, extra=(fist_at[0] - 74, fist_at[1] - 54), outline=False)
        F.body(B.hammer(*hammer_at))
        F.body(B.bell_mouth(exit_, mouth, 6.2, 3.9, fire=fire))
    draw.mouth = mouth
    return draw


NAMED_ARMS = {'sword_shoulder': sword_shoulder, 'pistol_hang': pistol_hang, 'shot': shot_arm}


# ------------------------------------------------------------------ the build
def build(P):
    """Stamp him in the approved order, with the pose's substitutions."""
    import aface
    F = Frame(P)
    hx = P.head[0]

    def skirt(part):
        return squash(part, 70, P.skirt_to) if P.skirt_to is not None else part
    F.body(skirt(B.coat_back(P.sweep)))
    if P.legs is None:
        lx, ly = P.legs_off
        F.put(B.legs(), lx, ly)
        for b_, c_ in (B.boot(0), B.boot(1)):
            F.put(b_, lx, ly)
            F.put(c_, lx, ly)
    else:
        P.legs(F)
    F.body(B.tee())
    band, tails = B.sash()
    F.body(band)
    F.body(amap(B.BUCKLE, 45, 65), outline=False)
    F.body(skirt(B.coat_panel(1, flare=P.flare, sweep=P.sweep - P.part_skirt)))
    F.body(skirt(B.coat_panel(0, sweep=P.sweep + P.part_skirt)))
    F.body(tails)
    F.body(B.collar(), extra=(hx // 2, 0))
    F.body(H.neck(), extra=(hx, 0))
    F.body(B.tee_collar(), extra=(hx // 2, 0), outline=False)
    F.body(B.chain(), extra=(hx // 2, 0), outline=False)
    arm_r = NAMED_ARMS.get(P.arm_r, P.arm_r) if isinstance(P.arm_r, str) else P.arm_r
    if arm_r is not None:
        arm_r(F)
    for d in P.before_head:
        d(F)
    if P.hat is not None and B.BANDANA:
        for t in B.bandana_tails(P.tails):
            F.put(t, P.bob[0] + P.head[0] + P.hat_off[0], P.bob[1] + P.head[1] + P.hat_off[1])
    l, r = H.ears()
    F.headpart(l)
    F.headpart(r)
    F.headpart(H.face_base())
    F.headpart(aface.features(P.expr), outline=False)
    if P.sparkle:
        F.headpart({(56, 36): 'W', (56, 37): 'W', (56, 38): 'Y', (56, 39): 'W', (56, 40): 'W', (54, 38): 'W',
                    (55, 38): 'W', (57, 38): 'W', (58, 38): 'W'}, outline=False)
    before = dict(F.cv.px)
    if P.hair == 'tossed':
        import jhead
        F.headpart(jhead.hair_hatless(short_lock=True))
    else:
        F.headpart(H.hair())
    F.headpart(H.flyaways(), outline=False)
    hair_px = [q for q, k in F.cv.px.items() if before.get(q) != k]
    if P.hat is not None:
        hdx, hdy = P.bob[0] + P.head[0] + P.hat_off[0], P.bob[1] + P.head[1] + P.hat_off[1]
        hat = H.hat(P.hat)
        F.put(hat, hdx, hdy, outline='soft')
        if P.hat_clip:
            top = {}
            for (x, y) in hat:
                X, Y = x + hdx + P.ox, y + hdy + P.oy
                top[X] = min(top.get(X, Y), Y)
            for q in sorted(hair_px):
                if q[0] in top and q[1] < top[q[0]]:
                    if q in before:
                        F.cv.px[q] = before[q]
                    else:
                        del F.cv.px[q]
    arm_l = NAMED_ARMS.get(P.arm_l, P.arm_l) if isinstance(P.arm_l, str) else P.arm_l
    if arm_l is not None:
        arm_l(F)
    for d in P.extra:
        d(F)
    return F.cv


def squash(part, y0, y_to):
    """Resample a part's rows from y0 down so its bottom row lands on y_to (nearest row): the coat's
    skirt folding shorter as he kneels, its trimmed hem kept intact."""
    ymax = max(y for (_, y) in part)
    if y_to >= ymax:
        return part
    rows = {}
    for (x, y), k in part.items():
        rows.setdefault(y, {})[x] = k
    out = {q: k for q, k in part.items() if q[1] < y0}
    for t in range(y0, y_to + 1):
        sy = int(round(y0 + (t - y0) * (ymax - y0) / float(y_to - y0)))
        for x, k in rows.get(sy, {}).items():
            out[(x, t)] = k
    return out


def fill_pinholes(px, w, h):
    """Close single transparent pixels walled in on all four sides (the approved shot frame has one,
    at (77, 57) between the hammer's and the fist's keylines), with the commonest non-black
    neighbour, else black. Ties broken in a fixed order, so the build never varies."""
    add = []
    for y in range(h):
        for x in range(w):
            if (x, y) in px:
                continue
            n = [px.get((x + dx, y + dy)) for dx, dy in N4]
            if all(n):
                c = [k for k in n if k != 'k']
                add.append(((x, y), max(sorted(set(c)), key=c.count) if c else 'k'))
    for q, k in add:
        px[q] = k
    return px


def render(P, pinholes=True):
    """The pose's keys, the approved palette merges applied and pinholes closed."""
    px = {q: MERGE.get(k, k) for q, k in build(P).px.items()}
    return fill_pinholes(px, P.fw, P.fh) if pinholes else px


def image(P):
    return kit.image(render(P), P.fw, P.fh)


# the approved frames, as Poses
def idle0():
    return Pose()


def shot0(**kw):
    kw.setdefault('head', (-2, 0))
    kw.setdefault('hat', -0.06)
    kw.setdefault('flare', True)
    kw.setdefault('tails', 1.0)
    kw.setdefault('expr', 'shot')
    kw.setdefault('arm_r', 'shot')
    kw.setdefault('sparkle', True)
    return Pose(**kw)
