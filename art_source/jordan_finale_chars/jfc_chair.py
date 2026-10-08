"""Jordan's gaming chair: a racing-style chair in charcoal with pink racing stripes (pink is his:
the Peach tee's dress band, his wristband, the funko pop cloud), drawn in his palette only.

The chair is modelled as a handful of solids so its four views through the swivel (back, three-
quarter back, side, three-quarter front) agree with each other: every solid is projected (jfc_base's
oblique view: verticals full length, depth at half rate), its visible faces are filled and shaded by
how they face the light (upper left, toward the camera, like the whole cast), and each solid is
keylined as it is stamped, so the parts separate with the house style's black lines.

Only the seat turns on the swivel (seat, backrest, armrests); the gas lift and the five-star base
stay put, as a real chair's do, so they are the same pixels in every frame.

Chair-local space: x right, y forward (the way the sitter faces), z up; units are frame pixels.
The swivel axis stands on the floor at frame pixel PIVOT.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfc_base as B  # noqa: E402

# the floor point under the gas lift, in 128-frame pixels: the front caster's lowest texel then lands
# on the contract's anchor row 127 at x = 64 (checked in _selftest)
PIVOT = (64, 118)

# light from the upper left, a little toward the camera (world: x east, y north, z up)
_L = (-0.55, -0.45, 0.70)
_n = math.sqrt(sum(c * c for c in _L))
LIGHT = tuple(c / _n for c in _L)

RAMPS = {
    #          shadow lit-less  base  lit   glint
    'fabric': ('1', '2', '2', '3'),
    'stripe': ('q', 'q', 'q', 'q'),       # deep pink; decals() lights only the stripes' tops
    'metal':  ('1', '1', '2', '3'),
    'wheel':  ('1', '1', '2', '3'),
}


#GEOMETRY

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def prism(outline, z0, z1):
    """A vertical prism over a CCW (seen from above) outline [(x, y)]: bottom, top and side faces."""
    top = [(x, y, z1) for (x, y) in outline]
    bot = [(x, y, z0) for (x, y) in reversed(outline)]
    faces = [top, bot]
    n = len(outline)
    for i in range(n):
        (xa, ya), (xb, yb) = outline[i], outline[(i + 1) % n]
        faces.append([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)])
    return faces


def slab(outline_uh, origin, u_axis, h_axis, depth):
    """A flat solid: an outline [(u, h)] (CCW seen from the front) in the plane through `origin`
    spanned by u_axis and h_axis, `depth` thick toward the back (-normal)."""
    nrm = _cross(h_axis, u_axis)          # the front normal (forward, a little up)
    def P(u, h, d):
        return tuple(origin[i] + u * u_axis[i] + h * h_axis[i] - d * nrm[i] for i in range(3))
    front = [P(u, h, 0) for (u, h) in outline_uh]
    back = [P(u, h, depth) for (u, h) in reversed(outline_uh)]
    faces = [front, back]
    n = len(outline_uh)
    for i in range(n):
        (ua, ha), (ub, hb) = outline_uh[i], outline_uh[(i + 1) % n]
        faces.append([P(ua, ha, 0), P(ua, ha, depth), P(ub, hb, depth), P(ub, hb, 0)])
    return faces


def octagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(22.5 + 45 * i)), cy + r * math.sin(math.radians(22.5 + 45 * i)))
            for i in range(8)]


def box_outline(x0, x1, y0, y1, bevel=0.0):
    b = bevel
    if not b:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [(x0 + b, y0), (x1 - b, y0), (x1, y0 + b), (x1, y1 - b), (x1 - b, y1), (x0 + b, y1), (x0, y1 - b), (x0, y0 + b)]


#THE CHAIR, IN CHAIR-LOCAL SPACE

SEAT_TOP = 21.0
BACK_TILT = math.radians(10)          # the backrest reclines this far
BACK_ORIGIN = (0.0, -10.5, 19.0)      # the backrest's front face meets the seat here
# the backrest's front outline (u across, h up its face): a racing back with shoulder wings
BACK_OUTLINE = [(-11.5, 0), (11.5, 0), (11.2, 6), (10.8, 9), (12.6, 12), (13.8, 14.6), (13.2, 16.8),
                (9.6, 18.4), (7.8, 20.6), (7.0, 23.6), (5.6, 25.4), (3.2, 26.0), (-3.2, 26.0), (-5.6, 25.4),
                (-7.0, 23.6), (-7.8, 20.6), (-9.6, 18.4), (-13.2, 16.8), (-13.8, 14.6), (-12.6, 12), (-10.8, 9),
                (-11.2, 6)]
BACK_DEPTH = 4.5
# the racing stripes: two bands up the backrest, on both faces
STRIPES = [[(-5.8, 1.2), (-4.0, 1.2), (-3.6, 24.8), (-5.0, 24.2)],
           [(4.0, 1.2), (5.8, 1.2), (5.0, 24.2), (3.6, 24.8)]]


def back_axes():
    u = (1.0, 0.0, 0.0)
    h = (0.0, -math.sin(BACK_TILT), math.cos(BACK_TILT))
    return u, h


def seat_solids():
    """(name, material, faces) in chair-local space, for the parts that turn with the swivel."""
    out = []
    # the seat cushion, bevelled, with raised side bolsters
    out.append(('seat', 'fabric', prism(box_outline(-11.5, 11.5, -10.5, 11.0, 2.5), 16.5, SEAT_TOP)))
    for s in (-1, 1):
        x0, x1 = (-12.5, -8.5) if s < 0 else (8.5, 12.5)
        out.append(('bolster%+d' % s, 'fabric', prism(box_outline(x0, x1, -9.5, 10.0, 1.2), SEAT_TOP - 1, SEAT_TOP + 2.2)))
    u, h = back_axes()
    out.append(('back', 'fabric', slab(BACK_OUTLINE, BACK_ORIGIN, u, h, BACK_DEPTH)))
    for s in (-1, 1):
        cx = 14.2 * s
        out.append(('post%+d' % s, 'metal', prism(box_outline(cx - 0.9, cx + 0.9, -3.5, -1.5), 16.5, 28.5)))
        out.append(('pad%+d' % s, 'fabric', prism(box_outline(cx - 2.0, cx + 2.0, -8.5, 4.5, 1.0), 28.5, 31.0)))
    return out


def fixed_solids():
    """The gas lift and the five-star base: they never turn."""
    out = [('lift', 'metal', prism(octagon(0, 0, 1.8), 7.0, 17.0)),
           ('shroud', 'metal', prism(octagon(0, 0, 2.8), 5.5, 10.5)),
           ('hub', 'metal', prism(octagon(0, 0, 3.6), 3.8, 6.4))]
    for i, a in enumerate((0, 72, 144, 216, 288)):         # degrees from due south (the camera)
        t = math.radians(a)
        dx, dy = math.sin(t), -math.cos(t)                  # the leg's direction on the floor
        px, py = -dy, dx                                     # across it
        L, w = 17.0, 1.6
        # a tapered leg: its top slopes from the hub down toward the caster
        pts_top = [(px * w, py * w, 6.2), (px * w * 0.7 + dx * L, py * w * 0.7 + dy * L, 4.6),
                   (-px * w * 0.7 + dx * L, -py * w * 0.7 + dy * L, 4.6), (-px * w, -py * w, 6.2)]
        pts_bot = [(x, y, z - 2.0) for (x, y, z) in pts_top]
        faces = [pts_top[::-1], pts_bot]
        for j in range(4):
            a0, a1 = pts_top[j], pts_top[(j + 1) % 4]
            b0, b1 = pts_bot[j], pts_bot[(j + 1) % 4]
            faces.append([a0, a1, b1, b0])
        out.append(('leg%d' % i, 'metal', faces))
        cx, cy = dx * (L - 0.5), dy * (L - 0.5)
        out.append(('caster%d' % i, 'wheel', prism(octagon(cx, cy, 1.7), 0.0, 3.4)))
    return out


#RENDERING

def _world(p, yaw):
    return B.yaw_rot(p, yaw)


def _shade(normal, ramp):
    s = sum(normal[i] * LIGHT[i] for i in range(3))
    keys = RAMPS[ramp]
    if s > 0.62:
        return keys[3]
    if s > 0.25:
        return keys[2]
    if s > -0.05:
        return keys[1]
    return keys[0]


def _area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))


def render_solid(faces, material, yaw, ox, oy, turn=True):
    """One solid -> ({pixel: key}, depth). Faces are culled by their projected winding (a solid's
    faces all wind the same way seen from outside), filled back to front, shaded by normal."""
    part = {}
    depth_sum, n = 0.0, 0
    drawn = []
    for f in faces:
        w = [(_world(p, yaw) if turn else p) for p in f]
        a, b, c = w[0], w[1], w[2]
        nrm = _norm(_cross(_sub(b, a), _sub(c, a)))
        pts = [B.project(p, ox, oy) for p in w]
        # visible when the face turns toward the viewer: screen winding is flipped by the y-down axis
        if _area2(pts) >= 0:
            continue
        d = sum(p[1] - 0.3 * p[2] for p in w) / len(w)     # far = large
        drawn.append((d, pts, nrm))
    for d, pts, nrm in sorted(drawn, key=lambda t: -t[0]):
        key = _shade(nrm, material)
        for q in B.poly([(x - 0.5, y - 0.5) for (x, y) in pts]):
            part[q] = key
        depth_sum += d
        n += 1
    for f in faces:
        for p in f:
            w = _world(p, yaw) if turn else p
            depth_sum += w[1] - 0.3 * w[2]
            n += 1
    return part, depth_sum / max(1, n)


def solids(yaw):
    """Every solid of the chair at this yaw, rendered: [(name, part, depth)], unsorted."""
    ox, oy = PIVOT
    out = []
    for name, mat, faces in seat_solids():
        part, d = render_solid(faces, mat, yaw, ox, oy)
        out.append((name, part, d))
    for name, mat, faces in fixed_solids():
        part, d = render_solid(faces, mat, 0, ox, oy, turn=False)
        out.append((name, part, d))
    return out


def _face_pts(uh_pts, off, yaw):
    """Chair-local (u, h) points on the backrest, `off` behind its front face, as screen points."""
    ox, oy = PIVOT
    u, h = back_axes()
    nrm = _cross(h, u)
    pts3 = [tuple(BACK_ORIGIN[i] + uu * u[i] + hh * h[i] - off * nrm[i] for i in range(3)) for (uu, hh) in uh_pts]
    return [_world(p, yaw) for p in pts3]


def _visible(w, face):
    pts = [B.project(p, *PIVOT) for p in w]
    return (_area2(pts) < 0) if face == 'front' else (_area2(pts) > 0)


def decals(yaw):
    """What is painted on the backrest's faces, as screen pixels: the racing stripes and the seam
    that sets the padded bolsters off the centre panel (front face and back face)."""
    out = {}
    for face, off in (('front', -0.05), ('back', BACK_DEPTH + 0.05)):
        # the seam: the outline pulled in toward the panel's middle
        cx, ch = 0.0, 12.5
        seam = [(cx + (uu - cx) * 0.78, ch + (hh - ch) * 0.84) for (uu, hh) in BACK_OUTLINE]
        w = _face_pts(seam, off, yaw)
        if not _visible(w, face):
            continue
        pts = [B.project(p, *PIVOT) for p in w]
        pix = [(int(math.floor(x)), int(math.floor(y))) for (x, y) in pts]
        for a, b in zip(pix, pix[1:] + pix[:1]):
            for q in B.line(a[0], a[1], b[0], b[1]):
                out[q] = '1'
        for st in STRIPES:
            w = _face_pts(st, off, yaw)
            a, b, c = w[0], w[1], w[2]
            fn = _norm(_cross(_sub(b, a), _sub(c, a)))
            if face == 'back':
                fn = (-fn[0], -fn[1], -fn[2])
            spts = [B.project(p, *PIVOT) for p in w]
            key = _shade(fn, 'stripe')
            for q in B.poly([(x - 0.5, y - 0.5) for (x, y) in spts]):
                out[q] = key
            top = min(q[1] for q in B.poly([(x - 0.5, y - 0.5) for (x, y) in spts]))
            for q in B.poly([(x - 0.5, y - 0.5) for (x, y) in spts]):
                if q[1] <= top + 1:
                    out[q] = 'P'
    return out


def pad(part):
    """Round a flat-shaded solid off like padding: a lit rim on its upper left, a dark rim on its
    lower right (only over the base tone, so the faces' own light and shadow stay)."""
    B.rim(part, '3', -1, 0, only='2')
    B.rim(part, '3', 0, -1, only='2')
    B.rim(part, '1', 1, 0, only='2')
    B.rim(part, '1', 0, 1, only='2')
    return part


def build(yaw):
    """The whole chair at this yaw as one canvas (for looking at it on its own)."""
    cv = B.Canvas(B.FW, B.FH)
    for name, part, d in sorted(solids(yaw), key=lambda t: -t[2]):
        if name in ('back', 'seat', 'pad-1', 'pad+1', 'bolster-1', 'bolster+1'):
            pad(part)
        cv.stamp(part)
    back = [p for n, p, d in solids(yaw) if n == 'back'][0]
    for q, k in decals(yaw).items():
        if q in back and cv.px.get(q) not in (None, 'k'):
            cv.px[q] = k
    return cv


def _selftest():
    """The fixed base: the front caster's keyline is the lowest row, 127, under x = 64, and nothing
    of the caster is clipped by the frame's edge."""
    cv = build(0)
    low = max(y for (x, y) in cv.px)
    xs = sorted(x for (x, y) in cv.px if y == low)
    ok = (low == B.ANCHOR[1] and xs[0] <= B.ANCHOR[0] <= xs[-1]
          and all(cv.px[(x, low)] == 'k' for x in xs))
    print('chair floor contact: row %d, x %d..%d -> anchor %s ok=%s' % (low, xs[0], xs[-1], B.ANCHOR, ok))
    return ok


if __name__ == '__main__':
    _selftest()
    out = sys.argv[1] if len(sys.argv) > 1 else None
    ims = [B.image(build(y).px) for y in (0, 45, 90, 135)]
    if out:
        B.row([B.up(im, 5) for im in ims]).save(out)
        print('wrote', out)
