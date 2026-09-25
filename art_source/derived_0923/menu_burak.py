"""Tier 1 of the main-menu tower (Assets/UI/Screens/main_menu_bg.png): the boss Burak figure (boss 1,
@member), re-derived from his approved boss design, Captain Burak (burak_boss.png frame 0), the way
menu.py derived Matt's. The newcomer at the foot of the carpet is the PLAYER - bg.py's own 'player'
layer (player2.py) - and is not touched; the proof below checks that layer is identical.

WHAT WAS THERE. [burak] was the old headband boxer (17x30, a red 'RRRRR' headband) at CX - 40.

THE MASK. BURAK is frame 0 sampled by menu.py's raw_mask rule (4x4 supersamples per tower pixel, solid
at 34%, bottom-anchored) at Matt's and Computah's FACTOR 2.75 - the cast's 96 px scale - which makes
him 29x35, with accents taken from the same supersamples:
  - 'y' (drawn YL): the tricorn's gold trim - the cells in the hat's rows at least 50% his trim gold,
    which trace it tip, brim V, tip; so the tricorn reads as his, not as a cap
  - 'R' (drawn PK): the red bandana tails, cells at least 50% bandana red (the old figure's red
    headband carried on)
  - 'o' (drawn WH2): the cutlass blade, cells at least 50% steel
and two hand pixels, the tricorn's tip tops: the left one, which the 34% rule rounds off while it
keeps the right one (the sprite's tips mirror each other about x48.5), and both gilded, as the
sprite's gold-edged tips are. The coat, shirt and the coat's own trim stay silhouette, as Matt's
body does. measure() prints the counts.

THE PLACE. His old spot, CX - 40, anchor 14 (sprite x46.5-49.25, where his feet centre): the centre
line stays where the old figure's did; he clears Eric (tier 2, on the carpet) by 4 px and the
carpet's edge by 6.

    python menu_burak.py            # rebuild in memory, prove it, write previews to the scratchpad
    python menu_burak.py --ship     # ...then write masks_clean.txt, bg.py's tier-1 line,
                                    # main_menu_bg.png and main_menu_bg.aseprite, and check
"""
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import menu as M                                                 # the pipeline, its writers stubbed
import k923 as K                                                 # noqa: E402
from PIL import Image, ImageDraw                                 # noqa: E402

bg, fx, lib = M.bg, M.fx, M.lib
PNG, ASE, FX_PNG, MASKS_TXT, BG_PY = M.PNG, M.ASE, M.FX_PNG, M.MASKS_TXT, M.BG_PY
SPRITE = os.path.join(K.ASSETS, 'Characters', 'BurakBoss', 'burak_boss.png')

NAME, TIER = 'burak', 1
FACTOR = 2.75
ANCHOR = 14
X = bg.CX - 40
SHARE = 0.5
CLASSES = {'y': {'fff3b0', 'f5d94e', 'e0ab35', 'b07d22', '7a5216'},       # gold trim
           'R': {'d95763', 'ac3232', '6e1f22'},                            # bandana
           'o': {'fffcf4', 'e8e1d3', 'dce3ee', 'c3b9a9', 'a6afc1'}}        # steel / whites
ZONES = {'y': lambda x, y: y <= 5,                                          # the tricorn's rows
         'R': lambda x, y: 3 <= y <= 8,                                     # the tails
         'o': lambda x, y: 9 <= y <= 17 and x <= 8}                         # the cutlass blade
HAND = {(6, 0): 'y', (23, 0): 'y'}
BURAK = [
    '......y.....######.....y.....',   # 0  the tricorn: its tips and crown
    '......y...##########..y#.....',   # 1
    '......#y##############y......',   # 2
    '.......##yy#######yyy##...#..',   # 3  the gold trim down to the brim's point
    '........###yy###yy####RRRRR#.',   # 4  bandana tails
    '........######y######RRRRR#..',   # 5
    '........##############RR#....',   # 6
    '........##############RRRR#..',   # 7
    '........##############..###..',   # 8
    '##.....###############.......',   # 9  the cutlass raised beside his head
    '##.....###############.......',   # 10
    '#o#....################......',   # 11
    '.o##....##############.......',   # 12
    '.oo#....#############........',   # 13
    '..#o#....###########.........',   # 14
    '...#o#...###########.........',   # 15
    '....#o##..##########.........',   # 16
    '.....#o##############........',   # 17
    '.......###############.......',   # 18 coat
    '......#################......',   # 19
    '......#################......',   # 20
    '......##################.....',   # 21
    '......##################.....',   # 22
    '......##################.....',   # 23
    '......###################....',   # 24
    '.......##################....',   # 25
    '........#################....',   # 26
    '........##################...',   # 27
    '........##############.####..',   # 28 the spyglass hanging from his other hand
    '........##############..####.',   # 29
    '.......###############...####',   # 30
    '.......###############...####',   # 31
    '.......###############...###.',   # 32
    '.........#####..#####.....#..',   # 33 boots
    '.........#####..#####........',   # 34
]
PLACE_OLD = "    ('burak', 1, CX - 40, 8),\n"
PLACE_NEW = ("    # Tier 1's Burak is the boss, Captain Burak (burak_boss.png frame 0, see\n"
             "    # art_source/derived_0923/menu_burak.py); the newcomer at the foot is the player layer.\n"
             "    # Anchor 14 holds sprite x46.5-49.25, where his feet centre, on the old figure's centre line.\n"
             "    ('burak', 1, CX - 40, 14),\n")


# ---------------------------------------------------------------------------------------- derive
def sample(factor=FACTOR):
    px = Image.open(SPRITE).convert('RGBA').crop((0, 0, 96, 96)).load()
    xs = [x for y in range(96) for x in range(96) if px[x, y][3]]
    ys = [y for y in range(96) for x in range(96) if px[x, y][3]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    tw, th = int(round((x1 - x0) / factor)), int(round((y1 - y0) / factor))
    rows = []
    for ty in range(th):
        r = ''
        for tx in range(tw):
            hit = 0
            cnt = {k: 0 for k in CLASSES}
            for sy in range(M.SS):
                for sx in range(M.SS):
                    X_ = int(x0 + (tx + (sx + 0.5) / M.SS) * factor)
                    Y_ = int(y1 - (th - ty) * factor + ((sy + 0.5) / M.SS) * factor)
                    if 0 <= X_ < 96 and 0 <= Y_ < 96 and px[X_, Y_][3]:
                        hit += 1
                        h = '%02x%02x%02x' % px[X_, Y_][:3]
                        for k, v in CLASSES.items():
                            cnt[k] += h in v
            if hit / float(M.SS * M.SS) < M.THRESHOLD:
                r += '.'
                continue
            ch = '#'
            for k in ('y', 'R', 'o'):
                if ZONES[k](tx, ty) and cnt[k] / float(hit) >= SHARE:
                    ch = k
                    break
            r += ch
        rows.append(r)
    return rows, x0


def measure():
    raw, x0 = sample()
    assert len(raw) == len(BURAK) and len(raw[0]) == len(BURAK[0]), (len(raw), len(raw[0]))
    assert int((48 - x0) // FACTOR) == ANCHOR
    derived = [list(r) for r in raw]
    for (x, y), k in HAND.items():
        derived[y][x] = k
    derived = [''.join(r) for r in derived]
    diff = [(x, y) for y in range(len(raw)) for x in range(len(raw[0])) if derived[y][x] != BURAK[y][x]]
    counts = {k: sum(r.count(k) for r in BURAK) for k in 'yRo'}
    solid = sum(len(r) - r.count('.') for r in BURAK)
    print('raw sample at %.2f: %dx%d, anchor column %d; BURAK %d solid pixels: %d gold trim, %d bandana, %d blade'
          % (FACTOR, len(raw[0]), len(raw), ANCHOR, solid, counts['y'], counts['R'], counts['o']))
    print('BURAK is the sample and its accents exactly, plus %d hand pixel(s) %s; other differences: %s'
          % (len(HAND), sorted(HAND), diff or 'none'))
    assert not diff
    return raw


# ---------------------------------------------------------------------------------------- build
def use():
    assert len(set(len(r) for r in BURAK)) == 1
    assert set(''.join(BURAK)) <= set('.#+oRy')
    bg.MASKS[NAME] = list(BURAK)
    bg.PLACE[:] = [(n, k, (X if n == NAME else ax), (ANCHOR if n == NAME else a)) for (n, k, ax, a) in bg.PLACE]


def box(mask, ax, anchor):
    x0, y1 = ax - anchor, bg.feet_y(TIER)
    return (x0, y1 - len(mask) + 1, x0 + len(mask[0]) - 1, y1)


def outside(a, b, boxes):
    pa, pb = a.load(), b.load()
    return [(x, y) for y in range(a.height) for x in range(a.width)
            if pa[x, y] != pb[x, y] and (pa[x, y][3] or pb[x, y][3])
            and not any(q[0] <= x <= q[2] and q[1] <= y <= q[3] for q in boxes)]


def changed(a, b):
    pa, pb = a.load(), b.load()
    return [(x, y) for y in range(a.height) for x in range(a.width) if pa[x, y] != pb[x, y]]


def sha(path):
    return hashlib.sha256(K.read_bytes(path)).hexdigest()


def previews(before, after, boxes):
    up = M.up
    gap = 12
    tower = (bg.CX - 160, 0, bg.CX + 160, 360)
    a, b = up(before.crop(tower), 3), up(after.crop(tower), 3)
    t = Image.new('RGBA', (a.width * 2 + gap, a.height + 20), (10, 10, 12, 255))
    t.paste(a, (0, 20))
    t.paste(b, (a.width + gap, 20))
    d = ImageDraw.Draw(t)
    d.text((6, 4), 'before (live)', fill=(230, 230, 235, 255))
    d.text((a.width + gap + 6, 4), 'after: tier 1 is Captain Burak; the newcomer at the foot unchanged', fill=(230, 230, 235, 255))
    p1 = K.preview(t, 'menu_burak_tower_before_after_3x.png')
    z = (bg.CX - 100, 236, bg.CX + 30, 330)
    c, e = up(before.crop(z), 6), up(after.crop(z), 6)
    zz = Image.new('RGBA', (c.width * 2 + gap, c.height), (10, 10, 12, 255))
    zz.paste(c, (0, 0))
    zz.paste(e, (c.width + gap, 0))
    p2 = K.preview(zz, 'menu_burak_tier1_before_after_6x.png')
    diff = after.copy()
    diff.alpha_composite(Image.new('RGBA', diff.size, (0, 0, 0, 150)))
    pd, pb, pa = diff.load(), before.load(), after.load()
    for y in range(diff.height):
        for x in range(diff.width):
            if pb[x, y] != pa[x, y]:
                pd[x, y] = (255, 40, 200, 255)
    dd = ImageDraw.Draw(diff)
    for q in boxes:
        dd.rectangle([q[0] - 1, q[1] - 1, q[2] + 1, q[3] + 1], outline=(255, 220, 60, 255))
    p3 = K.preview(up(diff, 2), 'menu_burak_changed_pixels_2x.png')
    start = os.path.join(K.PREVIEWS, 'before_menu', 'main_menu_bg.png')
    out = [p1, p2, p3]
    if os.path.exists(start):
        s = up(Image.open(start).convert('RGBA').crop(tower), 3)
        w = Image.new('RGBA', (s.width * 2 + gap, s.height + 20), (10, 10, 12, 255))
        w.paste(s, (0, 20))
        w.paste(b, (s.width + gap, 20))
        dw = ImageDraw.Draw(w)
        dw.text((6, 4), 'session start', fill=(230, 230, 235, 255))
        dw.text((s.width + gap + 6, 4), 'now: Matt (tier 4), Computah alone (tier 3), Captain Burak (tier 1)',
                fill=(230, 230, 235, 255))
        out.append(K.preview(w, 'menu_tower_session_start_vs_now_3x.png'))
    return out


def replace_block(text):
    nl = M.newline_of(text)
    lines = text.split(nl)
    i = lines.index('[%s]' % NAME)
    j = i + 1
    while j < len(lines) and not lines[j].startswith('['):
        j += 1
    tail, body = lines[j:], lines[i + 1:j]
    trailing = []
    while body and not body[-1].strip():
        trailing.insert(0, body.pop())
    return nl.join(lines[:i + 1] + BURAK + trailing + tail)


def main(ship=False):
    measure()
    old_masks_text = open(MASKS_TXT, encoding='utf-8', newline='').read()
    old_bg_text = open(BG_PY, encoding='utf-8', newline='').read()
    masks0 = bg.load_masks(MASKS_TXT)
    place0 = {n: (ax, a) for (n, k, ax, a) in bg.PLACE}
    shipped_already = masks0[NAME] == BURAK and place0[NAME] == (X, ANCHOR)
    live = Image.open(PNG).convert('RGBA')
    live_fx = Image.open(FX_PNG).convert('RGBA')
    png_sha, ase_sha = sha(PNG), sha(ASE)

    comp0, _ = fx.build()
    print('baseline: bg.py + masks_clean.txt as they stand vs the live main_menu_bg.png:',
          K.pixel_diff(M.image(comp0), live) or 'identical')
    assert K.pixel_diff(M.image(comp0), live) is None, 'the live background is not what the pipeline builds - refusing'

    bdir = os.path.join(K.PREVIEWS, 'before_menu_burak')
    before_png, before_masks = os.path.join(bdir, 'main_menu_bg.png'), os.path.join(bdir, 'masks_clean.txt')
    ref = Image.open(before_png).convert('RGBA') if os.path.exists(before_png) else live
    ref_masks = bg.load_masks(before_masks) if os.path.exists(before_masks) else masks0
    boxes = [box(ref_masks[NAME], bg.CX - 40, 8), box(BURAK, X, ANCHOR)]
    for nm, q in zip(('old burak', 'Captain Burak'), boxes):
        print('  %-13s x%d..%d y%d..%d' % (nm, q[0], q[2], q[1], q[3]))

    use()
    comp, frames = fx.build()
    new = M.image(comp)
    strip = lib.Canvas(bg.W * fx.N, bg.H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * bg.W, 0)
    new_fx = M.image(strip)
    ch = changed(live, new)
    bad = outside(live, new, boxes)
    print('main_menu_bg vs live: %d px changed, %d of them outside the two boxes' % (len(ch), len(bad)))
    fx_d = K.pixel_diff(new_fx, live_fx)
    print('main_menu_bg_fx (12-frame overlay): rebuilt vs live:', fx_d or 'identical (the overlay never touches tier 1)')
    if bad or fx_d:
        raise SystemExit('refusing: a change outside tier 1\'s figure, or the fx overlay moved')
    for p in previews(ref, new, boxes):
        print(p)

    members_c = dict(bg.build()[1])['members']
    members = M.image(members_c)
    work = os.path.join(K.PREVIEWS, 'menu_burak_build')
    os.makedirs(work, exist_ok=True)
    png = K.refuse_live(os.path.join(work, 'main_menu_bg.png'))
    lpng = K.refuse_live(os.path.join(work, 'members_layer.png'))
    M.REAL_WRITE(png, comp.w, comp.h, comp.to_rgba())
    lib.validate_png(png, bg.W, bg.H)
    M.REAL_WRITE(lpng, bg.W, bg.H, members_c.to_rgba())
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
            out_n = len(outside(Image.open(a).convert('RGBA'), Image.open(b).convert('RGBA'), boxes))
            print('  layer %-8s changed; new cel vs the rebuilt members layer: %s; changed outside the boxes: %d px'
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
        print('masks_clean.txt and bg.py already carry this tier 1; nothing to write')
        return 0

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
    nl = M.newline_of(bg_now)
    place_old, place_new = PLACE_OLD.replace('\n', nl), PLACE_NEW.replace('\n', nl)
    assert bg_now.count(place_old) == 1, "bg.py's tier-1 PLACE line is not where it was"
    new_bg = bg_now.replace(place_old, place_new)
    for text, orig in ((new_masks, masks_now), (new_bg, bg_now)):
        assert text.count('\r\n') == text.count('\n') or '\r\n' not in orig
    for path, text in ((MASKS_TXT, new_masks), (BG_PY, new_bg)):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        print('wrote', path)
    for src, dst in ((png, PNG), (ase, ASE)):
        shutil.copyfile(src, dst)
        assert K.read_bytes(src) == K.read_bytes(dst), dst
        print('shipped', dst)

    blocks, cur = {}, None
    for ln in old_masks_text.splitlines():
        ln = ln.rstrip()
        if ln.startswith('['):
            cur = ln[1:-1]
            blocks[cur] = []
        elif ln.strip() and cur:
            blocks[cur].append(ln)
    after = bg.load_masks(MASKS_TXT)
    others = [n for n in blocks if n != NAME]
    print('masks_clean.txt: the other %d entries unchanged: %s; [burak] is the new mask: %s; entry order kept: %s'
          % (len(others), all(blocks[n] == after[n] for n in others), after[NAME] == BURAK,
             list(blocks) == list(after)))
    old_lines = bg_now.splitlines()
    new_lines = open(BG_PY, encoding='utf-8', newline='').read().splitlines()
    print('bg.py: only the tier-1 PLACE line changed (with a comment): %s'
          % ([l for l in old_lines if l not in new_lines] == PLACE_OLD.rstrip('\n').split('\n')
             and [l for l in new_lines if l not in old_lines] == PLACE_NEW.rstrip('\n').split('\n')))
    r = subprocess.run([sys.executable, '-c', M.RECHECK], capture_output=True, text=True, cwd=M.MM,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    print(r.stdout.strip() or r.stderr.strip())
    flat2 = os.path.join(work, 'landed_flat.png')
    K.aseprite([ASE, '--save-as', flat2])
    print('landed main_menu_bg.aseprite flattened vs landed PNG (imgdiff.pixel_diff):',
          K.pixel_diff(Image.open(flat2), Image.open(PNG)) or 'identical')
    return 0 if r.stdout.count('identical') == 2 else 1


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
