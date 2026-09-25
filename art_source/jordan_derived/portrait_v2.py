"""Jordan's dialogue portrait, Assets/Characters/Jordan/portrait.png (64x64), derived from the APPROVED
v2 redesign (2026-09-24, "approve jordans redesign"): Assets/Characters/Jordan/jordan_redesign_v2.png
frame 0, the v2 idle (which jordan_idle f0 equals). It replaces the 09-23 portrait (portrait.py),
which was cut the same way from the first redesign.

THE METHOD is the 09-23 portrait's, on the v2 rig (art_source/jordan_v2, imported, never edited):
  1. His own pixels: v2 frame 0 rebuilt in jv2_frames.build's own order minus the collector box, the
     hand holding it and the stick forearm raised to it (jv2_body.far_arm_box returns it as its own
     part), and minus the legs and shoes below the frame. The SAME crop as the 09-23 portrait:
     x27..69, y8..50, 43 source pixels. v2 slumps his head 2px forward and 1px down, so the head sits
     a little right of centre: the crane of his neck, not a framing slip.
  2. Scaled by 1.5 (dkit.resample, Josh's scaling), no pixel invented.
  3. The one-pixel rim-light pass.
  4. Hand detail in v2's own palette (jv2_base.PAL: the approved keys, the skin keys on the pallor):
     the 09-23 portrait's details on the face v2 keeps, re-authored because v2's one-row drop pairs
     the rows up differently at 1.5x; a black core down each of the rig's own dark grooves between
     the greasy clumps, carried into the hairline; the forelock's outline closed; the side hair
     parted; the thin neck's jaw shadow, back contour and Adam's apple; the gaping collar's band;
     the drooping sleeve's creases, both armpits, the far drape fold; the stain's core; the jewel.

THE NUMBERS (the coordinator's target: the same crop of v2 frame 0, box, hand and forearm out):
  that crop is 24.1% black over 22 colours; the portrait is 23.2% over 25 (v2 frame 0 alone 28.2%
  over 40, the sheet 28.8% over 40). Region by region: the head 20.9% against the crop's 20.3%; the
  body 29.3% against 33.8% - v2's thin neck, collar and sleeves are mostly outline at 1x, and a 1px
  line at 1.5x covers two thirds of the area it did. Straight 1.5x gives 17.4%. The rest could only
  come from doubled outlines or from turning his darkest tones black, which moves the number, not
  the drawing. measure() prints them on every build.

    python portrait_v2.py            # build into the scratchpad, measure, round-trip the .aseprite
    python portrait_v2.py --ship     # ...then write Assets/Characters/Jordan/portrait.png + .aseprite
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dkit                                                      # noqa: E402
V2 = os.path.join(dkit.ART, 'jordan_v2')
sys.path.insert(0, V2)
import jv2_base as B                                             # noqa: E402  (the v2 rig)
import jv2_body as body                                          # noqa: E402
import jv2_head as jhead                                         # noqa: E402
import jv2_frames as F                                           # noqa: E402
from kit import line                                             # noqa: E402
from PIL import Image                                            # noqa: E402

ASSET = os.path.join(dkit.ASSETS, 'Characters', 'Jordan', 'portrait')
SPRITE_V2 = os.path.join(dkit.ASSETS, 'Characters', 'Jordan', 'jordan_redesign_v2.png')
W = H = 64
SX0, SY0 = 27, 8          # the 09-23 portrait's window on frame 0
N = 43
PAL = B.PAL

RAMPS = ['abcde', 'hijlm', 'vVRTU', 'qPQ', 'gGoOY', '123']
RAMP_OF = {k: r for r in RAMPS for k in r}
HAIR = set('hijlmAY')
SKIN = set('abcde')
RED = set('vVRTU')


# ---------------------------------------------------------------------------------------- 1x
def bust_1x():
    """v2 frame 0 in jv2_frames.build's order, minus the legs and shoes (below the frame), the box,
    the hand on it and the forearm raised to it. Same head offset, same anchor shift."""
    cv = B.Canvas(96, 96)
    upper, sleeve, _forearm = body.far_arm_box()
    for part, outline in (upper, sleeve):
        cv.stamp(part, outline=outline)
    dx, dy = F.HEAD_AT[0]
    cv.stamp(body.neck(dx))
    cv.stamp(body.shirt(0))
    body.dandruff(cv.px)
    cv.stamp(B.shift(jhead.head(shout=False), dx, dy), outline=False)
    for part, outline in body.near_arm_hip():
        cv.stamp(part, outline=outline)
    return B.finish(cv.px)


def crop_numbers():
    """The target: the same crop of v2 frame 0 at 1x (box, hand and forearm out)."""
    b = bust_1x()
    vals = [k for (x, y), k in b.items() if SX0 <= x < SX0 + N and SY0 <= y < SY0 + N]
    return len(vals), sum(1 for k in vals if k == 'k') / len(vals), len(set(vals))


# ---------------------------------------------------------------------------------------- passes
def pline(px, pts, key, only):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for q in line(x0, y0, x1, y1):
            if px.get(q) in only:
                px[q] = key


def box(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def rim_pass(px, keep):
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
        (27, 19, 51, 47),        # the face keeps the rig's own values: eyes, nose, mouth, beard
        (17, 17, 23, 37),        # the ear and the rat-tail behind it
        (28, 47, 44, 56),        # the neck sits in the jaw's shadow and the collar's gape
        (23, 57, 46, 63),        # the princess print is a flat graphic
    ):
        keep |= box(*b)
    return keep


# The greasy hair: a black core down each of the rig's own dark grooves between the clumps (every
# one of these is an 'h' groove pixel in the resample); the oily shine band and the dandruff stay.
GROOVES = [(26, 17), (27, 13), (28, 14), (28, 15), (28, 16), (32, 17), (34, 12), (34, 13), (34, 14),
           (34, 15), (34, 16), (38, 11), (38, 17), (40, 12), (40, 13), (40, 14), (40, 15), (40, 16),
           (43, 9), (43, 10), (44, 11), (44, 17), (46, 12), (46, 13), (46, 14), (46, 15), (46, 16)]

# Rows 19..46 of the head by hand over the resampled pixels, the 09-23 portrait's details on the
# approved face (which v2 keeps exactly, a source row lower, so the rows pair up differently at 1.5x):
# the hair's underside as a black line over a cast-shadow band on the forehead, broken by the loose
# strand's root, its corner turning down the sideburn's front edge, the fallen forelock's outline
# closed; heavy brows with a lit top edge, a dark core and a black underside; half-lidded eyes looking
# screen-right, the irises in the lid's shadow; the tired bags; a nostril; the thin moustache parted
# at the philtrum; the lower lip lit on its upper left; the patchy beard's chin as three clumps with
# black only in the notches between their tips; the ear as its own shape.
FACE = [
    # x: 17-21 22-26 27-31 32-36 37-41 42-46 47-51 52
    (19, 17, "kikii hiiij iikkk kiiik kkkij iihhh ihhk. ."),
    (20, 17, "kiiki iiWWi jjkcc ciiic cckjj mmAjj ihhk. ."),
    (21, 17, "kjjki iiiij hkdee eeeie eekjj AAikc cbbk. ."),
    (22, 17, "kjjki iijii hkdee eeeie eedkj AAikc cbbk. ."),
    (23, 17, "kiiki jjjji hkdee eeeeh heddk kdddd cbbk. ."),
    (24, 17, ".kkki jjjji djiji ijiii ideed jijii iiik. ."),
    (25, 17, "...ki jjjji chhhh hhhhh hddee chhhh hhhk. ."),
    (26, 17, "...kk kjiih cckkk kkkkk khdde chkkk kchk. ."),
    (27, 17, "...ke dkiii ccccc bbbbb bbdde ddcbb bcck. ."),
    (28, 17, "..ked dkiii ccccc bbbbb bddde cdcbb bcck. ."),
    (29, 17, ".kdcb bkiii cckkk kkkkk dddde cckkk kcck. ."),
    (30, 17, ".kdck akiij cckWW WhhhW dddde ccWhh hkck. ."),
    (31, 17, ".kdcb akiij ccccW Wlhlc dddde ccWlh lcck. ."),
    (32, 17, ".kddc bkiij ccdbb bbbbd dddde bcbbb bcck. ."),
    (33, 17, ".kkdc bbjjc lldcd ddccd dddde eecdd ccck. ."),
    (34, 17, "..kdc bbjjl cldee cdddd dddde eebcc dcck. ."),
    (35, 17, "...kc bbjjl ccjdd cdddd dcbbd kabcc jcck. ."),
    (36, 17, "....k iijjl ccdjj cddjl ljihi lljih cjjk. ."),
    (37, 17, "..... kijjl ccdjj cddij jiihi jjihh cijk. ."),
    (38, 17, "..... .kijj jjcll jddbk kkkkk kkkbb jiik. ."),
    (39, 17, "..... .khhi cjjjj cjjip ddppp ppijj ciik. ."),
    (40, 17, "..... .khhi cjjjj jjjji apppp ppaij ciik. ."),
    (41, 17, "..... ..kkh iijcc jiiji hkkhh lljii cikk. ."),
    (42, 17, "..... ....k hhjll jihjl ljihj ljiih hk... ."),
    (43, 17, "..... ....k hhijl jihij ljihi jjihh hk... ."),
    (44, 17, "..... ..... kkhij iihhi jiihh iiihh hk... ."),
    (45, 17, "..... ..... ..khi ihkhi iihkh iihhh k.... ."),
    (46, 17, "..... ..... ..khh ihkkh ihhkk hihhk ..... ."),
]


# Each groove carried down into the hairline so every greasy clump closes; and the short side hair
# over the ear parted the way the 09-23 portrait's was, combed down and back.
GROOVE_ENDS = [(30, 18), (39, 18), (44, 18)]
SIDE_PARTINGS = [
    [(25, 18), (24, 19), (23, 20)],
    [(26, 21), (25, 23)],
]

# The body, which v2 made thin and frail in clothes that hang off him (x, y) -> key:
BODY = {
    # the thin neck: the jaw's shadow across its top under the beard (the rig's own shading, which
    # at 1x falls under the chin), a contour down its back edge where it passes in front of the skin
    # the gaping collar shows (at 1.5x the two ran into one tan blob), and the Adam's apple's
    # underside in shadow against its front edge
    (34, 48): 'c', (35, 48): 'b', (36, 48): 'b', (37, 48): 'b', (38, 48): 'b',
    (30, 52): 'k', (31, 53): 'k',
    (40, 51): 'k',
    # the gaping collar's black trim as a band: its rolled inside edge lit ('2') on the side toward
    # the light, one glint where it sags lowest, plain charcoal ('1') on the shadow side, where its
    # outer edge rolls over into a black fold against the tee
    (27, 56): '2', (30, 57): '3', (31, 57): '2', (32, 57): '2', (33, 57): '2',
    (42, 54): 'k', (42, 55): 'k', (39, 56): 'k',
    # the drooping near sleeve: a crease where it bunches at the armpit, its tail, the lit lip above
    # it, and the armpit itself closed to black where sleeve meets body
    (22, 58): 'k', (21, 59): 'k', (20, 60): 'k', (19, 61): 'V', (18, 62): 'V',
    (21, 58): 'T', (20, 59): 'T',
    (21, 62): 'k', (20, 63): 'k', (22, 61): 'T',       # a second, lower one, as the 09-23 sleeve had
    (23, 61): 'k', (23, 62): 'k', (23, 63): 'k',
    # the far side: the sack-like tee's long vertical drape fold, and the far armpit
    (46, 59): 'k', (46, 60): 'k', (46, 61): 'v', (45, 62): 'v',
    (49, 61): 'k', (49, 62): 'k',
    # the drip stain off the collar, darker at its core
    (41, 57): 'a', (42, 58): 'a',
    # the crown's red jewel, lit on its upper left
    (32, 60): 'T',
}


def build(detail=True):
    raw = dkit.resample(bust_1x(), SX0, SY0, N)
    px = dict(raw)
    if not detail:
        return px
    rim_pass(px, rim_keep())
    for q in GROOVES + GROOVE_ENDS:
        assert raw.get(q) == 'h', ('not a groove pixel in the resample', q, raw.get(q))
        px[q] = 'k'
    for ln in SIDE_PARTINGS:
        pline(px, ln, 'k', HAIR)
    dkit.patch(px, FACE)
    for q, k in BODY.items():
        assert q in raw, ('outside the silhouette', q)
        px[q] = k
    return px


def build_image():
    return dkit.image(build(), W, H, PAL)


# ---------------------------------------------------------------------------------------- measure
def measure(im):
    sheet = Image.open(SPRITE_V2).convert('RGBA')
    s, f0, p = dkit.stats(sheet), dkit.stats(sheet.crop((0, 0, 96, 96))), dkit.stats(im)
    n, blk, cols = crop_numbers()
    print('portrait.png            %4d px  black %4.1f%%  colours %d  alpha %s'
          % (p['opaque'], 100 * p['black'], p['colours'], p['alphas']))
    print('the same crop of v2 f0  %4d px  black %4.1f%%  colours %d   <- the target' % (n, 100 * blk, cols))
    print('v2 frame 0 alone        %4d px  black %4.1f%%  colours %d' % (f0['opaque'], 100 * f0['black'], f0['colours']))
    print('jordan_redesign_v2.png  %4d px  black %4.1f%%  colours %d' % (s['opaque'], 100 * s['black'], s['colours']))
    extra = {c[:3] for c in dkit.flat(im) if c[3]} - {tuple(v[:3]) for v in PAL.values()}
    print('colours outside the v2 palette:', sorted(extra) or 'none')
    return p


def main(ship=False):
    from imgdiff import pixel_diff
    im = build_image()
    out = os.path.join(dkit.PREVIEWS, 'build_v2')
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
