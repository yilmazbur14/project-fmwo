"""Matt's legs for the walk: the rig's trouser outline and foot maps, but each leg on its own so a
foot can lift and swing while the hips bob.

The rig (matt.trousers / matt.feet) builds both legs as one symmetric part. Here each leg's outline
is the rig's own left-leg outline (mirrored for the right), with every point carried by a blend of
the hip's shift (at the waistband) and the foot's shift (at the hem), so a lifted foot shortens its
leg and a bob stretches the planted one. Each leg is shaded as the rig shades it (a cylinder from
hip to ankle, the charcoal ramp) and stamped with its own keyline, the far leg first, so where the
legs overlap the near one's keyline is the split between them.

Feet are the rig's structure map (details.FOOT) shaded exactly as matt.feet() shades it, moved with
the foot.
"""
import mi_base as B
from mi_base import details, poly, sh, moved

# the rig's left-leg outline at stance 0 (matt.trousers), top centre round to the crotch
LEG_L = [(48, 70), (31.5, 70), (30, 74), (28.5, 79), (28, 83), (43.5, 83), (44.5, 80), (46, 77.5),
         (48, 76.5)]
TOP, HEM = 70.0, 83.0


def leg(side, hip_dy, fdx, fdy, lean=0.0, screen=False):
    """One trouser leg. hip_dy moves the waistband; (fdx, fdy) moves the hem with the foot.
    lean shifts the knee sideways (px) for a stride that swings a little out.

    screen=False is how the shipped walk was built: the shift is applied before the right leg is
    mirrored, so on the right leg +fdx moves the hem LEFT while its foot moves right. The approved
    walk was drawn and signed off that way and must keep its pixels, so it stays the default.
    screen=True applies fdx and lean in screen space on both legs (+ is right), which is what a
    stance that plants both feet wide needs."""
    pts = []
    for (x, y) in LEG_L:
        t = (y - TOP) / (HEM - TOP)
        knee = lean * 4 * t * (1 - t)
        dx = fdx * t + knee
        dy = hip_dy * (1 - t) + fdy * t
        if screen:
            x0 = (96 - x) if side else x
            pts.append((x0 + dx, y + dy))
        else:
            pts.append((x + dx, y + dy))
    if side and not screen:
        pts = [(96 - x, y) for (x, y) in pts]
    part = {p: 'L' for p in poly(pts)}
    # above the crotch each leg keeps to its own half, so the near leg's keyline lands on the
    # centre column: the rig's single-pixel seam
    crotch = 76.5 + hip_dy
    for (x, y) in list(part):
        if y < crotch and ((not side and x >= 48) or (side and x <= 48)):
            del part[(x, y)]
    # the inner edge at the crotch is the centre line; keep the leg to its own half above the hem
    hx0, hy0 = (38.5, 71 + hip_dy) if not side else (57.5, 71 + hip_dy)
    ax, ay = (36 + fdx, 87 + fdy) if not side else (60 + fdx, 87 + fdy)
    sh.cylinder(part, (hx0, hy0), (ax, ay), 8.5, 'NMLK', (0.84, 0.62, 0.2))
    return part


def foot(side, fdx, fdy, stance=0):
    """The rig's sock and trainer for one foot, shaded exactly as matt.feet() does, moved."""
    s = stance
    f = moved(details.foot_structure(side), (s if side else -s) + fdx, fdy)
    sock = {p: 'W' for p, k in f.items() if k == 'S'}
    upper = {p: 'C' for p, k in f.items() if k == 'U'}
    rubber = {p: 'W' for p, k in f.items() if k == 'W'}
    laces = {p: 'b' for p, k in f.items() if k == 'Y'}

    def mpt(p):
        return (96 - p[0], p[1]) if side else p
    c = mpt((35.5 - s, 87))
    c = (c[0] + fdx, c[1] + fdy)
    sh.cylinder(sock, (c[0], 80 + fdy), (c[0], 95 + fdy), 7.0, 'WXx', (0.35, -0.2))
    u = mpt((35 - s, 92))
    u = (u[0] + fdx, u[1] + fdy)
    sh.ellipsoid(upper, u[0], u[1], 11, 5, 'BCDE', (0.8, 0.45, 0.05))
    sh.ellipsoid(rubber, u[0], u[1] - 2, 11, 5, 'WXx', (0.2, -0.45))
    sh.ellipsoid(laces, u[0], u[1] - 3, 5, 3, 'abc', (0.7, 0.3))
    for d in (sock, upper, rubber, laces):
        f.update(d)
    return f


def walk_legs(hip_dy, left, right, back=0, screen=False):
    """Both legs and feet for one walk frame. left / right are (fdx, fdy, lean) for the screen-left
    and screen-right foot. `back` names the leg drawn first (0 or 1): the one further from camera.
    Returns [(part, outline)] in stamp order."""
    out = []
    order = (back, 1 - back)
    specs = {0: left, 1: right}
    for side in order:
        fdx, fdy, lean = specs[side]
        out.append((foot(side, fdx, fdy), False, side))
    for side in order:
        fdx, fdy, lean = specs[side]
        out.append((leg(side, hip_dy, fdx, fdy, lean, screen), True, side))
    # stamp: back foot, back leg, front foot, front leg
    res = []
    for side in order:
        res += [(p, ol) for (p, ol, s) in out if s == side and not ol]
        res += [(p, ol) for (p, ol, s) in out if s == side and ol]
    return res


def _selftest():
    """At rest the two legs, stamped this way, must rebuild the rig's own legs pixel for pixel."""
    import mi_fig as F
    rest = F.px_of(F.Fig())
    walk = F.px_of(F.Fig(legs=lambda f: walk_legs(0, (0, 0, 0), (0, 0, 0))))
    d = B.pixel_diff(B.image(rest), B.image(walk))
    print('walk legs at rest vs the rig:', d or 'identical')


if __name__ == '__main__':
    _selftest()
