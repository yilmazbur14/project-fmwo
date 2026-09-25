"""Previews of the 2x brawl art, written ONLY to a scratch folder (never Assets/):

    python gb_preview2x.py [out_dir]   # default: the session scratchpad's greyson_fight/player/2x/

    brawl_2x_vs_1x.png          the approved 1x poses (4x), the shipped x2 placeholder (2x) and the
                                native 2x approval pass (2x) side by side, so all three are the same size
    brawl_2x_native_pass.png    the approval pass alone: x2 then native for guard, full slip, parry snap,
                                at 6x and at game scale (3 px a texel)
    brawl_uppercut_4x.png       the back-view uppercut, normal and _super, at 4x with the ground,
                                the centre line and the 50 / 70 glove heights marked
    brawl_uppercut_vs_greyson.gif, brawl_uppercut_super_vs_greyson.gif
                                game scale (3 px a texel): the uppercut at the finisher's timings
                                against a crouched Greyson stand-in whose jaw sits on the plan's dazed chin

The Greyson stand-in is his approved greyson_redesign.png f0 with 9 rows taken out of his abs and 9
out of his thighs, so his jaw drops to his cell's row 65 (46 up), the plan's dazed chin. It stands in
for the brawl-set artist's dazed sheet and is not art.
Reads the project's assets; writes nothing else.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gb_player as G  # noqa: E402
import gb_player2x as G2  # noqa: E402
import gb_native2x as N  # noqa: E402
import gb_uppercut2x as U  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCRATCH = (r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
           r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\greyson_fight\player\2x')
MAT = os.path.join(G.ROOT, 'Assets', 'Environment', 'arena_mat.png')
GREYSON = os.path.join(G.ROOT, 'Assets', 'Characters', 'Greyson', 'greyson_redesign.png')
BG = (46, 49, 58, 255)
DARK = (14, 14, 18, 255)
INK = (225, 225, 232, 255)
NAMES = ['guard', 'guard bounce', 'slip L half', 'slip L full', 'slip R half', 'slip R full',
         'parry snap', 'parry absorb', 'hit lands', 'hit reel']
UP_ROLES = ['f0 ready', 'f1 charge', 'f2 charge', 'f3 launch', 'f4 rise', 'f5 CONTACT', 'f6 rise',
            'f7 apex', 'f8 fall', 'f9 land']


def up(im, s, marks=None):
    base = Image.new('RGBA', im.size, BG)
    base.alpha_composite(im)
    big = base.resize((im.width * s, im.height * s), Image.NEAREST)
    if marks:
        d = ImageDraw.Draw(big, 'RGBA')
        for y, col in marks:
            d.line([(0, y * s), (big.width, y * s)], fill=col)
    return big


def label(im, text, pad=14):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((2, 1), text, fill=INK)
    return out


def row(ims, gap=6):
    out = Image.new('RGBA', (sum(i.width for i in ims) + gap * (len(ims) - 1), max(i.height for i in ims)), DARK)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def col(ims, gap=6):
    out = Image.new('RGBA', (max(i.width for i in ims), sum(i.height for i in ims) + gap * (len(ims) - 1)), DARK)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def vs_1x():
    """Per column: the 1x approved cell (4x), its x2 (2x), and the native pass where it exists (2x)."""
    ph = G2.placeholder_cells()
    native = {c: fn() for c, n, fn in N.APPROVAL}
    cards = []
    for i, (name, grid) in enumerate(G.FRAMES):
        one = up(G.image(G.g(grid)), 4)
        one_cell = Image.new('RGBA', (128, 192), BG)
        one_cell.paste(one, (0, 6))       # ground lines level: 1x y 29 at 4x is 116 px, 2x y 61 at 2x is 122
        two = up(G2.image2x(ph[i][1]), 2)
        stack = [label(one_cell, '1x approved'), label(two, 'x2 (shipped)')]
        if i in native:
            stack.append(label(up(G2.image2x(native[i]), 2), 'native 2x'))
        cards.append(label(col(stack, gap=4), '%d %s' % (i, NAMES[i])))
    return col([row(cards[:5], gap=10), row(cards[5:], gap=10)], gap=10)


def native_pass():
    ph = G2.placeholder_cells()
    pairs = []
    for c, n, fn in N.APPROVAL:
        pairs.append(label(up(G2.image2x(ph[c][1]).crop((4, 4, 60, 64)), 6), '%d %s: x2' % (c, n)))
        pairs.append(label(up(G2.image2x(fn()).crop((4, 4, 60, 64)), 6), '%d %s: native' % (c, n)))
    small = []
    for c, n, fn in N.APPROVAL:
        small.append(up(G2.image2x(ph[c][1]), 3))
        small.append(up(G2.image2x(fn()), 3))
    return col([row(pairs, gap=8), label(row(small, gap=8), 'game scale (3 px a texel): x2 then native, per pose')])


def uppercut_sheet():
    marks = [(U.GROUND, (255, 90, 90, 150)), (U.GROUND - 50, (255, 220, 90, 140)), (U.GROUND - 70, (255, 140, 60, 140))]
    fr = U.frames()
    normal = [label(up(U.image(px), 4, marks), UP_ROLES[i]) for i, (r, px) in enumerate(fr)]
    sup = [label(up(U.image(px, U.PAL_SUPER), 4, marks), UP_ROLES[i] + ' super') for i, (r, px) in enumerate(fr)]
    return col([row(normal[:5]), row(normal[5:]), row(sup[:5]), row(sup[5:])], gap=8)


# ---- game scale
def greyson_standin(lift=0):
    """His approved f0 squashed to the dazed chin: 9 rows out of the abs, 9 out of the thighs."""
    src = Image.open(GREYSON).convert('RGBA').crop((0, 0, 112, 112))
    cut = set(range(62, 71)) | set(range(84, 93))
    out = Image.new('RGBA', (112, 112), (0, 0, 0, 0))
    y2 = 111
    for y in range(111, -1, -1):
        if y in cut:
            continue
        out.paste(src.crop((0, y, 112, y + 1)), (0, y2 - lift))
        y2 -= 1
    return out


def scene(player_im, frame_h, greyson_im, w=150, h=170):
    """Native texels, then x3: his feet at (75, 150); the player's origin 9 texels above that line
    (soles 4 texels in front of his, origin 13 above the soles), frame_h 96 (brawl) or 128 (uppercut)."""
    mat = Image.open(MAT).convert('RGBA')
    g = Image.new('RGBA', (w, h))
    g.paste(mat.crop((200, 60, 200 + w, 60 + h)), (0, 0))
    fx, fy = 75, 150
    g.alpha_composite(greyson_im, (fx - 56, fy - 111))
    ox, oy = fx, fy + 4 - 13
    top = oy - (80 if frame_h == 128 else 48)
    g.alpha_composite(player_im, (ox - 32, top))
    return g.resize((w * 3, h * 3), Image.NEAREST)


def uppercut_gif(path, pal):
    fr = [U.image(px, pal) for r, px in U.frames()]
    guard = G2.image2x(N.guard_px())
    stand = greyson_standin()
    lifted = greyson_standin(3)
    seq, times = [], []

    def add(player, fh, grey, t):
        seq.append(scene(player, fh, grey).convert('P', palette=Image.ADAPTIVE, colors=64))
        times.append(t)
    add(guard, 96, stand, 500)                       # the brawl guard, him dazed
    add(fr[0], 128, stand, 500)                      # ready (the mash prompt)
    for k in range(4):                               # the charge, speeding up as the meter fills
        add(fr[1], 128, stand, 80 if k < 2 else 50)
        add(fr[2], 128, stand, 80 if k < 2 else 50)
    for i, t in zip(range(3, 10), [50, 60, 60, 60, 140, 100, 160]):
        add(fr[i], 128, lifted if 5 <= i <= 7 else stand, t)
    add(fr[9], 128, stand, 700)
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=times, loop=0, disposal=2)


def main(argv):
    out = os.path.abspath(argv[0]) if argv else SCRATCH
    assets = os.path.normcase(os.path.realpath(os.path.join(G.ROOT, 'Assets')))
    real = os.path.normcase(os.path.realpath(out))
    if real == assets or real.startswith(assets + os.sep):
        print('refused: previews never go into Assets/')
        return 2
    os.makedirs(out, exist_ok=True)
    vs_1x().save(os.path.join(out, 'brawl_2x_vs_1x.png'))
    native_pass().save(os.path.join(out, 'brawl_2x_native_pass.png'))
    uppercut_sheet().save(os.path.join(out, 'brawl_uppercut_4x.png'))
    uppercut_gif(os.path.join(out, 'brawl_uppercut_vs_greyson.gif'), U.PAL)
    uppercut_gif(os.path.join(out, 'brawl_uppercut_super_vs_greyson.gif'), U.PAL_SUPER)
    contact = scene(U.image(U.frames()[5][1]), 128, greyson_standin(3))
    contact.save(os.path.join(out, 'brawl_uppercut_contact_3x.png'))
    for f in sorted(os.listdir(out)):
        print(os.path.join(out, f))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
