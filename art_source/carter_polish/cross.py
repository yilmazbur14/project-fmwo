"""Frame 1's crossed arms.

A = his right arm (screen left), B = his left arm (screen right). Each forearm rises from its elbow at
the side to its hand, which tucks under the OPPOSITE bicep, so the two make an X, B in front. In this
pose the arms come forward over the gi and the torn caps ride on top of the shoulders, as they did in
the approved frame - but the approved frame drew the front forearm as long 1px stripes, the back one
as a flat band of a single dark tone, and the tucked hand as a khaki brick.

Layering, each part keylined as it is stamped:
  A upper arm, B upper arm, the caps' torn teeth over both, A forearm minus B's upper arm (its hand
  goes under B's bicep), B forearm minus A's upper arm (its hand goes under A's bicep).
"""
from lib import poly, mirror_set, shade, n_sphere, n_cyl

TH_SKIN = [0.93, 0.80, 0.55, 0.28, 0.02]
WRAP_TH = [0.95, 0.80, 0.55, 0.30, 0.05]

# screen-left upper arm: the delt from under a strip of cap, the bicep bulging, down to the elbow
A_UP = [(22.5, 55), (25, 53), (28.5, 51.5), (31.5, 51.5), (33.5, 53.5), (34.5, 57), (34, 61),
        (32, 64.5), (28.5, 67.5), (24.5, 69), (21.5, 68.5), (19.5, 65.5), (19.2, 60.5), (20, 57)]
A_UP_LIGHT = (25.5, 57.0, 8.5, 10.0)

# forearm bands, elbow end first
A_FORE = [(20.5, 65.0), (22.0, 62.5), (61.5, 56.0), (62.0, 64.0), (23.5, 70.5), (21.0, 69.0)]
A_AXIS = ((22.0, 66.5), (61.8, 60.0))
B_FORE = [(74.5, 63.0), (73.0, 60.5), (33.5, 53.5), (34.0, 61.5), (72.0, 69.0), (74.0, 67.5)]
B_AXIS = ((73.0, 65.0), (33.8, 57.5))
A_WRAP_X = 56         # A's wrap: x >= this (keyline one column in)
B_WRAP_X = 39         # B's wrap: x <= this

# the torn edge of each cap over the top of its deltoid: (tip x, tip y, half width, root y)
TEETH_L = [(23.0, 56.5, 1.2, 54.0), (26.5, 55.5, 1.5, 52.5), (30.5, 55.5, 1.4, 52.0),
           (33.5, 55.0, 0.9, 53.0)]


def a_up():
    return poly(A_UP)


def b_up():
    return mirror_set(poly(A_UP))


def teeth(side):
    part = {}
    for tx, ty, hw, top in TEETH_L:
        if side:
            tx = 95 - tx
        for q in poly([(tx - hw - 0.7, top - 1.5), (tx + hw + 0.7, top - 1.5), (tx, ty)]):
            part[q] = 'e' if q[1] > top else 'd'
    return part


def band_tone(mask, axis, radius, tones):
    """Tone a forearm by its offset across the band: tones = (top, upper-mid, lower-mid, bottom) by
    the side facing up (the light) to the side facing down, so it reads as one clean cylinder."""
    (x0, y0), (x1, y1) = axis
    dx, dy = x1 - x0, y1 - y0
    L = (dx * dx + dy * dy) ** 0.5
    px, py = -dy / L, dx / L
    if py > 0:                       # point the normal up the screen, toward the light
        px, py = -px, -py
    out = {}
    for (x, y) in mask:
        s = ((x - x0) * px + (y - y0) * py) / radius
        out[(x, y)] = tones[0] if s > 0.5 else tones[1] if s > -0.2 else tones[2] if s > -0.65 else tones[3]
    return out


def arms():
    """[(part, keyline_it)] in stamp order."""
    au, bu = a_up(), b_up()
    cx, cy, rx, ry = A_UP_LIGHT
    a = shade(au, 'skin', n_sphere(cx, cy, rx, ry), TH_SKIN)
    b = shade(bu, 'skin', n_sphere(95 - cx + 2.0, cy, rx, ry), TH_SKIN)

    af = poly(A_FORE) - bu
    ap = band_tone(af, A_AXIS, 4.2, 'uuvw')
    aw = {q for q in af if q[0] >= A_WRAP_X}
    ap.update(shade(aw, 'wrap', n_cyl(A_AXIS[0], A_AXIS[1], 5.2), WRAP_TH, bias=1))
    for q in af:
        if q[0] == A_WRAP_X - 1:
            ap[q] = 'k'                          # where the wrap starts

    # B's forearm throws a shadow on the top of A's, just under its bottom edge
    bmask = poly(B_FORE)
    for (x, y) in list(ap):
        if ap[(x, y)] == 'k':
            continue
        if (x, y - 1) in bmask:
            ap[(x, y)] = 'k'                    # contact shadow: B sits right on top of A
        elif (x, y - 2) in bmask:
            ap[(x, y)] = 'W' if ap[(x, y)] in 'wv' else 'w'

    bf = poly(B_FORE) - au
    bp = band_tone(bf, B_AXIS, 4.2, 'tuvw')
    bw = {q for q in bf if q[0] <= B_WRAP_X}
    bp.update(shade(bw, 'wrap', n_cyl(B_AXIS[0], B_AXIS[1], 5.2), WRAP_TH))
    for q in bf:
        if q[0] == B_WRAP_X + 1:
            bp[q] = 'k'
        elif q[0] == B_WRAP_X - 3 and bp.get(q) not in (None, 'k'):
            bp[q] = 'j' if q[1] % 2 else 'l'      # the edge of the next turn of cloth

    # the front forearm's top ridge takes the light, full length between the wrap and the elbow
    for x in range(B_WRAP_X + 3, 71):
        col = sorted(y for (xx, y) in bp if xx == x and bp[(xx, y)] != 'k')
        if col:
            bp[(x, col[0])] = 's'
    # each bicep darkens toward its inner edge, where the other arm's hand tucks under it
    for part, inner in ((a, max), (b, min)):
        rows = {}
        for (x, y) in part:
            rows.setdefault(y, []).append(x)
        for y, xs in rows.items():
            xi = inner(xs)
            if part.get((xi, y)) in ('u', 'v', 't'):
                part[(xi, y)] = 'v'
    return [(a, True), (b, True), (teeth(0), True), (teeth(1), True), (ap, True), (bp, True)]
