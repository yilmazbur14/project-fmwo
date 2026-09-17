"""Carter's entrance, frame by frame.

Phases
  0..4    materialise - he knits together out of the aura, back turned
  5..8    mark flare  - loopable pulse, the sigil is the hero
  9..13   turn        - back -> 3/4 back -> profile -> 3/4 front -> front
  14..16  settle      - signature crossed pose, then the approved idle
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, ring,
                 erode, poly, ell, PALC, BLACK, bayer, band)
import parts as P
import aura as AU
import poses as PO
import render as R
import intro_lib as IL
from intro_lib import (MARK_C, compose, jitter, sweep, squeeze_specs, tint,
                       field_mask, sigil_paint, sigil_bloom, rim_light,
                       ground_glow, aura_heat, hsq_canvas, edge_shade, rim_edge)

SIGIL = None


def sigil_mask():
    global SIGIL
    if SIGIL is None:
        SIGIL = inter(PO.sigil(), PO.back_jacket())
    return SIGIL


def back_body():
    cv = Canvas()
    PO.draw_back(cv)
    return cv


# ================================================================ materialise

def gather_specs(t, k=0):
    """wisps converging on the mark; t=0 far and thin, t=1 pulled into him.

    Kept steep and columnar rather than radial - a pinwheel reads as decoration,
    a rising column reads as something arriving."""
    cx, cy = MARK_C
    out = []
    # steep side arms: they come in high and sweep down onto his shoulders
    for i, (sx, sy) in enumerate(((16.0, 6.0), (79.0, 4.0), (8.0, 30.0),
                                  (87.0, 27.0), (24.0, -2.0), (71.0, -3.0))):
        ex = cx + (sx - cx) * (0.18 + 0.10 * (1.0 - t))
        ey = cy + (sy - cy) * (0.30 + 0.16 * (1.0 - t))
        wob = math.sin(k * 0.8 + i * 1.3) * 3.0
        pts = [(ex, ey),
               (ex + (sx - ex) * 0.34 + wob, ey + (sy - ey) * 0.30 - 4.0),
               (ex + (sx - ex) * 0.72 - wob, ey + (sy - ey) * 0.72 - 2.0),
               (sx + (ex - sx) * t * 0.55, sy + (ey - sy) * t * 0.55)]
        out.append((pts, 3.6 + 6.8 * t, 1.1))
    # rising off the floor: the column he condenses inside
    for i, bx in enumerate((30.0, 38.5, 47.5, 56.5, 65.0)):
        lift = 30.0 + 46.0 * t
        sway = 3.4 * math.sin(k * 0.9 + i * 1.7)
        out.append(([(bx, 95.0),
                     (bx + sway, 95.0 - lift * 0.40),
                     (bx - sway * 0.8, 95.0 - lift * 0.74),
                     (bx + sway * 0.4, 95.0 - lift)],
                    3.2 + 6.8 * t, 1.1))
    return out


def gather_sparks(t, k):
    cx, cy = MARK_C
    pts = []
    for i in range(9):
        a = i * 2.0 * math.pi / 9 + 0.9 + k * 0.23
        r = (58.0 - 30.0 * t) * (0.82 + 0.2 * math.sin(i * 2.1 + k))
        x = cx + math.cos(a) * r * 0.94
        y = cy + math.sin(a) * r * 1.06
        if 1.0 < x < W - 1 and 1.0 < y < H - 1:
            pts.append((x + 0.5, y + 0.5))
    return pts


# per-stage: squeeze, reveal threshold, void stain on formed flesh, crown blend
MAT = [
    # k=0 has no body at all - only the gathering wisps and the ember seed
    dict(t=0.00, sq=None, thr=None, void=1.00, crown=0.00),
    dict(t=0.30, sq=0.76, thr=0.32, void=0.80, crown=0.00),
    dict(t=0.58, sq=0.89, thr=0.58, void=0.50, crown=0.18),
    dict(t=0.82, sq=0.96, thr=0.86, void=0.22, crown=0.55),
    dict(t=1.00, sq=1.00, thr=9.99, void=0.00, crown=1.00),
]


def seed_spark(cv, k, level):
    """the ember that becomes the mark - visible before the body exists."""
    cx, cy = MARK_C
    r = 2.1 + 1.7 * level
    core = ell(cx, cy, r, r * 0.8)
    halo = ell(cx, cy, r + 2.6, r * 0.8 + 2.0)
    cv.paint(bayer(sub(halo, core), 7 + int(4 * level), k), PALC['Y'])
    cv.paint(core, PALC['y'])
    cv.paint(erode(core, 1), PALC['x'] if level > 0.5 else PALC['X'])


def frame_materialise(k):
    st = MAT[k]
    t = st['t']
    body = Canvas()
    if st['thr'] is not None:
        full = back_body()
        if st['sq'] and st['sq'] < 0.999:
            # the whole form condenses here, head included - this is the shape
            # coalescing, not a body turning, so no head exemption
            full = hsq_canvas(full, st['sq'], keep_head=False)
        bm = full.mask_of()
        thr = st['thr']
        # Four SOLID bands with a coarse noisy boundary, not a dithered wash.
        # A 4x4 Bayer fill reads as TV static once it is blown up 3x; letting
        # the field's own blob noise cut the band edges gives chunky, organic
        # shapes and a front you can actually see travelling outward.
        got = field_mask(thr, bm)
        half = IL.field_band(thr, thr + 0.17, bm)
        shell = IL.field_band(thr + 0.17, thr + 0.32, bm)
        haze = IL.field_band(thr + 0.32, thr + 0.58, bm)
        for y in range(H):
            for x in range(W):
                if (got[y][x] or half[y][x]) and full.px[y][x] is not None:
                    body.px[y][x] = full.px[y][x]
        if st['void'] > 0.01:
            tint(body, got, PALC['T'], st['void'] * 0.74, skip_black=True)
        tint(body, half, PALC['T'], 0.82)
        body.paint(shell, PALC['S'])
        # only the outermost band breaks up, and in 2x2 blocks so it reads as
        # matter still gathering rather than noise
        body.paint(IL.block_dither(haze, 10, 2, k), PALC['T'])
        body.paint(IL.block_dither(haze, 4, 2, k + 7), PALC['S'])
        # the forming front: a solid bright line riding the edge of the reveal
        fringe = IL.field_band(thr - 0.020, thr + 0.016, bm)
        body.paint(fringe, PALC['Q'])
        body.paint(IL.field_band(thr - 0.008, thr + 0.006, bm), PALC['P'])
        # re-close the silhouette so it never looks torn
        body.outline(body.mask_of())

    crown = st['crown']
    specs = gather_specs(t, k)
    sparks = gather_sparks(t, k)
    if crown > 0.01:
        # grow straight into the shape the flare phase opens on, so frame 4
        # and frame 5 share an aura and the phase join is invisible
        cr = IL.entr_specs(k, scale=0.55 + 0.45 * crown,
                           reach=0.42 + 0.58 * crown)
        specs = specs + cr
        sp2 = IL.entr_sparks(k)
        sparks = sparks + sp2[:int(round(len(sp2) * crown))]
    cv = compose(body, specs, sparks, haze_in=4 + int(6 * t), haze_out=int(4 * t),
                 off=k, hot=t > 0.25)
    if crown > 0.01:
        IL.soften(cv, grow(body.mask_of(), 1), near=9, far=28, seed=k)
    if st['thr'] is not None:
        sg = sigil_mask()
        if st['sq'] and st['sq'] < 0.999:
            sg = IL.hsq_mask(sg, st['sq'], keep_head=False)
        sg = inter(sg, cv.mask_of())
        sigil_paint(cv, sg, 0.20 + 0.25 * t)
        sigil_bloom(cv, sg, 0.25 * t)
    else:
        seed_spark(cv, k, 0.45)
    return cv


# ================================================================ mark flare

FLARE_LV = [0.14, 0.55, 1.00, 0.48]


def frame_flare(i):
    lv = FLARE_LV[i]
    k = i + 5
    body = back_body()
    bm = body.mask_of()
    sg = sigil_mask()
    # bloom FIRST, emblem last: the mark and its dark contour have to be painted
    # over the glow or the flare swallows the shape at its peak
    sigil_bloom(body, sg, lv, host=PO.back_jacket())
    rim_light(body, bm, lv, reach=34.0 + 12.0 * lv)
    sigil_paint(body, sg, lv)

    # one spec set the whole pulse through - swapping sets mid-loop pops the
    # tendril count, so the size is modulated instead
    specs = IL.entr_specs(k, scale=0.80 + 0.36 * lv, reach=0.82 + 0.26 * lv)
    cv = compose(body, specs, IL.entr_sparks(k),
                 haze_in=5 + int(6 * lv), haze_out=int(5 * lv), off=k)
    aura_heat(cv, grow(bm, 1), lv)
    IL.soften(cv, grow(bm, 1), near=9 + int(4 * lv), far=30, seed=k)
    ground_glow(cv, lv)
    if lv >= 0.95:
        # spokes of light bursting off the peak
        cx, cy = MARK_C
        for i2 in range(12):
            a = i2 * math.pi / 6 + 0.26
            for r in range(14, 40):
                x = int(round(cx + math.cos(a) * r * 0.95))
                y = int(round(cy + math.sin(a) * r * 1.05))
                if not (0 <= x < W and 0 <= y < H):
                    break
                if bm[y][x]:
                    continue
                if (r + i2) % 3 == 0:
                    cv.px[y][x] = PALC['X'] if r < 24 else PALC['y']
    return cv


# ================================================================ turn
# He pivots so his left shoulder swings toward the camera: at the profile beat
# he faces screen-left.  phi 0 = back, 90 = profile, 180 = front.
# silhouette squeeze = sqrt(cos^2 phi + D^2 sin^2 phi), D = body depth / width.

DEPTH = 0.45
# phi, arm swing toward the crossed pose, how lit the mark still reads
# The arm swing starts DURING the turn, not after it: coming round with the
# arms hanging and then snapping to folded reads as a cut, so by the time he
# faces front the forearms are already three quarters of the way up and the
# fold lands as a deliberate beat rather than a pop.
TURN = [
    dict(phi=40.0, arm=0.00, mark=0.40, bridge=0.00),
    dict(phi=90.0, arm=0.00, mark=0.46, bridge=0.00),
    dict(phi=132.0, arm=0.20, mark=0.00, bridge=0.00),
    dict(phi=162.0, arm=0.48, mark=0.00, bridge=0.22),
    dict(phi=180.0, arm=0.78, mark=0.00, bridge=0.58),
]


def sq_of(phi):
    r = math.radians(phi)
    return math.sqrt(math.cos(r) ** 2 + DEPTH ** 2 * math.sin(r) ** 2)


def front_body(arm_t=0.0):
    """approved standing body; arm_t lerps the arms toward the crossed pose."""
    cv = Canvas()
    if arm_t <= 0.001:
        R.body(cv)
        # bind the wraps: the shipped render leaves them as flat cream capsules
        IL.wrap_bands_both(cv, union(P.wraps_wrist(), P.wraps_fist()),
                           (22.0, 64.0), (19.8, 78.2))
    else:
        import intro_arms as IA
        IA.draw_lerp(cv, arm_t)
    return cv


def frame_turn(i):
    import intro_profile as IP
    st = TURN[i]
    phi, k = st['phi'], 9 + i
    s = sq_of(phi)
    if abs(phi - 90.0) < 1.0:
        # edge-on: the squeezed back view, then the back-lit pivot treatment.
        # turn_scale holds the skull near full width while the ribcage narrows
        # to 0.45, which is exactly the read that says "side on".
        body = back_body()
        sg = sigil_mask()
        sigil_bloom(body, sg, 0.70, host=PO.back_jacket())
        sigil_paint(body, sg, 0.80)
        body = IP.pivot_treatment(hsq_canvas(body, s))
    elif phi < 90.0:
        body = back_body()
        sg = sigil_mask()
        sigil_bloom(body, sg, st['mark'] * 0.8, host=PO.back_jacket())
        rim_light(body, body.mask_of(), st['mark'] * 0.8, reach=32.0)
        sigil_paint(body, sg, st['mark'])
        body = hsq_canvas(body, s)
        # the mark swings toward the trailing (screen-right) edge
        body = IL.shift_canvas(body, int(round(4.0 * (1.0 - s))))
    else:
        body = front_body(arm_t=st['arm'])
        if phi < 179.0:
            body = hsq_canvas(body, s)
            body = IL.shift_canvas(body, -int(round(5.0 * (1.0 - s))))
        IP.ignite_eyes(body, max(0.0, min(1.0, (phi - 110.0) / 70.0)))
    # leading (screen-left) edge lit, trailing edge rolling away
    if phi < 175.0:
        rim_edge(body, -1, 'X', 0.55 if phi > 90 else 0.35)
        edge_shade(body, 1, 0.5)

    lean = 10.0 * math.sin(math.radians(phi)) * (1.0 if phi < 90 else -1.0)
    specs = sweep(squeeze_specs(IL.entr_specs(k, 0.94, 0.96), 0.55 + 0.45 * s),
                  lean, droop=1.8)
    sp = IL.entr_sparks(k)
    br = st['bridge']
    if br > 0.01:
        # the last turn frame hands over to the sheet's own crown, so cutting
        # into approved frame 1 next reads as the aura flaring up on the
        # signature rather than as a change of style
        specs = specs + IL.scale_w(jitter(AU.FLARE, k, 1.2), br, 0.45 + 0.55 * br)
        sp = sp + AU.FLARE_SPARKS[:int(round(len(AU.FLARE_SPARKS) * br))]
    cv = compose(body, specs, sp, haze_in=8, haze_out=3, off=k)
    aura_heat(cv, grow(body.mask_of(), 1), 0.30 + 0.45 * st['mark'])
    IL.soften(cv, grow(body.mask_of(), 1), near=9, far=28, seed=k)
    return cv


# ================================================================ settle
# 14 = the approved signature pose, 15 = arms dropping, 16 = the approved idle.
# The two approved frames are spliced in verbatim by build_intro.py so the
# handover to the fight's idle is pixel exact.

SETTLE_ARM = [1.00, 0.45, 0.00]


def frame_settle(i):
    body = front_body(arm_t=SETTLE_ARM[i])
    k = 14 + i
    lv = (0.55, 0.30, 0.18)[i]
    # this frame is sandwiched between the two verbatim approved frames, so it
    # uses the sheet's own aura rather than the entrance set
    specs = IL.scale_w(jitter(AU.FLARE, k, 1.3), 0.70 + 0.30 * lv, 0.78 + 0.22 * lv)
    cv = compose(body, specs, AU.FLARE_SPARKS,
                 haze_in=6 + int(5 * lv), haze_out=int(4 * lv), off=k)
    aura_heat(cv, grow(body.mask_of(), 1), 0.35 * lv)
    return cv
