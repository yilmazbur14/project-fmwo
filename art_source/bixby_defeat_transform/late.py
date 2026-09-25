"""Transformation frames 10-25: the beast, in the approved Hades design. Every frame keeps the purpose
and cue of the shipped sequence (LiamEntranceLayout / BixbyBeastIntro):

  10-14  he swells (scale 0.55 .. 0.95) and rises (lift 26 .. 38) as a blood-red silhouette with mint
         eyes. The old sequence grew a horn per head here; the design has no horns, so the beat per
         frame is the heads IGNITING instead: 11 the middle head's drop ears catch fire, 12 the left
         head's, 13 the right head's and the white tail tip, 14 the back splits where the wings will tear.
  15-17  at full size and hover height, the wings tear out (15), unfurl (16) and snap open (17).
  18-19  it implodes (dark, light sucked in) and holds (a white-hot core in the chest).
  20     it detonates: the beast black against the flash, eyes blazing.
  21-22  the beast stands in the smoke, cold: eyes dark, ear tips and wing edges out.
  23     the middle head's eyes and ears light.  24  the side heads' and the wings' light.
  25     = the approved hover frame 0 (frame.build('up', 0)), lifted HOVER_HEIGHT: where the beast takes over.
"""
import common as C
import faces
import frame
import fx
import pose as PS
import sidemaps
import midmaps
import tfx
from pal import amap

AX, AY = C.T_ANCHOR
LIFT = [0, 0, 0, 0, 0, 0, 0, 5, 13, 21, 26, 30, 34, 36, 38, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40]
SPEC = {
    10: dict(scale=0.55, wings=0.0, lit='', tail=False, rays=(14, 40, 150, 0.1)),
    11: dict(scale=0.68, wings=0.0, lit='M', tail=False, rays=(15, 44, 158, 0.5)),
    12: dict(scale=0.78, wings=0.0, lit='ML', tail=False, rays=(16, 48, 166, 0.9)),
    13: dict(scale=0.88, wings=0.0, lit='MLR', tail=True, rays=(17, 52, 172, 1.3)),
    14: dict(scale=0.95, wings=0.0, lit='MLR', tail=True, rays=(18, 56, 178, 1.7)),
    15: dict(scale=1.0, wings=0.58, lit='MLR', tail=True, rays=(19, 58, 184, 2.1)),
    16: dict(scale=1.0, wings=0.82, lit='MLR', tail=True, rays=(20, 60, 190, 2.5)),
    17: dict(scale=1.0, wings=1.0, lit='MLRW', tail=True, rays=(22, 62, 196, 2.9)),
}

# Re-keying the approved colours into the transformation's blood-red: structure lines darkest, whites
# brightest, every ramp folded onto the fur ramp q r s t u.
TINT = {'k': 'q', 'q': 'q', 'r': 'r', 's': 'r', 't': 's', 'u': 't', 'v': 'u',
        'a': 'q', 'b': 'q', 'c': 'r', 'd': 'r', 'e': 's', 'f': 's',
        'z': 's', 'y': 's', 'x': 't', 'w': 'u',
        'g': 'r', 'G': 's', 'o': 't', 'O': 'u',
        'l': 'q', 'L': 'r', 'm': 's', 'M': 't',
        'n': 'r', 'N': 's', 'p': 't', 'P': 'u', 'Y': 'u',
        'S': 'r', 'T': 's', 'U': 't', 'W': 'u',
        'A': 'q', 'B': 'r', 'C': 'r',
        'h': 'q', 'i': 's', 'j': 't'}
DARKEN = {'u': 'r', 't': 'r', 's': 'q', 'r': 'q', 'q': 'A'}
MINT = set('hijW')


def beast_origin(lift):
    return (C.BEAST_IN_T[0], C.BEAST_IN_T[1] - lift)


#FEATURE PIXELS (beast-frame texels of the approved hover pose)

def ear_fire(head):
    if head == 'M':
        return faces.ear_fire(frame.xf(frame.MID, 0))
    right = faces.ear_fire(frame.xf(frame.SIDE, 0))
    return right if head == 'R' else {(191 - x, y): k for (x, y), k in right.items()}


def eye_centres():
    """Centres of each eye's mint, per head: {'M': [...], 'L': [...], 'R': [...]}."""
    def centre(part):
        mint = [p for p, k in part.items() if k in 'ijW']
        return (sum(p[0] for p in mint) / len(mint), sum(p[1] for p in mint) / len(mint))
    right, left = midmaps.eye_parts(0, PS.MID_DY0)
    far = amap(sidemaps.FAR_EYE, sidemaps.FAR_EYE_XY[0] + PS.SIDE_MDX0, sidemaps.FAR_EYE_XY[1] + PS.SIDE_MDY0)
    near = amap(sidemaps.NEAR_EYE, sidemaps.NEAR_EYE_XY[0] + PS.SIDE_MDX0, sidemaps.NEAR_EYE_XY[1] + PS.SIDE_MDY0)
    R = [centre(far), centre(near)]
    return {'M': [centre(left), centre(right)], 'R': R, 'L': [(191 - x, y) for (x, y) in R]}


def tail_tip_pixels(keys):
    tip = PS.tail_tip()
    return {p for p in tip if keys.get(p) in ('x', 'w', 'y')}


#THE SILHOUETTE STAGES

def stage_pose(wings, lit, wings_lit):
    P = PS.make()
    if wings <= 0:
        P['hide'] = ('wings',)
    elif wings < 1:
        P['wings'] = PS.wing_moved(PS.WING_UP, sx=wings, sy=wings)
    P['wing_glow'] = 1 if wings_lit else 0
    P['mid'] = dict(ears=1 if 'M' in lit else 0)
    P['side'] = dict(ears=1 if 'R' in lit else 0)
    P['side_left'] = dict(ears=1 if 'L' in lit else 0)
    return P


def tinted(P, lit, tail, wings_lit, eyes=True, dark=False):
    keys = PS.build(P).px
    keep = set()
    for head in lit:
        if head in 'MLR':
            keep |= {p for p, k in ear_fire(head).items() if keys.get(p) == k}
    if tail:
        keep |= tail_tip_pixels(keys)
    if wings_lit:
        for side in (1, -1):
            m = PS.wing_membrane(P['wings'])
            for (x, y), k in m.items():
                q = (x, y) if side > 0 else (191 - x, y)
                if k in 'uvP' and keys.get(q) == k:
                    keep.add(q)
    out = {}
    for p, k in keys.items():
        if p in keep and not dark:
            out[p] = k
        elif eyes and k in MINT and (k != 'W' or any(keys.get((p[0] + dx, p[1] + dy)) in 'hij'
                                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))):
            out[p] = k if not dark else {'j': 'i', 'W': 'i', 'i': 'h', 'h': 'q'}[k]
        else:
            t = TINT[k]
            out[p] = DARKEN[t] if dark else t
    return out


def rimmed(keys, dark=False):
    """A readable edge on the scaled silhouette: a lit rim, brightest on the top and left."""
    mask = set(keys)
    edge = C.inner_edge(mask)
    for p in edge:
        k = keys[p]
        if k in MINT or k in ('x', 'w', 'y', 'v', 'P', 'Y'):
            continue
        up = (p[0], p[1] - 1) not in mask or (p[0] - 1, p[1]) not in mask
        if dark:
            keys[p] = 'r' if up else 'q'
        else:
            keys[p] = 'u' if up else 't'
    return keys


def silhouette(i, dark=False, eyes=True, wings=None, lit=None, tail=None, wings_lit=None, scale=None):
    """Body layer (T-frame key dict) and its mask for a stage."""
    s = SPEC.get(i, SPEC[17])
    scale = s['scale'] if scale is None else scale
    wings = s['wings'] if wings is None else wings
    lit = s['lit'] if lit is None else lit
    tail = s['tail'] if tail is None else tail
    wings_lit = ('W' in lit) if wings_lit is None else wings_lit
    P = stage_pose(wings, lit, wings_lit)
    keys = tinted(P, lit, tail, wings_lit, eyes=eyes, dark=dark)
    keys = tfx.resample(keys, C.BEAST_FW, C.BEAST_FH, scale, C.BEAST_ANCHOR)
    keys = rimmed(keys, dark)
    ox, oy = beast_origin(LIFT[i])
    body = C.shift(keys, ox, oy)
    return body, set(body)


def scale_pt(p, f):
    return (C.BEAST_ANCHOR[0] + (p[0] - C.BEAST_ANCHOR[0]) * f, C.BEAST_ANCHOR[1] + (p[1] - C.BEAST_ANCHOR[1]) * f)


def to_t(p, lift):
    ox, oy = beast_origin(lift)
    return (p[0] + ox, p[1] + oy)


def swell(i):
    """10-17."""
    s = SPEC[i]
    lift = LIFT[i]
    gy = AY - lift
    back, front = {}, {}
    body, m = silhouette(i)
    n, r0, r1, ph = s['rays']
    tfx.rays(back, AX, gy - 60 * s['scale'], n, r0, r1, phase=ph)
    tfx.ground_disc(back, AX, AY - 5, 34, 7, level=0.5)
    cy = gy - 60 * s['scale']
    sc = s['scale']
    seeds = [(AX - 18 * sc, cy + 26 * sc, 2.6), (AX + 16 * sc, cy + 24 * sc, 0.6), (AX, cy + 38 * sc, 1.57),
             (AX - 34 * sc, cy + 30 * sc, 2.0), (AX + 34 * sc, cy + 32 * sc, 1.1)]
    tfx.crack_lines(body, m, seeds, level=3, seed=21 + i, length=8 + 14 * sc)
    tfx.rim_flames(front, m, t=i, height=6, seed=5 + i, dense=3)
    tfx.ember_swirl(front, AX, gy - 20, t=i, n=24, rx=58, ry=34, seed=13 + i)
    # the beat of each frame: a head igniting, the tail tip catching, the back splitting, the wings
    new = {11: 'M', 12: 'L', 13: 'R'}.get(i)
    if new:
        pts = list(ear_fire(new))
        xs = [scale_pt(p, sc)[0] for p in pts]
        ys = [scale_pt(p, sc)[1] for p in pts]
        x0, y0 = to_t((min(xs), min(ys)), lift)
        x1, y1 = to_t((max(xs), max(ys)), lift)
        tfx.burst(front, (x0 - 6, y0 - 4, x1 + 6, y1 + 8), 16, seed=41 + i)
    if i == 13:
        tx, ty = to_t(scale_pt((12, 104), sc), lift)
        tfx.burst(front, (tx - 8, ty - 12, tx + 8, ty + 6), 10, seed=61, hot_ratio=0.9, sizes=(1, 2))
    if i == 14:
        for bx in (AX - 30, AX + 30):
            tfx.crack_lines(body, m, [(bx, gy - 72, 1.2), (bx, gy - 68, 4.4), (bx, gy - 70, -1.57)], level=3,
                            seed=61 + bx, length=8)
    if i >= 15:
        tfx.burst(front, (AX - 96, gy - 120, AX + 96, gy - 40), 18 + 10 * (i - 15), seed=71 + i, hot_ratio=0.6)
    return back, body, front


def implode(i):
    """18: collapsing inward. 19: the held breath before the blast."""
    lift = LIFT[i]
    gy = AY - lift
    back, front = {}, {}
    body, m = silhouette(i, dark=True, eyes=(i == 18), scale=1.0, wings=1.0, lit='', tail=False, wings_lit=False)
    if i == 18:
        cy = gy - 60
        tfx.crack_lines(body, m, [(AX - 18, cy + 26, 2.6), (AX + 16, cy + 24, 0.6), (AX, cy + 38, 1.57)],
                        level=2, seed=31, length=18)
        tfx.implode_streaks(front, AX, gy - 60, 106, 42, n=26, seed=5)
        tfx.ground_disc(back, AX, AY - 5, 30, 6, level=0.4)
    else:
        cx, cy = AX, gy - 58
        for (dx, dy, k) in ((0, 0, tfx.WHITE), (1, 0, 'Y'), (-1, 0, 'Y'), (0, 1, 'Y'), (0, -1, 'Y'),
                            (2, 0, 'P'), (-2, 0, 'P'), (0, 2, 'P'), (0, -2, 'P'), (1, 1, 'P'), (-1, -1, 'P')):
            front[(cx + dx, cy + dy)] = k
        tfx.implode_streaks(front, cx, cy, 30, 12, n=14, seed=9, colours=('P', 'v', 'u'))
    return back, body, front


def detonate():
    i = 20
    lift = LIFT[i]
    gy = AY - lift
    back, front = {}, {}
    tfx.flash_disc(back, AX, gy - 62, 102, spikes=20, phase=0.15, sq=0.88)
    _, m = silhouette(i, scale=1.0, wings=1.0, lit='', tail=False, wings_lit=False)
    body = {p: 'k' for p in m}
    ox, oy = beast_origin(lift)
    for head, pts in eye_centres().items():
        for (ex, ey) in pts:
            x, y = int(round(ex + ox)), int(round(ey + oy))
            body[(x, y)] = tfx.WHITE
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                body[(x + dx, y + dy)] = 'j'
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                body[(x + dx, y + dy)] = 'i'
    fx.embers(front, (AX - 150, gy - 150, AX + 150, gy + 40), 26, seed=83, hot_ratio=0.8, sizes=(2, 3))
    return back, body, front


#THE BEAST IN FULL COLOUR (21-25)

def final_pose(mid_lit, side_lit):
    P = PS.make()
    g = 1 if side_lit else 0
    P['wing_glow'] = g
    P['mid'] = dict(ears=1 if mid_lit else 0, eye_glow=1 if mid_lit else 0)
    P['side'] = dict(ears=g, eye_glow=g)
    return P


def reveal(i):
    lift = LIFT[i]
    gy = AY - lift
    back, front = {}, {}
    mid_lit = i >= 23
    side_lit = i >= 24
    ox, oy = beast_origin(lift)
    img = PS.build(final_pose(mid_lit, side_lit)).image()
    body = C.to_keys(img, ox, oy)
    if i == 25:
        return back, body, front
    m = set(body)
    keep_out = m
    if i == 21:
        tfx.flash_disc(back, AX, gy - 62, 78, spikes=16, phase=0.6, core=0.3, ring_w=0.30, sq=0.88)
        tfx.rim_glow(front, m, tfx.WHITE, 'Y')
        tfx.smoke_ring(front, AX, gy - 40, 100, 44, r=8, n=11, seed=17, keep_out=keep_out, thin=0.0)
        fx.embers(front, (AX - 140, gy - 140, AX + 140, gy + 30), 30, seed=91, hot_ratio=0.7, sizes=(1, 2, 3))
    elif i == 22:
        tfx.rim_glow(front, m, 'P', 'u')
        tfx.smoke_ring(front, AX, gy - 36, 116, 52, r=7, n=11, seed=19, keep_out=keep_out, thin=0.3)
        fx.embers(front, (AX - 140, gy - 150, AX + 140, gy + 20), 22, seed=93, hot_ratio=0.5, sizes=(1, 2))
    elif i == 23:
        tfx.smoke_ring(front, AX, gy - 30, 124, 56, r=6, n=10, seed=23, keep_out=keep_out, thin=0.6)
        fx.embers(front, (AX - 130, gy - 150, AX + 130, gy + 10), 16, seed=95, hot_ratio=0.4, sizes=(1, 2))
        for (ex, ey) in eye_centres()['M']:
            tfx.mint_flare(front, ex + ox, ey + oy)
    elif i == 24:
        tfx.smoke_ring(front, AX, gy - 24, 132, 60, r=5, n=9, seed=29, keep_out=keep_out, thin=0.9)
        fx.embers(front, (AX - 120, gy - 140, AX + 120, gy), 10, seed=97, hot_ratio=0.3, sizes=(1, 2))
        for head in 'LR':
            for (ex, ey) in eye_centres()[head]:
                tfx.mint_flare(front, ex + ox, ey + oy)
    return back, body, front


def layers(i):
    if 10 <= i <= 17:
        return swell(i)
    if i in (18, 19):
        return implode(i)
    if i == 20:
        return detonate()
    return reveal(i)


def image(i):
    back, body, front = layers(i)
    im = C.to_image(back, C.TW, C.TH)
    im.alpha_composite(C.to_image(body, C.TW, C.TH))
    im.alpha_composite(C.to_image(front, C.TW, C.TH))
    return im


def frames():
    return [image(i) for i in range(10, 26)]
