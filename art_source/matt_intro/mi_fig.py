"""One frame of Matt from a spec, in the rig's own stamp order (back to front):

    back-layer parts (an arm reaching behind him)
    legs: trousers, then socks and trainers
    torso: sweatshirt, hem band
    collar (unless the jaw is dropped over it)
    mid-layer parts (the arms, ports and hands, anything held low)
    neck (only when the head is lifted off the collar)
    hair, moved with the head, and the combed strands
    the face map
    front-layer parts (a hand on his head, the doll, sweat, steam, anger marks)

Spec fields default to the approved idle, so Fig() builds approved frame 0 pixel for pixel and
Fig(roar=True, face='ROAR', ...) builds approved frame 1 minus its rings (checked in _selftest).
"""
import mi_base as B
import mi_arms as A
from mi_base import matt, rig_face, details, moved

W = H = 96


class Fig:
    def __init__(self, **kw):
        self.roar = False                # the rig's roar flag: collar shadow off, roar spikes
        self.spikes = None               # None: the rig's idle/roar spikes; else [centre, inner, outer]
        self.head = (0, 0)               # whole-head shift (hair and face)
        self.face = None                 # (rows, x0, y0) or None for the approved idle face
        self.collar = True
        self.neck = False                # fill under a lifted chin
        self.arms = None                 # [Arm, Arm] or None for the approved idle arms
        self.legs = None                 # callable(Fig) -> [(part, outline)] or None for the rig's
        self.stance = None               # None: the rig's (0 idle, 2 roar)
        self.body = (0, 0)               # torso/arms/collar shift (not the legs)
        self.parts = []                  # [(part, outline, layer)] extra parts: 'back'|'mid'|'front'|'top'
        self.fx = set()                  # pixels that are effects (float free of a keyline)
        self.comb = True
        self.hem = True                  # the hem band (a bent-over pose tucks it out of sight)
        self.torso_fn = None             # overrides for a turned body: callables returning parts
        self.hem_fn = None
        self.collar_fn = None
        self.hair_fn = None              # callable(P) -> hair part
        self.tilt = 0.0                  # crest tilt in degrees (a head tilt); 0 uses the rig's own hair
        self.torso_hook = None           # callable(part) to edit the sweatshirt before stamping
        self.face_hook = None            # callable(px) run after the face is stamped
        self.anchors = {}
        for k, v in kw.items():
            if not hasattr(self, k):
                raise AttributeError(k)
            setattr(self, k, v)

    def pose(self):
        P = matt.Pose(self.roar)
        if self.spikes is not None:
            P.spikes = list(self.spikes)
        if self.stance is not None:
            P.stance = self.stance
        # Headroom: the approved sheet tops out on row 1 (the centre spike's tip, length 27 from a
        # crown on row 30). A longer centre spike, or a lifted head, would push the tip off the
        # frame and clip it, so the centre spike is capped to end where the approved one does.
        cap = 27 + self.head[1] + P.head_dy
        c = list(P.spikes[0])
        if c[2] > cap:
            c[2] = cap
            P.spikes = [tuple(c)] + list(P.spikes[1:])
        return P


def comb(cv, dx, dy):
    """The rig's combed strands (matt.STRANDS), laid over hair tones only, shifted with the head."""
    for (x, y, k) in matt.STRANDS:
        q = (x + dx, y + dy)
        if cv.px.get(q) in ('i', 'j', 'h', 'l'):
            cv.px[q] = k


def build(f):
    P = f.pose()
    cv = B.Canvas(W, H)
    bx, by = f.body
    hx, hy = f.head

    def stamp_layer(name):
        for part, ol, layer in f.parts:
            if layer == name:
                cv.stamp(part, outline=ol)
        for arm in (f.arms or []):
            for part, ol, layer in A.parts(arm):
                if layer == name:
                    cv.stamp(moved(part, bx, by), outline=ol)

    stamp_layer('back')
    stamp_layer('back2')                 # over a back-layer arm, still behind the body
    # legs
    if f.legs is None:
        cv.stamp(matt.trousers(P))
        for ft in matt.feet(P):
            cv.stamp(ft, outline=False)
    else:
        for part, ol in f.legs(f):
            cv.stamp(part, outline=ol)
    # torso
    shirt = f.torso_fn() if f.torso_fn else matt.sweatshirt(P)
    if f.torso_hook:
        f.torso_hook(shirt)
    cv.stamp(moved(shirt, bx, by))
    if f.hem:
        cv.stamp(moved(f.hem_fn() if f.hem_fn else matt.hem_band(P), bx, by))
    # the collar goes down before the arms (a gesturing forearm can cross the chest in front of it;
    # the approved hanging arms never touch it, so the order changes nothing for them)
    if f.collar:
        cv.stamp(moved(f.collar_fn() if f.collar_fn else details.collar(), bx, by), outline=False)
    # arms
    if f.arms is None:
        for side in (0, 1):
            for part, outline in matt.arm_parts(P, side):
                cv.stamp(moved(part, bx, by), outline=outline)
        (pdx, pdy), (fdx, fdy) = matt.arm_offsets(P)
        pl, pr = details.ports()
        cv.stamp(moved(pl, pdx + bx, pdy + by), outline=False)
        cv.stamp(moved(pr, -pdx + bx, pdy + by), outline=False)
        fl, fr = details.fists()
        cv.stamp(moved(fl, fdx + bx, fdy + by), outline=False)
        cv.stamp(moved(fr, -fdx + bx, fdy + by), outline=False)
    stamp_layer('mid')
    if f.neck:
        stamp_neck(cv, f)
    # head
    if f.hair_fn:
        cv.stamp(moved(f.hair_fn(P), hx, hy + P.head_dy))
    elif f.tilt:
        import mi_hair
        cv.stamp(moved(mi_hair.hair(P.spikes, f.tilt), hx, hy + P.head_dy))
    else:
        cv.stamp(moved(matt.hair(P), hx, hy + P.head_dy))
    if f.comb:
        comb(cv, hx, hy + P.head_dy)
    if f.face is None:
        rows, x0, y0 = rig_face.IDLE, rig_face.X0, rig_face.IDLE_Y0
    else:
        rows, x0, y0 = f.face
    cv.stamp(moved(B.amap(rows, x0, y0), hx, hy + P.head_dy), outline=False)
    if f.face_hook:
        f.face_hook(cv.px)
    stamp_layer('front')
    stamp_layer('top')
    return cv


def stamp_neck(cv, f):
    """Under a lifted chin: the neck in the jaw's shadow, between the collar's walls."""
    bx, by = f.body
    hx, hy = f.head
    part = {}
    for y in range(47, 54):
        for x in range(42, 55):
            part[(x + bx, y + by)] = '4' if y < 50 else '3'
    # keylines down both sides
    for y in range(47, 54):
        part[(41 + bx, y + by)] = 'k'
        part[(55 + bx, y + by)] = 'k'
    cv.stamp(part, outline=False)


def close_pinholes(px, fx=()):
    """A transparent pixel boxed in on four sides by drawn pixels (a gap between two keylined
    shapes, one texel wide) is filled with keyline, as the house style separates shapes."""
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) in px:
                continue
            n4 = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
            if all(q in px and q not in fx for q in n4):
                px[(x, y)] = 'k'
    return px


def px_of(f):
    return close_pinholes(B.clip(build(f).px), f.fx)


# ---------------------------------------------------------------------------------------- self-test

def _selftest():
    ok = True
    idle = px_of(Fig())
    d = B.pixel_diff(B.image(idle), B.approved_sheet().crop((0, 0, 96, 96)))
    print('Fig() vs approved idle:', d or 'identical')
    ok &= d is None
    roar = Fig(roar=True, collar=False, face=(rig_face.ROAR, rig_face.X0, rig_face.ROAR_Y0))
    rp = px_of(roar)
    ref = {p: k for p, k in B.approved_frame_px(1).items() if k not in 'zZ'}
    # the rig's rings also lay an 'E' edge round themselves, only where nothing else is drawn
    cv = matt.build(True)
    ring_px = {p for p, k in cv.px.items() if k in 'zZ'}
    edge = set()
    for (x, y) in ring_px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            edge.add((x + dx, y + dy))
    ref = {p: k for p, k in ref.items() if not (k == 'E' and p in edge and p not in rp)}
    d = B.pixel_diff(B.image(rp), B.image(ref))
    print('Fig(roar) vs approved roar minus rings:', d or 'identical')
    ok &= d is None
    # the general arm builder against the rig's for the approved geometry, same stamp order
    return ok


if __name__ == '__main__':
    _selftest()
