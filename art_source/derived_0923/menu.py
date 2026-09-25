"""Matt's silhouette on the main-menu tower (Assets/UI/Screens/main_menu_bg.png), re-derived from his
approved matt.png frame 0 and rebuilt through the menu's own pipeline (art_source/main_menu/bg.py).
The method is Jordan's (art_source/jordan_derived/menu.py); only the [matt] entry changes.

WHAT WAS THERE. [matt] was a 15x29 stand-in - a plain figure, drawn before he had art - on tier 4
(tan), centred on the carpet at CX.

THE MASK. MATT below is frame 0 sampled the way masks_josh.py and jordan_derived/menu_mask.py do it
(raw_mask: 4x4 supersamples per tower pixel, solid at 34% coverage, bottom-anchored so his soles
stand exactly on the tier) at FACTOR, with the empty top row dropped, then hand-cleaned:
  - the crest: the five spikes as sampled, yellow ('y', drawn YL) on each spike's tip core - the
    cells whose supersamples are at least 90% his tip yellow (sample()); at 50% the whole crest
    went yellow and read as a crown, not as five tipped spikes. Of the 14 yellow crest pixels, 10
    are those cores; measure() lists the other four: the centre spike's point, which the 34% rule
    rounds off, put back on top, and three that carry a core one pixel further along its spike.
    The outer-left tip, sampled flat, is pointed like the right one
  - the yellow collar as one 'y' row under the chin, where the sampler finds it
  - the gaps between his hanging arms and his body carried down to the fists (the sampler closed
    the left one two rows early), the fists beside his thighs, the legs symmetric with a pixel
    between the trainers
Everything else is the sampler's. measure() prints how many pixels differ from the raw sample.

THE SCALE. FACTOR 2.75 makes him 27x35: in family with the tower's members (Josh 25x33, Carter
25x31, Jordan 24x43 at the summit), a little bigger than the 25-wide middle of the cast as his
stocky 96 px sprite is, and 3 px inside the carpet's gold edges on each side, so his hanging arms
never touch it. At 2.5 (30x38) he fills the carpet edge to edge; at 3.0 (25x32) he would stand
shorter than Josh (25x33), whose sprite is 80 px to his 96. The upper three spikes keep a pixel
of carpet between them at 2.75.

THE ANCHOR. Column 13 holds sprite x46.75-49.5, where his feet centre (x48), so he stands on CX, the
carpet's centre line, where the stand-in stood (its anchor 7 of a symmetric 15).

    python menu.py            # rebuild in memory, prove it, write previews to the scratchpad
    python menu.py --ship     # ...then write masks_clean.txt, bg.py's anchor, main_menu_bg.png and
                              # main_menu_bg.aseprite, one write each, and check what landed
Runs in its own process: bg.py does `from lib import *` and needs art_source/main_menu/lib.py.
"""
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import k923 as K                                                 # noqa: E402

MM = os.path.join(K.ART, 'main_menu')
SCREENS = os.path.join(K.ASSETS, 'UI', 'Screens')
PNG = os.path.join(SCREENS, 'main_menu_bg.png')
ASE = os.path.join(SCREENS, 'main_menu_bg.aseprite')
FX_PNG = os.path.join(SCREENS, 'main_menu_bg_fx.png')
MASKS_TXT = os.path.join(MM, 'masks_clean.txt')
BG_PY = os.path.join(MM, 'bg.py')
SPRITE = os.path.join(K.ASSETS, 'Characters', 'Matt', 'matt.png')

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
from PIL import Image                                            # noqa: E402

NAME, TIER = 'matt', 4
FACTOR = 2.75
ANCHOR = 13
SS, THRESHOLD = 4, 0.34
TIP_YELLOW = 0.9
YELLOW = {'fff6be', 'f8db66', 'e2b13c', 'ac7c26', '6a4618'}      # his dyed-tip / collar ramp
MATT = [
    '.............y.............',   # 0  the centre spike's point, put back
    '............#y#............',   # 1
    '........##..#y#..##........',   # 2
    '........#y#.#y#.#yy#.......',   # 3  tip cores: the inner pair and the centre
    '........#y#######y#........',   # 4
    '........###########........',   # 5
    '.....##################....',   # 6
    '....yyy##############yy#...',   # 7  the outer pair's tips
    '.....##################....',   # 8
    '......###############......',   # 9  head
    '.......#############.......',   # 10
    '........############.......',   # 11
    '........############.......',   # 12
    '.......#############.......',   # 13
    '.......#############.......',   # 14
    '........###########........',   # 15
    '.........#########.........',   # 16
    '.........#########.........',   # 17
    '....###.###########.####...',   # 18 the shoulders rise either side of the collar
    '...#######yyyyyyyy#######..',   # 19 the yellow collar
    '..#######################..',   # 20
    '..#######################..',   # 21
    '.#########################.',   # 22
    '###########################',   # 23
    '######.#############.######',   # 24 the arms hang clear of the body
    '#####..#############..#####',   # 25
    '######.#############.######',   # 26
    '######.#############.######',   # 27
    '######.#############.######',   # 28
    '######.######.######.######',   # 29 fists beside the thighs
    '......######...######......',   # 30 legs
    '......######...######......',   # 31
    '......######...######......',   # 32
    '.....########.########.....',   # 33 trainers, a pixel apart
    '.....########.########.....',   # 34
]
PLACE_OLD = "    ('matt', 4, CX, 7),\n"
PLACE_NEW = ("    # Matt's mask is his approved matt.png frame 0 (see art_source/derived_0923/menu.py). Anchor\n"
             "    # 13 holds sprite x46.75-49.5, where his feet centre, which keeps him on CX, the carpet's\n"
             "    # centre line, where the stand-in figure stood.\n"
             "    ('matt', 4, CX, 13),\n")


# ---------------------------------------------------------------------------------------- derive
def frame0():
    return Image.open(SPRITE).convert('RGBA').crop((0, 0, 96, 96))


def sample(factor=FACTOR):
    """raw_mask (jordan_derived/menu_mask.py) on frame 0, plus each solid cell's tip-yellow share."""
    im = frame0()
    px = im.load()
    xs = [x for y in range(96) for x in range(96) if px[x, y][3]]
    ys = [y for y in range(96) for x in range(96) if px[x, y][3]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    tw, th = int(round((x1 - x0) / factor)), int(round((y1 - y0) / factor))
    rows, share = [], []
    for ty in range(th):
        r, s = '', []
        for tx in range(tw):
            hit = yel = 0
            for sy in range(SS):
                for sx in range(SS):
                    X = int(x0 + (tx + (sx + 0.5) / SS) * factor)
                    Y = int(y1 - (th - ty) * factor + ((sy + 0.5) / SS) * factor)
                    if 0 <= X < 96 and 0 <= Y < 96 and px[X, Y][3]:
                        hit += 1
                        yel += '%02x%02x%02x' % px[X, Y][:3] in YELLOW
            solid = hit / float(SS * SS) >= THRESHOLD
            r += '#' if solid else '.'
            s.append(yel / float(hit) if solid else 0.0)
        rows.append(r)
        share.append(s)
    return rows, share, x0


def measure():
    raw, share, x0 = sample()
    assert raw[0].strip('.') == '', 'the sampled top row is no longer empty'
    raw, share = raw[1:], share[1:]                              # the empty top row dropped
    raw = ['.' * len(raw[0])] + raw                              # MATT's row 0 is the put-back point
    share = [[0.0] * len(raw[0])] + share
    assert len(raw) == len(MATT) and len(raw[0]) == len(MATT[0]), (len(raw), len(MATT))
    sil = sum(1 for y in range(len(MATT)) for x in range(len(MATT[0])) if (MATT[y][x] != '.') != (raw[y][x] != '.'))
    solid = sum(r.count('#') + r.count('y') for r in MATT)
    tips = [(x, y) for y in range(9) for x in range(len(MATT[0])) if MATT[y][x] == 'y']
    cores = [(x, y) for y in range(9) for x in range(len(MATT[0])) if share[y][x] >= TIP_YELLOW]
    print('raw sample at %.2f: %dx%d (top row empty, dropped); MATT %dx%d, %d solid pixels; silhouette '
          'differs from the raw sample at %d pixels' % (FACTOR, len(raw[0]), len(raw) - 1, len(MATT[0]),
                                                         len(MATT), solid, sil))
    print('crest yellow: %d pixels; the sampled >=%d%% tip-yellow cores: %d, all yellow in MATT: %s; '
          'yellow pixels that are not a core: %s' % (len(tips), int(TIP_YELLOW * 100), len(cores),
                                                     all(MATT[y][x] == 'y' for x, y in cores),
                                                     sorted(set(tips) - set(cores))))
    return sil


# ---------------------------------------------------------------------------------------- build
def use(mask, anchor):
    assert len(set(len(r) for r in mask)) == 1
    assert set(''.join(mask)) <= set('.#+oRy'), set(''.join(mask))
    bg.MASKS[NAME] = list(mask)
    bg.PLACE[:] = [(n, k, ax, anchor if n == NAME else a) for (n, k, ax, a) in bg.PLACE]


def image(c):
    im = Image.new('RGBA', (c.w, c.h), (0, 0, 0, 0))
    im.putdata([(lib.DB32[p] + (255,)) if p is not None else (0, 0, 0, 0) for row in c.p for p in row])
    return im


def box_of(mask, anchor):
    ax = [a for (n, k, a, _) in bg.PLACE if n == NAME][0]
    x0, y1 = ax - anchor, bg.feet_y(TIER)
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


def changed_bbox(a, b):
    pa, pb = a.load(), b.load()
    pts = [(x, y) for y in range(a.height) for x in range(a.width) if pa[x, y] != pb[x, y]]
    if not pts:
        return 0, None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return len(pts), (min(xs), min(ys), max(xs), max(ys))


def sha(path):
    return hashlib.sha256(K.read_bytes(path)).hexdigest()


# ---------------------------------------------------------------------------------------- previews
def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def previews(old, new, region):
    gap = 12
    full = Image.new('RGBA', (old.width * 2, old.height * 4 + gap), (10, 10, 12, 255))
    full.paste(up(old, 2), (0, 0))
    full.paste(up(new, 2), (0, old.height * 2 + gap))
    p1 = K.preview(full, 'menu_matt_bg_before_after_2x.png')
    box = (bg.CX - 60, 100, bg.CX + 60, 235)
    a, b = up(old.crop(box), 6), up(new.crop(box), 6)
    top = Image.new('RGBA', (a.width * 2 + gap, a.height), (10, 10, 12, 255))
    top.paste(a, (0, 0))
    top.paste(b, (a.width + gap, 0))
    p2 = K.preview(top, 'menu_matt_tier4_before_after_6x.png')
    summit = (bg.CX - 110, 0, bg.CX + 110, 240)
    c, d = up(old.crop(summit), 3), up(new.crop(summit), 3)
    s = Image.new('RGBA', (c.width * 2 + gap, c.height), (10, 10, 12, 255))
    s.paste(c, (0, 0))
    s.paste(d, (c.width + gap, 0))
    p3 = K.preview(s, 'menu_matt_summit_before_after_3x.png')
    # the region itself, with the changed pixels flagged, to show nothing moved outside it
    x0, y0, x1, y1 = region
    diff = Image.new('RGBA', old.size, (0, 0, 0, 0))
    po, pn, pd = old.load(), new.load(), diff.load()
    for y in range(old.height):
        for x in range(old.width):
            if po[x, y] != pn[x, y]:
                pd[x, y] = (255, 40, 200, 255)
    m = new.copy()
    m.alpha_composite(Image.new('RGBA', m.size, (0, 0, 0, 150)))
    m.alpha_composite(diff)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(m)
    dr.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], outline=(255, 220, 60, 255))
    p4 = K.preview(up(m, 2), 'menu_matt_changed_pixels_2x.png')
    return p1, p2, p3, p4


# ---------------------------------------------------------------------------------------- ship
def newline_of(text):
    return '\r\n' if '\r\n' in text else '\n'


def replace_block(text):
    """masks_clean.txt with only the [matt] block's rows replaced, in the file's own line endings."""
    nl = newline_of(text)
    lines = text.split(nl)
    i = lines.index('[%s]' % NAME)
    j = i + 1
    while j < len(lines) and not lines[j].startswith('['):
        j += 1
    tail = lines[j:]
    body = lines[i + 1:j]
    trailing = []
    while body and not body[-1].strip():
        trailing.insert(0, body.pop())
    return nl.join(lines[:i + 1] + MATT + trailing + tail)


def main(ship=False):
    measure()
    old_masks_text = open(MASKS_TXT, encoding='utf-8', newline='').read()
    old_bg_text = open(BG_PY, encoding='utf-8', newline='').read()
    old_mask = bg.load_masks(MASKS_TXT)[NAME]
    old_anchor = [a for (n, k, x, a) in bg.PLACE if n == NAME][0]
    live = Image.open(PNG).convert('RGBA')
    live_fx = Image.open(FX_PNG).convert('RGBA')
    png_sha, ase_sha = sha(PNG), sha(ASE)
    shipped_already = (old_mask == MATT and old_anchor == ANCHOR)

    # the pipeline, untouched, must reproduce the live files before anything changes
    comp0, frames0 = fx.build()
    base = image(comp0)
    print('baseline: bg.py + masks_clean.txt as they stand vs the live main_menu_bg.png:',
          K.pixel_diff(base, live) or 'identical')
    assert K.pixel_diff(base, live) is None, 'the live background is not what the pipeline builds - refusing'

    use(MATT, ANCHOR)
    comp, frames = fx.build()
    new = image(comp)
    strip = lib.Canvas(bg.W * fx.N, bg.H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * bg.W, 0)
    new_fx = image(strip)

    ob, nb = box_of(old_mask, old_anchor), box_of(MATT, ANCHOR)
    region = (min(ob[0], nb[0]), min(ob[1], nb[1]), max(ob[2], nb[2]), max(ob[3], nb[3]))
    print('old [matt] %dx%d at x%d..%d y%d..%d, anchor %d; new %dx%d at x%d..%d y%d..%d, anchor %d'
          % (len(old_mask[0]), len(old_mask), ob[0], ob[2], ob[1], ob[3], old_anchor,
             len(MATT[0]), len(MATT), nb[0], nb[2], nb[1], nb[3], ANCHOR))
    print("his region (both silhouettes' union): x%d..%d y%d..%d" % (region[0], region[2], region[1], region[3]))
    # the proof is against the live file (a re-run after the ship finds nothing to change); the
    # pre-change backup, when there is one, is only the 'before' of the previews
    before = os.path.join(K.PREVIEWS, 'before_menu', 'main_menu_bg.png')
    ref = Image.open(before).convert('RGBA') if os.path.exists(before) else live
    bad = outside(new, live, region)
    n, bbox = changed_bbox(live, new)
    print('main_menu_bg vs live: %d px changed%s, %d of them outside his region' %
          (n, (' (bbox x%d..%d y%d..%d)' % (bbox[0], bbox[2], bbox[1], bbox[3])) if bbox else '', len(bad)))
    fx_d = K.pixel_diff(new_fx, live_fx)
    print('main_menu_bg_fx (12-frame overlay): rebuilt vs live:', fx_d or 'identical (the overlay never touches his region)')
    if bad or fx_d:
        raise SystemExit('refusing: a change outside his region, or the fx overlay moved')
    for p in previews(ref, new, region):
        print(p)

    members_c = dict(bg.build()[1])['members']
    members = image(members_c)
    work = os.path.join(K.PREVIEWS, 'menu_build')
    os.makedirs(work, exist_ok=True)
    png = K.refuse_live(os.path.join(work, 'main_menu_bg.png'))
    lpng = K.refuse_live(os.path.join(work, 'members_layer.png'))
    REAL_WRITE(png, comp.w, comp.h, comp.to_rgba())             # the pipeline's own writer and check
    lib.validate_png(png, bg.W, bg.H)
    REAL_WRITE(lpng, bg.W, bg.H, members_c.to_rgba())
    assert K.pixel_diff(Image.open(png), new) is None and K.pixel_diff(Image.open(lpng), members) is None

    ase = K.refuse_live(os.path.join(work, 'main_menu_bg.aseprite'))
    K.aseprite(['--script-param', 'in=' + ASE, '--script-param', 'layer=members', '--script-param', 'cel=' + lpng,
                '--script-param', 'out=' + ase, '--script', os.path.join(HERE, 'layer_splice.lua')])
    flat = os.path.join(work, 'ase_flat.png')
    K.aseprite([ase, '--save-as', flat])
    d = K.pixel_diff(Image.open(flat), new)
    print('main_menu_bg.aseprite, members cel swapped, flattened vs the new PNG (imgdiff.pixel_diff):', d or 'identical')
    abad = 1 if d else 0
    for layer in [nm for nm, _ in bg.LAYERS]:
        a, b = os.path.join(work, 'old_%s.png' % layer), os.path.join(work, 'new_%s.png' % layer)
        K.aseprite([ASE, '--layer', layer, '--save-as', a])
        K.aseprite([ase, '--layer', layer, '--save-as', b])
        dl = K.pixel_diff(Image.open(a), Image.open(b))
        if layer == 'members':
            dm = K.pixel_diff(Image.open(b), members)
            out_n = len(outside(Image.open(a).convert('RGBA'), Image.open(b).convert('RGBA'), region))
            print('  layer %-8s changed; new cel vs the rebuilt members layer: %s; changed outside his region: %d px'
                  % (layer, dm or 'identical', out_n))
            abad += bool(dm) or bool(out_n)
        else:
            print('  layer %-8s %s' % (layer, dl or 'identical to the live file'))
            abad += bool(dl)
    if abad:
        raise SystemExit('.aseprite check failed - refusing')
    if not ship:
        return 0
    if shipped_already:
        print('masks_clean.txt and bg.py already carry this [matt]; nothing to write')
        return 0

    # ---- ship: back up, re-read everything right before writing, one write each
    bdir = os.path.join(K.PREVIEWS, 'before_menu')
    os.makedirs(bdir, exist_ok=True)
    for src, nm in ((MASKS_TXT, 'masks_clean.txt'), (BG_PY, 'bg.py'), (PNG, 'main_menu_bg.png'),
                    (ASE, 'main_menu_bg.aseprite')):
        if not os.path.exists(os.path.join(bdir, nm)):
            shutil.copyfile(src, os.path.join(bdir, nm))
    masks_now = open(MASKS_TXT, encoding='utf-8', newline='').read()
    bg_now = open(BG_PY, encoding='utf-8', newline='').read()
    if masks_now != old_masks_text or bg_now != old_bg_text or sha(PNG) != png_sha or sha(ASE) != ase_sha:
        raise SystemExit('masks_clean.txt, bg.py, main_menu_bg.png or its .aseprite changed while this ran - refusing')
    new_masks = replace_block(masks_now)
    nl = newline_of(bg_now)
    place_old, place_new = PLACE_OLD.replace('\n', nl), PLACE_NEW.replace('\n', nl)
    assert bg_now.count(place_old) == 1, "bg.py's matt PLACE line is not where it was"
    new_bg = bg_now.replace(place_old, place_new)
    assert new_masks.count('\r\n') == new_masks.count('\n') or '\r\n' not in masks_now
    assert new_bg.count('\r\n') == new_bg.count('\n') or '\r\n' not in bg_now
    for path, text in ((MASKS_TXT, new_masks), (BG_PY, new_bg)):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        print('wrote', path)
    for src, dst in ((png, PNG), (ase, ASE)):
        shutil.copyfile(src, dst)
        assert K.read_bytes(src) == K.read_bytes(dst), dst
        print('shipped', dst)

    # ---- what landed
    before_blocks, cur = {}, None
    for ln in old_masks_text.splitlines():
        ln = ln.rstrip()
        if ln.startswith('['):
            cur = ln[1:-1]
            before_blocks[cur] = []
        elif ln.strip() and cur:
            before_blocks[cur].append(ln)
    after = bg.load_masks(MASKS_TXT)
    others = [n for n in before_blocks if n != NAME]
    print('masks_clean.txt: the other %d entries unchanged: %s; [matt] is the new mask: %s; entry order kept: %s'
          % (len(others), all(before_blocks[n] == after[n] for n in others), after[NAME] == MATT,
             list(before_blocks) == list(after)))
    old_lines = bg_now.splitlines()
    new_lines = open(BG_PY, encoding='utf-8', newline='').read().splitlines()
    print('bg.py: only the matt PLACE line changed (%d lines added, the rest untouched): %s'
          % (len(new_lines) - len(old_lines),
             [l for l in old_lines if l not in new_lines] == [PLACE_OLD.rstrip('\n')]
             and [l for l in new_lines if l not in old_lines] == PLACE_NEW.rstrip('\n').split('\n')))
    r = subprocess.run([sys.executable, '-c', RECHECK], capture_output=True, text=True, cwd=MM,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    print(r.stdout.strip() or r.stderr.strip())
    flat2 = os.path.join(work, 'landed_flat.png')
    K.aseprite([ASE, '--save-as', flat2])
    print('landed main_menu_bg.aseprite flattened vs landed PNG (imgdiff.pixel_diff):',
          K.pixel_diff(Image.open(flat2), Image.open(PNG)) or 'identical')
    return 0 if r.stdout.count('identical') == 2 else 1


RECHECK = r'''
import sys
sys.dont_write_bytecode = True
import pngio, lib
def _r(*a, **k): raise RuntimeError('no writes')
pngio.write_png = _r; lib.write_png = _r
import bg, fx
sys.path.insert(0, '..')
from imgdiff import pixel_diff
from PIL import Image
comp, frames = fx.build()
im = Image.new('RGBA', (comp.w, comp.h)); im.putdata([(lib.DB32[p] + (255,)) if p else (0, 0, 0, 0) for row in comp.p for p in row])
st = lib.Canvas(bg.W * fx.N, bg.H)
for i, fr in enumerate(frames):
    st.blit(fr, i * bg.W, 0)
fxim = Image.new('RGBA', (st.w, st.h)); fxim.putdata([(lib.DB32[p] + (255,)) if p else (0, 0, 0, 0) for row in st.p for p in row])
print('fresh bg.build() from the written files vs the shipped PNG:', pixel_diff(im, Image.open(r'%s')) or 'identical',
      '| fresh fx overlay vs main_menu_bg_fx.png:', pixel_diff(fxim, Image.open(r'%s')) or 'identical')
''' % (PNG, FX_PNG)


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
