"""Jordan's silhouette on the main-menu tower (Assets/UI/Screens/main_menu_bg.png), re-derived from the
APPROVED v2 redesign (2026-09-24, jordan_redesign_v2.png frame 0) and rebuilt through the menu's own
pipeline (art_source/main_menu/bg.py). It replaces the 09-23 silhouette (menu.py) of the first redesign.
Re-sampled 2026-09-28 for the fitted tee (art_source/jordan_fit, approved "everywhere"): rows 17-31;
and again the same day for the SKINNY build (art_source/jordan_fit/skinny, approved): rows 18-35.

THE SCALE AND ANCHOR are the 09-23 entry's, as asked: factor 2.0, anchor 10.
  - menu_mask.new_mask(2.0, SPRITE_V2): v2 frame 0 at 2.0 is 24x44 (the top row empty, dropped).
  - v2's thinner akimbo elbow starts his bounding box at x29 (the first redesign's at x27), so the raw
    mask's column 9 holds sprite x47-48, where his body centres. One column of margin on the left puts
    that on column 10, so bg.py's PLACE (anchor 10) is unchanged and he stands on CX exactly as the
    09-23 silhouette did.

THE MASK is the sampler's, hand-cleaned only here (see jordan_derived/menu_mask.py for the sampler):
  - the collector box opened a pixel clear of his head down its full height (column 16 samples both
    the face's edge at x61 and the box's keyline at x62, so they merged), squared off, its red header
    as 'R' and its window as pale 'o' with the plumber figure inside, red cap and all - the 09-23 box,
    a row lower, as v2 holds it
  - a pixel between the sneakers (the 1x gap, x48-49, falls between two columns)
  Nothing else is touched: the greasy crest flicking forward, the notch of the thin neck, the narrow
  sloped shoulders, the skinny tee (a sack, then fitted, then skinny, all on 2026-09-28's round of
  refits) and the stick legs are all as sampled. The skinny build's thinner arms open, at 2.0, a 2x2
  gap inside the akimbo elbow (rows 23-24) and a notch between the tee and the hanging far arm (rows
  22-24): both are the sampler's, and the elbow gap now reads as the hand on his hip (the fitted
  tee's one-pixel gap sampled solid, and a one-cell hole opened by hand read as a stray fleck).

    python menu_v2.py            # rebuild in memory, prove it, write previews to the scratchpad
    python menu_v2.py --ship     # ...then write masks_clean.txt's [jordan] block, main_menu_bg.png and
                                 # main_menu_bg.aseprite, one write each, and check what landed

Runs in its own process: bg.py does `from lib import *` and needs art_source/main_menu/lib.py, which
the portrait's rig (Josh's lib, via Jordan's kit) would shadow.
"""
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MM = os.path.join(ROOT, 'art_source', 'main_menu')
SCREENS = os.path.join(ROOT, 'Assets', 'UI', 'Screens')
PNG = os.path.join(SCREENS, 'main_menu_bg.png')
ASE = os.path.join(SCREENS, 'main_menu_bg.aseprite')
FX_PNG = os.path.join(SCREENS, 'main_menu_bg_fx.png')
MASKS_TXT = os.path.join(MM, 'masks_clean.txt')
BG_PY = os.path.join(MM, 'bg.py')
PREVIEWS = os.environ.get(
    'JORDAN_DERIVED_PREVIEWS',
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\jordan_derived')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

sys.dont_write_bytecode = True
sys.path.insert(0, MM)
import pngio                                                     # noqa: E402
import lib                                                       # noqa: E402

REAL_WRITE = pngio.write_png


def _refuse(*a, **k):
    raise RuntimeError('menu_v2.py never lets the menu pipeline write; it writes its own files')


pngio.write_png = _refuse
lib.write_png = _refuse
import bg                                                        # noqa: E402
import fx                                                        # noqa: E402
sys.path.insert(0, os.path.join(ROOT, 'art_source'))
from imgdiff import pixel_diff                                   # noqa: E402
from PIL import Image                                            # noqa: E402

FACTOR = 2.0
ANCHOR = 10
JORDAN = [
    '................##.......',   # 0  the greasy crest, flicking forward
    '.............#####.......',   # 1
    '..........########.......',   # 2
    '.......###########.......',   # 3
    '.......###########.......',   # 4
    '......###########........',   # 5
    '.....############........',   # 6  the rat-tail at the back of his head
    '......###########........',   # 7
    '......###########.#######',   # 8  the collector box, a pixel clear of his head
    '......###########.#RRRRR#',   # 9  its red header
    '......###########.#RRRRR#',   # 10
    '.......##########.#######',   # 11
    '........#########.#ooooo#',   # 12 its window, the plumber figure inside
    '.........########.#ooRoo#',   # 13
    '..........######..#oo#oo#',   # 14 chin
    '...........###....#o###o#',   # 15 the thin neck
    '.......########...#ooooo#',   # 16 narrow sloped shoulders
    '......##########.########',   # 17 his hand under the box, a notch clear of the fitted shoulder
    '......###################',   # 18 the near shoulder in to the skinny tee
    '.....##############......',   # 19
    '....################.....',   # 20
    '...################......',   # 21
    '..#############.###......',   # 22 the stick arm down to his hip, the far arm hanging clear of the tee
    '.###..#########.###......',   # 23 the gap inside the akimbo elbow (sampled: 2x2 on the skinny arm)
    '.###..#########..#.......',   # 24 the far elbow
    '...############..........',   # 25
    '....###########..........',   # 26 the skinny tee, 15px at the chest
    '.....##########..........',   # 27
    '.......########..........',   # 28
    '.......########..........',   # 29 tapering to his 13px waist
    '.......########..........',   # 30
    '.......########..........',   # 31 its hem
    '.......###.###...........',   # 32 stick legs, knock-kneed, a pixel thinner
    '.......#######...........',   # 33
    '.......#######...........',   # 34
    '.......###.###...........',   # 35
    '......####..###..........',   # 36
    '.....#####..####.........',   # 37
    '.....#####..####.........',   # 38
    '.....#####..####.........',   # 39
    '....######.######........',   # 40
    '....#######.######.......',   # 41 a pixel between the sneakers
    '.....#############.......',   # 42
]
PLACE_LINE = "    ('jordan', 10, CX, 10),"


# ---------------------------------------------------------------------------------------- build
def use(mask, anchor):
    """Point bg at a [jordan] mask and anchor, in memory only."""
    assert len(set(len(r) for r in mask)) == 1
    assert set(''.join(mask)) <= set('.#+oRy'), set(''.join(mask))
    bg.MASKS['jordan'] = list(mask)
    bg.PLACE[:] = [(n, k, ax, anchor if n == 'jordan' else a) for (n, k, ax, a) in bg.PLACE]


def image(c):
    im = Image.new('RGBA', (c.w, c.h), (0, 0, 0, 0))
    im.putdata([(lib.DB32[p] + (255,)) if p is not None else (0, 0, 0, 0) for row in c.p for p in row])
    return im


def box_of(mask, anchor):
    ax = [a for (n, k, a, _) in bg.PLACE if n == 'jordan'][0]
    x0, y1 = ax - anchor, bg.feet_y(10)
    return (x0, y1 - len(mask) + 1, x0 + len(mask[0]) - 1, y1)


def outside(a, b, box):
    pa, pb = a.load(), b.load()
    x0, y0, x1, y1 = box
    bad = []
    for y in range(a.height):
        for x in range(a.width):
            if x0 <= x <= x1 and y0 <= y <= y1:
                continue
            p, q = pa[x, y], pb[x, y]
            if p != q and (p[3] or q[3]):
                bad.append((x, y, p, q))
    return bad


def aseprite(args):
    subprocess.run([ASEPRITE, '-b'] + args, check=True, capture_output=True)


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def previews(old, new):
    os.makedirs(PREVIEWS, exist_ok=True)
    gap = 12
    full = Image.new('RGBA', (old.width * 2, old.height * 4 + gap), (10, 10, 12, 255))
    full.paste(up(old, 2), (0, 0))
    full.paste(up(new, 2), (0, old.height * 2 + gap))
    full.save(os.path.join(PREVIEWS, 'v2_menu_bg_before_after_2x.png'))
    box = (bg.CX - 60, 0, bg.CX + 60, 90)
    a, b = up(old.crop(box), 6), up(new.crop(box), 6)
    top = Image.new('RGBA', (a.width * 2 + gap, a.height), (10, 10, 12, 255))
    top.paste(a, (0, 0))
    top.paste(b, (a.width + gap, 0))
    top.save(os.path.join(PREVIEWS, 'v2_menu_summit_before_after_6x.png'))


def newline_of(text):
    return '\r\n' if '\r\n' in text else '\n'


def replace_jordan_block(text):
    """masks_clean.txt with only the [jordan] block's rows replaced, in the file's own line endings."""
    nl = newline_of(text)
    lines = text.split(nl)
    i = lines.index('[jordan]')
    j = i + 1
    while j < len(lines) and not lines[j].startswith('['):
        j += 1
    body = lines[i + 1:j]
    trailing = []
    while body and not body[-1].strip():
        trailing.insert(0, body.pop())
    return nl.join(lines[:i + 1] + JORDAN + trailing + lines[j:])


def parse_masks(text):
    ms, cur = {}, None
    for ln in text.splitlines():
        ln = ln.rstrip()
        if ln.startswith('['):
            cur = ln[1:-1]
            ms[cur] = []
        elif ln.strip() and cur:
            ms[cur].append(ln)
    return ms


def main(ship=False):
    masks_text = open(MASKS_TXT, encoding='utf-8', newline='').read()
    bg_text = open(BG_PY, encoding='utf-8', newline='').read()
    assert bg_text.count(PLACE_LINE) == 1, "bg.py's jordan PLACE is not anchor 10 any more - refusing"
    old_mask = bg.load_masks(MASKS_TXT)['jordan']
    png_sha = hashlib.sha256(open(PNG, 'rb').read()).hexdigest()
    ase_sha = hashlib.sha256(open(ASE, 'rb').read()).hexdigest()
    live = Image.open(PNG).convert('RGBA')
    live_fx = Image.open(FX_PNG).convert('RGBA')

    comp0, _ = fx.build()
    print('baseline: bg.py + masks_clean.txt as they stand vs the live main_menu_bg.png:',
          pixel_diff(image(comp0), live) or 'identical')
    assert pixel_diff(image(comp0), live) is None, 'the live background is not what the pipeline builds - refusing'

    use(JORDAN, ANCHOR)
    comp, frames = fx.build()
    new = image(comp)
    strip = lib.Canvas(bg.W * fx.N, bg.H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * bg.W, 0)
    new_fx = image(strip)

    ob, nb = box_of(old_mask, ANCHOR), box_of(JORDAN, ANCHOR)
    region = (min(ob[0], nb[0]), min(ob[1], nb[1]), max(ob[2], nb[2]), max(ob[3], nb[3]))
    print('live [jordan] %dx%d at x%d..%d y%d..%d; v2 %dx%d at x%d..%d y%d..%d'
          % (len(old_mask[0]), len(old_mask), ob[0], ob[2], ob[1], ob[3],
             len(JORDAN[0]), len(JORDAN), nb[0], nb[2], nb[1], nb[3]))
    print("Jordan's region (both silhouettes' union): x%d..%d y%d..%d" % (region[0], region[2], region[1], region[3]))
    assert nb[1] >= 0, 'the new silhouette leaves the top of the screen'
    bad = outside(new, live, region)
    changed = sum(1 for y in range(new.height) for x in range(new.width) if new.getpixel((x, y)) != live.getpixel((x, y)))
    print('main_menu_bg: %d px changed, %d of them outside the region' % (changed, len(bad)))
    fx_d = pixel_diff(new_fx, live_fx)
    print('main_menu_bg_fx: rebuilt vs live:', fx_d or 'identical (the overlay never touches his region)')
    if bad or fx_d:
        raise SystemExit('refusing: a change outside his region, or the fx overlay moved')

    backup = os.path.join(PREVIEWS, 'before_v2', 'main_menu_bg_live.png')
    previews(Image.open(backup).convert('RGBA') if os.path.exists(backup) else live, new)
    members_c = dict(bg.build()[1])['members']
    members = image(members_c)
    work = os.path.join(PREVIEWS, 'menu_build_v2')
    os.makedirs(work, exist_ok=True)
    png = os.path.join(work, 'main_menu_bg.png')
    lpng = os.path.join(work, 'members_layer.png')
    REAL_WRITE(png, comp.w, comp.h, comp.to_rgba())          # the pipeline's own writer and check
    lib.validate_png(png, bg.W, bg.H)
    REAL_WRITE(lpng, bg.W, bg.H, members_c.to_rgba())
    assert pixel_diff(Image.open(png), new) is None and pixel_diff(Image.open(lpng), members) is None

    ase = os.path.join(work, 'main_menu_bg.aseprite')
    aseprite(['--script-param', 'in=' + ASE, '--script-param', 'layer=members', '--script-param', 'cel=' + lpng,
              '--script-param', 'out=' + ase, '--script', os.path.join(HERE, 'layer_splice.lua')])
    flat = os.path.join(work, 'ase_flat.png')
    aseprite([ase, '--save-as', flat])
    print('main_menu_bg.aseprite flattened vs the new PNG (imgdiff.pixel_diff):', pixel_diff(Image.open(flat), new) or 'identical')
    abad = 1 if pixel_diff(Image.open(flat), new) else 0
    for layer in [n for n, _ in bg.LAYERS]:
        a, b = os.path.join(work, 'old_%s.png' % layer), os.path.join(work, 'new_%s.png' % layer)
        aseprite([ASE, '--layer', layer, '--save-as', a])
        aseprite([ase, '--layer', layer, '--save-as', b])
        if layer == 'members':
            dm = pixel_diff(Image.open(b), members)
            out = outside(Image.open(a).convert('RGBA'), Image.open(b).convert('RGBA'), region)
            print('  layer %-8s new cel vs the rebuilt members layer: %s; changed outside the region: %d px'
                  % (layer, dm or 'identical', len(out)))
            abad += bool(dm) or bool(out)
        else:
            d = pixel_diff(Image.open(a), Image.open(b))
            print('  layer %-8s %s' % (layer, d or 'identical to the live file'))
            abad += bool(d)
    if abad:
        raise SystemExit('.aseprite check failed - refusing')
    if not ship:
        return 0

    # ---- ship: re-read everything right before writing; write each file in one go
    if (open(MASKS_TXT, encoding='utf-8', newline='').read() != masks_text
            or hashlib.sha256(open(PNG, 'rb').read()).hexdigest() != png_sha
            or hashlib.sha256(open(ASE, 'rb').read()).hexdigest() != ase_sha):
        raise SystemExit('masks_clean.txt, main_menu_bg.png or its .aseprite changed while this ran - refusing')
    new_masks = replace_jordan_block(masks_text)
    with open(MASKS_TXT, 'w', encoding='utf-8', newline='') as f:
        f.write(new_masks)
    print('wrote', MASKS_TXT)
    for src, dst in ((png, PNG), (ase, ASE)):
        shutil.copyfile(src, dst)
        with open(src, 'rb') as a, open(dst, 'rb') as b:
            assert a.read() == b.read(), dst
        print('shipped', dst)

    before, after = parse_masks(masks_text), bg.load_masks(MASKS_TXT)
    others = [n for n in before if n != 'jordan']
    print('masks_clean.txt: the other %d entries unchanged: %s; [jordan] is the v2 mask: %s; entry order kept: %s; '
          'line endings kept: %s' % (len(others), all(before[n] == after[n] for n in others), after['jordan'] == JORDAN,
                                     list(before) == list(after),
                                     newline_of(open(MASKS_TXT, encoding='utf-8', newline='').read()) == newline_of(masks_text)))
    print('bg.py untouched:', open(BG_PY, encoding='utf-8', newline='').read() == bg_text)
    r = subprocess.run([sys.executable, '-c', RECHECK], capture_output=True, text=True, cwd=MM,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    print(r.stdout.strip() or r.stderr.strip())
    return 0 if 'identical' in r.stdout else 1


RECHECK = r'''
import sys
sys.dont_write_bytecode = True
import pngio, lib
def _r(*a, **k): raise RuntimeError('no writes')
pngio.write_png = _r; lib.write_png = _r
import bg
sys.path.insert(0, '..')
from imgdiff import pixel_diff
from PIL import Image
comp, _ = bg.build()
im = Image.new('RGBA', (comp.w, comp.h)); im.putdata([(lib.DB32[p] + (255,)) if p else (0, 0, 0, 0) for row in comp.p for p in row])
print('fresh bg.build() from the written files vs the shipped PNG:',
      pixel_diff(im, Image.open(r'%s')) or 'identical')
''' % PNG


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
