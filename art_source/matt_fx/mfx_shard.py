"""matt_glass_shard.png: the glass shards that rain from the ceiling. 8 frames of 16x24, one strip:
  frame = shape * 2 + spin     shape 0 dagger, 1 trapezoid, 2 wide wedge, 3 notched sliver
  spin 0 and 1 alternate at 0.06 s while it falls: 1 is 0 mirrored with its lit and shaded faces swapped,
  so the tumbling shard flashes.
THE PIVOT IS THE BOTTOM CENTRE (8, 24): every shard falls tip first and its tip is on the bottom row, at
columns 7-8, so the pivot is the point that meets the floor. As a centred Sprite2D: offset (0, -12).
The glass ramp, opaque, no keyline: a #B8ECF5 or #E6FBFF body, the lit face white, the far face
#7FC9DB, a #4D8FA6 edge down the shaded side and a white glint near the top.
"""
import mfx_pal as pal

W, H = 16, 24
FRAME_SIZE = (16, 24)
NOTE = '8 frames: frame = shape*2 + spin (0.06 s); pivot bottom centre (8,24), offset (0,-12)'

# Polygons (x, y) in texel corners, tip at the bottom centre (8, 24).
SHAPES = [
    [(8, 24.5), (5.2, 19), (4.6, 6), (8, 1), (11.2, 7), (10.8, 19)],          # dagger: a long faceted blade
    [(8, 24.5), (3.6, 18.5), (3.8, 4), (12.6, 2), (12.4, 18)],               # trapezoid: a pane's corner
    [(8, 24.5), (2.4, 16.5), (3.4, 6), (14.4, 7.5), (13.4, 17)],             # wide wedge
    [(8, 24.5), (5, 19.5), (5.2, 4), (8.2, 5.8), (11, 2.5), (11.6, 18.5)],   # sliver with a broken top
]


def inside(px, py, poly):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def draw(poly, mirror):
    pts = [(W - x, y) for (x, y) in poly] if mirror else poly
    cover = {(x, y) for y in range(H) for x in range(W) if inside(x + 0.5, y + 0.5, pts)}
    # a clean 2-texel point on the bottom row, joined to the body, so the pivot is where it meets the floor
    low = max(y for (x, y) in cover)
    for y in range(low + 1, H):
        cover |= {(7, y), (8, y)}
    xs = [x for (x, y) in cover]
    mid = (min(xs) + max(xs)) / 2.0
    g = pal.blank(W, H)
    for (x, y) in cover:
        left_out = (x - 1, y) not in cover
        right_out = (x + 1, y) not in cover
        up_out = (x, y - 1) not in cover
        lit_left = not mirror                      # spin 0 is lit from the left, spin 1 from the right
        if (left_out and lit_left) or (right_out and not lit_left) or up_out:
            k = 'W'
        elif (right_out and lit_left) or (left_out and not lit_left):
            k = 'K'
        else:
            k = 'E' if ((x < mid) == lit_left) else 'I'
        g[y][x] = k
    # a glint near the top
    top = min(y for (x, y) in cover)
    gx = [x for (x, y) in cover if y == top + 2]
    if gx:
        g[top + 2][gx[len(gx) // 2]] = 'W'
    return pal.rows(g)


def frames():
    out = []
    for poly in SHAPES:
        out.append(draw(poly, False))
        out.append(draw(poly, True))
    return out
