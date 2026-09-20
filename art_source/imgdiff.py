"""Pixel-exact image comparison for the art round-trip checks.

  python imgdiff.py        # run the self-test

WHY THIS MODULE EXISTS
Every topic used to compare a PNG with its Aseprite round-trip like this:

    ImageChops.difference(a, b).getbbox() is None     # "identical"

Pillow 10 changed Image.getbbox() to default to alpha_only=True, so from then
on that line compared SILHOUETTES and ignored colour completely.  Two images
that share an outline but differ in every single red pixel passed it as
identical.  That is not a hypothetical: it was found when new heart-beat frames
compared "identical" to the shipped sheet while differing in every red channel.
The phrase "round-trip lossless, 0 mismatches" appears throughout this
project's art deliveries, and wherever it came from that line it meant only
"the transparency matches".

WHAT pixel_diff COMPARES
Alpha on every pixel, and colour on every pixel that shows on either side.
Colour underneath a fully transparent pixel is deliberately ignored: it is
invisible, and Aseprite is free to rewrite it on export, so comparing it would
raise false alarms.  That matches the hand-written checks in ui_kit/rtcheck.py
and victory_screen/rtcheck.py, which were always sound.

Do not "simplify" this back to a bare .getbbox().  If you want the short form,
it is .getbbox(alpha_only=False) - but prefer pixel_diff, which also says how
many pixels moved and by how much, instead of just failing.
"""
from PIL import Image, ImageChops


def pixel_diff(a, b):
    """None if two images match, else a one-line description of how they differ."""
    if a.size != b.size:
        return "size %s vs %s" % (a.size, b.size)
    a, b = a.convert("RGBA"), b.convert("RGBA")
    d = ImageChops.difference(a, b)
    r, g, bl, al = d.split()
    # Colour only counts where a pixel shows on one side or the other.
    shows = ImageChops.lighter(a.getchannel("A"), b.getchannel("A")).point(lambda v: 255 if v else 0)
    rgb = ImageChops.multiply(ImageChops.lighter(ImageChops.lighter(r, g), bl), shows)
    if rgb.getbbox(alpha_only=False) is None and al.getbbox(alpha_only=False) is None:
        return None
    def px(im):  # Pillow 12 renamed getdata -> get_flattened_data
        flat = getattr(im, "get_flattened_data", None)
        return list(flat() if flat else im.getdata())

    pa, pb = px(a), px(b)
    bad = [i for i, (p, q) in enumerate(zip(pa, pb))
           if p[3] != q[3] or ((p[3] or q[3]) and p[:3] != q[:3])]
    i = bad[0]
    return ("%d of %d px differ, first at (%d,%d) %s vs %s, worst channel delta %d"
            % (len(bad), len(pa), i % a.width, i // a.width, pa[i], pb[i],
               max(rgb.getextrema()[1], al.getextrema()[1])))


def same(a, b):
    """True if the two images match. Use pixel_diff when you want the detail."""
    return pixel_diff(a, b) is None


# ------------------------------------------------------------------ self-test


def _selftest():
    """Negative controls. Case 2 is the one the old idiom let through."""
    def old(x, y):
        return x.size == y.size and ImageChops.difference(x, y).getbbox() is None

    solid = Image.new("RGBA", (16, 16), (200, 30, 30, 255))
    cases = []

    # Must MATCH.
    cases.append(("identical", solid, solid.copy(), False))
    blank, churn = Image.new("RGBA", (16, 16), (0, 0, 0, 0)), Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    churn.putpixel((3, 3), (99, 88, 77, 0))
    cases.append(("rgb rewritten under a transparent pixel", blank, churn, False))

    # Must DIFFER.
    cases.append(("every colour pixel differs", solid, Image.new("RGBA", (16, 16), (30, 200, 30, 255)), True))
    one = solid.copy(); one.putpixel((5, 7), (201, 30, 30, 255))
    cases.append(("one pixel, red channel off by one", solid, one, True))
    alpha = solid.copy(); alpha.putpixel((2, 2), (200, 30, 30, 0))
    cases.append(("one pixel turned transparent", solid, alpha, True))
    cases.append(("size mismatch", solid, Image.new("RGBA", (8, 8)), True))
    fig = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    for y in range(4, 20):
        for x in range(6, 18):
            fig.putpixel((x, y), (180, 40, 40, 255))
    shade = fig.copy()
    for y in range(4, 20):
        for x in range(6, 18):
            shade.putpixel((x, y), (179, 40, 40, 255))
    cases.append(("figure recoloured, silhouette kept", fig, shade, True))

    bad = 0
    for name, x, y, want_diff in cases:
        got = pixel_diff(x, y)
        ok = (got is not None) == want_diff
        bad += not ok
        print("%-5s %-42s %s" % ("PASS" if ok else "FAIL", name, got or "match"))
        if want_diff and x.size == y.size and old(x, y):
            print("      ^ the old getbbox() idiom called this identical")
    print("self-test: %d cases, %d failures" % (len(cases), bad))
    return bad


if __name__ == "__main__":
    import sys
    sys.exit(1 if _selftest() else 0)
