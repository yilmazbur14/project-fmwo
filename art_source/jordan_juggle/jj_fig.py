"""One Jordan, built upright in the rig's BUILD coordinates for a body that will be turned `theta`.

The redesign rig builds a frame back to front (jordan.build): jeans, sneakers, the far arm, the neck,
the shirt, the head, the near arm, the box, the hand on the box. A juggle frame is the same stack
from a spec, every part coming from the rig or from jj_light's copies of its rule parts with their
lit edges facing the key light for this theta. The canvas has no edge (a tumbling man throws his
feet past his own 96x96 frame), and every pixel remembers which part put it there, so the drawn maps
can be re-lit afterwards and the lint can measure him part by part.

At theta 0 with the rig's own parts, build() is the rig's frame pixel for pixel (_selftest).
"""
import jj_base as J
import jj_light as L
from jj_base import S, jordan

N4 = J.N4


class Canvas:
    """lib.Canvas without edges, remembering each pixel's part, and each part's own tones as it was
    stamped (before anything later covered it), which is what the lint checks the light on."""

    def __init__(self):
        self.px = {}
        self.owner = {}
        self.counts = {}

    def stamp(self, part, outline=True, owner='?'):
        from collections import Counter
        self.counts.setdefault(owner, Counter()).update(part.values())
        if outline:
            body = set(part)
            for (x, y) in body:
                for dx, dy in N4:
                    q = (x + dx, y + dy)
                    if q not in body:
                        self.px[q] = 'k'
                        self.owner[q] = owner
        for q, k in part.items():
            self.px[q] = k
            self.owner[q] = owner


class JFig:
    """A juggle pose. Each field is a callable taking the Light, returning [(part, outline, owner)]
    in BUILD coordinates, stamped in this order:

        legs      jeans and sneakers
        back      the far arm and anything behind the torso
        neck, shirt (the rig's, lit for the turn, moved by `body`)
        head      (what, tilt, dx, dy): a head (jj_snap's rows), tilted about the neck
        front     the near arm, the box, the hands, in the order given
    """

    def __init__(self, **kw):
        self.legs = None
        self.back = None
        self.body = (0, 0)
        self.head = ('idle', 0, 3, 2)      # v2's slump: the head pushed forward and sunk (jv2_frames)
        self.front = None
        self.fold = 1                      # the tee's folds: 0 pinched at the hip, 1 hanging straight
        self.fx = set()
        for k, v in kw.items():
            if not hasattr(self, k):
                raise AttributeError(k)
            setattr(self, k, v)


NECK_PIVOT = (45, 33)


def head_part(spec):
    """(what, tilt, dx, dy) -> the head part in build coordinates. what: a head name in jj_snap
    ('pain', 'daze', 'idle'...) or ('rows', rows, flopped) for a juggle face. Built the way v2 builds
    its heads (jv2_head.head, janim_heads.head): the expression's face rows, 22 down, which are the
    approved face, under a whole hair map for rows 7-21 with the rat-tail's tip: the shipped v2 flopped
    quiff (jj_snap.flopped_hair) on the fight rig's flopped heads and every face flagged flopped, v2's
    standing greasy hair (jv2_head.hair) on the rest."""
    what, tilt, dx, dy = spec
    if isinstance(what, str):
        rows, flopped = S.head_rows(what), what in S.FLOPPED
    else:
        _, rows, flopped = what
    face = S.amap(rows, S.X0, S.Y0)
    part = {q: k for q, k in face.items() if q[1] >= 22}
    part.update(S.flopped_hair() if flopped else J.V2H.hair())
    if tilt:
        part = S.tilt2(part, tilt, NECK_PIVOT, 'xy')
        S.close_gaps(part)
    return S.shift(part, dx, dy)


# Where each drawn map's light is re-cut, and on which of its tones.
RELIT = {
    'head': ('skin', L.SKIN, 'edcb'),
    'head_hair': ('hair', L.HAIR_GLOSS, 'YAmlji'),
    'hand': ('skin', L.SKIN, 'edcb'),
    'shoe': ('shoe', L.SHOE, '321'),
}


def build(f, theta=0.0, relit=True):
    light = L.Light(theta)
    cv = Canvas()
    bx, by = f.body

    def stamp_list(parts, shift=(0, 0)):
        for part, ol, owner in parts:
            cv.stamp(J.moved(part, *shift) if shift != (0, 0) else part, outline=ol, owner=owner)

    if f.legs:
        stamp_list(f.legs(light))
    if f.back:
        stamp_list(f.back(light), (bx, by))
    cv.stamp(J.moved(L.neck(f.head[2], light), bx, by), owner='neck')
    cv.stamp(J.moved(L.shirt(f.fold, light), bx, by), owner='shirt')
    for (x, y), k in J.V2.DANDRUFF.items():        # jv2_body.dandruff, carried with the body
        q = (x + bx, y + by)
        if cv.px.get(q) in ('R', 'T', 'V', 'v'):
            cv.px[q] = k
            cv.owner[q] = 'dandruff'
    hp = head_part(f.head)
    cv.stamp(J.moved(hp, bx, by), outline=False, owner='head')
    if f.front:
        stamp_list(f.front(light), (bx, by))

    if relit and not light.default:
        target = L.light3(theta)
        base = L.LIGHT3
        # the head: its skin on the skull, its hair on the same skull
        hm = L.part_model(cv.owner, 'head', pad=2.0)
        if hm:
            L.relight_keep_counts(cv.px, cv.owner, {'head'}, hm, base, target, L.SKIN, 'edcb')
            L.relight_keep_counts(cv.px, cv.owner, {'head'}, hm, base, target, L.HAIR_GLOSS, 'YAmlji')
        for name in sorted(set(cv.owner.values())):
            if name.startswith('hand'):
                m = L.part_model(cv.owner, name)
                L.relight_keep_counts(cv.px, cv.owner, {name}, m, base, target, L.SKIN, 'edcb', 0.62)
            elif name.startswith('shoe'):
                m = L.part_model(cv.owner, name)
                L.relight_keep_counts(cv.px, cv.owner, {name}, m, base, target, L.SHOE, '321', 0.62)
    return cv


def close_holes(px, fx=()):
    """A transparent pixel boxed in on four sides becomes keyline (janim_defeat.fill_holes)."""
    if not px:
        return px
    x0, y0, x1, y1 = J.bbox(px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) in px:
                continue
            if all(q in px and q not in fx for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                px[(x, y)] = 'k'
    return px


# ------------------------------------------------------------------------------ the approved idle
def idle_fig():
    """jv2_frames.build(0) as a JFig: the approved v2 idle, from the v2 rig's own parts."""
    V2 = J.V2

    def legs(light):
        far, near = V2.shoes()
        return [(L.legs(light), True, 'legs'), (far, False, 'shoe_far'), (near, False, 'shoe_near')]

    def back(light):
        return [(p, ol, o) for (p, ol), o in zip(V2.far_arm_box(), ('arm_far', 'sleeve_far', 'arm_far'))]

    def front(light):
        arm, sl, hand = V2.near_arm_hip()
        return [(arm[0], True, 'arm_near'), (sl[0], True, 'sleeve_near'), (hand[0], False, 'hand_near'),
                (jordan.box_part(2, 2), False, 'box'),
                (S.amap(V2.FAR_HAND_BOX, 61, 44), False, 'hand_far')]

    return JFig(legs=legs, back=back, head=('idle', 0, 3, 2), front=front, fold=0)


def _selftest():
    cv = build(idle_fig(), 0)
    px = {(x + S.ANCHOR_SHIFT, y): k for (x, y), k in cv.px.items()}
    d = S.pixel_diff(J.image(px, 96, 96), J.approved_sheet().crop((0, 0, 96, 96)))
    print('build(idle_fig()) vs approved jordan_redesign_v2.png f0:', d or 'identical')
    return d is None


if __name__ == '__main__':
    _selftest()
