"""Overlay pieces for Mason's poses. Drawn with 1px black outlines and colours
from the approved palette or the existing cast palette:
  #D9A066 nugget, #1A1A1A / #666666 phone, #639BFF glint (Greyson)
  #4B692F stink lines (Jordan)"""
import math
import rig
from rig import (BLACK, WHITE, CREAM, CREAM_HI, CREAM_MID, CREAM_DEEP, RED, RED_HI,
                 YEL, YEL_MID, YEL_DEEP, KHAKI, KHAKI_DK, draw_part, band, LX, LY, LZ)

NUG      = '#D9A066'
PHONE    = '#1A1A1A'
PHONE_HI = '#666666'
GLINT    = '#639BFF'
STINK    = '#4B692F'

def shifted(pts, dx, dy):
    return [(x + dx, y + dy) for (x, y) in pts]

def mirror_x(pts):
    return [(63 - x, y) for (x, y) in reversed(pts)]

# ----- limb builder: capsules along a centreline, cylinder-shaded ---------------
def limb_mask(pts, radii):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; R = max(radii) + 1
    mask = {}
    for y in range(int(min(ys) - R), int(max(ys) + R) + 1):
        for x in range(int(min(xs) - R), int(max(xs) + R) + 1):
            best = None
            for i in range(len(pts) - 1):
                ax, ay = pts[i]; bx, by = pts[i + 1]
                vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / L2))
                nx, ny = ax + t * vx, ay + t * vy
                r = radii[i] + (radii[i + 1] - radii[i]) * t
                d = math.hypot(x - nx, y - ny)
                if d <= r and (best is None or d / r < best[0]):
                    best = (d / r, (x - nx) / r, (y - ny) / r)
            if best: mask[(x, y)] = best
    return mask

def mask_draw(c, mask, colour_of):
    """outline = mask pixels touching the outside (4-neighbour), 1px, black"""
    inter = set()
    for (x, y), val in mask.items():
        if any((x + dx, y + dy) not in mask for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
            c.put(x, y, BLACK)
        else:
            col = colour_of(x, y, val)
            if col: c.put(x, y, col)
            inter.add((x, y))
    return inter

def cyl_lum(val):
    _, ox, oy = val
    nz = math.sqrt(max(0.0, 1.0 - ox * ox - oy * oy))
    return ox * LX + oy * LY + nz * LZ

def wing_colour(x, y, val):
    return band(cyl_lum(val), rig.TH['wing'])

def yellow_colour(x, y, val):
    v = cyl_lum(val)
    return YEL if v > 0.30 else (YEL_MID if v > -0.25 else YEL_DEEP)

def limb(pts, radii, colour=wing_colour, grooves=(), frame='body'):
    """frame: 'body' -> points are body-local, 'head' -> head-local, 'abs'"""
    def f(c):
        ox, oy = {'body': (c.bdx, c.bdy), 'head': c.head, 'abs': (0, 0)}[frame]
        if frame == 'body':
            ox += rig.rh(getattr(c, 'shear', 0.0) * 11)   # ride the body lean
        m = limb_mask(shifted(pts, ox, oy), radii)
        inter = mask_draw(c, m, colour)
        for (x, y) in grooves:
            if (x + ox, y + oy) in inter: c.put(x + ox, y + oy, CREAM_MID)
    return f

def pair(pts_r, radii, grooves_r=(), dx=0, dy=0):
    """the same limb on both sides, mirrored about x = 31.5"""
    pl = [(63 - x - dx, y + dy) for (x, y) in pts_r]
    pr = [(x + dx, y + dy) for (x, y) in pts_r]
    gl = [(63 - x - dx, y + dy) for (x, y) in grooves_r]
    gr = [(x + dx, y + dy) for (x, y) in grooves_r]
    return [limb(pl, radii, grooves=gl), limb(pr, radii, grooves=gr)]

# ----- food ----------------------------------------------------------------------
NUGGET = [(2,0),(5,0),(6,1),(7,2),(7,4),(6,5),(2,5),(0,4),(0,2)]
NUGGET_BITTEN = [(3,0),(5,0),(6,1),(7,2),(7,4),(6,5),(3,5),(2,4),(3,3),(2,2),(3,1)]

def nugget(ox, oy, bitten=False, crumbs=()):
    """head-local position"""
    def f(c):
        hx, hy = c.head
        x0, y0 = ox + hx, oy + hy
        pts = shifted(NUGGET_BITTEN if bitten else NUGGET, x0, y0)
        def shade(x, y):
            u, v = x - x0, y - y0
            if u + v <= 3: return CREAM
            if u + v >= 9: return CREAM_DEEP
            return NUG
        line, inter = draw_part(c, pts, shade)
        for (u, v) in ((4, 2), (2, 3), (5, 4)):
            if (x0 + u, y0 + v) in inter: c.put(x0 + u, y0 + v, CREAM_DEEP)
        for (u, v) in crumbs:
            c.put(x0 + u, y0 + v, NUG)
    return f

def fries(ox, oy):
    """red carton with a clump of fries; body-local top-left of the carton"""
    def f(c):
        x0, y0 = ox + c.bdx, oy + c.bdy
        clump = shifted([(1,-3),(2,-4),(3,-2),(4,-4),(5,-3),(6,-1),(6,1),(1,1),(0,-1)], x0, y0)
        draw_part(c, clump, lambda x, y: YEL_MID if (x - x0) in (3, 5) else YEL)
        carton = shifted([(0,0),(7,0),(6,6),(1,6)], x0, y0)
        draw_part(c, carton, lambda x, y: RED_HI if (x - x0) <= 2 else RED)
    return f

# ----- phone ---------------------------------------------------------------------
def phone(ox, oy):
    """head-local position"""
    def f(c):
        hx, hy = c.head
        x0, y0 = ox + hx, oy + hy
        body = shifted([(0,0),(5,0),(5,10),(0,10)], x0, y0)
        draw_part(c, body, lambda x, y: PHONE_HI if x - x0 == 1 else PHONE)
        c.put(x0 + 1, y0 + 2, GLINT)
    return f

# ----- effects -------------------------------------------------------------------
def sweat(points):
    """small teardrops; head-local tip positions"""
    def f(c):
        hx, hy = c.head
        for (x, y) in points:
            x += hx; y += hy
            for p in [(x, y), (x - 1, y + 1), (x + 1, y + 1), (x - 1, y + 2), (x + 1, y + 2), (x, y + 3)]:
                c.put(*p, BLACK)
            c.put(x, y + 1, WHITE); c.put(x, y + 2, GLINT)
    return f

def lines(segs, col=BLACK, local='abs'):
    def f(c):
        ox, oy = {'abs': (0, 0), 'head': c.head, 'body': (c.bdx, c.bdy)}[local]
        for seg in segs:
            for i in range(len(seg) - 1):
                for p in rig.bres(seg[i][0] + ox, seg[i][1] + oy, seg[i + 1][0] + ox, seg[i + 1][1] + oy):
                    c.put(*p, col)
    return f

def star(cx, cy, local='head'):
    """little dizzy star: yellow plus-shape with black outline"""
    def f(c):
        ox, oy = {'abs': (0, 0), 'head': c.head, 'body': (c.bdx, c.bdy)}[local]
        x, y = cx + ox, cy + oy
        body = [(0,-2),(0,-1),(-1,0),(0,0),(1,0),(0,1),(-2,0),(2,0),(0,2)]
        core = [(0,-1),(-1,0),(0,0),(1,0),(0,1)]
        for (u, v) in body:
            for (du, dv) in ((1,0),(-1,0),(0,1),(0,-1)):
                if (u + du, v + dv) not in body: c.put(x + u + du, y + v + dv, BLACK)
        for (u, v) in body: c.put(x + u, y + v, YEL)
        c.put(x, y, WHITE)
    return f
