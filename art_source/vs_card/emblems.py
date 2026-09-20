"""Ghosted emblems for the watermark behind each boss's bust.

All of them sit in the same box: centred at (0.80*w, h/2), half-size 0.40*h, so
every card's watermark lands in the same place. Shapes are given as polygons in
0..1 box coordinates and scaled in; "cross" is kept as explicit pixel maths so
Eric's already-shipped band_right rebuilds byte-identical.
"""
import math

_UNIT = {
    # machine/lifter: a bolt
    "bolt": [[(0.58, 0.00), (0.18, 0.56), (0.46, 0.56), (0.34, 1.00), (0.84, 0.40), (0.54, 0.40)]],
    # card shark: a spade
    "spade": [[(0.50, 0.00), (0.88, 0.44), (0.88, 0.62), (0.70, 0.73), (0.56, 0.64),
               (0.61, 0.86), (0.70, 1.00), (0.30, 1.00), (0.39, 0.86), (0.44, 0.64),
               (0.30, 0.73), (0.12, 0.62), (0.12, 0.44)]],
    # the demon: an inverted triangle with a bar
    "demon": [[(0.04, 0.10), (0.96, 0.10), (0.50, 0.98)],
              [(0.20, 0.00), (0.34, 0.16), (0.10, 0.14)],
              [(0.80, 0.00), (0.66, 0.16), (0.90, 0.14)]],
    # the throne: a crown
    "crown": [[(0.04, 0.94), (0.04, 0.26), (0.23, 0.54), (0.39, 0.06), (0.50, 0.42),
               (0.61, 0.06), (0.77, 0.54), (0.96, 0.26), (0.96, 0.94)]],
    # the lifter: a dumbbell
    "dumbbell": [[(0.00, 0.30), (0.16, 0.30), (0.16, 0.70), (0.00, 0.70)],
                 [(0.18, 0.18), (0.34, 0.18), (0.34, 0.82), (0.18, 0.82)],
                 [(0.36, 0.42), (0.64, 0.42), (0.64, 0.58), (0.36, 0.58)],
                 [(0.66, 0.18), (0.82, 0.18), (0.82, 0.82), (0.66, 0.82)],
                 [(0.84, 0.30), (1.00, 0.30), (1.00, 0.70), (0.84, 0.70)]],
    # the beast: a flame
    "flame": [[(0.50, 0.00), (0.66, 0.22), (0.62, 0.34), (0.78, 0.30), (0.86, 0.50),
               (0.80, 0.74), (0.60, 0.92), (0.40, 0.92), (0.20, 0.74), (0.14, 0.50),
               (0.22, 0.30), (0.38, 0.34), (0.34, 0.22)]],
    # the admin: a shield
    "shield": [[(0.50, 0.00), (0.94, 0.17), (0.94, 0.56), (0.50, 1.00), (0.06, 0.56), (0.06, 0.17)]],
}


def _star(points=5, r_out=0.5, r_in=0.21):
    pts = []
    for i in range(points * 2):
        a = -math.pi / 2 + i * math.pi / points
        r = r_out if i % 2 == 0 else r_in
        pts.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
    return [pts]


def _crescent(seg=28):
    """Sleeping giant: a moon, built as one polygon so a plain fill works."""
    ox, oy, orr = 0.46, 0.50, 0.48
    ix, iy, ir = 0.66, 0.44, 0.39
    a0, a1 = math.radians(58), math.radians(302)
    out = [(ox + math.cos(a0 + (a1 - a0) * i / seg) * orr,
            oy + math.sin(a0 + (a1 - a0) * i / seg) * orr) for i in range(seg + 1)]
    b0, b1 = math.radians(292), math.radians(68)
    inn = [(ix + math.cos(b0 + (b1 - b0) * i / seg) * ir,
            iy + math.sin(b0 + (b1 - b0) * i / seg) * ir) for i in range(seg + 1)]
    return [out + inn]


_UNIT["star"] = _star()[0] and _star()
_UNIT["moon"] = _crescent()


def emblem(name, w, h):
    """Polygons in pixel coordinates for a w x h band."""
    cx, cy, arm = int(w * 0.80), h // 2, int(h * 0.40)
    if name == "cross":
        thick = int(h * 0.105)
        return [[(cx - thick, cy - arm), (cx + thick, cy - arm), (cx + thick, cy - thick),
                 (cx + arm, cy - thick), (cx + arm, cy + thick), (cx + thick, cy + thick),
                 (cx + thick, cy + arm), (cx - thick, cy + arm), (cx - thick, cy + thick),
                 (cx - arm, cy + thick), (cx - arm, cy - thick), (cx - thick, cy - thick)]]
    out = []
    for poly in _UNIT[name]:
        out.append([(cx - arm + round(px * 2 * arm), cy - arm + round(py * 2 * arm)) for px, py in poly])
    return out
