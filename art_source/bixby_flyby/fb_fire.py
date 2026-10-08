"""The breath's fire, in the Inferno ramp (art_source/bixby_inferno_fx/pal.py): white-hot '!', then
Y P p N, cooling to n and r at the rims. Like every fire on this beast it carries no black keyline; its
rim is the ramp's dark red, as on the flood, the burst and the approved fire breath.

One model draws both the streams in the frame and the curtain sprite: three ribbons of falling fire, one
per maw, over a darker glow that fills the wall between them. A ribbon has a hot core and cooler rims;
streaky noise stretched down the fall makes it pour. In the curtain the ribbons sit on columns 4.5, 15.5
and 26.5 of its 32 (the leading edge is column 31); in the frame the same columns are counted back from
the lead exit, so the streams run straight into the curtain that hangs from the exit row.
"""
import fb_common  # noqa: F401  (puts the rig on sys.path, read-only)
import math

FIRE = ['r', 'n', 'N', 'p', 'P', 'Y', '!']
CUTS = [0.16, 0.28, 0.40, 0.52, 0.66, 0.80, 0.93]      # heat at which each key starts
CURTAIN_W = 32
CURTAIN_ROWS = 48
FRAMES = 4
RIBBONS = [26.5, 15.5, 4.5]                            # ribbon centres in curtain columns: lead, mid, near
RIBBON_HALF = 5.2


def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _smooth(t):
    return t * t * (3 - 2 * t)


def noise(x, y, seed=0, px=None, py=None):
    """Value noise on a 1-unit lattice, optionally periodic in x (px) and y (py)."""
    x0, y0 = math.floor(x), math.floor(y)
    fx, fy = _smooth(x - x0), _smooth(y - y0)

    def h(ix, iy):
        if px:
            ix %= px
        if py:
            iy %= py
        return _hash(ix, iy, seed)
    a = h(x0, y0) + (h(x0 + 1, y0) - h(x0, y0)) * fx
    b = h(x0, y0 + 1) + (h(x0 + 1, y0 + 1) - h(x0, y0 + 1)) * fx
    return a + (b - a) * fy


def streak(c, r, t):
    """Streaky noise at curtain column c, curtain row r, frame t: stretched down the fall, periodic in
    CURTAIN_ROWS rows and FRAMES frames (a frame moves it 12 rows down, so frame 4 is frame 0)."""
    rr = r - t * (CURTAIN_ROWS / FRAMES)
    n1 = noise(c / 2.2, rr / 12.0, 7, py=CURTAIN_ROWS // 12)
    n2 = noise(c / 1.3, rr / 6.0, 19, py=CURTAIN_ROWS // 6)
    n3 = noise(c / 4.0, rr / 16.0, 31, py=CURTAIN_ROWS // 16)
    return 0.45 * n1 + 0.3 * n2 + 0.25 * n3


def wobble(i, r, t):
    """A ribbon's sideways sway down the fall: noise, periodic over the curtain and the loop."""
    rr = r - t * (CURTAIN_ROWS / FRAMES)
    return 2.4 * (noise(i * 5 + 1, rr / 8.0, 43, py=CURTAIN_ROWS // 8) - 0.5) +         1.2 * (noise(i * 5 + 3, rr / 4.0, 47, py=CURTAIN_ROWS // 4) - 0.5)


def heat(c, r, t, ribbons=RIBBONS, half=RIBBON_HALF, base=0.46, grow=None):
    """Heat of the wall at curtain column c, curtain row r (grow(i) -> 0..1 narrows a ribbon near its
    maw; base 0 leaves only the ribbons)."""
    n = streak(c, r, t)
    h = (base + (n - 0.5) * 0.36) if base > 0 else -1.0
    for i, rc in enumerate(ribbons):
        g = 1.0 if grow is None else grow(i)
        if g <= 0:
            continue
        rr = r - t * (CURTAIN_ROWS / FRAMES)
        w = half * (0.5 + 0.5 * g) * (0.85 + 0.35 * noise(i * 9 + 2, rr / 8.0, 53, py=CURTAIN_ROWS // 8))
        d = abs(c - (rc + wobble(i, r, t) * g)) / w
        if d < 1.25:
            core = max(0.0, 1.0 - d)
            hh = 0.50 + 0.46 * core * core + (n - 0.5) * 0.42
            h = max(h, hh)
    return h


def key_for(h):
    k = None
    for cut, kk in zip(CUTS, FIRE):
        if h >= cut:
            k = kk
    return k


def curtain_frame(t, top_cap=False):
    """One CURTAIN_W x CURTAIN_ROWS frame: seamless stacked, a loop over FRAMES; leading edge column 31."""
    out = {}
    for r in range(CURTAIN_ROWS):
        for c in range(CURTAIN_W):
            h = heat(c, r, t)
            if c <= 2:                                   # the trailing edge frays into the burning floor
                h -= 0.14 * (3 - c) + (1 - streak(c, r, t)) * 0.22
            k = key_for(h)
            if k:
                out[(c, r)] = k
    for r in range(CURTAIN_ROWS):                       # the leading edge: a crisp hot line
        n = streak(CURTAIN_W - 1, r, t)
        out[(CURTAIN_W - 1, r)] = 'P' if n > 0.45 else 'p'
        if out.get((CURTAIN_W - 2, r)) in (None, 'r', 'n'):
            out[(CURTAIN_W - 2, r)] = 'N'
    return out


def streams(maws, lead_x, exit_row, t, bottom=157):
    """{(x, y): key}: the three streams in the frame, from the maws (lead, mid, near: (x, y) where the
    fire's front edge leaves each maw) down to `bottom`, on the curtain's columns counted back from lead_x.
    A stream bursts white from its maw and opens to its ribbon over the first rows; the wall's glow fills
    in between once they have opened."""
    band0 = lead_x - (CURTAIN_W - 1)
    maw_rows = [my for (mx, my) in maws]
    top = int(math.floor(min(maw_rows)))
    out = {}
    for y in range(top, bottom + 1):
        r = y - exit_row
        opened = [min(1.0, max(0.0, (y - maw_rows[i] + 1) / 6.0)) for i in range(3)]
        below = min(y - m for m in maw_rows)
        for x in range(band0, lead_x + 1):
            c = x - band0
            h = heat(c, r, t, base=0.0, grow=lambda i: opened[i])
            if below >= 3:
                fill = heat(c, r, t, ribbons=[], base=0.46)
                h = max(h, fill - 0.3 * max(0.0, (8 - below) / 5.0))
            if below < 3:
                h += 0.2                                 # white-hot as it leaves the maws
            if c == CURTAIN_W - 1 and below >= 2:
                h = max(h, 0.56)
            k = key_for(h)
            if k:
                out[(x, y)] = k
    return out
