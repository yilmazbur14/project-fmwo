"""The torn sleeveless gi top: collar over the traps, a cap of cloth over each deltoid that ends in
torn teeth, a side panel down to the belt, and the lapel band along the open front.

Approved design kept: the same coverage as carter_akuma frame 0 (caps over the delts, lapels down
the sides of the chest to the belt). Execution changed:
  * the torn edge is four real teeth per cap, 2-4 px deep, so it survives 3x; the old zigzag was
    re-rasterised at 0.84 and most of its teeth merged into the keyline;
  * the lapel is a band with a fold line behind it, continuing up round the neck as the collar;
    the old lapels were a 1px bright-blue stripe each ('racing stripes');
  * one light: each cap is lit on its upper left, so the left cap is the brightest cloth and the
    right cap only catches light near the collar.
"""
from lib import poly, mirror_set, shade, n_sphere, n_cyl, fill, stroke

TH = [0.99, 0.84, 0.60, 0.30, 0.02]

# Left half (his right side, screen left), pixel-centre coordinates. The inner edge stops one pixel
# short of chest.CHEST's lapel keyline.
OUTLINE_L = [
    (40.5, 48.5), (36, 49), (32, 49.5), (29, 50.5), (26, 52), (23.5, 54), (21.5, 57), (20.5, 59.5),
    (20.5, 61), (21.5, 63.5), (23.0, 61.5), (23.5, 60.5),          # tooth A, notch
    (24.5, 62.0), (25.5, 64.5), (27.0, 61.5), (27.5, 60.5),        # tooth B, notch
    (28.0, 62.0), (28.5, 63.0), (29.5, 61.0), (30.0, 60.5),        # tooth C (short), notch
    (30.5, 62.0), (31.0, 63.5), (31.5, 62),                        # tooth D into the armpit
    (32, 64), (32, 68.5), (38, 68.5), (38, 64), (37, 63), (37, 53), (38, 52), (39, 51), (40, 50),
]


def mask_l():
    return poly(OUTLINE_L)


def lapel_band(m, side):
    """The three pixels of cloth next to the open front, and the collar they run up into."""
    inner = {}
    for (x, y) in m:
        row = [q[0] for q in m if q[1] == y]
        edge = max(row) if side == 0 else min(row)
        inner[(x, y)] = abs(edge - x)
    band = {q for q, d in inner.items() if d <= 2 and q[1] >= 51}
    collar = {q for q in m if q[1] <= 52 and (q[0] >= 32 if side == 0 else q[0] <= 63)}
    return band | collar


def half(side):
    m = mask_l()
    if side:
        m = mirror_set(m)
    cx = 27.0 if side == 0 else 68.0
    band = lapel_band(m, side)
    cap = {q for q in m - band if q[1] <= 63 and (q[0] <= 32 if side == 0 else q[0] >= 63)}
    panel = m - band - cap
    part = {}
    # cap: a sphere over the deltoid; its brightest step is 'b' (a hand-placed 'a' glint only)
    part.update(shade(cap, 'bcdef', n_sphere(cx, 55.5, 10.5, 9.5), TH[1:]))
    # the tatters hang in the cap's own shadow
    for (x, y) in cap:
        if y >= 61:
            part[(x, y)] = 'e' if part[(x, y)] in 'de' else 'd'
    # side panel, in the arm's shadow
    part.update(shade(panel, 'cdef', n_cyl((cx + (6 if side == 0 else -6), 60), (cx + (6 if side == 0 else -6), 70), 6.0), TH[2:]))
    # lapel band: lit where it rises over the traps, a crisp fold line behind it
    for q in band:
        x, y = q
        if y <= 52:
            k = 'b' if side == 0 else 'c'
        else:
            k = 'c'
        part[q] = k
    for (x, y) in band:
        if y >= 53:
            row = [q[0] for q in band if q[1] == y]
            outer = min(row) if side == 0 else max(row)
            inner = max(row) if side == 0 else min(row)
            if x == outer:
                part[(x, y)] = 'k'                     # the keyline behind the lapel
            elif x == inner:
                part[(x, y)] = 'd' if side == 0 else 'b'   # the rolled edge: in shade on the left, lit on the right
    # the same keyline carries on up over the trap as the edge of the collar
    for (x, y) in COLLAR_LINE_L:
        q = (x, y) if side == 0 else (95 - x, y)
        if q in part:
            part[q] = 'k'
    return part


COLLAR_LINE_L = [(34, 52), (33, 51), (32, 50)]


def jacket():
    return [half(0), half(1)]
