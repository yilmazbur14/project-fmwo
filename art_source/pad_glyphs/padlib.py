"""padlib - tiny pixel-art helpers for the FMWO gamepad glyph set.

Everything is drawn in the DawnBringer-32 palette that the rest of the
project's UI already uses (verified against Assets/UI/key_shift.png,
key_arrows.png, hype_meter_frame.png, ui_card_frame.png).
"""
from PIL import Image

# ---------------------------------------------------------------- palette ---
# DB32 entries actually present in the existing UI art.
BLACK   = (0x00, 0x00, 0x00)
NAVY    = (0x22, 0x20, 0x34)   # glyph / recess colour on every keycap
WHITE   = (0xFF, 0xFF, 0xFF)

# keycap plastic ramp, lifted straight off key_q.png / key_shift.png
PL_HI   = (0xFF, 0xFF, 0xFF)
PL_FACE = (0xCB, 0xDB, 0xFC)
PL_MID  = (0x9B, 0xAD, 0xB7)
PL_LOW  = (0x84, 0x7E, 0x87)
PL_DARK = (0x69, 0x6A, 0x6A)
PL_DEEP = (0x59, 0x56, 0x52)

# brass accent ramp, lifted off hype_meter_frame.png / ui_card_frame.png
BR_HI   = (0xFB, 0xF2, 0x36)
BR_FACE = (0xEE, 0xC3, 0x9A)
BR_MID  = (0xD9, 0xA0, 0x66)
BR_LOW  = (0x8A, 0x6F, 0x30)
BR_DARK = (0x52, 0x4B, 0x24)

INDIGO  = (0x3F, 0x3F, 0x74)
PLUM    = (0x45, 0x28, 0x3C)

# four face-button ramps (face / mid / dark), all DB32
RAMP_GREEN  = ((0x99, 0xE5, 0x50), (0x6A, 0xBE, 0x30), (0x4B, 0x69, 0x2F))
RAMP_RED    = ((0xD9, 0x57, 0x63), (0xAC, 0x32, 0x32), (0x66, 0x39, 0x31))
RAMP_BLUE   = ((0x63, 0x9B, 0xFF), (0x5B, 0x6E, 0xE1), (0x3F, 0x3F, 0x74))
RAMP_YELLOW = ((0xFB, 0xF2, 0x36), (0xD9, 0xA0, 0x66), (0x8A, 0x6F, 0x30))

RAMP_PLASTIC = (PL_FACE, PL_MID, PL_DARK)
RAMP_BRASS   = (BR_HI, BR_MID, BR_LOW)


class C:
    """A tiny indexed canvas. Transparent where nothing was drawn."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    # -- primitives ---------------------------------------------------------
    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[(x, y)] = c

    def get(self, x, y):
        return self.px.get((int(x), int(y)))

    def has(self, x, y):
        return (int(x), int(y)) in self.px

    def clear(self, x, y):
        self.px.pop((int(x), int(y)), None)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def disc(self, cx, cy, r, c):
        """Filled circle. cx/cy are in *pixel-centre* space, so use 16.0 to
        centre a disc on a 32px canvas."""
        r2 = r * r
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = (x + 0.5) - cx, (y + 0.5) - cy
                if dx * dx + dy * dy <= r2:
                    self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = ((x + 0.5) - cx) / rx, ((y + 0.5) - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    self.set(x, y, c)

    def rrect(self, x0, y0, x1, y1, rad, c):
        """Rounded rectangle with a chamfered/rounded corner of `rad`."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                # corner test
                cx = x0 + rad if x < x0 + rad else (x1 - rad if x > x1 - rad else x)
                cy = y0 + rad if y < y0 + rad else (y1 - rad if y > y1 - rad else y)
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy <= rad * rad + rad * 0.6:
                    self.set(x, y, c)

    def blit(self, other, ox, oy):
        for (x, y), c in other.px.items():
            self.set(x + ox, y + oy, c)

    # -- masks --------------------------------------------------------------
    def mask(self, pred=None):
        if pred is None:
            return set(self.px.keys())
        return {p for p, c in self.px.items() if pred(c)}

    def mask_of(self, colours):
        colours = set(colours)
        return {p for p, c in self.px.items() if c in colours}

    # -- shading ------------------------------------------------------------
    def bevel(self, mask, hi, lo, hi_only=False, lo_only=False):
        """Light from the top-left: paint the top/left inner edge of `mask`
        with `hi` and the bottom/right inner edge with `lo`."""
        hi_px, lo_px = [], []
        for (x, y) in mask:
            up_out = (x, y - 1) not in mask
            lf_out = (x - 1, y) not in mask
            dn_out = (x, y + 1) not in mask
            rt_out = (x + 1, y) not in mask
            if (up_out or lf_out) and not (dn_out or rt_out):
                hi_px.append((x, y))
            elif (dn_out or rt_out) and not (up_out or lf_out):
                lo_px.append((x, y))
            elif up_out or lf_out:
                # thin arm: top/left wins
                hi_px.append((x, y))
        if not lo_only:
            for p in hi_px:
                self.set(p[0], p[1], hi)
        if not hi_only:
            for p in lo_px:
                self.set(p[0], p[1], lo)

    def shade_dome(self, cx, cy, r, ramp, hi=WHITE, rim=True):
        """Shade a circular button so it reads as a lit dome."""
        face, mid, dark = ramp
        lx, ly = -0.7071, -0.7071          # light from the top-left
        # specular centre
        px_, py_ = cx + lx * r * 0.42, cy + ly * r * 0.42
        for y in range(self.h):
            for x in range(self.w):
                if not self.has(x, y):
                    continue
                fx, fy = (x + 0.5) - cx, (y + 0.5) - cy
                d = (fx * fx + fy * fy) ** 0.5
                t = d / r
                if t > 1.02:
                    continue
                l = 0.0 if d < 0.001 else (fx * lx + fy * ly) / d
                dlx, dly = (x + 0.5) - px_, (y + 0.5) - py_
                dl = ((dlx * dlx + dly * dly) ** 0.5) / r
                if rim and t > 0.90:
                    self.set(x, y, dark if l < 0.10 else mid)
                elif rim and t > 0.78:
                    self.set(x, y, mid if l < 0.35 else face)
                elif dl < 0.36:
                    self.set(x, y, hi)
                elif dl > 1.02:
                    self.set(x, y, mid)
                else:
                    self.set(x, y, face)

    # -- outline ------------------------------------------------------------
    def outline(self, c=BLACK, diagonal=True):
        """Wrap every drawn pixel in a 1px pure-black outline."""
        m = set(self.px.keys())
        nbr = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if diagonal:
            nbr += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        add = set()
        for (x, y) in m:
            for dx, dy in nbr:
                p = (x + dx, y + dy)
                if p not in m and 0 <= p[0] < self.w and 0 <= p[1] < self.h:
                    add.add(p)
        for p in add:
            self.px[p] = c
        return add

    def inner_outline(self, mask, c=BLACK):
        """Draw a 1px black border *around* `mask` (inside the rest of art)."""
        nbr = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
        add = set()
        for (x, y) in mask:
            for dx, dy in nbr:
                p = (x + dx, y + dy)
                if p not in mask:
                    add.add(p)
        for p in add:
            if 0 <= p[0] < self.w and 0 <= p[1] < self.h:
                self.px[p] = c

    # -- io -----------------------------------------------------------------
    def image(self):
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        pix = im.load()
        for (x, y), c in self.px.items():
            pix[x, y] = (c[0], c[1], c[2], 255)
        return im

    def save(self, path):
        self.image().save(path)

    # -- checks -------------------------------------------------------------
    def check_symmetry(self, axis_x=None, axis_y=None, label=''):
        """axis_x: mirror x' = axis_x - x (use w-1 for a full mirror)."""
        bad = []
        if axis_x is not None:
            for (x, y), c in self.px.items():
                mx = axis_x - x
                if 0 <= mx < self.w and self.px.get((mx, y)) != c:
                    bad.append(((x, y), (mx, y)))
        if axis_y is not None:
            for (x, y), c in self.px.items():
                my = axis_y - y
                if 0 <= my < self.h and self.px.get((x, my)) != c:
                    bad.append(((x, y), (x, my)))
        if bad:
            print('  ! %s: %d asymmetric pixels, e.g. %s' % (label, len(bad), bad[:3]))
        return not bad


# ---------------------------------------------------------------- 5x7 font ---
# Chunky pixel numerals/letters in the same spirit as the SHIFT keycap text.
GLYPHS = {
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
}


def text(c, s, x, y, col, spacing=1):
    for ch in s:
        g = GLYPHS[ch]
        for gy, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == '#':
                    c.set(x + gx, y + gy, col)
        x += len(g[0]) + spacing
    return x
