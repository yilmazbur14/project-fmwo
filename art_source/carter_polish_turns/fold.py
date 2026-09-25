"""His arms folding into the signature cross (the entrance's last turn beats) and out of it (the
settle), in between the two approved poses: arms hanging (carter_polish frame 0) and arms crossed
(frame 1).

The approved pair draw the forearm about 17 px from elbow to knuckles when it hangs and about 40 px
when it crosses his chest, so the in-betweens follow what a fold really looks like from the front:

  DIAG (t ~ 0.45-0.5)      the upper arms still hang; the forearms swing in from the elbows, down and
                           across, and the wrapped fists meet in front of the belt knot
  LOW X (t ~ 0.8)          the approved crossed pose with the forearms not yet home: each keeps the
                           cross's angle (3 deg lower) but stops a fifth short, so neither hand has
                           tucked under the other arm yet and both wraps show

Both are built from the approved parts with the approved shading: the hanging arm maps (arms.py), the
crossed upper arms and forearm toning (cross.py's a_up / b_up / band_tone, the wrap on its cylinder),
the torn caps' teeth over the shoulders.

    diag(t=0.47)    -> [(part, keyline), ...] the fold's middle (intro frames 12 and 15)
    low_x(t=0.78)   -> [(part, keyline), ...]
    body(parts)     -> the front body (front.py's stamping) with these arms in place of the approved ones
"""
import math

from lib import Canvas, amap, poly, shade, n_cyl
import arms as AR
import cross as CR
import front
import jacket as JK
import chest as CH

# ------------------------------------------------------------------ the fold's middle

# the hanging arm maps down to the elbow (rows 56..67); below it the forearm swings in
ARM_L_UPPER = AR.ARM_L[:12]
ARM_R_UPPER = AR.ARM_R[:12]


def _band(elbow, hand, w0, w1):
    """A forearm as a band from its elbow to its hand end, square-ended like cross.A_FORE."""
    (x0, y0), (x1, y1) = elbow, hand
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    return [(x0 - ux * 1.0 + nx * w0 * 0.2, y0 - uy * 1.0 + ny * w0 * 0.2),
            (x0 + nx * w0 * 0.5, y0 + ny * w0 * 0.5),
            (x1 + nx * w1 * 0.5, y1 + ny * w1 * 0.5),
            (x1 - nx * w1 * 0.5, y1 - ny * w1 * 0.5),
            (x0 - nx * w0 * 0.5, y0 - ny * w0 * 0.5),
            (x0 - ux * 1.0 - nx * w0 * 0.2, y0 - uy * 1.0 - ny * w0 * 0.2)]


def diag(t=0.47):
    """The forearms swinging in from the elbows, down and across, the wrapped fists meeting in front
    of the belt knot (t 0.45-0.5: the fold's middle, or the unfold's)."""
    au = amap(ARM_L_UPPER, 18, 56)
    bu = amap(ARM_R_UPPER, 64, 56)
    for part, xs in ((au, range(19, 29)), (bu, range(67, 77))):
        for x in xs:
            if (x, 67) in part and part[(x, 67)] != 'k':
                part[(x, 68)] = 'w' if part[(x, 67)] in 'vw' else 'v'
    ae, be = (23.5, 66.5), (71.5, 66.5)
    reach = 0.30 + 0.45 * t
    ah = (ae[0] + 34.0 * reach, 76.0 - 10.0 * t)
    bh = (be[0] - 34.0 * reach, 76.0 - 10.0 * t)
    parts = [(au, False), (bu, False)]
    wrap_len = 7.5
    for e, h, tones, bias in ((ae, ah, 'tuvw', 0), (be, bh, 'tuvw', 0)):
        band = poly(_band(e, h, 7.5, 8.5))
        axis = (e, h)
        p = CR.band_tone(band, axis, 4.0, tones)
        (x0, y0), (x1, y1) = axis
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        wrap = {q for q in band if ((q[0] - x0) * ux + (q[1] - y0) * uy) >= L - wrap_len}
        p.update(shade(wrap, 'wrap', n_cyl(e, h, 5.0), CR.WRAP_TH, bias=bias))
        for q in band:
            s = (q[0] - x0) * ux + (q[1] - y0) * uy
            if abs(s - (L - wrap_len - 0.5)) < 0.5:
                p[q] = 'k'                      # where the wrap starts
            elif s >= L - 1.3:
                p[q] = 't' if q[1] % 2 == 0 else 'u'     # the knuckles, bare
        parts.append((p, True))
    return parts


# ------------------------------------------------------------------ low X: the cross, not yet home

def _toward(p, q, f):
    return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)


def _rotate(p, c, deg):
    a = math.radians(deg)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def low_x(t=0.78):
    """cross.arms() with each forearm pulled back along its own line - a fifth short at t = 0.78,
    home at t = 1 - and dipped a few degrees about its elbow."""
    k = (1.0 - t) / 0.22                       # 1 at t = 0.78
    drop = 3.0 * k                             # degrees: the X keeps its angle
    short = 0.20 * k                           # the hands a fifth of the way short of the biceps
    au, bu = CR.a_up(), CR.b_up()
    cx, cy, rx, ry = CR.A_UP_LIGHT
    a = shade(au, 'skin', CR.n_sphere(cx, cy, rx, ry), CR.TH_SKIN)
    b = shade(bu, 'skin', CR.n_sphere(95 - cx + 2.0, cy, rx, ry), CR.TH_SKIN)

    ae, ah = CR.A_AXIS                          # elbow, hand
    be, bh = CR.B_AXIS
    ah2 = _rotate(_toward(ah, ae, short), ae, drop)          # A points right: clockwise lowers it
    bh2 = _rotate(_toward(bh, be, short), be, -drop)         # B points left: counter-clockwise
    a_axis, b_axis = (ae, ah2), (be, bh2)
    a_band = poly(_band(ae, ah2, 8.0, 8.0))
    b_band = poly(_band(be, bh2, 8.0, 8.0))
    wrap_len = 7.0

    def wrap_of(band, axis):
        (x0, y0), (x1, y1) = axis
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        return {q for q in band if ((q[0] - x0) * ux + (q[1] - y0) * uy) >= L - wrap_len}, (ux, uy, L)

    af = a_band - bu
    ap = CR.band_tone(af, a_axis, 4.2, 'uuvw')
    aw, (aux, auy, aL) = wrap_of(af, a_axis)
    ap.update(shade(aw, 'wrap', n_cyl(a_axis[0], a_axis[1], 5.2), CR.WRAP_TH, bias=1))
    for q in af:
        s = (q[0] - ae[0]) * aux + (q[1] - ae[1]) * auy
        if abs(s - (aL - wrap_len - 0.5)) < 0.5:
            ap[q] = 'k'                          # where the wrap starts
    bmask = b_band
    for (x, y) in list(ap):
        if ap[(x, y)] == 'k':
            continue
        if (x, y - 1) in bmask:
            ap[(x, y)] = 'k'                     # B lies right on top of A
        elif (x, y - 2) in bmask:
            ap[(x, y)] = 'W' if ap[(x, y)] in 'wv' else 'w'

    bf = b_band - au
    bp = CR.band_tone(bf, b_axis, 4.2, 'tuvw')
    bw, (bux, buy, bL) = wrap_of(bf, b_axis)
    bp.update(shade(bw, 'wrap', n_cyl(b_axis[0], b_axis[1], 5.2), CR.WRAP_TH))
    for q in bf:
        s = (q[0] - be[0]) * bux + (q[1] - be[1]) * buy
        if abs(s - (bL - wrap_len - 0.5)) < 0.5:
            bp[q] = 'k'
    # the front forearm's top ridge takes the light between the elbow and the wrap
    top = {}
    for (x, y), key in bp.items():
        if key != 'k':
            top[x] = min(top.get(x, y), y)
    for x, y in top.items():
        s = (x - be[0]) * bux + (y - be[1]) * buy
        if 3 < s < bL - wrap_len - 1:
            bp[(x, y)] = 's'
    for part, inner in ((a, max), (b, min)):
        rows = {}
        for (x, y) in part:
            rows.setdefault(y, []).append(x)
        for y, xs in rows.items():
            xi = inner(xs)
            if part.get((xi, y)) in ('u', 'v', 't'):
                part[(xi, y)] = 'v'
    # the knuckles at each hand's end, keyed across the wrap's front
    for band_pts, (ux, uy, L), e, part in ((aw, (aux, auy, aL), ae, ap), (bw, (bux, buy, bL), be, bp)):
        for q in band_pts:
            s = (q[0] - e[0]) * ux + (q[1] - e[1]) * uy
            if s >= L - 1.2 and part.get(q) not in (None, 'k'):
                part[q] = 't' if (q[1] % 2 == 0) else 'u'
    return [(a, True), (b, True), (CR.teeth(0), True), (CR.teeth(1), True), (ap, True), (bp, True)]


# ------------------------------------------------------------------ the body

def body(parts, crossed_torso=False, head=True):
    """front.py's stamping with these arms. crossed_torso: the arms come forward over the gi as in the
    crossed pose (arms stamped after the jacket); otherwise they hang at his sides under the caps.
    head=False leaves the head off, for a frame that wears its own."""
    cv = front.lower_body(Canvas())
    if crossed_torso:
        for j in JK.jacket():
            cv.stamp(j)
        cv.stamp(CH.chest(), outline=False)
        for bd in CH.beads():
            cv.stamp(bd, outline=False)
        front.belt(cv)
        for part, outline in parts:
            cv.stamp(part, outline=outline)
    else:
        upper = parts[:2]
        rest = parts[2:]
        for part, outline in upper:
            cv.stamp(part, outline=outline)
        for j in JK.jacket():
            cv.stamp(j)
        cv.stamp(CH.chest(), outline=False)
        for bd in CH.beads():
            cv.stamp(bd, outline=False)
        front.belt(cv)
        for part, outline in rest:
            cv.stamp(part, outline=outline)
    return front.head(cv) if head else cv
