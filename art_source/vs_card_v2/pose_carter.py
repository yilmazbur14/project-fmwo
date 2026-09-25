"""CARTER - back turned, the 天 burning white, one red eye glaring back over his shoulder at Burak.

Built from his own pixels: two approved sheets that share one back view (carter_polish_turns builds
both on backview.headless()):
  * carter_look_back.png frame 3 - the base: the gi with every dark line and fold, the head come
    round over his shoulder with the red slit staring back
  * carter_victory.png frame 4   - the burn: the 天's white strokes and the bloom that touches them,
                                   and the lit aura
Same frame, same pixels, so every join is his own.

He glares toward screen RIGHT in the look-back; Burak is on the left. Mirroring the figure would
move the light (STYLE.md: one light, upper left), so the body stays exactly as drawn - the 天 reads
the right way round with no fix - and only the head turns (turn_head_left): mirrored about its own
centre line, then re-lit, the dome taking its tones from the unmirrored sphere and the face side
stepping one tone up its ramp toward the light.

Then Scale2x, and the 2x pass (detail): the house keyline inside every aura spike, a red rim where
the burning strokes meet the gi, and the eye flash streaking off the slit toward Burak.

build(mirrored=True) keeps the whole-figure mirror that was tried first, for comparison only: it
turns him to Burak too, but lit from the upper right.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402

LOOK = ("Carter/carter_look_back.png", 3)
BURN = ("Carter/carter_victory.png", 4)
# look_back's own aura tones (dim) and the victory frame's (lit)
AURA_DIM = {"#19062A", "#780C28", "#2E0C4C", "#90102A"}
AURA_LIT = {"#19062A", "#C01830", "#FF4A3C", "#2E0C4C", "#FF9A6A", "#7C2EB0", "#780C28"}
# the head's own materials in the look-back: skin, beard, the eye, the cross earring
HEAD = {"#DB976C", "#B86C4E", "#F0B98E", "#FBD6B0", "#84412F", "#B05B21", "#703414", "#D66C28",
        "#F09040", "#4A2210", "#552619", "#FFB45E", "#E0203C", "#FF5A62", "#FFD2D8", "#E6ECF2",
        "#BED6FF", "#9BADB7"}
EARRING = {"#E6ECF2", "#BED6FF", "#9BADB7", "#E2A2F4", "#FFD2D8"}
NECK_ROW = 44               # from here down, the body is the victory frame's
TEN_BOX = (29, 51, 67, 70)  # the 天 and its bloom; symmetric about the frame's centre line


def frame(spec):
    path, i = spec
    return P.load(path, (i * 96, 0, i * 96 + 96, 96))


HOT = {"#FFFFFF", "#FFE2C0"}                 # the burning 天's core and halo in the victory frame
BLOOM = {"#FF4A3C", "#C01830", "#FF9A6A"}    # the red it throws onto the gi
TEN_RIM, TEN_FILL = "#FF4A3C", "#FF9A6A"     # the resting 天 on the look-back's gi
WHITE, CREAM = (255, 255, 255, 255), (255, 226, 192, 255)


def assemble(burn_style="rim", mirrored=False):
    """look_back frame 3 is the base: its gi keeps every dark line and fold, and its 天 is the one
    that burns. burn_style:
        "rim"     the resting glyph's own fill goes white-hot (cream where it meets the red rim),
                  its red rim stays - the red 天 burning through to white - with the victory
                  frame's sparks thrown just around it
        "victory" the victory frame's own burn transplanted: its fatter white strokes and the bloom
                  that touches them
    From the victory frame too: the lit aura."""
    look, burn = frame(LOOK), frame(BURN)
    out = look.copy()
    o, lp, bp = out.load(), look.load(), burn.load()
    if burn_style == "victory":
        glyph = {(x, y) for y in range(NECK_ROW, 80) for x in range(96)
                 if bp[x, y][3] > 128 and P.hexc(bp[x, y]) in HOT}
    else:
        glyph = {(x, y) for y in range(TEN_BOX[1], TEN_BOX[3]) for x in range(TEN_BOX[0], TEN_BOX[2])
                 if lp[x, y][3] > 128 and P.hexc(lp[x, y]) in (TEN_RIM, TEN_FILL)}
    near = set()
    for (x, y) in glyph:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near.add((x + dx, y + dy))
    for y in range(96):
        for x in range(96):
            l, b = lp[x, y], bp[x, y]
            lh = P.hexc(l) if l[3] > 128 else None
            bh = P.hexc(b) if b[3] > 128 else None
            if (x, y) in glyph:
                if burn_style == "victory":
                    o[x, y] = b
                elif lh == TEN_FILL:
                    inner = all((x + dx, y + dy) in glyph and
                                P.hexc(lp[x + dx, y + dy]) == TEN_FILL
                                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    o[x, y] = WHITE if inner else CREAM
            elif (x, y) in near and bh in BLOOM and lh not in HEAD:
                o[x, y] = b
            elif y < NECK_ROW + 4 and bh in AURA_LIT and (lh is None or lh in AURA_DIM):
                o[x, y] = b            # the lit aura, but never over the turned head
            elif (x < 20 or x > 76) and bh in AURA_LIT and (lh is None or lh in AURA_DIM):
                o[x, y] = b            # the side spikes, down the flanks
            elif lh in AURA_DIM and bh is None:
                o[x, y] = (0, 0, 0, 0)  # a dim spike the burning frame doesn't have
    if not mirrored:
        return out
    flipped = P.mirror(out)
    # the 天 back the right way round
    ten = out.crop(TEN_BOX)
    flipped.paste(ten, TEN_BOX[:2])
    return flipped


SPIKE_EDGE = "#19062A"                       # the aura's dark rim
SPIKE_FILL = {"#C01830", "#FF4A3C", "#FF9A6A", "#780C28", "#90102A"}
GI = {"#1D2B60", "#14204A", "#0C1430", "#2D4392", "#23184E", "#1B1C4C", "#150F33"}
EYE_AT = (76, 80)                            # 2x, mirrored: the left end of the red slit
EYE_AT_R = (115, 80)                         # 2x, as drawn: the right end of the red slit


def detail(im, mirrored=False):
    """The 2x pass - what the 1x sprite had no room for.
      * every aura spike gets the house keyline: its dark rim's inner texel, where it meets the red,
        goes black, and the purple stays outside it as the glow
      * the 天 burns at the edge: a red texel wherever the white stroke meets the gi
      * the red eye flares: a glint streak off the slit, trailing toward Burak past his profile"""
    px = im.load()
    w, h = im.size
    hexat = lambda x, y: P.hexc(px[x, y]) if 0 <= x < w and 0 <= y < h and px[x, y][3] > 128 else None
    n4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    ink, rim = [], []
    for y in range(h):
        for x in range(w):
            c = hexat(x, y)
            if c == SPIKE_EDGE and any(hexat(x + dx, y + dy) in SPIKE_FILL for dx, dy in n4):
                ink.append((x, y))
            elif c in GI and any(hexat(x + dx, y + dy) in HOT for dx, dy in n4):
                rim.append((x, y))
    for q in ink:
        px[q] = (0, 0, 0, 255)
    for q in rim:
        px[q] = P.rgba("#FF4A3C")
    # the eye flash: a white core line with red either side, tapering off away from his face
    ex, ey = EYE_AT if mirrored else EYE_AT_R
    step = -1 if mirrored else 1
    for i in range(30):
        x = ex + step * i
        if x < 0:
            break
        core = "#FFFFFF" if i < 12 else ("#FFD2D8" if i < 20 else "#FF4A3C")
        if hexat(x, ey) is None or i < 8:
            px[x, ey] = P.rgba(core)
        edge = "#FF4A3C" if i < 14 else "#C01830"
        if i < 22:
            for yy in (ey - 1, ey + 1):
                if hexat(x, yy) is None:
                    px[x, yy] = P.rgba(edge)
    return im


SKIN_RAMP = ["#84412F", "#B86C4E", "#DB976C", "#F0B98E", "#FBD6B0"]
BEARD_RAMP = ["#4A2210", "#552619", "#703414", "#B05B21", "#D66C28", "#F09040", "#FFB45E"]
HEAD_BOX = (28, 20, 70, 53)       # the look-back's head, earring and beard, at 1x
HEAD_AXIS2 = 97                   # mirror the head about x = 48.5, its own centre line
DOME_ROWS = (20, 34)              # the back head's sphere (lookback.py: rows 24-33 are the dome)


def _shift(hexc, ramp, by):
    i = ramp.index(hexc)
    return ramp[max(0, min(len(ramp) - 1, i + by))]


def turn_head_left(native):
    """Turn the look-back's head to glare over his LEFT shoulder, at Burak, keeping the one light.

    The body stays exactly as drawn. Only the head is mirrored, about its own centre line, and then
    re-lit, because a mirror moves the light with it:
      * the dome (the back head's sphere) takes its tones from the unmirrored head at the same
        texel - the same sphere under the same upper-left light
      * below the dome, the face half (now on the left, turned to the light) comes up one step of
        its ramp and the back-of-skull half down one step; the beard, all on the face side, up one
    Ink, the red eye and the cross earring are untouched."""
    src = native.load()
    head = set()
    x0, y0, x1, y1 = HEAD_BOX
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = src[x, y]
            if p[3] > 128 and (P.hexc(p) in HEAD or P.hexc(p) in EARRING):
                head.add((x, y))
    ring = set()
    for (x, y) in head:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in head and src[q][3] > 128 and src[q][:3] == (0, 0, 0):
                    ring.add(q)
    body = native.copy()
    b = body.load()
    for q in head | ring:
        b[q] = (0, 0, 0, 0)
    turned = Image.new("RGBA", native.size, (0, 0, 0, 0))
    t = turned.load()
    for (x, y) in head | ring:
        nx = HEAD_AXIS2 - x
        if 0 <= nx < native.width:
            t[nx, y] = src[x, y]
    mid = HEAD_AXIS2 / 2.0
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = t[x, y]
            if p[3] <= 128:
                continue
            h = P.hexc(p)
            if h in SKIN_RAMP:
                if DOME_ROWS[0] <= y < DOME_ROWS[1] and src[x, y][3] > 128                         and P.hexc(src[x, y]) in SKIN_RAMP:
                    t[x, y] = src[x, y]
                else:
                    t[x, y] = P.rgba(_shift(h, SKIN_RAMP, 1 if x < mid else -1))
            elif h in BEARD_RAMP:
                t[x, y] = P.rgba(_shift(h, BEARD_RAMP, 1))
    body.alpha_composite(turned)
    return body


def build(burn_style="victory", mirrored=False, look="left"):
    """look="left": native body, head turned to Burak and re-lit (the one-light rule).
    mirrored=True: the whole figure flipped (the light flips with it) - kept for comparison."""
    if mirrored:
        return detail(P.scale2x(assemble(burn_style, True)), True)
    base = assemble(burn_style, False)
    if look == "left":
        return detail(P.scale2x(turn_head_left(base)), True)
    return detail(P.scale2x(base), False)


if __name__ == "__main__":
    out = sys.argv[1]
    a = assemble()
    P.save_zoom(a, os.path.join(out, "carter_pose_1x_8x.png"), 8)
    b = build()
    P.save_zoom(b, os.path.join(out, "carter_pose_2x_4x.png"), 4)
    print("1x", P.numbers(a), "2x", P.numbers(b))
