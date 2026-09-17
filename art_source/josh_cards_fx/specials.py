"""card_specials.png - every phase-2 three-card-monte asset on one 5x3 grid of 48x64 cells.

  row 0 : 0 SAFE   1 STAMINA DRAIN   2 INVERSE CONTROLS   3 BACK          4 (empty)
  row 1 : 5..8 SHUFFLE BLUR (a card sliding fast, left to right)          9 (empty)
  row 2 : 10..14 REVEAL FLASH - a face-agnostic gold burst OVERLAY

The reveal is an overlay rather than a baked flip so one 5-frame burst serves all three faces:
the coder plays it on top of the card and swaps BACK -> the drawn face on its middle frame.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *
from cardlib import _outline_cells

CW, CH = 48, 64
COLS, ROWS = 5, 3
MX, MY = CW / 2.0, CH / 2.0


# --------------------------------------------------------------------------- card body
def card_body(c, ox=0, oy=0, rim=('D', 'A'), face='n', shade='N', inner=None, pad=3):
    """The shared card blank: rounded rect, gold rim, 1px black outline.  Returns the cell set
    of the face area so a design can be masked to it."""
    cells, inner_cells = set(), set()
    hw, hh = CW / 2.0 - pad, CH / 2.0 - pad
    for y in range(CH):
        for x in range(CW):
            u, v = (x + 0.5 - MX) / hw, (y + 0.5 - MY) / hh
            au, av = abs(u), abs(v)
            rc = 0.22
            if au > 1 - rc and av > 1 - rc:
                if math.hypot((au - (1 - rc)) / rc, (av - (1 - rc)) / rc) > 1.0:
                    continue
            if au > 1 or av > 1:
                continue
            cells.add((ox + x, oy + y))
            lit = (-u) * 0.5 + (-v) * 0.5
            if au > 0.90 or av > 0.92:
                ch = rim[0] if lit > -0.15 else rim[1]
            elif au > 0.80 or av > 0.85:
                ch = 'K'
            else:
                # the whole cream field is glyph-able, so a spade is never clipped at the lobes
                inner_cells.add((ox + x, oy + y))
                # dithered light/shadow split - a hard diagonal across a flat face looks cut out
                hi = lit > -0.25 + (hashf(x, y, 61) - 0.5) * 0.10
                ch = (inner or face) if hi else (shade if inner is None else inner)
            c.p[oy + y][ox + x] = ch
    _outline_cells(c, cells, '#')
    return inner_cells


# Glyph radius.  SQUARE, so a spade stays a spade instead of stretching into a leaf the way an
# un-corrected 32x46 unit box makes it - and small enough that the lobes are not clipped off by
# the card's inner area, which is what turned the spade into a heart.
GR = 15.0


def sym_glyph(c, cells, fn, ox, oy, cy_off=0.0):
    """Paint a glyph over the card's inner area from a (u, v)->char function, u/v in [-1, 1]."""
    for (x, y) in cells:
        u = (x - ox + 0.5 - MX) / GR
        v = (y - oy + 0.5 - MY - cy_off) / GR
        ch = fn(u, v)
        if ch:
            c.p[y][x] = ch


def spade(u, v):
    """Unit spade, point up at v = -1.

    The upper edges are CONCAVE (the ** 1.55 curve).  A straight-sided cone over two lobes reads
    as a leaf or a heart at sprite size; the inward curve is what makes it read as a spade.
    """
    if (u + 0.44) ** 2 + (v - 0.22) ** 2 <= 0.46 ** 2:
        return True
    if (u - 0.44) ** 2 + (v - 0.22) ** 2 <= 0.46 ** 2:
        return True
    if -1.0 <= v <= 0.30 and abs(u) <= 1.00 * ((v + 1.0) / 1.30) ** 1.38:
        return True
    if 0.40 <= v <= 0.96:
        t = (v - 0.40) / 0.56
        return abs(u) <= 0.06 + 0.34 * t ** 3.0
    return False


def shade3(lit, ramp):
    return ramp[0] if lit > 0.42 else (ramp[1] if lit > -0.10 else ramp[2])


def keyline(c, inner, cols, col='#'):
    """1px black keyline around every glyph drawn in `cols` - the house style, and what stops a
    flat green spade sitting on flat cream with no edge at all."""
    hit = {(x, y) for (x, y) in inner if c.p[y][x] in cols}
    edge = set()
    for (x, y) in hit:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            n = (x + dx, y + dy)
            if n not in hit and n in inner:
                edge.add(n)
    for (x, y) in edge:
        c.p[y][x] = col
    return c


# --------------------------------------------------------------------------- the three faces
def face_safe(c, ox, oy):
    """Calm: a green-and-gold spade with a bold gold tick struck through it."""
    inner = card_body(c, ox, oy, rim=('F', 'D'), face='n', shade='N')
    def g(u, v):
        s, t = u * 1.22, v * 0.95
        if spade(s, t):
            return shade3(-s * 0.55 - t * 0.55, ['e', 'C', 'c'])
        return None
    sym_glyph(c, inner, g, ox, oy, cy_off=-2.0)
    keyline(c, inner, 'eCc')
    # the tick: a thick gold stroke with a black keyline, so it reads over the spade
    # The tick crosses the spade's LOBES, never its point - the point is the part that makes a
    # spade read as a spade, and an overlay through it turns the whole glyph into a green blob.
    pts = [(-12, 1), (-5, 10), (12, -10)]
    stroke = set()
    for a in range(2):
        x0, y0 = pts[a]
        x1, y1 = pts[a + 1]
        n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2
        for s in range(n + 1):
            t = s / float(n)
            px = int(round(ox + MX + x0 + (x1 - x0) * t))
            py = int(round(oy + MY + y0 + (y1 - y0) * t))
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if abs(dx) + abs(dy) <= 2:
                        stroke.add((px + dx, py + dy))
    for (x, y) in stroke:
        if (x, y) in inner:
            c.p[y][x] = 'Y'
    for (x, y) in stroke:                                   # shade + keyline
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            if (x + dx, y + dy) in stroke or (x + dx, y + dy) not in inner:
                continue
            c.p[y + dy][x + dx] = '#'
    for (x, y) in stroke:                                   # a shadow lip under the stroke
        if (x, y + 1) not in stroke and (x, y) in inner and c.p[y][x] == 'Y':
            c.p[y][x] = 'D'
    return inner


def face_drain(c, ox, oy):
    """Stamina drain: a cracked spade bleeding sickly green out of its base."""
    inner = card_body(c, ox, oy, rim=('G', 'g'), face='N', shade='u')
    def g(u, v):
        s, t = u * 1.20, v * 0.94
        if not spade(s, t):
            return None
        # a jagged crack splitting the spade down its middle
        cx = 0.10 * math.sin(t * 5.2) + 0.06 * math.sin(t * 11.0)
        if abs(s - cx) < 0.085 and t > -0.34:   # starts below the point, which stays intact
            return 'j'
        return shade3(-s * 0.55 - t * 0.55, ['h', 'G', 'g'])
    sym_glyph(c, inner, g, ox, oy, cy_off=-5.0)
    # drips leaking straight out of the spade's base into shallow pools
    for (dx, ln) in ((-7, 5), (-1, 9), (6, 6)):
        x = int(ox + MX) + dx
        y0 = int(oy + MY) + 8
        for s in range(ln):
            y = y0 + s
            if (x, y) in inner:
                c.p[y][x] = 'g'
                if (x + 1, y) in inner:
                    c.p[y][x + 1] = 'G'
        _masked_disc(c, inner, x, y0 + ln + 1, 2.0, 'J')
        _masked_disc(c, inner, x - 0.5, y0 + ln + 0.5, 1.1, 'g')
    # one keyline over ALL the drain greens, after the drips - keylining the spade first would
    # then treat its own mid-tones as an edge and score black lines through the glyph
    keyline(c, inner, 'hGgjJ')
    return inner


def _masked_disc(c, inner, cx, cy, r, ch):
    """A blob clipped to the card's face, so a drip can never spill over the border."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x, y) in inner and math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                c.p[y][x] = ch


def face_inverse(c, ox, oy):
    """Inverse controls: two mirrored arrows crossing over a purple spade."""
    inner = card_body(c, ox, oy, rim=('P', 'p'), face='N', shade='u')
    def g(u, v):
        s, t = u * 1.30, v * 1.01
        if spade(s, t):
            return shade3(-s * 0.55 - t * 0.55, ['o', 'P', 'p'])
        return None
    sym_glyph(c, inner, g, ox, oy, cy_off=-6.0)
    keyline(c, inner, 'oPp')

    def arrow(cxp, cyp, sign, col, edge):
        """A chunky horizontal arrow pointing `sign`, with a black keyline."""
        cells = set()
        for dx in range(-11, 12):
            for dy in range(-4, 5):
                inside = False
                if abs(dy) <= 1 and (dx * sign) <= 4:                     # shaft
                    inside = True
                if (dx * sign) > 3 and abs(dy) <= 4 - ((dx * sign) - 4):  # head
                    inside = True
                if inside:
                    cells.add((cxp + dx, cyp + dy))
        for (x, y) in cells:
            if (x, y) in inner:
                c.p[y][x] = col
        for (x, y) in cells:                                              # keyline
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                if (x + dx, y + dy) not in cells and (x + dx, y + dy) in inner:
                    c.p[y + dy][x + dx] = edge
        return cells

    a1 = arrow(int(ox + MX) - 2, int(oy + MY) + 6, -1, 'w', '#')
    a2 = arrow(int(ox + MX) + 2, int(oy + MY) + 17, 1, 'w', '#')
    # a 1px shadow lip along each arrow's underside, so it has a little thickness
    for cells in (a1, a2):
        for (x, y) in cells:
            if (x, y + 1) not in cells and (x, y) in inner and c.p[y][x] == 'w':
                c.p[y][x] = 'z'
    return inner


def face_back(c, ox, oy):
    """Josh's card back: deep red, gold rim, a cream lattice and a centred gold spade."""
    inner = card_body(c, ox, oy, rim=('D', 'A'), face='Q', shade='q', inner='q')
    for (x, y) in inner:
        u = (x - ox + 0.5 - MX) / (CW / 2.0 - 8)
        v = (y - oy + 0.5 - MY) / (CH / 2.0 - 9)
        a, b = u * 3.4 + v * 4.6, u * 3.4 - v * 4.6
        lat = (abs(a - math.floor(a) - 0.5) > 0.40) or (abs(b - math.floor(b) - 0.5) > 0.40)
        lit = (-u) * 0.5 + (-v) * 0.5
        if lat:
            c.p[y][x] = 'u' if lit > -0.1 else 'U'
        else:
            c.p[y][x] = 'Q' if lit > 0.0 else 'q'
    def g(u, v):
        s, t = u * 1.85, v * 1.45
        if abs(s) <= 1.05 and abs(t) <= 1.05 and spade(s, t):
            return shade3(-s * 0.55 - t * 0.55, ['F', 'D', 'A'])
        return None
    sym_glyph(c, inner, g, ox, oy)
    # a dark keyline round the centre spade so it does not melt into the lattice
    sp = {(x, y) for (x, y) in inner if c.p[y][x] in 'FDA'}
    for (x, y) in sp:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (x + dx, y + dy) in inner and (x + dx, y + dy) not in sp:
                c.p[y + dy][x + dx] = 'L'
    return inner


# --------------------------------------------------------------------------- shuffle blur
def shuffle_frame(c, ox, oy, i):
    """A card back sliding fast to the right: leaned over, horizontally smeared, speed lines.
    4 frames, seamless as a loop."""
    # The card always leans BACK against its travel and always slides right, so the four frames
    # cycle as one continuous skid rather than wobbling from side to side.
    lean = (-6.0, -11.0, -11.0, -6.0)[i]
    slide = (-9, -3, 3, 9)[i]
    smear = (0.70, 0.46, 0.46, 0.70)[i]
    tmp = Cv(CW, CH)
    face_back(tmp, 0, 0)
    # shear + horizontal squash, about the card's centre
    for y in range(CH):
        for x in range(CW):
            v = (y + 0.5 - MY) / (CH / 2.0)
            sx = (x + 0.5 - MX) / smear + MX - v * lean - slide
            xi = int(sx)
            if 0 <= xi < CW and tmp.p[y][xi] != '.':
                c.p[oy + y][ox + x] = tmp.p[y][xi]
    # speed lines streaking off the trailing (left) edge, brightest where they meet the card
    for k in range(8):
        ly = int(4 + k * 8 + (i % 2) * 3)
        if not (0 <= ly < CH):
            continue
        ln = 7 + (k * 5) % 10
        for s in range(ln):
            x = s
            if 0 <= x < CW and c.p[oy + ly][ox + x] == '.':
                t = s / float(ln - 1)
                c.p[oy + ly][ox + x] = ramp_pick(['A', 'D', 'F', 'Y'], t)
    return c


# --------------------------------------------------------------------------- reveal flash
def reveal_frame(c, ox, oy, i):
    """5 frames of a gold burst, drawn to sit ON TOP of a 48x64 card at the same position."""
    rad, rw, amp, rays_n, star = [(8.0, 8.0, 1.00, 0, 1.00),
                                  (16.0, 12.0, 1.00, 8, 0.80),
                                  (23.0, 12.0, 0.90, 10, 0.50),
                                  (29.0, 10.0, 0.62, 10, 0.22),
                                  (34.0, 7.0, 0.34, 8, 0.00)][i]
    ramp = ['A', 'D', 'F', 'Y', 'w']
    for y in range(CH):
        for x in range(CW):
            # dx scaled by the cell aspect (64/48) so the burst is an ellipse matched to the
            # card: it reaches the left/right and top/bottom edges at the same moment
            dx, dy = (x + 0.5 - MX) * 1.333, y + 0.5 - MY
            d = math.hypot(dx, dy)
            if d > rad:
                continue
            # a SHELL: brightest at the leading edge, hollow behind it.  Clamping to [0, 1] is
            # what stops the interior overflowing the ramp and going solid white.
            t = max(0.0, min(1.0, 1.0 - (rad - d) / rw)) * amp
            if i == 0:
                t = amp * (1.0 - d / rad) ** 0.5        # the first frame is a filled pop
            if (x * 7 + y * 11) % 5 == 0:
                t *= 0.8
            k = int(t * len(ramp))
            if k > 0:
                c.p[oy + y][ox + x] = ramp[min(k - 1, len(ramp) - 1)]
    # radiating streaks - the anime "ta-da" cue
    for k in range(rays_n):
        a = math.radians(k * (360.0 / max(1, rays_n)) + i * 9.0)
        for s in range(int(rad * 0.55), int(rad * 1.5)):
            x = int(MX + math.cos(a) * s * 0.75)
            y = int(MY + math.sin(a) * s)
            if not (0 <= x < CW and 0 <= y < CH):
                break
            v = amp * (1.0 - (s - rad * 0.55) / max(1.0, rad * 0.95))
            kk = int(v * len(ramp))
            if kk > 0:
                c.p[oy + y][ox + x] = ramp[min(kk - 1, len(ramp) - 1)]
    # four-point sparkle stars, strongest on the first frames
    if star > 0.05:
        for (sx, sy, sz) in ((0.30, 0.22, 5), (0.72, 0.62, 4), (0.20, 0.78, 3), (0.80, 0.30, 3)):
            px, py = int(CW * sx), int(CH * sy)
            n = max(1, int(sz * star))
            for s in range(-n, n + 1):
                for (dx, dy) in ((s, 0), (0, s)):
                    if 0 <= px + dx < CW and 0 <= py + dy < CH:
                        c.p[oy + py + dy][ox + px + dx] = 'w' if abs(s) < 2 else 'F'
    return c


# --------------------------------------------------------------------------- sheet
def build():
    s = Cv(CW * COLS, CH * ROWS)
    face_safe(s, 0, 0)
    face_drain(s, CW, 0)
    face_inverse(s, CW * 2, 0)
    face_back(s, CW * 3, 0)
    for i in range(4):
        shuffle_frame(s, CW * i, CH, i)
    for i in range(5):
        reveal_frame(s, CW * i, CH * 2, i)
    return s


def cells():
    """The sheet split into 48x64 cells, for previews and GIFs."""
    s = build()
    out = []
    for r in range(ROWS):
        for col in range(COLS):
            cc = Cv(CW, CH)
            for y in range(CH):
                for x in range(CW):
                    cc.p[y][x] = s.p[r * CH + y][col * CW + x]
            out.append(cc)
    return out
