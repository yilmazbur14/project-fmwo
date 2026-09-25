"""Burak's dialogue portrait, Assets/Characters/Burak/portrait.png (64x64), derived from his APPROVED
VS card pose (art_source/vs_card_v2 pose_burak.py -> scratchpad vs_redesign/final/pose_burak.png).

balloon.gd loads res://Assets/Characters/<speaker>/portrait.png and shows it at 128x128; with no file
it hides the frame, which is why his five lines in Matt's intro (and the NEW GAME cutscene's) have
run without one. Bust framing, the shoulders running off the bottom edge, like every other portrait.

THE METHOD - the cast's (Jordan's art_source/jordan_derived/portrait.py, Matt's mi_portrait.py):
his own pixels, cropped and fitted. What differs is the fit.
  1. The source is the approved PNG itself, 352x132. It is pxkit.scale2x(sprite()) - the pose was
     drawn as a 176x66 sprite and doubled with Scale2x (STYLE.md: "Burak ... is drawn as a 1x
     sprite at a head of about 30 px and gets the same Scale2x"). Scale2x is exactly invertible:
     in every 2x2 block the source pixel fills at least two cells and each replaced cell takes a
     different neighbour, so the block's majority IS the source pixel. unscale2x() takes it, and
     build() proves the inversion by running Scale2x on the result and requiring the approved PNG
     back pixel for pixel. The rig is not imported: parallel artists are editing vs_card_v2.
  2. THE FIT IS 1:1 on that 176x66 sprite. The other portraits scale up (Jordan 1.5x, Matt 1.25x)
     because their sprites' faces are 20-26 px; Burak's pose face is already 28 px across (Jordan's
     portrait face is ~28, Josh's ~26, Matt's ~31) and his hair 46. So no resample at all: every
     pixel is the approved pose's own, keylines, ramps and all, and the black ratio and colour count
     are inherited rather than rebuilt. The approved 2x itself would need a 0.5x downscale, which
     would break its keylines; the inverse of its Scale2x is that downscale done losslessly.
  3. The window, x68..131 y2..65 of the sprite: all of it that there is below the hair (the pose
     is cut at y65 by the band's bottom rule, so the bust runs off the bottom edge as the others'
     do), the spike tips one row under the top edge, the whole head centred (hair x77..122 lands on
     columns 9..54), the whole raised glove (its right keyline, x131, is the last column), and the
     headband's knot with the roots of both tails leaving the left edge, so the tails still read.
     Three windows were compared (x66, x68, x72): x72 loses the tails, x66 cuts the glove.
  No hand detail is added: a close-up that is not enlarged has nothing to fill, and anything drawn
  on the approved pixels would be invention.

THE NUMBERS (measure() prints them on every build). The portrait is 24.7% black over 17 colours;
the same crop of the 1x sprite is the same image; the same crop of the approved 2x PNG (x136..263,
y4..131) is 24.9% over 17; the whole pose 26.1% over 17 (its extra black is the two long thin
tails, all keyline, which a bust leaves out). No white, as his pose rule requires. Alpha 0 / 255.

    python burak_portrait.py            # build into the scratchpad, measure, round-trip, previews
    python burak_portrait.py --ship     # ...then write Assets/Characters/Burak/portrait.png + .aseprite
"""
import os
import shutil
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import k923 as K                                                 # noqa: E402
import balloon_mock                                              # noqa: E402
from PIL import Image                                            # noqa: E402

APPROVED = os.path.join(K.SCRATCH, 'vs_redesign', 'final', 'pose_burak.png')
# The approved file's pixels, pinned: a later edit to the pose must be re-approved before it can
# change the portrait. (sha256 of the RGBA bytes, not the file, so a re-save cannot trip it.)
APPROVED_RGBA_SHA = 'ceb918930054a77d836b335f16e2db49b2c028d21f41f5f406edda0f995cee84'
DIR = os.path.join(K.ASSETS, 'Characters', 'Burak')
ASSET = os.path.join(DIR, 'portrait')
X0, Y0, W, H = 68, 2, 64, 64                     # the window on the 176x66 sprite
LINE = "No the challenge has been brutal and everyone's so weird"   # Dialogue/MattPreFight.dialogue


# ---------------------------------------------------------------------------------------- Scale2x
def _norm(im):
    im = im.convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            px[x, y] = (0, 0, 0, 0) if p[3] < 128 else (p[0], p[1], p[2], 255)
    return im


def scale2x(im):
    """EPX, exactly as art_source/vs_card_v2/pxkit.scale2x does it (copied, not imported)."""
    im = _norm(im)
    w, h = im.size
    src = im.load()
    out = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    dst = out.load()

    def at(x, y):
        return src[x, y] if 0 <= x < w and 0 <= y < h else (0, 0, 0, 0)

    for y in range(h):
        for x in range(w):
            p = src[x, y]
            a, b, c, d = at(x, y - 1), at(x + 1, y), at(x - 1, y), at(x, y + 1)
            dst[2 * x, 2 * y] = a if (c == a and c != d and a != b) else p
            dst[2 * x + 1, 2 * y] = b if (a == b and a != c and b != d) else p
            dst[2 * x, 2 * y + 1] = c if (d == c and d != b and c != a) else p
            dst[2 * x + 1, 2 * y + 1] = d if (b == d and b != a and d != c) else p
    return out


def unscale2x(im):
    """The source of a Scale2x image: each 2x2 block's majority. Refuses a tie (not Scale2x output)."""
    im = _norm(im)
    src = im.load()
    w, h = im.width // 2, im.height // 2
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            c = Counter([src[2 * x, 2 * y], src[2 * x + 1, 2 * y],
                         src[2 * x, 2 * y + 1], src[2 * x + 1, 2 * y + 1]]).most_common()
            if len(c) > 1 and c[0][1] == c[1][1]:
                raise ValueError('block (%d,%d) has no majority: not a Scale2x image' % (x, y))
            dst[x, y] = c[0][0]
    return out


# ---------------------------------------------------------------------------------------- build
def approved():
    im = Image.open(APPROVED).convert('RGBA')
    got = K.sha(im.tobytes())
    if got != APPROVED_RGBA_SHA:
        raise SystemExit('pose_burak.png is not the approved pose this portrait was cut from '
                         '(rgba sha %s) - re-approve before rebuilding' % got)
    return im


def sprite_1x():
    """The approved pose at its native sprite scale, proved exact."""
    pose = approved()
    one = unscale2x(pose)
    d = K.pixel_diff(scale2x(one), pose)
    if d:
        raise SystemExit('Scale2x of the recovered sprite is not the approved pose: %s' % d)
    return one, pose


def build():
    one, _ = sprite_1x()
    return one.crop((X0, Y0, X0 + W, Y0 + H))


# ---------------------------------------------------------------------------------------- measure
def measure(im):
    one, pose = sprite_1x()
    rows = [
        ('portrait.png (64x64)', im),
        ('same crop of the pose sprite, 1x', one.crop((X0, Y0, X0 + W, Y0 + H))),
        ('same crop of approved pose_burak.png, 2x', pose.crop((2 * X0, 2 * Y0, 2 * X0 + 2 * W, 2 * Y0 + 2 * H))),
        ('approved pose_burak.png, whole', pose),
    ]
    for name, x in rows:
        print(K.fmt(name, K.stats(x)))
    s = K.stats(im)
    cols = sorted({'%02X%02X%02X' % c[:3] for c in K.flat(im) if c[3]})
    pose_cols = sorted({'%02X%02X%02X' % c[:3] for c in K.flat(pose) if c[3]})
    print('alpha values %s; white present: %s; colours outside the approved pose: %s'
          % (s['alphas'], 'FFFFFF' in cols, sorted(set(cols) - set(pose_cols)) or 'none'))
    return s


# ---------------------------------------------------------------------------------------- previews
def previews(im):
    one, pose = sprite_1x()
    src2x = pose.crop((2 * X0, 2 * Y0, 2 * X0 + 2 * W, 2 * Y0 + 2 * H))
    win = one.copy()
    from PIL import ImageDraw
    frame = K.up(win, 3)
    ImageDraw.Draw(frame).rectangle([X0 * 3 - 1, Y0 * 3 - 1, (X0 + W) * 3, (Y0 + H) * 3], outline=(255, 210, 60, 255))
    K.preview(K.label(frame, 'the pose sprite (1x, recovered from the approved 2x), 3x, the window boxed'),
              'burak_window_on_pose_3x.png')
    K.preview(K.row([K.label(K.up(src2x, 3), 'approved pose_burak.png, same window, 3x (= 6x of 1x)'),
                     K.label(K.up(im, 6), 'portrait.png 64x64 at 6x')]), 'burak_portrait_6x_vs_pose.png')
    cast = [K.label(K.up(im, 4), 'Burak (new)')]
    for n in ('Matt', 'Jordan', 'Josh', 'Carter', 'Eric'):
        cast.append(K.label(K.up(Image.open(os.path.join(K.ASSETS, 'Characters', n, 'portrait.png')), 4), n))
    K.preview(K.row(cast), 'burak_portrait_beside_cast_4x.png')
    K.preview(balloon_mock.balloon(im, 'Burak', LINE), 'burak_portrait_in_balloon.png')


# ---------------------------------------------------------------------------------------- main
def main(ship=False):
    im = build()
    out = os.path.join(K.PREVIEWS, 'burak_build')
    os.makedirs(out, exist_ok=True)
    png, ase = K.refuse_live(os.path.join(out, 'portrait.png')), K.refuse_live(os.path.join(out, 'portrait.aseprite'))
    im.save(png)
    assert K.pixel_diff(Image.open(png), im) is None
    measure(im)
    d = K.ase_from_png(png, ase)
    print('aseprite round trip (imgdiff.pixel_diff):', d or 'identical')
    previews(im)
    if d or not ship:
        return 1 if d else 0

    # ---- ship: the folder is new; refuse to overwrite anything there that is not this build
    os.makedirs(DIR, exist_ok=True)
    if os.path.exists(ASSET + '.png') and K.pixel_diff(Image.open(ASSET + '.png'), im):
        raise SystemExit('%s exists and is not this build (someone else\'s?) - refusing' % (ASSET + '.png'))
    for src, dst in ((png, ASSET + '.png'), (ase, ASSET + '.aseprite')):
        shutil.copyfile(src, dst)
        assert K.read_bytes(src) == K.read_bytes(dst), dst
        print('shipped', dst)
    landed = K.pixel_diff(Image.open(ASSET + '.png'), im)
    print('landed PNG vs build:', landed or 'identical')
    back = os.path.join(out, 'landed_ase_export.png')
    K.aseprite([ASSET + '.aseprite', '--save-as', back])
    d2 = K.pixel_diff(Image.open(back), Image.open(ASSET + '.png'))
    print('landed .aseprite exported vs landed PNG (imgdiff.pixel_diff):', d2 or 'identical')
    return 1 if (landed or d2) else 0


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
