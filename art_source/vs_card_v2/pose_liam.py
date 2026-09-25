"""LIAM & BIXBY - Liam's glasses push with its glint, and Bixby's centre head looming over his
shoulder, cropped by the band's top rule.

Built from their own pixels, both natively lit from the upper left, so nothing is mirrored:
  * liam_glasses_push.png frame 3 - Liam: the finger on the bridge, the lenses gone to glare and the
                                    four-point glint on them (the push's peak), his headband's tails
                                    trailing. At 2x (Scale2x), like every 64 px sheet.
  * bixby_beast.png frame 0       - Bixby (the approved Hades-Cerberus redesign): the centre head
                                    only - the spiked mane, Liam's headband plate and its tails, the
                                    green eyes, the open jaws and tongue, the studded collar - cut
                                    along its own keyline (segment.py). At 1x: his sheet's head is
                                    already card-sized (STYLE.md), so the cut's silhouette keyline is
                                    grown outward by one texel to match everyone else's 2.
The one place the cut is not along a keyline: the wing's purple line runs down the outside of the
mane with no ink between them (x 60-63 and 128-131, rows 43-67), so those wing pixels are dropped
and the mane's edge there is closed with ink before the keyline is grown.

Bixby stands behind Liam's left shoulder (screen right), higher, so the raised arm and the glint
stay clear and his jaws hang over Liam's shoulder; the top rule crops the spikes above his headband.
Liam's glasses sit on the shared eye line (band row 58); Bixby looms above it.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402
import segment as S                                                           # noqa: E402

LIAM = ("Liam/liam_glasses_push.png", 3, 64, 64)
BIXBY = ("Bixby/bixby_beast.png", 0, 192, 160)

# the centre head: every component inside this box (frame 0 coordinates) that is not the wing's...
HEAD_BOX = (58, 0, 134, 106)
WING = {"#221A28", "#362A3E", "#4E3F5A", "#7A5AAE", "#A98AE6"}
# ...plus the headband's tails, which trail out past the box to the right
TAILS = [28, 35, 36]

# where each figure goes on the pose's canvas (texels): Bixby's cut head, Liam's 2x frame. Bixby
# stands 104 to the right of Liam's frame, so Liam's headband tails (2x x 88-124, in front of him)
# cross only his mane and never his snout, and 40 higher, so his eyes glare down from above Liam's
# hair. (Tried and dropped: the tails layered behind Bixby, which leaves their keyline scribbled
# across his face; Bixby nearer, where the tails reach his nose.)
CANVAS = (224, 168)
BIXBY_AT = (104, 0)
LIAM_AT = (0, 40)


def frame(spec):
    path, i, w, h = spec
    return P.load(path, (i * w, 0, i * w + w, h))


def bixby_head():
    f = frame(BIXBY)
    comps = S.components(f)
    x0, y0, x1, y1 = HEAD_BOX
    keep = []
    for c in comps:
        bx0, by0, bx1, by1 = c["box"]
        cols = {P.hexc(q) for q in c["colours"]}
        if c["id"] in TAILS or (bx0 >= x0 and by0 >= y0 and bx1 <= x1 and by1 <= y1 and not cols <= WING):
            keep.append(c["id"])
    head = S.take(f, comps, keep)
    px = head.load()
    for y in range(head.height):
        for x in range(head.width):
            if px[x, y][3] > 128 and P.hexc(px[x, y]) in WING:
                px[x, y] = P.CLEAR
    close_edges(head)
    P.outline(head)                     # grown to 2, like everyone else's
    return head.crop(head.getbbox()), head.getbbox()


def close_edges(im):
    """Ink every clear texel that touches colour directly - an edge the cut left without its line."""
    px = im.load()
    w, h = im.size
    add = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 128:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128 and px[nx, ny][:3] != (0, 0, 0):
                    add.append((x, y))
                    break
    for q in add:
        px[q] = P.BLACK
    return im


def liam():
    im = P.scale2x(frame(LIAM))
    return im


def assemble():
    canvas = Image.new("RGBA", CANVAS, P.CLEAR)
    head, box = bixby_head()
    canvas.paste(head, BIXBY_AT, head)
    L = liam()
    canvas.alpha_composite(L, LIAM_AT) if LIAM_AT[0] >= 0 and LIAM_AT[1] >= 0 else canvas.paste(L, LIAM_AT, L)
    return canvas


def build():
    im = assemble()
    return im.crop(im.getbbox())


if __name__ == "__main__":
    out = sys.argv[1]
    b = build()
    P.save_zoom(b, os.path.join(out, "liam_pose_4x.png"), 4)
    head, _ = bixby_head()
    P.save_zoom(head, os.path.join(out, "bixby_head_4x.png"), 4)
    print("liam frame 3", P.numbers(frame(LIAM)), "2x", P.numbers(liam()))
    print("bixby frame 0", P.numbers(frame(BIXBY)), "head", head.size, P.numbers(head))
    print("pose", b.size, P.numbers(b))
