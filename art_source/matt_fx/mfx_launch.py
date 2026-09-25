"""matt_trueshot_launch.png: the cyan-white wisps that curl back from a Trueshot's launch point. 25 frames
of 48x48, one strip:
  frames 0-4     heading 0 degrees      (the wave travelling right, the wisps curling back to the left)
  frames 5-9     heading 22.5
  frames 10-14   heading 45
  frames 15-19   heading 67.5
  frames 20-24   heading 90             (the wave travelling down)
5 frames per heading at 0.05 s, played once at the release. Godot angles (y down); flip_h for a leftward
heading, flip_v for an upward one, as for the wave. It is the same design rotated about the pivot, and it
is symmetric about the travel axis, so the flips hold.

THE PIVOT IS THE FRAME CENTRE (24, 24): put it on the launch point (the wave's spawn, mouth + perp *
lateral, 40 px behind the wave's centre at the release), so the Sprite2D needs no offset under any flip.

In the Mystic Shot's cyan, tying the wave to the bolt: a white-hot flash at the launch point, then two
wisps sweeping back along either side of the travel axis, each winding into a curl at its tip, with
a few motes. Over the 5 frames the flash dies, the wisps grow, their roots
dissolve from the launch point outward, and they cool from white-cyan to #22C3E8, which sits at the mat's brightness, so the last
frame dissolves into the floor.
"""
import math

import mfx_pal as pal

W = H = 48
PX, PY = 24.0, 24.0
FRAME_SIZE = (48, 48)
NOTE = '25 frames: 0/22.5/45/67.5/90 deg x 5; 0.05 s, once at the release'
HEADINGS = (0.0, 22.5, 45.0, 67.5, 90.0)
FRAMES = 5

# A wisp: start point (design coords), start heading (degrees, screen, y down), a gentle arc over its
# whole length, then from `curl_from` (a fraction of the length) a curl that winds the tip round into a
# small loop (+ is clockwise on screen, so the upper wisp curls outward and over like a breaking wave),
# length, root thickness. The lower wisp mirrors the upper one about the travel axis.
WISPS = [
    dict(start=(-1.0, -1.5), head=200.0, arc=36.0, curl=285.0, curl_from=0.5, length=22.0, thick=2,
         main=True),
]
# Per frame: (visible from s0 to s1 as a fraction of the length).
GROW = [(0.0, 0.22), (0.0, 0.6), (0.06, 0.88), (0.3, 1.0), (0.66, 1.0)]


def wisp_points(w, mirror):
    """(s, x, y) samples along a wisp in design coordinates, curling harder toward its tip."""
    x, y = w['start']
    if mirror:
        y = -y
    pts = []
    n = int(w['length'] / 0.1)
    for i in range(n + 1):
        s = i * 0.1
        t = s / w['length']
        c0 = w['curl_from']
        curl = w['curl'] * (max(0.0, t - c0) / (1.0 - c0)) ** 1.35
        psi = w['head'] + w['arc'] * t + curl
        if mirror:
            psi = 360.0 - psi
        pts.append((s, x, y))
        x += math.cos(math.radians(psi)) * 0.1
        y += math.sin(math.radians(psi)) * 0.1
    return pts


def to_frame(X, Y, theta):
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    return PX + X * c - Y * s, PY + X * s + Y * c


def to_design(x, y, theta):
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    px, py = x + 0.5 - PX, y + 0.5 - PY
    return px * c + py * s, -px * s + py * c


def pixel_perfect(run):
    out = list(run)
    i = 1
    while i < len(out) - 1:
        (ax, ay), (bx, by), (cx, cy) = out[i - 1][0], out[i][0], out[i + 1][0]
        if abs(ax - cx) == 1 and abs(ay - cy) == 1 and (ax == bx or ay == by):
            del out[i]
        else:
            i += 1
    return out


# The wisp's core colour by frame, root to tip (sampled along t), and its edge colour by frame. They stay
# white-cyan for most of their life and cool only at the end, as light, not smoke.
CORE = ['WDD', 'DDC', 'DCC', 'CCB', 'CBB']
EDGE = ['C', 'C', 'B', 'B', 'B']


def wisp_colour(t, f, main):
    ramp = CORE[f]
    k = ramp[min(len(ramp) - 1, int(t * len(ramp)))]
    if not main and k == 'W':
        k = 'D'
    return k


def paint_wisps(g, theta, f):
    s0f, s1f = GROW[f]
    for w in WISPS:
        for mirror in (False, True):
            run = []
            for s, X, Y in wisp_points(w, mirror):
                t = s / w['length']
                if not (s0f <= t <= s1f):
                    continue
                fx, fy = to_frame(X, Y, theta)
                p = (int(math.floor(fx)), int(math.floor(fy)))
                if not run or run[-1][0] != p:
                    run.append((p, t))
            run = pixel_perfect(run)
            for (x, y), t in run:
                pal.put(g, x, y, wisp_colour(t, f, w['main']))
            # the main wisp is 2 texels thick for most of its length: a cyan edge on its outer side
            if w['thick'] == 2:
                side = -1.0 if mirror else 1.0
                edge = []
                for s, X, Y in wisp_points(w, mirror):
                    t = s / w['length']
                    if not (s0f <= t <= min(s1f, 0.72)):
                        continue
                    # the outer side: the normal pointing away from the travel axis
                    fx, fy = to_frame(X, Y - side * 0.95, theta)
                    q = (int(math.floor(fx)), int(math.floor(fy)))
                    if not edge or edge[-1][0] != q:
                        edge.append((q, t))
                for (x, y), t in pixel_perfect(edge):
                    if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
                        g[y][x] = EDGE[f]


FLASH = [
    # (radius, key) discs, innermost last; and spikes (angle, length, key) in design coordinates
    dict(discs=[(3.2, 'C'), (2.3, 'D'), (1.5, 'W')],
         spikes=[(90, 6.5, 'C'), (270, 6.5, 'C'), (180, 5.5, 'D'), (135, 4.5, 'B'), (225, 4.5, 'B')]),
    dict(discs=[(2.2, 'C'), (1.2, 'D')], spikes=[(90, 4.0, 'B'), (270, 4.0, 'B')]),
    dict(discs=[(1.0, 'B')], spikes=[]),
    dict(discs=[], spikes=[]),
    dict(discs=[], spikes=[]),
]


def paint_flash(g, theta, f):
    spec = FLASH[f]
    for rr, k in spec['discs']:
        for y in range(H):
            for x in range(W):
                X, Y = to_design(x, y, theta)
                if math.hypot(X, Y) <= rr:
                    g[y][x] = k
    for ang, length, k in spec['spikes']:
        run = []
        s = 0.0
        while s <= length:
            X, Y = math.cos(math.radians(ang)) * s, math.sin(math.radians(ang)) * s
            fx, fy = to_frame(X, Y, theta)
            p = (int(math.floor(fx)), int(math.floor(fy)))
            if not run or run[-1][0] != p:
                run.append((p, s))
            s += 0.1
        for (x, y), s in pixel_perfect(run):
            if g[y][x] == '.':
                g[y][x] = k


# Motes shed backward: (design x, |y|, key) per frame, mirrored about the axis.
MOTES = [[], [(-7.0, 5.5, 'D')], [(-11.0, 7.5, 'C'), (-6.0, 9.5, 'D')], [(-15.0, 9.0, 'B'), (-10.0, 12.0, 'C')],
         [(-19.0, 10.0, 'B'), (-14.0, 14.0, 'B')]]


def paint_motes(g, theta, f):
    for X, Y, k in MOTES[f]:
        for sy in (1, -1):
            fx, fy = to_frame(X, Y * sy, theta)
            x, y = int(math.floor(fx)), int(math.floor(fy))
            if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
                g[y][x] = k


def frame(theta, f):
    g = pal.blank(W, H)
    paint_wisps(g, theta, f)
    paint_flash(g, theta, f)
    paint_motes(g, theta, f)
    return pal.rows(g)


def frames():
    by = {}
    for theta in (0.0, 22.5, 45.0):
        by[theta] = [frame(theta, f) for f in range(FRAMES)]
    by[67.5] = [pal.transpose(fr) for fr in by[22.5]]
    by[90.0] = [pal.transpose(fr) for fr in by[0.0]]
    out = []
    for theta in HEADINGS:
        out.extend(by[theta])
    return out


# The in-between headings, shipped as their own sheet (matt_trueshot_launch_mid.png) so the live sheet above
# never changes: 20 frames of 48x48, 11.25 deg f0-4, 33.75 f5-9, 56.25 f10-14, 78.75 f15-19. The same design
# rotated about the same pivot (the frame centre); 56.25 and 78.75 are the exact transposes of 33.75 and
# 11.25.
HEADINGS_MID = (11.25, 33.75, 56.25, 78.75)


def frames_mid():
    by = {}
    for theta in (11.25, 33.75):
        by[theta] = [frame(theta, f) for f in range(FRAMES)]
    by[56.25] = [pal.transpose(fr) for fr in by[33.75]]
    by[78.75] = [pal.transpose(fr) for fr in by[11.25]]
    out = []
    for theta in HEADINGS_MID:
        out.extend(by[theta])
    return out
