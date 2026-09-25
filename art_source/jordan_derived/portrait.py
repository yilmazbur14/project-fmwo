"""Jordan's dialogue portrait, Assets/Characters/Jordan/portrait.png (64x64), derived from the approved
2026-09-23 redesign (Assets/Characters/Jordan/jordan_redesign.png) rather than drawn beside it.

balloon.gd shows it at 128x128 in the dialogue box; the VS card's placeholder bust
(Scripts/VsCardArtLayout.gd) draws the same file at 1.5x its 3x art scale, standing on its bottom
centre. So: bust framing, the shoulders running off the bottom edge, like every other portrait.

THE METHOD (Josh's portrait, art_source/josh_redesign/portrait.py, did exactly this today)
  1. His own pixels: frame 0 rebuilt from the rig in the rig's own order (art_source/jordan_redesign,
     imported, never edited) minus the collector box, the hand holding it and that raised forearm,
     which would otherwise poke up beside his shoulder as a cut-off stub. Cropped at x27..69, y8..50:
     43 source pixels, centred on his anchor column x48, one row over the tip of the quiff.
  2. Scaled by 1.5 (dkit.resample, Josh's scaling): every source pixel lands on exactly one output
     pixel and each pair gets one 'between' pixel copying a neighbour, never a blend. The head is 22
     source pixels wide, 33 at 1.5x, which is where the other portraits sit; the frame runs from the
     quiff's tip to the top of the princess print, the collar and her crown included.
  3. A one-pixel rim-light pass: a lit edge where a shape meets its keyline above, a dark edge where
     it meets one below, one ramp step each.
  4. Hand detail the 96px sprite had no room for, all in his own palette (kit.PAL): the greasy quiff
     parted into locks up from the hairline and over the crest, a lit strand beside each and the
     sheen kept; its underside as a black line over a cast-shadow band on the forehead, broken by
     three lock tips and the loose strand that falls across it; the short sides combed back; heavy
     straight brows with a lit top edge and a black underside; half-lidded eyes looking screen-right,
     the irises in the lid's shadow; the tired bags under both; a nostril; the ear as its own shape;
     the thin moustache parted at the philtrum and bare at both corners; the lower lip lit on its
     upper left over a shadow; the patchy beard's chin as three clumps with black only in the notches
     between their tips; the collar's black trim as one clean band, lit along its inside edge,
     sagging right of centre; the drip stain; the sleeve's creases, both armpits, the drape the
     stretched collar pulls; the crown's jewel lit and the princess's hair stranded.

THE NUMBERS. The sheet is 27.6% pure black over 40 colours (frame 0 alone 27.1%, 40). The portrait
  is 23.6% over 27. Like for like: the same crop of frame 0 (x27..69, y8..50, box and hand out) is
  23.8% over 23 - the sheet's 40 colours and its extra black come from what a bust leaves out: the
  jeans, the sneakers and the collector box, which alone is 43.9% black. Region by region the
  portrait is the denser: its head 22.0% black against the sprite head's 19.2%. Straight 1.5x gives
  17.2% (a keyline is perimeter, a close-up is area); the detail pass brings it up the house-style
  way, with interior line on overlapping forms. It stops there on purpose: the rest would have to
  come from doubled outlines or from turning his darkest hair tone to black, which only moves the
  number. measure() prints both on every build.

    python portrait.py            # build into the scratchpad, measure, round-trip the .aseprite
    python portrait.py --ship     # ...then write Assets/Characters/Jordan/portrait.png + .aseprite
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True        # importing the rig must leave no __pycache__ in its folder
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dkit                                                      # noqa: E402
import jordan                                                    # noqa: E402  (the rig)
import torso                                                     # noqa: E402
import head as headmod                                           # noqa: E402
from kit import Canvas, capsule, line                            # noqa: E402
from PIL import Image                                            # noqa: E402

ASSET = os.path.join(dkit.ASSETS, 'Characters', 'Jordan', 'portrait')
W = H = 64
SX0, SY0 = 27, 8          # the window's top-left in frame 0
N = 43                    # source pixels across and down; 1.5x of 43 is 64

RAMPS = ['abcde', 'hijlm', 'vVRTU', 'qPQ', 'gGoOY', '123']
RAMP_OF = {k: r for r in RAMPS for k in r}
HAIR = set('hijlmA')
SKIN = set('abcde')
RED = set('vVRTU')


# ---------------------------------------------------------------------------------------- 1x
def far_arm_no_forearm():
    """The rig's far arm with the box in its hand, minus the forearm: only the upper arm's capsule
    is kept, so what is left runs down behind the sleeve and off the frame."""
    (limb, _), (sleeve, _) = jordan.far_arm_box()
    upper = capsule((59.5, 46), (63, 55), 2.6, 2.3)
    return [({q: k for q, k in limb.items() if q in upper}, True), (sleeve, True)]


def bust_1x():
    """Frame 0 in the rig's own build order (jordan.build), minus the legs and shoes (below the
    frame), the box, the hand on it and the raised forearm. Same slouch, same anchor shift."""
    cv = Canvas(96, 96)
    for part, outline in far_arm_no_forearm():
        cv.stamp(part, outline=outline)
    cv.stamp(jordan.neck())
    cv.stamp(torso.shirt())
    hd = {(x + 1, y + 1): k for (x, y), k in headmod.head(shout=False).items()}
    cv.stamp(hd, outline=False)
    for part, outline in jordan.near_arm_hip():
        cv.stamp(part, outline=outline)
    return {(x + jordan.ANCHOR_SHIFT, y): k for (x, y), k in cv.px.items()}


# ---------------------------------------------------------------------------------------- passes
def pline(px, pts, key, only):
    """Recolour along a polyline, only where the pixel is one of `only`."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for q in line(x0, y0, x1, y1):
            if px.get(q) in only:
                px[q] = key


def box(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def rim_pass(px, keep):
    """1px lit edge where a shape meets its keyline above, 1px dark edge where it meets one below,
    one ramp step each way. Anything in `keep` is left alone."""
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


def rim_keep():
    keep = set()
    for b in (
        (24, 18, 48, 45),        # the face keeps the sprite's own values: eyes, nose, mouth, beard
        (14, 25, 23, 36),        # the ear
        (24, 45, 44, 51),        # the neck sits in the jaw's shadow, not a lit rim
        (23, 54, 45, 63),        # the princess print is a flat graphic
    ):
        keep |= box(*b)
    return keep


# ---------------------------------------------------------------------------------------- the face
# Rows 17..45 of the head by hand, over the resampled pixels. The sprite's own features, drawn at
# the close-up's size: the quiff's underside as a black line over a cast-shadow band on the
# forehead, with three lock tips and the loose greasy strand breaking it; heavy straight brows with
# a lit top edge and a crisp black underside; half-lidded eyes looking screen-right (irises in the
# lid's shadow on top, brown below, the near eye's outer corner closed); tired bags under both; the
# nostril; the lower lip lit on its upper left; the patchy beard's clumps notched apart at the chin.
FACE = [
    # x: 14-18 19-23 24-28 29-33 34-38 39-43 44-48 49
    (17, 14, "....k jjiij iiikk kkikk kkkik kikkk kkkk. ."),
    (18, 14, "...kj iijji jikcc ccccc ccccc cciic bbbk. ."),
    (19, 14, "...ki iijji hjdee eeeee eeddd ddddi cbbk. ."),
    (20, 14, "...ki iiiij hhdee eeeee eeddd ddddi bbbk. ."),
    (21, 14, "...ki jjjji hhdee eeeee eeddd ddddd cbbk. ."),
    (22, 14, "...ki jjjji hhdde eeeee eeeed ddddd cbbk. ."),
    (23, 14, "...ki jjjji djiji ijiii iddee jijii iiik. ."),
    (24, 14, "...ki ijiih chhhh hhhhh hhdde chhhh hhhk. ."),
    (25, 14, "...ki ijiii cckkk kkkkk khdde chkkk kchk. ."),
    (26, 14, "..kkd dciii ccccc bbbbb bbdde ddcbb bcck. ."),
    (27, 14, ".kddb bciii cckkk kkkkk dddde cckkk kcck. ."),
    (28, 14, ".kddb bciii cckWW WhhhW dddde ccWhh hkck. ."),
    (29, 14, ".kdda aciij ccccW Wlhlc dddde ccWlh lcck. ."),
    (30, 14, ".kddb bciij ccdbb bbbbd dddde bcbbb bcck. ."),
    (31, 14, ".kddb bciij ccdcd ddccd dddde bcddc ccck. ."),
    (32, 14, ".kkcc cbjjc lldcc ccddd dddde eebcc dcck. ."),
    (33, 14, "...kb bbjjl ccjee edddd dcbbd aabcc jcck. ."),
    (34, 14, "...kb bbjjl ccjdd cdddd dcbbd kabcc jcck. ."),
    # the thin moustache, lit toward its near end and parted at the philtrum, bare at both corners
    (35, 14, "....k kijjl ccdjj cddjl ljihi lljih cjjk. ."),
    (36, 14, "..... .kijj jjcll jddbk kkkkk kkkbb jiik. ."),
    # the lower lip lit on its upper left, its corners and underside a step darker
    (37, 14, "..... .kijj jjjll jddbp ddppp ppibb ciik. ."),
    (38, 14, "..... .khhi cjjjj cjjia ppppp paijj ciik. ."),
    # the lip's shadow on the chin, then three clumps of the fuller chin beard, each lit on its upper
    # left and darkest at its tip, with black only in the V notches between the tips
    (39, 14, "..... ..khh iijcc jiiji hkkhh hjjii ciik. ."),
    (40, 14, "..... ...kh iijcc jljij lljih lljih cik.. ."),
    (41, 14, "..... ....k hhijj lljhj ljjih jljih hk... ."),
    (42, 14, "..... ..... khhij jjihi jjiih ijiih hk... ."),
    (43, 14, "..... ..... .khhi iihkh iiihk hiihh k.... ."),
    (44, 14, "..... ..... ..khh ihhkk hihhk khihk k.... ."),
]

# The ear as its own shape: a keyline over its top where the hair meets it and down its front edge,
# the helix lit, the bowl shaded to its deepest pixel, the lobe lit.
EAR = [
    # x: 14-18 19-23
    (25, 14, "...kk k____"),
    (27, 14, ".kedd bk___"),
    (28, 14, ".kdcb bk___"),
    (29, 14, ".kdck ak___"),
    (30, 14, ".kdcb ak___"),
    (31, 14, ".kddc bk___"),
    (32, 14, ".kkdc bb___"),
    (33, 14, "...kc bb___"),
]

# The collar's black trim as one clean band, two pixels on each side of the U (the rolled rib lit
# along its inside edge, charcoal outside), sagging lowest right of centre as in the sprite; and the
# drip stain just off it, darker at its core.
COLLAR = [
    # x: 19-23 24-28 29-33 34-38 39-43 44
    (48, 19, "___UT 12kdc ccccc ccccb k11kk k"),
    (49, 19, "___RT 12kdc ccccc cccck 11VVV k"),
    (50, 19, "____V R12kk kcccc ccckk 11VVV v"),
    (51, 19, "_____ RR112 2kkkc cck11 RVVVV V"),
    (52, 19, "_____ RRRR1 132kb bk11R RVVVV V"),
    (53, 19, "_____ RRRRR R112k kk11R babVV V"),
    (54, 19, "_____ RRRRR RRR12 211RR RbaVV V"),
    (55, 19, "_____ RRRRR RYR11 11oRR RRbVV V"),
]

# The shirt's folds, which the 96px sprite had no room for: a crease where the near sleeve bunches
# at the armpit, both armpits closed to black where sleeve meets body, the drape the stretched collar
# drags down on either side of the print, and the far side's fold toward his hip.
FOLDS_K = [
    [(22, 55), (21, 56), (20, 57)],                  # near sleeve crease, deepest at the armpit
    [(21, 60), (19, 61)],                            # a second, lower one where the sleeve bunches
    [(22, 59), (22, 61)],                            # near armpit
    [(49, 57), (49, 58)],                            # far armpit, down to where the sleeve steps in
    [(27, 54), (26, 56)],                            # drape left of the print
    [(44, 52), (45, 53)],                            # drape right of the collar, toward his hip
    [(52, 60), (51, 62)],                            # the far sleeve folding under its hem
]
FOLDS_SHADE = [
    ([(19, 58), (17, 59), (16, 59)], 'V', 'R'),      # the near crease's tail
    ([(21, 55), (20, 56), (19, 57)], 'T', 'R'),      # lit lip above it
    ([(18, 61), (15, 62)], 'V', 'R'),                # the lower crease's tail
    ([(20, 59), (18, 60)], 'T', 'R'),                # lit lip above it
    ([(25, 57), (25, 58)], 'V', 'R'),                # the left drape's tail
    ([(43, 51), (46, 54), (46, 56)], 'v', 'V'),      # far side, toward his hip
    ([(44, 50), (46, 52)], 'R', 'V'),                # lit lip above it
]

# The side hair, combed back and down, gets partings of its own; the sideburn's front edge is a
# contour where it meets the temple, running into the brow's tail.
SIDE_PARTINGS = [
    [(25, 13), (23, 15), (21, 17)],
    [(24, 20), (22, 22), (21, 24)],
]
SIDEBURN_EDGE = [(25, 19), (25, 22)]

# The print: its crown's jewel lit on the upper left and shadowed lower right, and the far edge of
# her hair and crown turning into the gold ramp's shadow, as the sprite's print does lower down.
PRINT = [
    # x: 33 34
    (57, 33, "T_"),
    (58, 33, "_V"),
]
PRINT_SHADE = [((38, 57), 'G'), ((40, 58), 'G'), ((41, 59), 'o'), ((43, 60), 'G'), ((43, 61), 'G'),
               ((43, 62), 'G'), ((43, 63), 'G'),
               # strands through her hair under the crown, falling toward the fringe line
               ((27, 60), 'o'), ((28, 61), 'o'), ((31, 60), 'o'), ((31, 61), 'o'), ((35, 60), 'o'),
               ((36, 61), 'o'), ((25, 60), 'Y'), ((25, 61), 'Y')]

# Two short partings in the crest, where the locks converge on the front tuft.
CREST_PARTINGS = [
    [(32, 9), (34, 7)],
    [(39, 9), (40, 7)],
]

# The locks of the quiff: a black parting between each pair, running up from the hairline and back
# over the crest the way the sprite's own dark partings do, and a lit strand on the far side of each
# (the next lock's edge toward the light).
LOCK_PARTINGS = [
    [(26, 16), (27, 14), (28, 12), (30, 10)],
    [(33, 16), (33, 14), (32, 12)],
    [(36, 16), (35, 14), (34, 12), (35, 10), (37, 8)],
    [(41, 16), (40, 14), (39, 12), (40, 10), (41, 8)],
    [(45, 15), (44, 13), (43, 11), (44, 9)],
]
LOCK_SHINE = [
    [(28, 15), (29, 13), (31, 11)],
    [(34, 15), (34, 13)],
    [(37, 15), (36, 13), (36, 11)],
    [(42, 15), (41, 13), (41, 11)],
]


def build():
    px = dkit.resample(bust_1x(), SX0, SY0, N)
    rim_pass(px, rim_keep())
    for ln in LOCK_PARTINGS:
        pline(px, ln, 'k', HAIR)
    for ln in LOCK_SHINE:
        pline(px, ln, 'm', set('hij'))
    for ln in SIDE_PARTINGS:
        pline(px, ln, 'k', HAIR)
        pline(px, [(x + 1, y) for x, y in ln], 'l', set('hij'))
    for ln in CREST_PARTINGS:
        pline(px, ln, 'k', HAIR)
    dkit.patch(px, FACE)
    pline(px, SIDEBURN_EDGE, 'k', HAIR)
    dkit.patch(px, EAR)
    dkit.patch(px, COLLAR)
    for ln in FOLDS_K:
        pline(px, ln, 'k', RED)
    for ln, key, only in FOLDS_SHADE:
        pline(px, ln, key, set(only))
    dkit.patch(px, PRINT)
    for q, k in PRINT_SHADE:
        if px.get(q) in set('oOY'):
            px[q] = k
    return px


def build_image():
    return dkit.image(build(), W, H)


# ---------------------------------------------------------------------------------------- measure
def measure(im):
    sprite = Image.open(dkit.SPRITE).convert('RGBA')
    s, p = dkit.stats(sprite), dkit.stats(im)
    f0 = dkit.stats(sprite.crop((0, 0, 96, 96)))
    print('portrait.png          %4d px  black %4.1f%%  colours %d  alpha %s'
          % (p['opaque'], 100 * p['black'], p['colours'], p['alphas']))
    print('jordan_redesign.png   %4d px  black %4.1f%%  colours %d' % (s['opaque'], 100 * s['black'], s['colours']))
    print('  frame 0 alone       %4d px  black %4.1f%%  colours %d' % (f0['opaque'], 100 * f0['black'], f0['colours']))
    extra = {c[:3] for c in dkit.flat(im) if c[3]} - {tuple(v[:3]) for v in dkit.PAL.values()}
    print('colours outside kit.PAL:', sorted(extra) or 'none')
    return p


def main(ship=False):
    """Build both files in the scratchpad, prove the .aseprite re-exports to exactly the PNG's
    pixels, and only then (--ship) copy each into Assets in one write, and check what landed."""
    if ship:
        raise SystemExit('SUPERSEDED: this is the 09-23 portrait of the first redesign. Jordan v2 was approved '
                         '2026-09-24 and his portrait is now built by portrait_v2.py; this rig refuses to ship.')
    from imgdiff import pixel_diff
    im = build_image()
    out = os.path.join(dkit.PREVIEWS, 'build')
    os.makedirs(out, exist_ok=True)
    png, ase = os.path.join(out, 'portrait.png'), os.path.join(out, 'portrait.aseprite')
    im.save(png)
    measure(im)
    subprocess.run([dkit.ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    subprocess.run([dkit.ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    print('aseprite round trip (imgdiff.pixel_diff):', d or 'identical')
    if d or not ship:
        return 1 if d else 0
    for src, dst in ((png, ASSET + '.png'), (ase, ASSET + '.aseprite')):
        shutil.copyfile(src, dst)
        with open(src, 'rb') as a, open(dst, 'rb') as b:
            assert a.read() == b.read(), dst
        print('shipped', dst)
    landed = pixel_diff(Image.open(ASSET + '.png'), im)
    print('landed PNG vs build:', landed or 'identical')
    return 1 if landed else 0


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
