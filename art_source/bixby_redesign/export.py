"""Build the approval sheet (3 frames of 192x160), save the .aseprite beside it, check the round trip
pixel-exactly, measure it against the approved beast, and render the previews.

    python export.py            # SAFE: numbers and previews into the scratchpad only
    python export.py --write    # also writes Assets/Characters/Bixby/bixby_beast_redesign.png + .aseprite
"""
import os
import subprocess
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import frame  # noqa: E402
import view  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402  (art_source/imgdiff.py)

ROOT = os.path.dirname(os.path.dirname(HERE))
BIXBY = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby')
OUT_PNG = os.path.join(BIXBY, 'bixby_beast_redesign.png')
OUT_ASE = os.path.join(BIXBY, 'bixby_beast_redesign.aseprite')
OLD = os.path.join(BIXBY, 'bixby_beast.png')
ASEPRITE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'
REFS = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
        'a7fc2846-afef-472d-979b-e17143793a0f/images/')
S = view.SCRATCH
FW, FH = 192, 160
POSES = ['up', 'down', 'sig']
BG = (30, 28, 36, 255)


def frames():
    return [frame.build(p, frame.BOB[p]).image() for p in POSES]


def sheet(fr):
    out = Image.new('RGBA', (FW * len(fr), FH), (0, 0, 0, 0))
    for i, f in enumerate(fr):
        out.alpha_composite(f, (i * FW, 0))
    return out


def measure(im, label):
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    cnt = Counter(px)
    black = cnt.get((0, 0, 0, 255), 0)
    keyline = cnt.most_common(1)[0][0]
    semi = sum(1 for c in px if c[3] < 255)
    print('%-26s opaque %6d  colours %3d  black %5.2f%%  most common #%02X%02X%02X  semi-alpha %d  bbox %s'
          % (label, len(px), len(cnt), 100.0 * black / len(px), keyline[0], keyline[1], keyline[2], semi,
             im.getbbox()))


def on(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def before_after(fr):
    """4x on a dark background: the approved beast's hover frame, then the three new frames."""
    old = Image.open(OLD).convert('RGBA').crop((0, 0, FW, FH))
    cells = [(old, 'BEFORE'), (fr[0], 'AFTER 0'), (fr[1], 'AFTER 1'), (fr[2], 'AFTER 2')]
    gap = 6
    W = 2 * FW + gap
    H = 2 * FH + gap
    grid = Image.new('RGBA', (W, H), (18, 17, 22, 255))
    for i, (im, _) in enumerate(cells):
        x = (i % 2) * (FW + gap)
        y = (i // 2) * (FH + gap)
        grid.alpha_composite(on(im), (x, y))
    big = up(grid, 4)
    big.save(S + 'before_after_4x.png')
    return big


def preview_shadow(f, w=150, h=22):
    """A stand-in air shadow for the preview only: a plain pixel ellipse about the body's width. (The
    shipped bixby_beast_shadow.png follows the old silhouette; a matching one is for the full-sheet pass.)"""
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    for y in range(h):
        for x in range(w):
            if ((x - cx) / (w / 2.0)) ** 2 + ((y - cy) / (h / 2.0)) ** 2 <= 1.0:
                sh.putpixel((x, y), (0, 0, 0, int(255 * 0.38)))
    return sh, 96.0


def game_scale(fr):
    """3x game scale on the arena mat, beside the player. Hovering frames are drawn HOVER_HEIGHT texels
    above the floor point with an air shadow under them (38% black), as the fight draws them."""
    mat = Image.open(os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')).convert('RGBA')
    player = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')) \
        .convert('RGBA').crop((0, 0, 32, 32))
    hover = 40
    panels = []
    for i, f in enumerate(fr):
        # a 250x250 texel window of the mat: floor point low and centred
        win = mat.crop((150, 20, 150 + 250, 20 + 250)).copy()
        floor = (125, 222)
        sh, cx = preview_shadow(f)
        win.alpha_composite(sh, (int(round(floor[0] - 96 + cx - sh.width / 2.0)), floor[1] - sh.height // 2))
        win.alpha_composite(f, (floor[0] - 96, floor[1] - hover - 151))
        # the player facing up at him, off to the lower left
        win.alpha_composite(player, (12, 208))
        panels.append(up(win, 3))
    gap = 12
    out = Image.new('RGBA', (sum(p.width for p in panels) + gap * (len(panels) - 1), panels[0].height),
                    (18, 17, 22, 255))
    x = 0
    for p in panels:
        out.alpha_composite(p, (x, 0))
        x += p.width + gap
    out.save(S + 'gamescale_3x.png')
    return out


def refs_strip(fr):
    """The three references at a common height beside the new frames at 2x."""
    h = 320
    ims = []
    for name in ('5.png', '4.png', '6.png'):
        r = Image.open(REFS + name).convert('RGBA')
        ims.append(r.resize((int(r.width * h / r.height), h), Image.LANCZOS))
    for f in fr:
        ims.append(up(on(f), 2))
    gap = 10
    out = Image.new('RGBA', (sum(i.width for i in ims) + gap * (len(ims) - 1), h), (18, 17, 22, 255))
    x = 0
    for i in ims:
        out.alpha_composite(i, (x, 0))
        x += i.width + gap
    out.save(S + 'refs_strip.png')
    return out


def aseprite(png, ase):
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True)
    back = os.path.join(S, 'roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True)
    diff = pixel_diff(Image.open(png), Image.open(back))
    print('round trip png -> aseprite -> png:', diff or 'pixel-exact match')
    return diff


if __name__ == '__main__':
    fr = frames()
    sh = sheet(fr)
    measure(Image.open(OLD).convert('RGBA'), 'approved hover sheet')
    measure(Image.open(OLD).convert('RGBA').crop((0, 0, FW, FH)), 'approved hover frame 0')
    for i, f in enumerate(fr):
        measure(f, 'redesign frame %d (%s)' % (i, POSES[i]))
    measure(sh, 'redesign sheet')
    before_after(fr)
    game_scale(fr)
    refs_strip(fr)
    view.save(sh, 'sheet_2x.png', 2)
    if '--write' in sys.argv:
        os.makedirs(BIXBY, exist_ok=True)
        sh.save(OUT_PNG)
        print('wrote', OUT_PNG)
        aseprite(OUT_PNG, OUT_ASE)
        print('wrote', OUT_ASE)
