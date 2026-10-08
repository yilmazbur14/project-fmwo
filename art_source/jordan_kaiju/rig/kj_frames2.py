"""The two approval frames at the architect's layout scale: kaiju_mounted_idle, kaiju_breath_charge.

build() draws on the working canvas; layers() splits it into kaiju / fx / rider; frame() crops
everything to the delivered frame and returns the anchors in frame coordinates.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kj_shade as S  # noqa: E402
import kj_kaiju2 as KJ  # noqa: E402
import kj_rider as R  # noqa: E402

SEAT_DESIGN = (126.0, 65.5)          # the top-back of the skull at the neck base
JORDAN_SEAT = (49, 70)               # his seat in his own build coordinates (hips centre, bottom)
FX_KEYS = set('XKJI8WQ')
LAST = {}


def rider_offset():
    sx, sy = KJ.Ti(*SEAT_DESIGN)
    return sx - JORDAN_SEAT[0], sy - JORDAN_SEAT[1]


def shaded(prims, bias=0.0, seed=None, rim=True, bounce=0.25, **kw):
    part, info = S.shade(prims, 'hide', bias=bias, bounce=bounce, **kw)
    if seed is not None:
        KJ.bumps(part, seed=seed)
        KJ.scales(part, seed=seed)
    if rim:
        S.rim_light(part)
    return part, info


def stamp(cv, prims, cast=2, floor=None, **kw):
    part, _ = shaded(prims, **kw)
    cv.stamp(part, cast=cast, floor=floor)
    return part


def build(charge=False, head=None):
    head = head or ('grin' if charge else 'admire')
    cv = KJ.KCanvas()
    glow = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.5} if charge else {}
    s_front = KJ.ridge_s_at_index(KJ.TAIL_FRONT_END)
    lit_parts, fx = [], set()
    plate_rows = {row: KJ.plates(glow, row) for row in ('far', 'main')}

    def plate_pass(front):
        for row in ('far', 'main'):
            for (part, g), (s_, size, gg) in zip(plate_rows[row], KJ.PLATES):
                if (s_ < s_front) == front:
                    cv.stamp(part, cast=0 if row == 'far' else 1, floor=KJ.TAIL_FLOOR)
                    if glow.get(g):
                        lit_parts.append(part)

    plate_pass(front=False)                                           # the back's plates, behind all
    stamp(cv, KJ.tail_back_prims(), seed=3)                           # the tail's root
    stamp(cv, KJ.far_leg_prims(), bias=-0.14, seed=5, bounce=0.2)
    fp = KJ.far_foot_prims()
    far_foot = stamp(cv, fp[:1], bias=-0.12, bounce=0.2)
    for toe in fp[1:]:
        stamp(cv, [toe], bias=-0.08, cast=1)
    cv.stamp(KJ.claws([(149, 170, 1, 0.3), (143, 171, 1, 0.5)], 3), cast=0)
    up, fore, fingers, tips = KJ.far_arm_parts()
    stamp(cv, up, bias=-0.14)
    stamp(cv, fore, bias=-0.1, cast=1)
    for f in fingers:
        stamp(cv, f, bias=-0.05, cast=1)
    cv.stamp(KJ.claws(tips, 3), cast=0)
    tp = KJ.torso_prims()                                             # the belly, the chest over it
    for prims, seed in ((tp[:1], 11), (tp[1:], 12)):
        torso, tinfo = shaded(prims, bias=-0.04, seed=seed, bounce=0.3)
        region = KJ.belly(torso, tinfo)
        cv.stamp(torso)
    nl, _ = shaded(KJ.near_leg_prims(), bias=-0.02, seed=13, bounce=0.3)
    KJ.seam(nl, [(64, 129), (70, 124), (78, 121), (86, 122), (93, 126)])          # the hip seam
    cv.stamp(nl)
    nfp = KJ.near_foot_prims()
    stamp(cv, nfp[:1], bounce=0.2)
    for toe in nfp[1:]:
        stamp(cv, [toe], bias=0.04, cast=1)
    cv.stamp(KJ.claws([(99, 170, 1, 0.2), (92, 172, 1, 0.6)], 3), cast=0)
    plate_pass(front=True)                                            # the tail curl's plates
    tf, _ = shaded(KJ.tail_front_prims(), seed=4)
    KJ.seam(tf, [(47, 163), (53, 165), (60, 167.5), (64, 172)])                # the tail-base seam (its swivel)
    cv.stamp(tf, floor=KJ.TAIL_FLOOR)
    open_by = 8 if charge else 0                                      # the head
    jaw = KJ.jaw_part(open_by)
    cv.stamp(jaw)
    hd = KJ.head_part()
    cv.stamp(hd)
    fx |= KJ.mouth(cv, open_by, glow=charge, jaw_px=jaw, head_px=hd)
    up, fore, palm, fingers, tips = KJ.near_arm_parts()               # the near arm
    ua, _ = shaded(up, bias=0.02, bounce=0.2)
    KJ.seam(ua, [(80, 99), (86, 102), (95, 100)])                     # the shoulder seam
    cv.stamp(ua)
    stamp(cv, fore, bias=0.02, cast=1, bounce=0.2)
    stamp(cv, palm, bias=0.04, cast=1)
    for f in fingers:
        stamp(cv, f, bias=0.08, cast=1)
    cv.stamp(KJ.claws(tips, 3.5), cast=0)
    KJ.gloss(cv.px)
    KJ.creases(cv.px)
    KJ.folds(cv.px)
    KJ.star_mark(cv.px)
    if charge:
        fx |= KJ.glow_halo(cv, lit_parts)
        fx |= KJ.sparks(cv, [(48, 150), (44, 128), (52, 108), (40, 140), (47, 163)])
    pre = dict(cv.px)
    dx, dy = rider_offset()
    rider = {q: k for q, k in R.build(head, dx, dy).items() if 0 <= q[0] < cv.w and 0 <= q[1] < cv.h}
    for q, k in rider.items():
        cv.px[q] = k
    if not charge:
        bx, by = 83 + dx, 27 + dy                       # a glint off the open box (the idle's sparkle)
        for q, k in {(bx, by): 'W', (bx + 1, by): 'Q', (bx - 1, by): 'Q', (bx, by + 1): 'Q', (bx, by - 1): 'Q'}.items():
            if q not in cv.px:
                cv.px[q] = k
                fx.add(q)
    fx |= KJ.close_holes(cv.px)
    fx = {q for q in fx if q in cv.px and cv.px[q] in FX_KEYS and q not in rider}
    LAST.update(pre=pre, rider=rider)
    return cv.px, fx


def layers(charge=False, head=None):
    final, fx = build(charge, head)
    pre, rider = LAST['pre'], LAST['rider']
    kaiju = {q: k for q, k in final.items() if q not in rider and q not in fx}
    kaiju.update({q: k for q, k in pre.items() if q in rider and q not in fx})
    fxl = {q: final[q] for q in fx}
    rl = {q: final[q] for q in rider}
    comp = dict(kaiju)
    comp.update(fxl)
    comp.update(rl)
    assert comp == final, 'layers do not composite to the frame'
    return final, fx, {'kaiju': kaiju, 'fx': fxl, 'rider': rl}


if __name__ == '__main__':
    for name, ch in (('idle', False), ('charge', True)):
        px, fx = build(ch)
        im = K.render(px, KJ.CW, KJ.CH)
        print(K.look(im, 'v2_%s_3x.png' % name, 3))
        print(name, K.stats(im), K.bbox(px), {k: len(v) for k, v in K.audit(px, fx).items()})
