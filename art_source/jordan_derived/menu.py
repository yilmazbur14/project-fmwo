"""Jordan's silhouette on the main-menu tower (Assets/UI/Screens/main_menu_bg.png), re-derived from the
approved 2026-09-23 redesign and rebuilt through the menu's own pipeline (art_source/main_menu/bg.py).

THE MASK. JORDAN below is hand-cleaned from menu_mask.new_mask(FACTOR) - frame 0 of
jordan_redesign.png sampled the way masks_josh.py samples Josh's - with its empty top row dropped:
  - the quiff kept exactly as sampled: the crest highest at the front, its front a pixel proud of the
    brow; no cap (the old entry's '+' band was the old design's cap)
  - the collector box he holds up beside his face opened a pixel clear of his head down its full
    height (col 16 samples both the head's keyline, x59, and the box's, x60, so it merged), its red
    header as 'R', its window as pale 'o' with the plumber figure inside, red cap and all
  - the hand on his hip: the gap inside the elbow opened to three pixels so the akimbo reads
  - the legs' one-pixel gap carried down to a pixel between the sneakers; the soles touch
Everything else is the sampler's.

THE SCALE. menu_mask.py fits his old entry's scale: 1.6 (IoU 0.873 against the old cleaned mask).
The redesign is 87px from quiff to sole (the old sprite was 61), so at 1.6 he is 54 rows tall; on
tier 10 (feet on y47) his top six rows - the quiff - would be off the top of the screen. FACTOR 2.0
is the scale nearest 1.6 that keeps the whole quiff on screen with sky over it: 24x43 (the old entry
was 17x38), his crest on y5.

THE ANCHOR. Column 10 holds sprite x47-48, where the redesign's body centres (x48), so his centre
line stays on CX = 440, where the previous design stood (old: column 8 of a symmetric 17).

    python menu.py            # rebuild in memory, prove it, write previews to the scratchpad
    python menu.py --ship     # ...then write masks_clean.txt, bg.py's anchor, main_menu_bg.png and
                              # main_menu_bg.aseprite, one write each, and check what landed

Runs in its own process: bg.py does `from lib import *` and needs art_source/main_menu/lib.py, which
the portrait's rig (Josh's lib, via Jordan's kit) would shadow.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

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
    raise RuntimeError('menu.py never lets the menu pipeline write; it writes its own files')


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
    '............####........',   # 0  the quiff's crest, highest at the front
    '..........######........',   # 1
    '......###########.......',   # 2  its front a pixel proud of the brow
    '......###########.......',   # 3
    '......##########........',   # 4
    '.....###########........',   # 5
    '.....###########........',   # 6
    '.....###########.#######',   # 7  the collector box, a pixel clear of his head
    '.....###########.#RRRRR#',   # 8  its red header
    '.....###########.#RRRRR#',   # 9
    '......##########.#######',   # 10
    '......##########.#ooooo#',   # 11 its window, the plumber figure inside
    '.......#########.#ooRoo#',   # 12
    '........#######..#oo#oo#',   # 13
    '........######...#o###o#',   # 14 chin, neck
    '......##########.#ooooo#',   # 15 collar
    '....####################',   # 16 shoulders; his hand under the box
    '...#####################',   # 17
    '...#################....',   # 18
    '..##################....',   # 19
    '.###################....',   # 20
    '.###################....',   # 21
    '####..##############....',   # 22 hand on his hip: the gap inside the elbow
    '#####.#############.....',   # 23
    '.###############.#......',   # 24
    '..###############.......',   # 25
    '...##############.......',   # 26
    '.....############.......',   # 27
    '.....############.......',   # 28
    '.....############.......',   # 29
    '.....############.......',   # 30
    '.....############.......',   # 31
    '.....######.######......',   # 32 legs, the far knee bent
    '.....######.######......',   # 33
    '.....######..#####......',   # 34
    '.....######.######......',   # 35
    '.....######.#####.......',   # 36
    '.....######.#####.......',   # 37
    '.....#####..#####.......',   # 38
    '.....#####..#####.......',   # 39
    '....#####..######.......',   # 40
    '....#######.######......',   # 41 a pixel between the sneakers
    '.....#############......',   # 42
]
PLACE_OLD = "    ('jordan', 10, CX, 8),\n"
PLACE_NEW = ("    # Jordan's mask is the approved 2026-09-23 redesign (jordan_redesign.png frame 0, see\n"
             "    # art_source/jordan_derived/menu.py). Anchor 10 holds sprite x47-48, where the redesign's\n"
             "    # body centres, which keeps his centre line on CX, where the previous design stood.\n"
             "    ('jordan', 10, CX, 10),\n")


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
    """The screen rectangle a [jordan] mask covers on tier 10, inclusive."""
    ax = [a for (n, k, a, _) in bg.PLACE if n == 'jordan'][0]
    x0, y1 = ax - anchor, bg.feet_y(10)
    return (x0, y1 - len(mask) + 1, x0 + len(mask[0]) - 1, y1)


def outside(a, b, box):
    """Pixels that differ between two same-size images outside box (x0, y0, x1, y1), inclusive."""
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


def sha(im):
    return hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()


def aseprite(args):
    subprocess.run([ASEPRITE, '-b'] + args, check=True, capture_output=True)


# ---------------------------------------------------------------------------------------- previews
def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def previews(old, new):
    os.makedirs(PREVIEWS, exist_ok=True)
    gap = 12
    full = Image.new('RGBA', (old.width * 2, old.height * 4 + gap), (10, 10, 12, 255))
    full.paste(up(old, 2), (0, 0))
    full.paste(up(new, 2), (0, old.height * 2 + gap))
    full.save(os.path.join(PREVIEWS, 'menu_bg_before_after_2x.png'))
    box = (bg.CX - 60, 0, bg.CX + 60, 90)
    a, b = up(old.crop(box), 6), up(new.crop(box), 6)
    top = Image.new('RGBA', (a.width * 2 + gap, a.height), (10, 10, 12, 255))
    top.paste(a, (0, 0))
    top.paste(b, (a.width + gap, 0))
    top.save(os.path.join(PREVIEWS, 'menu_summit_before_after_6x.png'))
    return full, top


# ---------------------------------------------------------------------------------------- ship
def newline_of(text):
    """The file's own line ending (masks_clean.txt and bg.py are CRLF), kept on every line written."""
    return '\r\n' if '\r\n' in text else '\n'


def replace_jordan_block(text):
    """masks_clean.txt with only the [jordan] block's rows replaced, in the file's own line endings."""
    nl = newline_of(text)
    lines = text.split(nl)
    i = lines.index('[jordan]')
    j = i + 1
    while j < len(lines) and not lines[j].startswith('['):
        j += 1
    tail = lines[j:]
    body = lines[i + 1:j]
    trailing = []                                  # keep whatever blank lines separated the blocks
    while body and not body[-1].strip():
        trailing.insert(0, body.pop())
    return nl.join(lines[:i + 1] + JORDAN + trailing + tail)


def main(ship=False):
    if ship:
        raise SystemExit('SUPERSEDED: this placed the 09-23 silhouette of the first redesign. Jordan v2 was '
                         'approved 2026-09-24 and his silhouette is now re-derived by menu_v2.py; this script '
                         'refuses to ship.')
    old_masks_text = open(MASKS_TXT, encoding='utf-8', newline='').read()
    old_mask = bg.load_masks(MASKS_TXT)['jordan']
    old_anchor = [a for (n, k, x, a) in bg.PLACE if n == 'jordan'][0]
    live = Image.open(PNG).convert('RGBA')
    live_fx = Image.open(FX_PNG).convert('RGBA')

    # the pipeline, untouched, must still reproduce the live files before anything changes
    comp0, frames0 = fx.build()
    base = image(comp0)
    print('baseline: bg.py as it stands vs the live main_menu_bg.png:', pixel_diff(base, live) or 'identical')
    assert pixel_diff(base, live) is None, 'the live background is not what the pipeline builds - refusing'

    use(JORDAN, ANCHOR)
    comp, frames = fx.build()
    new = image(comp)
    strip = lib.Canvas(bg.W * fx.N, bg.H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * bg.W, 0)
    new_fx = image(strip)

    ob, nb = box_of(old_mask, old_anchor), box_of(JORDAN, ANCHOR)
    region = (min(ob[0], nb[0]), min(ob[1], nb[1]), max(ob[2], nb[2]), max(ob[3], nb[3]))
    print('old [jordan] %dx%d at x%d..%d y%d..%d; new %dx%d at x%d..%d y%d..%d'
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

    # the 'before' of the previews is the pre-change backup when there is one, so a re-run after the
    # ship still shows the change rather than the new background against itself
    backup = os.path.join(PREVIEWS, 'before', 'main_menu_bg_old.png')
    previews(Image.open(backup).convert('RGBA') if os.path.exists(backup) else live, new)
    members_c = dict(bg.build()[1])['members']
    members = image(members_c)
    work = os.path.join(PREVIEWS, 'menu_build')
    os.makedirs(work, exist_ok=True)
    png = os.path.join(work, 'main_menu_bg.png')
    lpng = os.path.join(work, 'members_layer.png')
    REAL_WRITE(png, comp.w, comp.h, comp.to_rgba())          # the pipeline's own writer and check
    lib.validate_png(png, bg.W, bg.H)
    REAL_WRITE(lpng, bg.W, bg.H, members_c.to_rgba())
    assert pixel_diff(Image.open(png), new) is None and pixel_diff(Image.open(lpng), members) is None
    ase_sha = hashlib.sha256(open(ASE, 'rb').read()).hexdigest()

    # the .aseprite: swap the members cel inside the existing file; every other layer stays as it is
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
        d = pixel_diff(Image.open(a), Image.open(b))
        if layer == 'members':
            dm = pixel_diff(Image.open(b), members)
            print('  layer %-8s changed: new cel vs the rebuilt members layer: %s; outside the region: %d px'
                  % (layer, dm or 'identical', len(outside(Image.open(a).convert('RGBA'), Image.open(b).convert('RGBA'), region))))
            abad += bool(dm) or bool(outside(Image.open(a).convert('RGBA'), Image.open(b).convert('RGBA'), region))
        else:
            print('  layer %-8s %s' % (layer, d or 'identical to the live file'))
            abad += bool(d)
    if abad:
        raise SystemExit('.aseprite check failed - refusing')
    if not ship:
        return 0

    # ---- ship: re-read everything right before writing; write each file in one go
    masks_now = open(MASKS_TXT, encoding='utf-8', newline='').read()
    bg_now = open(BG_PY, encoding='utf-8', newline='').read()
    if (masks_now != old_masks_text or pixel_diff(Image.open(PNG), live)
            or hashlib.sha256(open(ASE, 'rb').read()).hexdigest() != ase_sha):
        raise SystemExit('masks_clean.txt, main_menu_bg.png or its .aseprite changed while this ran - refusing')
    new_masks = replace_jordan_block(masks_now)
    nl = newline_of(bg_now)
    place_old, place_new = PLACE_OLD.replace('\n', nl), PLACE_NEW.replace('\n', nl)
    assert bg_now.count(place_old) == 1, "bg.py's jordan PLACE line is not where it was"
    new_bg = bg_now.replace(place_old, place_new)
    assert new_masks.count('\r\n') == new_masks.count('\n') or '\r\n' not in masks_now
    assert new_bg.count('\r\n') == new_bg.count('\n') or '\r\n' not in bg_now
    for path, text in ((MASKS_TXT, new_masks), (BG_PY, new_bg)):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        print('wrote', path)
    for src, dst in ((png, PNG), (ase, ASE)):
        shutil.copyfile(src, dst)
        with open(src, 'rb') as a, open(dst, 'rb') as b:
            assert a.read() == b.read(), dst
        print('shipped', dst)

    # ---- what landed: the other blocks of masks_clean.txt are untouched, and the pipeline, run
    # afresh from the files as written, reproduces the shipped PNG
    before = {}
    cur = None
    for ln in old_masks_text.splitlines():                  # bg.load_masks on the text read at the start
        ln = ln.rstrip()
        if ln.startswith('['):
            cur = ln[1:-1]
            before[cur] = []
        elif ln.strip() and cur:
            before[cur].append(ln)
    after = bg.load_masks(MASKS_TXT)
    others = [n for n in before if n != 'jordan']
    print('masks_clean.txt: the other %d entries unchanged: %s; [jordan] is the new mask: %s; entry order kept: %s'
          % (len(others), all(before[n] == after[n] for n in others), after['jordan'] == JORDAN,
             list(before) == list(after)))
    old_lines = bg_now.splitlines()
    new_lines = open(BG_PY, encoding='utf-8', newline='').read().splitlines()
    print('bg.py: only the jordan PLACE line changed (%d lines added, the rest untouched): %s'
          % (len(new_lines) - len(old_lines),
             [l for l in old_lines if l not in new_lines] == [PLACE_OLD.rstrip('\n')]
             and [l for l in new_lines if l not in old_lines] == PLACE_NEW.rstrip('\n').split('\n')))
    r = subprocess.run([sys.executable, '-c', RECHECK], capture_output=True, text=True, cwd=MM,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    print(r.stdout.strip() or r.stderr.strip())
    return 0 if 'identical' in r.stdout else 1


# A fresh process imports bg from the files as written (writers stubbed) and compares its build with
# the shipped PNG.
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
