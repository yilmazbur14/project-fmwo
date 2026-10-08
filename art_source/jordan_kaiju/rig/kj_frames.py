"""The two approval frames: kaiju_mounted_idle and kaiju_breath_charge (W x H, soles on SOLE_Y)."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kj_shade as S  # noqa: E402
import kj_kaiju as KJ  # noqa: E402
import kj_rider as R  # noqa: E402

W, H = KJ.W, KJ.H
# Jordan's build coordinates -> frame: his seat on the back of the skull
RIDER_D = (77, -5)
SPLIT_CHEST = True


def shaded(prims, ramp='hide', **kw):
    part, info = S.shade(prims, ramp, **kw)
    return part, info


def stamp_prims(cv, prims, bias=0.0, seed=None, cast=2, rim=True, **kw):
    part, info = S.shade(prims, 'hide', bias=bias, **kw)
    if seed is not None:
        KJ.bumps(part, seed=seed)
    if rim:
        S.rim_light(part)
    cv.stamp(part, cast=cast)
    return part


def build(charge=False, head='admire'):
    cv = KJ.KCanvas()
    glow = {}
    if charge:
        glow = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.5}
    # plates behind: the far row, then the main row
    lit_parts = []
    for part, g in KJ.plates(glow, 'far'):
        cv.stamp(part, cast=0)
        if glow.get(g):
            lit_parts.append(part)
    for part, g in KJ.plates(glow, 'main'):
        cv.stamp(part, cast=1)
        if glow.get(g):
            lit_parts.append(part)
    fx = set()
    if charge:
        fx |= KJ.glow_halo(cv, lit_parts)
    # the tail
    stamp_prims(cv, KJ.tail_prims(), bias=0.0, seed=3, bounce=0.25)
    # the far leg and foot (each toe its own piece), the far arm (behind the torso)
    stamp_prims(cv, KJ.far_leg_prims(), bias=-0.14, seed=5, bounce=0.2)
    fp = KJ.far_foot_prims()
    stamp_prims(cv, fp[:1], bias=-0.12, bounce=0.2)
    for toe in fp[1:]:
        stamp_prims(cv, [toe], bias=-0.08, cast=1)
    cv.stamp(KJ.claws([(149, 170, 1, 0.3), (143, 171, 1, 0.5)], 3), cast=0)
    up, fore, fingers, tips = KJ.far_arm_parts()
    stamp_prims(cv, up, bias=-0.14)
    stamp_prims(cv, fore, bias=-0.1, cast=1)
    for f in fingers:
        stamp_prims(cv, f, bias=-0.05, cast=1)
    cv.stamp(KJ.claws(tips, 3), cast=0)
    # the torso and its belly scutes
    if SPLIT_CHEST:
        tp = KJ.torso_prims()
        for prims, seed in ((tp[:1], 11), (tp[1:], 12)):        # the belly, then the chest over it
            torso, tinfo = S.shade(prims, 'hide', bias=-0.04, bounce=0.3)
            KJ.bumps(torso, seed=seed)
            S.rim_light(torso)
            KJ.belly(torso, tinfo)
            cv.stamp(torso)
    else:
        torso, tinfo = S.shade(KJ.torso_prims(), 'hide', bias=-0.04, bounce=0.3)
        KJ.bumps(torso, seed=11)
        S.rim_light(torso)
        KJ.belly(torso, tinfo)
        cv.stamp(torso)
    # the near leg (the hip cut) and foot (each toe its own piece)
    nl, _ = S.shade(KJ.near_leg_prims(), 'hide', bias=-0.02, bounce=0.3)
    KJ.bumps(nl, seed=13)
    S.rim_light(nl)
    KJ.seam(nl, [(64, 129), (70, 124), (78, 121), (86, 122), (93, 126)])     # the hip cut
    cv.stamp(nl)
    nfp = KJ.near_foot_prims()
    stamp_prims(cv, nfp[:1], bias=0.0, bounce=0.2)
    for toe in nfp[1:]:
        stamp_prims(cv, [toe], bias=0.04, cast=1)
    cv.stamp(KJ.claws([(99, 170, 1, 0.2), (92, 172, 1, 0.6)], 3), cast=0)
    # the head and jaw
    open_by = 8 if charge else 0
    jaw = KJ.jaw_part(open_by)
    cv.stamp(jaw)
    hd, _ = KJ.head_part(charge)
    cv.stamp(hd)
    fx |= KJ.mouth(cv, open_by, glow=charge, jaw_px=jaw, head_px=hd)
    # the near arm: upper arm (the shoulder cut), forearm, palm, fingers, claws
    up, fore, palm, fingers, tips = KJ.near_arm_parts()
    ua, _ = S.shade(up, 'hide', bias=0.02, bounce=0.2)
    S.rim_light(ua)
    KJ.seam(ua, [(80, 99), (86, 102), (95, 100)])                            # the shoulder cut
    cv.stamp(ua)
    stamp_prims(cv, fore, bias=0.02, cast=1, bounce=0.2)
    stamp_prims(cv, palm, bias=0.04, cast=1)
    for f in fingers:
        stamp_prims(cv, f, bias=0.08, cast=1)
    cv.stamp(KJ.claws(tips, 3.5), cast=0)
    KJ.gloss(cv.px)
    KJ.creases(cv.px)
    KJ.star_mark(cv.px)
    if charge:
        fx |= KJ.sparks(cv, [(30, 132), (47, 116), (55, 99), (18, 140), (66, 84)])
    pre = dict(cv.px)                                   # the kaiju (and its effects) before Jordan
    # Jordan
    rider = {q: k for q, k in R.build(head, *RIDER_D).items() if 0 <= q[0] < W and 0 <= q[1] < H}
    for q, k in rider.items():
        cv.px[q] = k
    if not charge:
        # a glint off the open box: the idle's own sparkle (white, pink arms), free of keylines
        bx, by = 160, 22
        for q, k in {(bx, by): 'W', (bx + 1, by): 'Q', (bx - 1, by): 'Q', (bx, by + 1): 'Q', (bx, by - 1): 'Q'}.items():
            if q not in cv.px:
                cv.px[q] = k
                fx.add(q)
    fx |= KJ.close_holes(cv.px)
    fx = {q for q in fx if q in cv.px and cv.px[q] in KJ_FX_KEYS and q not in rider}
    LAST['pre'], LAST['rider'] = pre, rider
    return cv.px, fx


LAST = {}


def layers(charge=False, head=None):
    """The frame as three layers that composite (bottom to top) to exactly build(): 'kaiju' (whole,
    including what Jordan hides), 'fx' (glow halo, sparks, the mouth flare, the box glint: no
    keyline), 'rider' (Jordan). Returns (final px, fx set, {layer: px})."""
    head = head or ('grin' if charge else 'admire')
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


KJ_FX_KEYS = set('XKJI8WQ')


if __name__ == '__main__':
    for name, ch in (('idle', False), ('charge', True)):
        px, fx = build(ch)
        im = K.render(px, W, H)
        print(K.look(im, 'draft_%s_4x.png' % name, 4))
        print(name, K.stats(im))
