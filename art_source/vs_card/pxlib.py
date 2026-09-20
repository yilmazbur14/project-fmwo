"""Tiny pixel-art drawing helpers: crisp polygons, silhouette outlining, clipped shading."""
from PIL import Image, ImageDraw

def canvas(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def hx(c):
    c = c.lstrip("#")
    return (int(c[0:2],16), int(c[2:4],16), int(c[4:6],16), 255)

def poly(im, pts, color):
    d = ImageDraw.Draw(im)
    d.polygon([tuple(p) for p in pts], fill=hx(color) if isinstance(color,str) else color)

def poly_clip(im, pts, color):
    """Fill a polygon but only where the image is already opaque (stay inside the silhouette)."""
    m = canvas(*im.size)
    poly(m, pts, color)
    base = im.split()[3].point(lambda a: 255 if a > 128 else 0)
    mm = m.split()[3].point(lambda a: 255 if a > 128 else 0)
    from PIL import ImageChops
    keep = ImageChops.multiply(base, mm)
    im.paste(m, (0,0), keep)

def line(im, p0, p1, color, w=1):
    d = ImageDraw.Draw(im)
    d.line([tuple(p0), tuple(p1)], fill=hx(color) if isinstance(color,str) else color, width=w)

def lines_clip(im, pts, color, w=1):
    m = canvas(*im.size)
    d = ImageDraw.Draw(m)
    d.line([tuple(p) for p in pts], fill=hx(color) if isinstance(color,str) else color, width=w)
    base = im.split()[3].point(lambda a: 255 if a > 128 else 0)
    mm = m.split()[3].point(lambda a: 255 if a > 128 else 0)
    from PIL import ImageChops
    im.paste(m, (0,0), ImageChops.multiply(base, mm))

def px(im, pts, color):
    c = hx(color) if isinstance(color,str) else color
    for (x,y) in pts:
        if 0 <= x < im.width and 0 <= y < im.height:
            im.putpixel((int(x),int(y)), c)

def px_clip(im, pts, color):
    c = hx(color) if isinstance(color,str) else color
    for (x,y) in pts:
        if 0 <= x < im.width and 0 <= y < im.height and im.getpixel((int(x),int(y)))[3] > 128:
            im.putpixel((int(x),int(y)), c)

def plate(im, pts, base, hi=None, sh=None, ink="#000000", hi_h=1, sh_h=1):
    """One armour plate: a 1px black keyline, a lit top edge, a dark underside.

    This is the unit the game's sprites are actually built from - eric_sheet_v2
    is one pixel in five pure black because EVERY interior shape carries its own
    keyline, not just the silhouette. Drawing shapes with plate() instead of
    plain fills is what puts that black back."""
    from PIL import ImageFilter
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    grown = m.filter(ImageFilter.MaxFilter(3))
    im.paste(hx(ink) if isinstance(ink, str) else ink, (0, 0), grown)
    im.paste(hx(base) if isinstance(base, str) else base, (0, 0), m)
    if hi or sh:
        a = m.load()
        for x in range(im.width):
            ys = [y for y in range(im.height) if a[x, y]]
            if not ys:
                continue
            if hi:
                for y in ys[:hi_h]:
                    im.putpixel((x, y), hx(hi))
            if sh:
                for y in ys[-sh_h:]:
                    im.putpixel((x, y), hx(sh))
    return im


def seam(im, pts, color="#000000", w=1):
    """A hard black separation between two touching shapes."""
    ImageDraw.Draw(im).line([tuple(p) for p in pts],
                            fill=hx(color) if isinstance(color, str) else color, width=w)


def black_ratio(im):
    """Share of opaque pixels that are pure black - the check the sprite sets."""
    px = im.load()
    op = bk = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 128:
                op += 1
                if (r, g, b) == (0, 0, 0):
                    bk += 1
    return bk, op, (100.0 * bk / op if op else 0.0)


def outline(im, color="#000000", bottom=True):
    """Add a 1px outline in the transparent pixels orthogonally adjacent to opaque ones."""
    c = hx(color) if isinstance(color,str) else color
    w, h = im.size
    a = im.load()
    add = []
    for y in range(h):
        for x in range(w):
            if a[x,y][3] > 128: continue
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = x+dx, y+dy
                if 0 <= nx < w and 0 <= ny < h and a[nx,ny][3] > 128:
                    if not bottom and dy == -1: continue
                    add.append((x,y)); break
    for p in add: a[p[0],p[1]] = c
    return im

def save_zoom(im, path, f=1, bg=None):
    o = im
    if bg:
        b = Image.new("RGBA", im.size, hx(bg)); b.alpha_composite(im); o = b
    if f != 1: o = o.resize((o.width*f, o.height*f), Image.NEAREST)
    o.save(path)
