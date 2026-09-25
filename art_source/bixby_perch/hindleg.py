"""The hind leg on the rope (right leg; the left is its mirror): talons hooked over the top of the rope,
the white foot and shin hanging down from under it to the hock, a red fur tuft flaring off the hock, and
the big red thigh angling back in to the hip. Drawn in the approved leg's ramps and cuts (bone white
shin lit on its outer-left edge, ember-red thigh lit along its top), stamped with keylines by the canvas.

leg(J, grip) returns the parts back to front. J: paw (the toes' centre on the rope), hock, hip, and
optionally splay (0 hooked, 1 talons thrown open when he lets go).
"""
import math

from common import pal, shapes
from pal import fill, poly, ellipse
from shapes import capsule, edge, recolor, poly_line

TOE_DX = (-7.5, -2.5, 2.5, 7.5)       # toe centres across the paw


def toes(paw, splay=0.0):
    """Four toes curled over the rope's top: rounded white knuckles."""
    px, py = paw
    out = []
    for i, dx in enumerate(TOE_DX):
        lift = 1 if i in (1, 2) else 0            # the middle toes ride a texel higher
        t = fill(ellipse(px + dx * (1 + 0.25 * splay), py - 2 - lift, 2.6, 3.4), 'x')
        recolor(t, edge(t, 0, -1, 1), 'w')
        recolor(t, edge(t, -1, 0, 1), 'w', only='x')
        recolor(t, edge(t, 0, 1, 2), 'y')
        recolor(t, edge(t, 1, 0, 1), 'y')
        out.append(t)
    return out


def talon(base, tip, w=1.3):
    """A hooked charcoal talon from its base on a toe to its point: violet glint on the lit side."""
    (bx, by), (tx, ty) = base, tip
    mx, my = (bx + tx) / 2.0 + (tx - bx) * 0.15, (by + ty) / 2.0 - 0.8
    c = fill(poly([(bx - w, by), (bx + w, by), (mx + 0.6, my), (tx, ty), (mx - 0.6, my)]), 'c')
    recolor(c, edge(c, -1, 0, 1), 'd')
    recolor(c, edge(c, 0, -1, 1), 'e', only='d')
    recolor(c, edge(c, 1, 0, 1), 'b')
    return c


def talons(paw, splay=0.0):
    px, py = paw
    out = []
    for i, dx in enumerate(TOE_DX):
        lift = 1 if i in (1, 2) else 0
        bx = px + dx * (1 + 0.25 * splay)
        by = py - 5 - lift
        lean = -dx * 0.28 * (1 - splay) + dx * 0.6 * splay       # hooked in, or thrown open
        rise = 6 - 2 * splay
        out.append(talon((bx, by), (bx + lean, by - rise)))
    return out


def foot(paw):
    """The back of the paw, behind the rope band (it shows only if the rope row moves)."""
    px, py = paw
    f = fill(ellipse(px, py + 2, 10.5, 4.5), 'x')
    recolor(f, edge(f, 0, 1, 2), 'y')
    recolor(f, edge(f, 1, 0, 1), 'z')
    return f


def shin(ankle, hock, r0=5.2, r1=5.8):
    s = fill(capsule(ankle, hock, r0, r1), 'x')
    recolor(s, edge(s, -1, 0, 2), 'w', only='x')
    recolor(s, edge(s, 1, 0, 3), 'y')
    recolor(s, edge(s, 1, 0, 1), 'z')
    # a groove down the shin's front
    ax, ay = ankle
    hx, hy = hock
    for q in poly_line([(ax + 1, ay + 3), (hx + 1, hy - 3)]):
        if q in s and s[q] == 'x':
            s[q] = 'y'
    return s


def thigh(hock, hip, r_hock=8.0, r_hip=11.5):
    """The red thigh from the hock back in to the hip, with the tuft flaring out and down off the hock."""
    hx, hy = hock
    th = fill(capsule(hock, hip, r_hock, r_hip), 't')
    # the hock tuft: two flame-shaped blades raking out past the hock
    a = math.atan2(hy - hip[1], hx - hip[0])          # along the thigh toward the hock
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux                                  # across it (toward the lower side)

    def at(u, n):
        return (hx + ux * u + nx * n, hy + uy * u + ny * n)
    tuft = poly([at(-3, -6), at(6, -4), at(3, -1), at(9, 2), at(2, 3), at(5, 7), at(-4, 7)])
    th.update({p: 't' for p in tuft})
    recolor(th, edge(th, 0, -1, 1), 'u')
    recolor(th, edge(th, -1, 0, 1), 'u', only='t')
    recolor(th, edge(th, 1, 0, 2), 's')
    recolor(th, edge(th, 0, 1, 2), 's')
    recolor(th, edge(th, 0, 1, 1), 'r')
    # black fur cuts: one splitting the tuft off, one down the thigh's back
    for seg in ([at(1, 0), at(6, 2)], [at(-6, 3), at(-13, 6)]):
        for q in poly_line(seg):
            if q in th:
                th[q] = 'k'
    return th


def leg(J, grip='hook'):
    """Parts back to front: thigh, shin, foot, talons, toes (the toes curl over the talons' bases)."""
    splay = J.get('splay', 1.0 if grip == 'open' else 0.0)
    parts = [thigh(J['hock'], J['hip']), shin(J['ankle'], J['hock']), foot(J['paw'])]
    parts += talons(J['paw'], splay)
    parts += toes(J['paw'], splay)
    return parts
