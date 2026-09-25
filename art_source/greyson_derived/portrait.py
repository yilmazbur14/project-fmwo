"""Greyson's dialogue portrait, Assets/Characters/Greyson/portrait.png (64x64), derived from his APPROVED
redesign (2026-09-24, art_source/greyson_redesign/APPROVED.md): Assets/Characters/Greyson/
greyson_redesign.png frame 0, the ready stance. It replaces the user's own 05-27 drawing, backed up
beside the previews, which the redesign itself was drawn from (the vein, the eyes, the moustache).

THE METHOD is Jordan's and Josh's portraits' (art_source/jordan_derived/portrait_v2.py):
  1. His own pixels: frame 0 as the rig builds it (gr_fig.build('idle'), imported, never edited;
     it renders pixel-identical to the shipped PNG). Head and shoulders: the window x35..77,
     y25..67, 43 source pixels, centred on his mirror axis (column 56), one row over his crown.
     His normal arms, not the cannon: the arms only enter at the frame's edges as his shoulders.
  2. Scaled by 1.5 - but SYMMETRICALLY. The 1.5x of Josh's and Jordan's portraits pairs pixels
     from the window's left edge, so a feature and its mirror image get their 'between' pixels on
     different sides (his jaw came out a pixel wider on the right). Greyson is drawn front-on and
     mirror-symmetric, so here the pairs run outward from the axis on both sides and the axis
     column (the parting, the vein, the bridge of the nose) is doubled: 1 + 21 pairs... exactly 64.
     Every 'between' pixel still copies a neighbour, never a blend, and each side keeps its own
     pixels - the right side stays in the shade the rig lit it with.
  3. Hand detail the 112px sprite had no room for, in his own palette (gr_kit.PAL), every edit made
     on the left and mirrored except the lighting: the hairline joined into one clean separation
     (the rig's stepped keyline fell into dots at 1.5x), the black cut between each curtain's two
     locks carried up to the cheek, the nostrils, the teeth's gaps and the back teeth in shadow,
     the brows evened to one length.
  4. The silhouette keyline grown outward to 2px (SILHOUETTE_PX): see THE NUMBERS.

THE NUMBERS (the target: the same crop of frame 0 at 1x): the crop is 16.1% black over 21 colours;
  the portrait is 14.7% over 22 (frame 0 alone 17.3% over 28, the sheet 17.8% over 28) - inside the
  house tolerance for derived art (art_source/vs_card_v2/STYLE.md: +-2 points, +-3 colours).
  Greyson is skin-heavy and the house rule draws his muscle lines in dark skin tones, not black, so
  at 1.5x with one-pixel lines the portrait falls to 12.2% (straight 1.5x: 11.3%); the only black
  the rule allows inside him is where forms overlap, and that is all used above. The last step is
  STYLE.md's own for derived art shown bigger than its sheet (Danny's and Bixby's cards): the
  silhouette keyline grown outward by one pixel. GREYSON_SILHOUETTE_PX=1 builds the one-pixel
  version (Jordan's and Josh's line weight) at 12.2%, if the user prefers it.

    python -B portrait.py            # build into the scratchpad, measure, round-trip the .aseprite
    python -B portrait.py --ship     # ...then write Assets/Characters/Greyson/portrait.png + .aseprite
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ART = os.path.join(ROOT, 'art_source')
RIG = os.path.join(ART, 'greyson_redesign')
for _p in (RIG, ART):
    if _p not in sys.path:
        sys.path.append(_p)
import gr_kit as K                                               # noqa: E402  (the rig)
import gr_fig                                                    # noqa: E402
from PIL import Image, ImageDraw                                 # noqa: E402

ASSET = os.path.join(ROOT, 'Assets', 'Characters', 'Greyson', 'portrait')
SPRITE = os.path.join(ROOT, 'Assets', 'Characters', 'Greyson', 'greyson_redesign.png')
PREVIEWS = os.environ.get(
    'GREYSON_DERIVED_PREVIEWS',
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\greyson_portrait')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

W = H = 64
N = 43
SX0, SY0 = 35, 25          # the window: x35..77 (the axis, column 56, at offset 21), y25..67
AXIS = 21                  # the axis's offset in the window


# ---------------------------------------------------------------------------------------- 1x
def frame0():
    return dict(gr_fig.build('idle').px)


def crop_numbers(px=None):
    """The target: the same crop of frame 0 at 1x."""
    px = px or frame0()
    vals = [k for (x, y), k in px.items() if SX0 <= x < SX0 + N and SY0 <= y < SY0 + N]
    return len(vals), sum(1 for k in vals if k == 'k') / len(vals), len(set(vals))


# ---------------------------------------------------------------------------------------- 1.5x
def _pick(a, b, aa, bb):
    """The between pixel of a and b (aa, bb: the pixels beyond each). Never a blend. (Josh's rule;
    a is the INNER pixel of a horizontal pair here, so both sides of the axis fall back alike.)"""
    if a == b:
        return a
    if a is None or b is None:
        o = b if a is None else a
        return None if o == 'k' else o
    if a == 'k':
        return b
    if b == 'k':
        return a
    a_thin, b_thin = aa != a, bb != b
    if a_thin and not b_thin:
        return b
    if b_thin and not a_thin:
        return a
    return a


def xs_for(c):
    """Output column -> ([source x offsets, inner first], sign): sign +1 right of the axis, -1 left."""
    if c in (31, 32):
        return [AXIS], 0
    if c >= 33:
        if c == 63:
            return [N - 1], 1
        t = c - 33
        j, r = divmod(t, 3)
        inner = AXIS + 1 + 2 * j
        return ([inner] if r == 0 else [inner + 1] if r == 2 else [inner, inner + 1]), 1
    offs, _ = xs_for(63 - c)
    return [2 * AXIS - o for o in offs], -1


def omap_x(o, toward=0):
    """Source x offset -> its main output column (the axis covers 31 and 32: pick the side of
    `toward`, -1 left / +1 right)."""
    if o == AXIS:
        return 32 if toward > 0 else 31
    if o > AXIS:
        if o == N - 1:
            return 63
        j, r = divmod(o - (AXIS + 1), 2)
        return 33 + 3 * j + 2 * r
    return 63 - omap_x(2 * AXIS - o)


def omap_y(u):
    return 3 * (u // 2) + 2 * (u % 2)


def ys_for(r):
    q, m = divmod(r, 3)
    return [2 * q] if m == 0 else ([2 * q + 1] if m == 2 else [2 * q, 2 * q + 1])


def resample(px):
    def g(x, y):
        return px.get((SX0 + x, SY0 + y))

    out = {}
    for oy in range(64):
        ys = ys_for(oy)
        for ox in range(64):
            xs, sign = xs_for(ox)
            if len(xs) == 1 and len(ys) == 1:
                v = g(xs[0], ys[0])
            elif len(ys) == 1:
                y = ys[0]
                xi, xo = xs
                v = _pick(g(xi, y), g(xo, y), g(xi - sign, y), g(xo + sign, y))
            elif len(xs) == 1:
                x = xs[0]
                v = _pick(g(x, ys[0]), g(x, ys[1]), g(x, ys[0] - 1), g(x, ys[1] + 1))
            else:
                xi, xo = xs
                ti, to, bi, bo = g(xi, ys[0]), g(xo, ys[0]), g(xi, ys[1]), g(xo, ys[1])
                if (ti == bo == 'k' and 'k' not in (to, bi)) or (to == bi == 'k' and 'k' not in (ti, bo)):
                    v = 'k'                      # a diagonal keyline stays joined
                else:
                    top = _pick(ti, to, g(xi - sign, ys[0]), g(xo + sign, ys[0]))
                    bot = _pick(bi, bo, g(xi - sign, ys[1]), g(xo + sign, ys[1]))
                    v = _pick(top, bot, top, bot)
            if v is not None:
                out[(ox, oy)] = v
    # two diagonal source keyline pixels whose images land two apart get one bridge pixel, chosen
    # nearest the axis so the choice mirrors
    for y in range(N):
        for x in range(N):
            if g(x, y) != 'k':
                continue
            for dx in (1, -1):
                qx, qy = x + dx, y + 1
                if not (0 <= qx < N and qy < N) or g(qx, qy) != 'k' or 'k' in (g(qx, y), g(x, qy)):
                    continue
                P = (omap_x(x, dx), omap_y(y))
                Q = (omap_x(qx, -dx), omap_y(qy))
                if abs(P[0] - Q[0]) <= 1 and abs(P[1] - Q[1]) <= 1:
                    continue
                cands = [(bx, by) for bx in range(min(P[0], Q[0]), max(P[0], Q[0]) + 1)
                         for by in range(min(P[1], Q[1]), max(P[1], Q[1]) + 1)
                         if (bx, by) not in (P, Q) and max(abs(bx - P[0]), abs(by - P[1])) <= 1
                         and max(abs(bx - Q[0]), abs(by - Q[1])) <= 1]
                if cands and not any(out.get(c) == 'k' for c in cands):
                    out[min(cands, key=lambda c: (abs(c[0] - 31.5), c[1]))] = 'k'
    return out


# ---------------------------------------------------------------------------------------- detail
def _mirror(d):
    """A left-half edit list -> both halves (x' = 63 - x), the portrait's own axis."""
    out = dict(d)
    for (x, y), k in d.items():
        out[(63 - x, y)] = k
    return out


# Every edit is made on the left half and mirrored, so the portrait keeps his symmetry.
DETAIL = _mirror({
    # the hairline: the rig steps it two pixels a row with a keyline pixel every other step, which
    # at 1.5x fell apart into dots between the forehead and the mane; here it is one clean diagonal
    # separation from the parting's side down to the face's edge (the house rule: black between
    # overlapping forms)
    (26, 10): 'k', (25, 10): 'k', (23, 11): 'k', (22, 12): 'k', (20, 13): 'k', (19, 13): 'k',
    (17, 14): 'k', (16, 14): 'k',
    # the black cut that splits each curtain into two pointed locks, carried up from the jaw to the
    # cheek, so the locks read as locks beside his face and not just below it
    (10, 26): 'k', (10, 27): 'k', (10, 28): 'k', (10, 29): 'k', (10, 30): 'k', (10, 31): 'k',
    (10, 32): 'k',
    # the nostrils, one dark dot each side of the nose's tip
    (30, 28): 'k',
    # the teeth of his grin separated, the laterals from the incisors (a pale gap, not a line)
    (28, 31): 'X', (28, 32): 'X',
})
# The brows: the 1.5x's 'between' pick went to brow on his shaded side and to skin on his lit side,
# leaving the right brow a pixel longer; both are the left one's 7 pixels (x 19-25 / 38-44).
BROW_FIX = {(37, 15): '3', (37, 16): '3'}
# The back teeth of the grin in shadow, darker on his shaded side, as the rig lights the rest of him
# (not mirrored: the light is from the upper left).
TEETH_SHADE = {(25, 32): 'X', (38, 32): 'x'}


def grow_silhouette(px):
    """The silhouette's keyline grown outward by one pixel (4-neighbour ring of the transparent
    background round the figure, inside the frame): see SILHOUETTE_PX."""
    ring = {(x + dx, y + dy) for (x, y) in px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if (x + dx, y + dy) not in px and 0 <= x + dx < W and 0 <= y + dy < H}
    for q in ring:
        px[q] = 'k'
    return px


SILHOUETTE_PX = int(os.environ.get('GREYSON_SILHOUETTE_PX', '2'))


# ---------------------------------------------------------------------------------------- build
def build(detail=True):
    px = resample(frame0())
    if not detail:
        return px
    for q, k in DETAIL.items():
        assert q in px, ('outside the figure', q)
        px[q] = k
    px.update(BROW_FIX)
    px.update(TEETH_SHADE)
    if SILHOUETTE_PX == 2:
        grow_silhouette(px)
    return px


def build_image():
    return K.image(build(), W, H)


# ---------------------------------------------------------------------------------------- measure
def measure(im):
    sheet = Image.open(SPRITE).convert('RGBA')
    s, f0, p = K.stats(sheet), K.stats(sheet.crop((0, 0, 112, 112))), K.stats(im)
    n, blk, cols = crop_numbers()
    print('portrait.png                 %4d px  black %4.1f%%  colours %d  semi %d'
          % (p['opaque'], 100 * p['black'], p['colours'], p['semi']))
    print('the same crop of frame 0     %4d px  black %4.1f%%  colours %d   <- the target' % (n, 100 * blk, cols))
    print('frame 0 alone                %4d px  black %4.1f%%  colours %d' % (f0['opaque'], 100 * f0['black'], f0['colours']))
    print('greyson_redesign.png         %4d px  black %4.1f%%  colours %d' % (s['opaque'], 100 * s['black'], s['colours']))
    extra = {c[:3] for c in K.flat(im) if c[3]} - {tuple(v[:3]) for v in K.PAL.values()}
    print('colours outside gr_kit.PAL:', sorted(extra) or 'none')
    return p


def main(ship=False):
    from imgdiff import pixel_diff
    im = build_image()
    out = os.path.join(PREVIEWS, 'build')
    os.makedirs(out, exist_ok=True)
    png, ase = os.path.join(out, 'portrait.png'), os.path.join(out, 'portrait.aseprite')
    im.save(png)
    measure(im)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    print('aseprite round trip (imgdiff.pixel_diff):', d or 'identical')
    if d or not ship:
        return 1 if d else 0
    # The user's own 05-27 drawing, kept beside this rig (and in git's first commit). The gate ships
    # only over that drawing; once the portrait has shipped, a re-ship needs GREYSON_PORTRAIT_REPLACE=1.
    backup = os.path.join(HERE, 'user_portrait_0527.png')
    if not os.path.exists(backup):
        raise SystemExit('refusing: the user\'s own portrait must be backed up first (%s)' % backup)
    with open(backup, 'rb') as a, open(ASSET + '.png', 'rb') as b:
        live = b.read()
        if a.read() != live and not os.environ.get('GREYSON_PORTRAIT_REPLACE'):
            # the live file is no longer the user's drawing: somebody shipped over it since
            raise SystemExit('refusing: the live portrait.png is not the backed-up drawing any more')
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
