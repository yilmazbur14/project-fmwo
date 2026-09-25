"""Josh's dialogue portrait, Assets/Characters/Josh/portrait.png (64x64), derived from the approved
2026-09-23 redesign rather than drawn beside it.

balloon.gd shows it at 128x128 in the dialogue box; the VS card's placeholder bust
(Scripts/VsCardArtLayout.gd) draws the same file at 1.5x its 3x art scale, standing on its bottom
centre. So: bust framing, the shoulders running off the bottom edge, like every other portrait.

THE METHOD (what worked for the Eric and Computah busts, and why this one is 1.5x)
  1. His own pixels: frame 0 of josh_cards.png, rebuilt part by part from josh3.py in josh3's own
     order - minus the fan, the near hand and the near forearm, which would otherwise poke into
     the corner as a cut-off stub - and cropped at x20..62, y4..46.
  2. Scaled by 1.5. The head-and-shoulders span, from the crown's top to the ascot, is 43 source
     rows; a whole 2x fits only 32 of them in 64px (it cuts the beard and loses the collar, lapels
     and ascot), and 1x is no bigger than the sprite. At 1.5x the brim fills the frame edge to edge
     and the face is 33px wide, which is where the other portraits sit. The scale is done without
     inventing a pixel: every source pixel lands on exactly one output pixel, and each pair of them
     gets one 'between' pixel that copies one of its two neighbours - never a blend - chosen so a
     keyline stays one pixel wide and a diagonal keyline stays joined. His four-pixel eyes come out
     six pixels wide, one row tall, under their lid: the same eyes, not slabs.
     The tucked card is the one part redrawn from geometry, not pixels: its own four corners
     through josh3's own card_poly at 1.5x, because resampled tilted edges come out jagged.
  3. A one-pixel rim-light pass: a lit edge where a shape meets its keyline above, a dark edge
     where it meets one below, one ramp step each.
  4. Hand detail the 80px sprite had no room for, all in his own palette (lib.PAL): the spade
     rebuilt as a clean spade with a lit and a shadowed rim, its stem standing on the band; the band
     given its own keyline, so the card reads as tucked behind it, and a short glint; fold lines
     round both popped collars, and the shadow inside them where the sprite leaves pinholes; the
     hair swept back into locks and the fringe combed back; the boxed beard redrawn by hand in the
     sprite's own texture (flat i, lit j, dark h) as clumps with black only between their tips, and
     the shadow it throws on the neck; the face's contour where it meets the hair; each eye's outer
     corner, a nostril; the far lapel's shadow on the waistcoat.

THE NUMBERS
  The sprite is 28.3% pure black over 38 colours (frame 0 alone: 35). Straight 1.5x with one-pixel
  lines gives only ~20%, because a keyline is perimeter and a close-up is area; the detail pass
  brings it to ~26.5% over 35 colours, the way the house style does at a bigger size - interior
  line on overlapping forms, not thicker outlines. It stops there on purpose: the last points
  would have to come from doubled outlines or stripes, and the one attempt at that (parallel
  strokes through the beard) read as a grille and was taken out. measure() prints both numbers.

    python portrait.py            # build into ./out and measure
    python portrait.py --ship     # ...then write Assets/Characters/Josh/portrait.png + .aseprite
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import josh3                                                     # noqa: E402
import lib                                                       # noqa: E402
from lib import PAL                                              # noqa: E402
from PIL import Image                                            # noqa: E402

ASSET = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh', 'portrait'))
SPRITE = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh', 'josh_cards.png'))
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

W = H = 64
SX0, SY0 = 20, 4          # the window's top-left in frame 0: brim tip to brim tip, 2px over the crown
N = 43                    # source pixels across and down; 1.5x of 43 is 64

RAMPS = ['abcde', 'hijlm', 'wxyzZ', 'vVRT', 'gGoOY', '567890', 'nNsSt']
RAMP_OF = {k: r for r in RAMPS for k in r}
HAIR = set('hijlm')
SKIN = set('abcde')


# ---------------------------------------------------------------------------------------- 1x
def bust_1x(card=True):
    """Frame 0 in josh3's own build order, minus the fan, the near hand and the near forearm, and
    everything below the portrait's bottom edge."""
    cv = lib.Canvas()
    for c in josh3.collar():
        cv.stamp(c)
    cv.stamp(josh3.coat_back())
    for c in josh3.coat_panels():
        cv.stamp(c)
    cv.stamp(josh3.vest())
    lib.patch(cv.px, josh3.CHEST)
    for part, outline in josh3.far_arm():
        cv.stamp(part, outline=outline)
    cv.stamp(josh3.head())
    parts = josh3.hat()
    if not card:
        parts = [p for i, p in enumerate(parts) if i != 1]      # (crown, card, band, brim)
    for part, outline in parts:
        cv.stamp(part, outline=outline)
    upper, _forearm = josh3.near_arm()
    cv.stamp(upper)
    return cv.px


# ---------------------------------------------------------------------------------------- 1.5x
def omap(u):
    """Source offset -> output offset: pairs (2k, 2k+1) land on 3k and 3k+2, 3k+1 is between."""
    return 3 * (u // 2) + 2 * (u % 2)


def _pick(a, b, aa, bb):
    """The between pixel of a and b (aa, bb: the pixels beyond each). Never a blend."""
    if a == b:
        return a
    if a is None or b is None:
        o = b if a is None else a
        return None if o == 'k' else o          # a silhouette keyline stays one pixel wide
    if a == 'k':
        return b                                 # so does an interior one
    if b == 'k':
        return a
    a_thin, b_thin = aa != a, bb != b
    if a_thin and not b_thin:
        return b                                 # a one-pixel feature stays one pixel
    if b_thin and not a_thin:
        return a
    return a


def resample(px):
    def g(x, y):
        return px.get((SX0 + x, SY0 + y))

    def axis(o):
        q, r = divmod(o, 3)
        return [2 * q] if r == 0 else ([2 * q + 1] if r == 2 else [2 * q, 2 * q + 1])

    out = {}
    size = omap(N - 1) + 1
    for oy in range(size):
        ys = axis(oy)
        for ox in range(size):
            xs = axis(ox)
            if len(xs) == 1 and len(ys) == 1:
                v = g(xs[0], ys[0])
            elif len(ys) == 1:
                y = ys[0]
                v = _pick(g(xs[0], y), g(xs[1], y), g(xs[0] - 1, y), g(xs[1] + 1, y))
            elif len(xs) == 1:
                x = xs[0]
                v = _pick(g(x, ys[0]), g(x, ys[1]), g(x, ys[0] - 1), g(x, ys[1] + 1))
            else:
                tl, tr, bl, br = g(xs[0], ys[0]), g(xs[1], ys[0]), g(xs[0], ys[1]), g(xs[1], ys[1])
                if (tl == br == 'k' and 'k' not in (tr, bl)) or (tr == bl == 'k' and 'k' not in (tl, br)):
                    v = 'k'                      # a diagonal keyline stays joined
                else:
                    top = _pick(tl, tr, g(xs[0] - 1, ys[0]), g(xs[1] + 1, ys[0]))
                    bot = _pick(bl, br, g(xs[0] - 1, ys[1]), g(xs[1] + 1, ys[1]))
                    v = _pick(top, bot, top, bot)
            if v is not None:
                out[(ox, oy)] = v
    # two diagonal source keyline pixels whose images land two apart get the one bridge pixel
    for y in range(N):
        for x in range(N):
            if g(x, y) != 'k':
                continue
            for dx in (1, -1):
                qx, qy = x + dx, y + 1
                if not (0 <= qx < N and qy < N) or g(qx, qy) != 'k' or 'k' in (g(qx, y), g(x, qy)):
                    continue
                P, Q = (omap(x), omap(y)), (omap(qx), omap(qy))
                if abs(P[0] - Q[0]) <= 1 and abs(P[1] - Q[1]) <= 1:
                    continue
                cands = [(bx, by) for bx in range(min(P[0], Q[0]), max(P[0], Q[0]) + 1)
                         for by in range(min(P[1], Q[1]), max(P[1], Q[1]) + 1)
                         if (bx, by) not in (P, Q) and max(abs(bx - P[0]), abs(by - P[1])) <= 1
                         and max(abs(bx - Q[0]), abs(by - Q[1])) <= 1]
                if not any(out.get(c) == 'k' for c in cands):
                    out[cands[0]] = 'k'
    return out


def to_out(pt):
    """A source pixel-centre coordinate -> the output's, for geometry drawn at 1.5x."""
    return (1.5 * (pt[0] - SX0) + 0.25, 1.5 * (pt[1] - SY0) + 0.25)


def stamp(px, part, outline=True):
    if outline:
        body = set(part)
        for (x, y) in body:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and 0 <= q[0] < W and 0 <= q[1] < H:
                    px[q] = 'k'
    for q, k in part.items():
        if 0 <= q[0] < W and 0 <= q[1] < H:
            px[q] = k


def tucked_card():
    """The card from its own corners through josh3's card_poly, at 1.5x."""
    orig = josh3.poly
    josh3.poly = lambda pts: lib.poly([to_out(p) for p in pts])
    try:
        part = josh3.card_poly([(33, 16), (37, 14), (33, 6), (29, 8)], ['R'], face='0', border='9')
    finally:
        josh3.poly = orig
    for q in list(part):
        if part[q] == 'R':
            part[q] = '0'                        # its pip is redrawn at portrait size below
    return part


# ---------------------------------------------------------------------------------------- detail
def pline(px, pts, key, only):
    """Recolour along a polyline, only where the pixel is one of `only`."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for q in lib.line(x0, y0, x1, y1):
            if px.get(q) in only:
                px[q] = key


# The spade, rebuilt on column 36 from its 1x shape: 7 black wide inside a 1px gold rim, lit on
# the upper left (O), shadowed on the lower right (G), its stem standing on the band's keyline
# (row 14, drawn by band_keyline).
SPADE = [
    # x: 31-35 36-40 41
    (5, 31, "_____ O____ _"),
    (6, 31, "____O ko___ _"),
    (7, 31, "___Ok kkG__ _"),
    (8, 31, "__Okk kkkG_ _"),
    (9, 31, "_Okkk kkkkG _"),
    (10, 31, "_okkk kkkkG _"),
    (11, 31, "_okkk kkkkG _"),
    (12, 31, "__okk okkG_ _"),
    (13, 31, "___oo koG__ _"),
]
SPADE_BOX = (31, 5, 41, 14)

FACE = [
    # near eye: a six-pixel lid over a one-row eye (the sprite's four pixels at 1.5x), skin under
    (32, 26, "kkkkk k"),
    (33, 26, "0mlk0 0"),
    (34, 25, "dcccc cd"),
    # far eye: its white sits in the one row too
    (34, 40, "c"),
    # the tooth is one row, as at 1x
    (43, 37, "i"),
    # the near brow tapers to one row at its outer end
    (31, 24, "dd"),
    # a nostril where the 1x nose tip has its darkest pixel
    (40, 35, "k"),
    # each eye's almond closes at its outer corner, where the lid turns down
    (33, 25, "k"),
    (33, 42, "k"),
]

# The locks of the hair, swept back: separations run from the temple down and back, a lit strand
# beside each on the side the light comes from.
NEAR_LOCKS = [[(23, 25), (21, 28), (19, 31), (18, 34)], [(24, 29), (22, 32), (20, 35), (19, 38)],
              [(19, 25), (17, 29), (16, 32)]]
NEAR_SHINE = [[(22, 25), (20, 28), (18, 31)], [(23, 29), (21, 32), (19, 35)]]
# The fringe under the brim, combed back: a short parting every five pixels, lit beside it.
FRINGE = [((x, 26), 'k') for x in (28, 33, 38, 43)] + [((x - 1, 25), 'k') for x in (28, 33, 38, 43)] \
    + [((x + 1, 26), 'l') for x in (28, 33, 38, 43)] + [((x, 25), 'l') for x in (28, 33, 38, 43)]
FAR_LOCKS = [[(46, 27), (47, 31), (47, 36), (46, 40)], [(49, 26), (49, 30)]]
# The boxed beard by hand, in the sprite's own texture language (flat i, lit j on the near side,
# dark h at the edges): lit strands down the near cheek, the mustache lit at its near end, the lower
# lip's shadow, and four clumps across the chin - each lit on its upper left, black only in the
# gaps between their tips. '_' keeps what is there (the collar, the outlines).
BEARD = [
    # x: 17-21 22-26 27-31 32-36 37-41 42-45
    (41, 17, "_ijlj jiiic lljjj jjjjj jikcc iii_"),
    (42, 17, "_ijji jiiji iiikk kkkk0 00kii ihh_"),
    (43, 17, "_hhjj ijiij iiiih pppbh iiiii hhh_"),
    (44, 17, "___hh jhjii jiiih pppbi ijiii hhh_"),
    (45, 17, "_____ hjjih jjiih hhhhi ijiii hh__"),
    (46, 17, "_____ _iihk ijiih jjiih ijiih hh__"),
    (47, 17, "_____ __hhk iijik ijiik iihhh ____"),
    (48, 17, "_____ ___hh iiihk iiihk ihhh_ ____"),
    (49, 17, "_____ ___hh hihhh hihhh hah__ ____"),
]
# ...and it throws a shadow across the top of the neck
NECK_SHADOW = [(28, 50), (38, 50)]
# the shadow inside the popped collar, where the 1x sprite leaves pinholes between collar and neck
COLLAR_SHADOW = [(25, 51), (26, 51), (25, 52), (26, 52), (40, 50), (41, 50), (40, 51), (41, 51),
                 (40, 52), (41, 52), (42, 48), (43, 48), (42, 49), (43, 49)]


def card_detail(px):
    """1x: a '0' face in a '9' border with one red pip. Here the border's lower-right side is a step
    darker (8), as the crown beside it is, and the pip is 2x2 with its lit corner."""
    card = {q for q, k in px.items() if q[1] <= 14 and q[0] <= 27 and k in '0987'}
    for (x, y) in card:
        nb = {d: px.get((x + d[0], y + d[1])) for d in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        edge = [d for d, v in nb.items() if v == 'k' or v is None]
        if not edge:
            px[(x, y)] = '0'
        elif any(d in ((1, 0), (0, 1)) for d in edge):
            px[(x, y)] = '8'
        else:
            px[(x, y)] = '9'
    for q in ((18, 9), (19, 9), (18, 10), (19, 10)):
        px[q] = 'R'
    px[(18, 9)] = 'T'


def spade(px):
    x0, y0, x1, y1 = SPADE_BOX
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if px.get((x, y)) in ('k', 'o', 'O', 'G', 'g'):
                px[(x, y)] = 'y' if x <= 40 else 'x'   # the crown's own shading round the old spade
    lib.patch(px, SPADE)


def band_keyline(px):
    """The band is its own piece of cloth: a keyline along its top, over the crown and the card
    (which is why the card reads as tucked behind it), and its top row takes the light - the
    palest gold only in a short glint by the card, where the light is strongest."""
    for x in range(W):
        if px.get((x, 14)) is not None:
            px[(x, 14)] = 'k'
    for x in range(W):
        k = px.get((x, 15))
        if k == 'O' and x <= 23:
            px[(x, 15)] = 'Y'
        elif k == 'o':
            px[(x, 15)] = 'O'
        elif k == 'G':
            px[(x, 15)] = 'o'


def rim_pass(px, keep):
    """1px lit edge where a shape meets its keyline above, 1px dark edge where it meets one below,
    one ramp step each way. One-row pixels, and anything in `keep`, are left alone."""
    todo = {}
    for (x, y), k in px.items():
        if k not in RAMP_OF or (x, y) in keep:
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


def rim_keep(card):
    keep = set(card)             # the card gets its own border in card_detail
    boxes = [
        (24, 31, 44, 44),        # the eyes, the nose, the mouth and the tooth keep their own values
        SPADE_BOX,               # the spade has its own lit and shadowed rim
        (0, 15, 63, 15),         # the band's top row is lit by band_keyline
        (0, 24, 63, 26),         # the hair under the brim, as the sprite has it
    ]
    for x0, y0, x1, y1 in boxes:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                keep.add((x, y))
    return keep


def collar_folds(px):
    """A fold line between each popped collar's cream edge and its crimson face, carried round
    the collar's top as well as down its side."""
    # near collar: its cream edge back to one pixel (x13), the fold at x14 and under the top rim
    for y in range(42, 53):
        if px.get((14, y)) in ('9', '8', '0'):
            px[(14, y)] = 'k'
    for x in (15, 16):
        if px.get((x, 42)) in ('R', 'T'):
            px[(x, 42)] = 'k'
    # far collar: the fold between its crimson face and its one-pixel outer edge (x53), and under
    # its top rim
    for y in range(42, 53):
        if px.get((52, y)) in ('V', 'v') and px.get((53, y)) in ('8', '7'):
            px[(52, y)] = 'k'
    for x in range(48, 53):
        if px.get((x, 42)) in ('V', 'v'):
            px[(x, 42)] = 'k'


def collar_shade(px):
    """1x has the collars' crimson flat; close up they turn to their shadow tone at the foot."""
    for (x, y), k in list(px.items()):
        if 51 <= y <= 53 and k == 'R' and x <= 24:
            px[(x, y)] = 'V'
        if 51 <= y <= 53 and k == 'V' and 45 <= x <= 53:
            px[(x, y)] = 'v'


def lapel_shadow(px):
    """The far lapel stands off the waistcoat and shades the column beside it one indigo step down
    (S to s, s to N) - the darker tones the 1x waistcoat keeps for its hem."""
    step = {'t': 'S', 'S': 's', 's': 'N'}
    for y in range(55, 64):
        if px.get((36, y)) == 'k' and px.get((35, y)) in step:
            px[(35, y)] = step[px[(35, y)]]


def face_contour(px):
    """Where the face meets the hair, the house style's interior line."""
    for y in range(27, 40):
        xs = [x for x in range(20, 48) if px.get((x, y)) in SKIN]
        if not xs:
            continue
        for q in ((min(xs) - 1, y), (max(xs) + 1, y)):
            if px.get(q) in HAIR:
                px[q] = 'k'


# ---------------------------------------------------------------------------------------- build
def build():
    px = resample(bust_1x(card=False))
    base = dict(px)
    card = tucked_card()
    stamp(px, card)
    for (x, y), k in base.items():               # the band and the brim sit in front of the card
        if y >= 15:
            px[(x, y)] = k
    for q in [q for q in px if q[1] >= 15 and q not in base]:
        del px[q]
    spade(px)
    lib.patch(px, FACE)
    rim_pass(px, rim_keep(card))
    card_detail(px)
    band_keyline(px)
    for q in COLLAR_SHADOW:
        px.setdefault(q, 'k')
    collar_folds(px)
    collar_shade(px)
    for ln in NEAR_LOCKS + FAR_LOCKS:
        pline(px, ln, 'k', HAIR)
    for ln in NEAR_SHINE:
        pline(px, ln, 'm', HAIR)
    for q, k in FRINGE:
        if px.get(q) in HAIR:
            px[q] = k
    lib.patch(px, BEARD)
    pline(px, NECK_SHADOW, 'k', SKIN)
    face_contour(px)
    lapel_shadow(px)
    return px


def image(px):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < W and 0 <= y < H:
            im.putpixel((x, y), PAL[k])
    return im


def measure(im):
    sprite = Image.open(SPRITE).convert('RGBA')
    s, p = lib.stats(sprite), lib.stats(im)
    print('portrait.png   %4d px  black %4.1f%%  colours %d' % (p['opaque'], 100 * p['black'], p['colours']))
    print('josh_cards.png %4d px  black %4.1f%%  colours %d' % (s['opaque'], 100 * s['black'], s['colours']))
    extra = {c[:3] for c in im.getdata() if c[3]} - {tuple(v[:3]) for v in PAL.values()}
    print('colours outside lib.PAL:', sorted(extra) or 'none')
    return p


def main(ship=False):
    """Build both files in ./out, prove the .aseprite re-exports to exactly the PNG's pixels, and
    only then (--ship) copy each into Assets in one write, and check what landed."""
    from imgdiff import pixel_diff
    im = build_image()
    out = os.path.join(HERE, 'out')
    os.makedirs(out, exist_ok=True)
    png, ase = os.path.join(out, 'portrait.png'), os.path.join(out, 'portrait.aseprite')
    im.save(png)
    measure(im)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    print('aseprite round trip:', d or 'identical')
    if d or not ship:
        return 1 if d else 0
    for src, dst in ((png, ASSET + '.png'), (ase, ASSET + '.aseprite')):
        shutil.copyfile(src, dst)
        with open(src, 'rb') as a, open(dst, 'rb') as b:
            assert a.read() == b.read(), dst
        print('shipped', dst)
    return 0


def build_image():
    return image(build())


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
