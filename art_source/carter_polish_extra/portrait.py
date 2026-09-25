"""Carter's dialogue portrait, Assets/Characters/Carter/portrait.png (64x64), derived from the approved
2026-09-23 polish (Assets/Characters/Carter/carter_polish.png, frame 0) rather than drawn beside it.

balloon.gd loads res://Assets/Characters/Carter/portrait.png into the dialogue box, and the VS card's
placeholder bust (Scripts/VsCardArtLayout.gd PLACEHOLDER_BUST_SCALE 1.5) stands the same file on its
bottom centre. So: bust framing, head and shoulders, the shoulders running off the bottom edge, as in
Josh's portrait of the same day (art_source/josh_redesign/portrait.py), whose method this follows.

THE METHOD
  1. His own pixels: frame 0 of the SHIPPED carter_polish.png, read back to the polish palette keys,
     cropped at x 27..69, y 19..61 (43 x 43). x 27 puts the head's own centre (47.5) on the between
     pixel of a stretched pair, so the scaled head is mirror-exact about column 31; y 19 (odd) puts the
     two slit rows (39, 40) on one stretched pair, so each two-row slit becomes three rows - not four.
  2. Scaled by 1.5 with xlib.resample15 (Josh's scheme: every source pixel lands on one output pixel,
     each pair gets one between pixel that copies a neighbour, never a blend, keylines stay one wide).
  3. The aura is redrawn, not resampled: the approved IDLE tongues (aura.IDLE) through aura.tendril
     at 1.5x, ringed by the same rule (dark-violet edge, hot red near him, violet toward the tips), so
     the tongues keep clean edges instead of the resample's stair steps.
  4. A one-pixel rim-light pass: a lit edge where a shape meets its keyline above, a dark edge where it
     meets one below, one ramp step each (not on the eyes, the aura or the earring).
  5. Hand detail the 96px sprite had no room for, all in lib.PAL. Listed where it is drawn below.

    python portrait.py            # build into the scratchpad and measure
    python portrait.py --ship     # ...then write Assets/Characters/Carter/portrait.png + .aseprite
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlib                                                      # noqa: E402  (sets the paths)
import lib                                                       # noqa: E402
import aura as AU                                                # noqa: E402
from lib import grow, erode, patch, DARKER, LIGHTER, RAMP        # noqa: E402
from PIL import Image                                            # noqa: E402

W = H = 64
SX0, SY0, N = 27, 19, 43
AURA = set('xXyYzZPQRSTU')
RAMP_OF = {k: r for r in RAMP.values() for k in r}


def base():
    src = xlib.keys_of(xlib.POLISH_PNG, (0, 0, 96, 96))
    return xlib.resample15(src, SX0, SY0, N)


# ------------------------------------------------------------------ the aura, redrawn at 1.5x

def out_pt(p):
    return xlib.to_out(p, SX0, SY0)


def flames(body):
    """aura.IDLE's tongues at 1.5x, in aura.IDLE_ORDER, ringed like aura.flames: a one-pixel dark
    violet edge, then the hot ramp near him and the violet one toward the tips - the ring depths
    scaled by 1.5 so the tongue is the same mix of tones as on the sprite, not hotter."""
    near = grow(body, 12)
    part = {}
    for i in AU.IDLE_ORDER:
        ctrl, w0, w1 = AU.IDLE[i]
        whole = AU.tendril([out_pt(c) for c in ctrl], w0 * 1.5, w1 * 1.5) - body
        depth = {}
        ring = set(whole)
        d = 0
        while ring:
            inner = erode(ring, 1)
            for q in ring - inner:
                depth[q] = d
            ring = inner
            d += 1
        for q, d in depth.items():
            # aura.flames at 1x: hot U z z Y y, cool U T S R R by ring. Ring d here is 1x ring
            # 1 + (d - 1) / 1.5 (the edge stays one pixel): hot z 1-3, Y 4-5, y 6+;
            # cool T 1-2, S 3, R 4+.
            if d == 0:
                k = 'U'
            elif q in near:
                k = 'z' if d <= 3 else ('Y' if d <= 5 else 'y')
            else:
                k = 'T' if d <= 2 else ('S' if d == 3 else 'R')
            part[q] = k
    return {q: k for q, k in part.items() if 0 <= q[0] < W and 0 <= q[1] < H}


# ------------------------------------------------------------------ rim light

def rim_pass(px, keep):
    todo = {}
    for (x, y), k in px.items():
        if k not in RAMP_OF or (x, y) in keep or k in AURA:
            continue
        ramp = RAMP_OF[k]
        i = ramp.index(k)
        up, dn = px.get((x, y - 1)), px.get((x, y + 1))
        up_k = up in ('k', None)
        dn_k = dn in ('k', None)
        if up_k and not dn_k:
            todo[(x, y)] = ramp[min(i + 1, len(ramp) - 1)]
        elif dn_k and not up_k:
            todo[(x, y)] = ramp[max(i - 1, 0)]
    px.update(todo)


def boxes(*bs):
    out = set()
    for x0, y0, x1, y1 in bs:
        out |= {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}
    return out


# ------------------------------------------------------------------ hand detail

def mirror_x(x):
    """The scaled head is mirror-exact about output column 31 (see THE METHOD)."""
    return 62 - x


# The slits, each symmetric about its own centre (the resample's between pixels had made both read
# '77VOOOVV7'). The approved slit is a hot top row over a red one; at three rows the middle becomes
# the hottest line with one white-hot pixel at its heart, and the bottom row keeps the approved red.
SLIT = {30: "7VVOOOVV7", 31: "7VOOMOOV7", 32: "987777789"}
SLIT_X = (18, 36)


def eyes(px):
    for y, row in SLIT.items():
        for x0 in SLIT_X:
            for i, k in enumerate(row):
                px[(x0 + i, y)] = k


# Brow hair: lit strands along the top of each brow, growing out from the nose; the right brow is
# in shadow, so its strands are one step darker. The frown: a crease each side of the lit bridge.
BROW_STRANDS = [
    ([(27, 27), (24, 26), (21, 25)], '4', '5'),   # left brow (screen left): '5' body -> '4' strand
    ([(22, 26), (19, 25), (18, 24)], '3', '4'),
    ([(26, 28), (23, 27)], '4', '5'),
]


def brows(px):
    for pts, key, over in BROW_STRANDS:
        for q in lib.polyline(pts):
            if px.get(q) in over:
                px[q] = key
        # the same strand on the right brow, a step darker (it is on the shadow side)
        for (x, y) in lib.polyline(pts):
            q = (mirror_x(x), y)
            if px.get(q) in ('5', '6') and key in '34':
                px[q] = DARKER[key]
    # the underside of each brow sits in its own shadow
    for x in range(21, 29):
        for y in range(26, 29):
            if px.get((x, y)) == '5' and px.get((x, y + 1)) in ('k', 'v', 'u'):
                px[(x, y)] = '6'
    for (x, y) in [(29, 26), (29, 27), (29, 28)]:
        if px.get((x, y)) == 'u':
            px[(x, y)] = 'v'


NOSE = [
    (34, 28, "v"),          # the left nostril wing
    (34, 34, "w"),          # the right one, in shadow
    (35, 30, "www"),        # under the tip, between the nostrils
]

# The ears: the helix lit along its top, the fold inside it, the shadowed bowl.
EARS = [
    (25, 9, "tu"), (26, 9, "tuv"), (30, 9, "uw"), (31, 9, "uv"), (32, 9, "uv"),
]


def ears(px):
    patch(px, EARS)
    # the right ear is the left one's mirror, a step darker all through (shadow side)
    for y, x0, keys in EARS:
        for i, k in enumerate(keys):
            q = (mirror_x(x0 + i), y)
            if px.get(q) not in (None, 'k'):
                px[q] = DARKER[k]


def earring(px):
    """The Latin cross at portrait size: a lit left column, a shadowed right one, its foot darkest."""
    for (x, y) in [(10, 40), (10, 41), (10, 42), (10, 43)]:
        if px.get((x, y)) in ('#', '%'):
            px[(x, y)] = '&'
    px[(10, 44)] = '*'
    px[(9, 44)] = '&'


def moustache(px):
    """The approved moustache is its own lobe; its underside was shadow ('5') either side of the
    mouth line at 1x. Close up it gets its full keyline, and the shadow moves up inside it."""
    for x in list(range(22, 27)) + list(range(36, 41)):
        px[(x, 41)] = 'k'
    for x in range(22, 27):
        if px.get((x, 40)) in ('3', '4'):
            px[(x, 40)] = '4' if x < 24 else '5'
    for x in range(36, 41):
        if px.get((x, 40)) in ('3', '4'):
            px[(x, 40)] = '5'
    # either side of the mouth the lobe overhangs the lower beard: its contact line beneath it (the
    # mouth itself keeps one line over the lip - two read as a grimace)
    for x in list(range(22, 27)) + list(range(36, 41)):
        if px.get((x, 42)) in HAIR:
            px[(x, 42)] = 'k'


# Clumps in the beard, following the hair's fall toward the chin: a dark parting and a lit strand
# on its upper left. Short, irregular strokes - long parallel ones read as a grille.
BEARD_PARTS = [
    [(15, 37), (16, 40), (18, 43)],            # left sideburn into the jaw
    [(19, 42), (21, 45)],
    [(25, 43), (26, 46)],                      # chin, left of centre
    [(36, 43), (35, 46)],                      # chin, right of centre
    [(41, 42), (40, 45)],
    [(47, 37), (46, 40), (44, 43)],            # right sideburn into the jaw
]
BEARD_LIT = [
    [(14, 37), (15, 40), (17, 43)],
    [(24, 43), (25, 45)],
    [(18, 42), (20, 45)],
]
HAIR = set('123456')


def beard(px):
    for pts in BEARD_PARTS:
        for q in lib.polyline(pts):
            if px.get(q) in HAIR:
                px[q] = '5' if px[q] in '1234' else '6'
    for pts in BEARD_LIT:
        for q in lib.polyline(pts):
            if px.get(q) in HAIR:
                px[q] = LIGHTER[px[q]]
    # the tips of the chin clumps: a notch of black between them on the beard's lower edge
    for x in (28, 34):
        if px.get((x, 47)) in HAIR:
            px[(x, 47)] = 'k'


def contact_shadows(px):
    """Black where one form sits tight on another, as the approved lower body does under its rope
    belt ('its shadow is a second line right under it'): the beard on his chest and neck."""
    for x in range(24, 39):
        if px.get((x, 49)) in ('W', 'w'):
            px[(x, 49)] = 'k'


def occlusion_weight(px, front, behind, rows=None):
    """Where a `front` form's outline runs along its lower or right edge over a `behind` form, the
    behind form's pixel just past the line goes black: the contact shadow, one pixel, on the side
    away from the light. The beads on the chest, the beard over the collar."""
    todo = set()
    for (x, y), k in px.items():
        if k != 'k' or (rows and y not in rows):
            continue
        for dx, dy in ((1, 0), (0, 1)):
            f = px.get((x - dx, y - dy))
            b = (x + dx, y + dy)
            if f in front and px.get(b) in behind:
                todo.add(b)
    for q in todo:
        px[q] = 'k'
    return len(todo)


def brow_press(px):
    """The inner half of each brow bears down on its lid: the lash line takes a second row under
    the brow's inner end (the glare), the brow's own dark underside above it."""
    for x in range(21, 28):
        if px.get((x, 28)) in ('5', '6'):
            px[(x, 28)] = 'k'
        q = (mirror_x(x), 28)
        if px.get(q) in ('5', '6'):
            px[q] = 'k'


# Folds in the gi, from the collar out over each shoulder: a crease of black with the cloth lit on
# its upper side; the right shoulder is in shadow, so its lit edge is a step darker.
GI_FOLDS_L = [
    [(1, 52), (4, 50), (7, 49)],
    [(0, 58), (4, 55), (8, 53)],
]
# the shadowed shoulder: one longer, flatter crease - not the lit side's mirror, which read stamped
GI_FOLDS_R = [
    [(63, 55), (59, 52), (55, 50)],
]
GI = set('abcdef')


def small_ink(px):
    """The last of the interior line, each where the approved rig puts line at 1x:
      * the left lapel stands over his chest: its contact line on the skin beside its keyline
        (the right lapel's edge to the chest is its lit side, so it stays one pixel);
      * the mouth's corners tuck in under the moustache;
      * the deepest point of each beard parting;
      * the cross throws its contact shadow on the collar under it;
      * each ear's bowl, where the fold turns in."""
    for y in range(50, 63):
        for x in range(12, 22):
            if px.get((x, y)) == 'k' and px.get((x - 1, y)) in GI and px.get((x + 1, y)) in set('stuvw'):
                px[(x + 1, y)] = 'k'
                break
    for q in [(28, 42), (35, 42)]:
        if px.get(q) in set('W56w'):
            px[q] = 'k'
    for q in [(16, 40), (20, 44), (46, 40), (42, 44)]:
        if px.get(q) in HAIR:
            px[q] = 'k'
    for q in [(11, 45), (12, 45)]:
        if px.get(q) in GI:
            px[q] = 'k'
    for (x, y) in [(10, 30), (10, 31)]:
        for q in ((x, y), (mirror_x(x), y)):
            if px.get(q) in set('uvwW'):
                px[q] = 'W' if q[1] == 30 else 'w'
    # the left ear stands off his head: its shadow side is the junction, so the head takes the
    # contact line there (the right ear's junction is its lit side and stays one pixel)
    for y in range(29, 35):
        if px.get((12, y)) == 'k' and px.get((13, y)) in set('stuvw3'):
            px[(13, y)] = 'k'


def gi_folds(px):
    for folds, lit in ((GI_FOLDS_L, 'a'), (GI_FOLDS_R, 'b')):
        for pts in folds:
            for (x, y) in lib.polyline(pts):
                if px.get((x, y)) in GI:
                    px[(x, y)] = 'k'
                    if px.get((x, y - 1)) in GI:
                        px[(x, y - 1)] = lit
                    if px.get((x, y + 1)) in GI:
                        px[(x, y + 1)] = DARKER[px[(x, y + 1)]]


FORMS = {
    'skin': set('stuvwW'),
    'hair': set('123456'),
    'gi': set('abcdef'),
    'bead': set('GHIJL'),
    'steel': set('#%&*'),
}
FORM_OF = {k: f for f, ks in FORMS.items() for k in ks}


def weight_shadow(px, exclude=(), min_thick=3):
    """The 1.5x line weight on the SILHOUETTE: where the outline runs along the lower or right edge
    of a form (the side away from the upper-left light) with air or aura beyond it, it takes a second
    pixel from the form - one pixel inside - wherever the form is at least min_thick deep behind that
    edge, so thin features keep their shape. Lit edges and interior lines stay one pixel; interior
    ink is placed by hand (contact_shadows, folds). `exclude`: pixels never thickened."""
    todo = set()
    for (x, y), k in px.items():
        if k != 'k':
            continue
        for dx, dy in ((-1, 0), (0, -1)):           # the form lies up or left of this line
            p = (x + dx, y + dy)
            f = FORM_OF.get(px.get(p))
            if f is None or p in exclude or px.get(p) == 'L':
                continue
            beyond = px.get((x - dx, y - dy))        # the other side: open air or the aura
            if beyond is not None and beyond not in AURA:
                continue
            deep = all(FORM_OF.get(px.get((x + dx * d, y + dy * d))) == f for d in range(1, min_thick + 1))
            if deep:
                todo.add(p)
    for q in todo:
        px[q] = 'k'
    return len(todo)


def weight_right(px, xmin, rows, keys):
    """A second pixel of keyline on the shadow side (the right) of a form: the form's own pixel
    just inside a keyline that has air (or aura) to its right."""
    out = []
    for y in rows:
        for x in range(xmin, W - 1):
            if px.get((x, y)) in keys and px.get((x + 1, y)) == 'k' and \
                    (px.get((x + 2, y)) is None or px.get((x + 2, y)) in AURA):
                out.append((x, y))
    for q in out:
        px[q] = 'k'


# ------------------------------------------------------------------ beads, redrawn round

# The approved 4x4 bead in its 1px keyline is nearly half ink at 1x; at 1.5x the same bead keeps
# that weight by carrying its keyline two pixels deep round the lower right (the side away from the
# light), with the shadow core (J, L) still showing inside it.
BEAD9 = [
    "..kkkkk..",
    ".kGGGHHk.",
    "kGGGHHHIk",
    "kGGHHHIIk",
    "kGHHHIIkk",
    "kHHHIIJkk",
    "kHHIIJLkk",
    ".kIJkkkk.",
    "..kkkkk..",
]


def beads(px):
    """The juzu at 1.5x from chest.bead_centres, each bead a round 9x9 (the approved 6x6 bead at
    1.5x) lit on its upper left, stamped ends-to-middle as chest.beads does."""
    import chest as CH
    cs = [out_pt(c) for c in CH.bead_centres()]
    old = {q for q, k in px.items() if k in 'GHIJL'}
    order = sorted(range(len(cs)), key=lambda i: cs[i][1])
    new = {}
    for i in order:
        cx, cy = cs[i]
        x0, y0 = int(round(cx - 4.0)), int(round(cy - 4.0))
        for r, row in enumerate(BEAD9):
            for c, k in enumerate(row):
                if k != '.':
                    new[(x0 + c, y0 + r)] = k
    covered = set(new)
    for q in old - covered:
        px[q] = 'u'
    for q, k in new.items():
        if 0 <= q[0] < W and 0 <= q[1] < H:
            px[q] = k


def build(stage=99):
    px = base()
    for q in [q for q, k in px.items() if k in AURA]:
        del px[q]
    body = set(px)
    if stage >= 1:
        keep = boxes((16, 28, 46, 34),       # eyes and lids keep their own values
                     (6, 35, 13, 45))        # the earring
        rim_pass(px, keep)
    if stage >= 2:
        eyes(px)
        brows(px)
        patch(px, NOSE)
        ears(px)
        earring(px)
        moustache(px)
        beard(px)
        beads(px)
    if stage >= 3:
        contact_shadows(px)
        weight_shadow(px, exclude=boxes((16, 28, 46, 34), (6, 35, 13, 45)))
    if stage >= 4:
        occlusion_weight(px, set('GHIJL'), set('stuvwWabcdef'))     # the beads on chest and gi
        occlusion_weight(px, set('123456'), set('stuvwWabcdef'), rows=range(42, 50))   # beard on collar
        brow_press(px)
        gi_folds(px)
        small_ink(px)
    fl = flames(body)
    for q, k in fl.items():
        px.setdefault(q, k)
    return px


def image(px):
    return xlib.image(px, W, H)


def measure(im):
    sprite = Image.open(xlib.POLISH_PNG).convert('RGBA')
    src = sprite.crop((SX0, SY0, SX0 + N, SY0 + N))
    for label, m in (('portrait.png', xlib.measure(im)),
                     ('carter_polish.png (2 frames)', xlib.measure(sprite)),
                     ('  frame 0', xlib.measure(sprite.crop((0, 0, 96, 96)))),
                     ('  frame 0, the same crop at 1x', xlib.measure(src))):
        print('%-32s %s' % (label, xlib.fmt(m)))
    extra = {c[:3] for c in lib.flat(im) if c[3]} - {v[:3] for v in lib.PAL.values()}
    print('colours outside lib.PAL:', sorted(extra) or 'none')


def main():
    im = image(build())
    measure(im)
    out = os.path.join(xlib.SCRATCH, 'work')
    os.makedirs(out, exist_ok=True)
    im.save(os.path.join(out, 'portrait_build.png'))
    xlib.upscale(xlib.on_bg(im), 8).save(os.path.join(out, 'portrait_build_8x.png'))
    if '--ship' in sys.argv:
        for p in xlib.ship(im, xlib.CARTER, 'portrait'):
            print('shipped', p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
