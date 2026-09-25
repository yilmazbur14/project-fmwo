"""Rounded-volume shading for drawn shapes: the 4-5 tone ramp that follows a form, not a flat fill.

A shape is a polygon (its silhouette, exact to the texel) plus a bulge: an ellipsoid (centre, radii)
whose normal lights the pixels inside the polygon. Light comes from the cast's upper left, a little
toward the viewer. The normal's dot with the light picks a tone from the shape's ramp through fixed
thresholds, so tones fall in clean bands the way the sprites' do - no dithering, no gradients.

    Painter(w, h).shape(pts, ramp, bulge=(cx, cy, rx, ry), key=True, rim=True)

Every shape is drawn over what is already there, ringed by a 1-texel keyline (key=True) - the
house rule that every interior shape carries its own line - and optionally lit along its top-left
edge by a 1-texel rim (rim=True) in the ramp's lightest tone.
"""
import math

from PIL import Image, ImageDraw, ImageFilter

INK = (0, 0, 0, 255)
LIGHT = (-0.55, -0.72, 0.42)          # upper left, toward the viewer
_n = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _n for c in LIGHT)


def rgba(c):
    if isinstance(c, tuple):
        return c if len(c) == 4 else c + (255,)
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


def mask_of(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    return m


def ell_mask(size, cx, cy, rx, ry):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    return m


class Painter:
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.size = (w, h)

    def tone(self, x, y, bulge, ramp, cuts, light=LIGHT):
        cx, cy, rx, ry = bulge
        nx = (x + 0.5 - cx) / rx
        ny = (y + 0.5 - cy) / ry
        d = nx * nx + ny * ny
        if d >= 1.0:
            nx, ny, nz = nx / math.sqrt(d), ny / math.sqrt(d), 0.0
        else:
            nz = math.sqrt(1.0 - d)
        lit = nx * light[0] + ny * light[1] + nz * light[2]
        # ramp is darkest first; cuts are the dot-product thresholds between its steps
        i = 0
        while i < len(cuts) and lit > cuts[i]:
            i += 1
        return ramp[min(i, len(ramp) - 1)]

    def shape(self, pts, ramp, bulge=None, key=True, rim=True, cuts=None, mask=None, light=LIGHT,
              flat=None):
        """Draw one keylined, volume-shaded shape over the canvas. Returns its mask."""
        m = mask if mask is not None else mask_of(self.size, pts)
        if key:
            grown = m.filter(ImageFilter.MaxFilter(3))
            self.im.paste(INK, (0, 0), grown)
        ramp = [rgba(c) for c in ramp]
        if cuts is None:
            cuts = default_cuts(len(ramp))
        if bulge is None:
            bb = m.getbbox()
            bulge = ((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0, (bb[2] - bb[0]) / 2.0 + 1,
                     (bb[3] - bb[1]) / 2.0 + 1)
        px = self.im.load()
        mp = m.load()
        bb = m.getbbox()
        if bb is None:
            return m
        for y in range(bb[1], bb[3]):
            for x in range(bb[0], bb[2]):
                if mp[x, y] > 128:
                    px[x, y] = rgba(flat) if flat else self.tone(x, y, bulge, ramp, cuts, light)
        if rim:
            self.rim(m, ramp[-1])
        return m

    def rim(self, m, colour):
        """A 1-texel lit edge on the top and left of a shape, just inside its keyline."""
        px = self.im.load()
        mp = m.load()
        bb = m.getbbox()
        w, h = self.size
        for y in range(bb[1], bb[3]):
            for x in range(bb[0], bb[2]):
                if mp[x, y] <= 128:
                    continue
                up = mp[x, y - 1] if y > 0 else 0
                lf = mp[x - 1, y] if x > 0 else 0
                upl = mp[x - 1, y - 1] if x > 0 and y > 0 else 0
                if up <= 128 or (lf <= 128 and upl <= 128):
                    px[x, y] = rgba(colour)

    def line(self, pts, colour=INK, width=1):
        ImageDraw.Draw(self.im).line([tuple(p) for p in pts], fill=rgba(colour), width=width)

    def fill(self, pts, colour, clip=None):
        """A flat polygon, optionally only where `clip` (a mask) is set."""
        m = mask_of(self.size, pts)
        if clip is not None:
            from PIL import ImageChops
            m = ImageChops.multiply(m, clip)
        self.im.paste(rgba(colour), (0, 0), m)

    def px(self, pts, colour):
        c = rgba(colour)
        p = self.im.load()
        for (x, y) in pts:
            if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
                p[x, y] = c


def default_cuts(n):
    """Dot-product cuts for an n-tone ramp (darkest first). Wider mid bands than shadow bands."""
    table = {
        1: [],
        2: [0.30],
        3: [0.05, 0.62],
        4: [-0.05, 0.35, 0.75],
        5: [-0.15, 0.18, 0.50, 0.82],
        6: [-0.25, 0.05, 0.32, 0.58, 0.86],
    }
    return table[n]
