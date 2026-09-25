"""Cut a sprite frame into its parts along its own keylines, so a pose can be re-assembled from the
character's pixels: move an arm, flip a blade, keep a head.

    comps = components(im)            # 4-connected runs of non-keyline colour
    part  = take(im, comps, pick)     # the chosen components plus the keyline that rings them

The keyline is shared between touching shapes, so a black pixel goes with every part it touches
(8-neighbourhood). Re-compositing the parts in the right order then puts back exactly one line
wherever two parts meet, and a part moved away from its neighbour keeps a closed outline.
"""
from PIL import Image

CLEAR = (0, 0, 0, 0)


def is_key(p, key=(0, 0, 0)):
    return p[3] > 128 and p[:3] == tuple(key)


def components(im, key=(0, 0, 0)):
    """[{id, pixels:set, box:(x0,y0,x1,y1), colours:set}] for every 4-connected region of
    opaque, non-keyline pixels."""
    w, h = im.size
    px = im.load()
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if seen[y][x] or p[3] <= 128 or is_key(p, key):
                continue
            stack = [(x, y)]
            seen[y][x] = True
            pix = set()
            cols = set()
            while stack:
                cx, cy = stack.pop()
                pix.add((cx, cy))
                cols.add(px[cx, cy][:3])
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx]:
                        q = px[nx, ny]
                        if q[3] > 128 and not is_key(q, key):
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            xs = [q[0] for q in pix]
            ys = [q[1] for q in pix]
            out.append({"id": len(out), "pixels": pix, "box": (min(xs), min(ys), max(xs), max(ys)),
                        "colours": cols})
    return out


def keyring(im, pixels, key=(0, 0, 0)):
    """The keyline pixels 8-adjacent to a pixel set."""
    w, h = im.size
    px = im.load()
    ring = set()
    for (x, y) in pixels:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in pixels and is_key(px[nx, ny], key):
                    ring.add((nx, ny))
    return ring


def take(im, comps, ids, key=(0, 0, 0), ring=True):
    """A new image holding only the chosen components (and, by default, their keyline)."""
    px = im.load()
    pix = set()
    for c in comps:
        if c["id"] in ids:
            pix |= c["pixels"]
    if ring:
        pix |= keyring(im, pix, key)
    out = Image.new("RGBA", im.size, CLEAR)
    o = out.load()
    for (x, y) in pix:
        o[x, y] = px[x, y]
    return out


def erase(im, part):
    """im minus every pixel that is opaque in part."""
    out = im.copy()
    o = out.load()
    p = part.load()
    for y in range(im.height):
        for x in range(im.width):
            if p[x, y][3] > 128:
                o[x, y] = CLEAR
    return out


def shift(part, dx, dy, size=None):
    size = size or part.size
    out = Image.new("RGBA", size, CLEAR)
    out.alpha_composite(part, (dx, dy)) if dx >= 0 and dy >= 0 else out.paste(part, (dx, dy), part)
    return out


def mirror_about(part, axis2, size=None):
    """Mirror a part about the vertical line x = axis2 / 2 (axis2 = 2*axis, so half-texel axes stay
    integer): x' = axis2 - 1 - x."""
    size = size or part.size
    out = Image.new("RGBA", size, CLEAR)
    src = part.load()
    dst = out.load()
    for y in range(part.height):
        for x in range(part.width):
            p = src[x, y]
            if p[3] > 128:
                nx = axis2 - 1 - x
                if 0 <= nx < size[0] and y < size[1]:
                    dst[nx, y] = p
    return out


def tint_view(im, comps, groups):
    """Debug: every chosen group of component ids in its own flat colour."""
    palette = [(255, 80, 80, 255), (80, 220, 80, 255), (80, 140, 255, 255), (255, 220, 60, 255),
               (220, 90, 255, 255), (60, 230, 230, 255), (255, 150, 40, 255), (160, 160, 160, 255)]
    out = im.copy()
    o = out.load()
    for gi, ids in enumerate(groups):
        for c in comps:
            if c["id"] in ids:
                for (x, y) in c["pixels"]:
                    o[x, y] = palette[gi % len(palette)]
    return out
