"""Tier 3 of the main-menu tower (Assets/UI/Screens/main_menu_bg.png): Computah ALONE, re-derived from
his redesigned computah_idle.png frame 0 the way menu.py derived Matt's, and Greyson's figure gone
(he left the fight on 2026-09-22).

WHAT WAS THERE. [computah] was the old grey thin robot (15x29, a red antenna tip and red eyes) at
CX - 46, and [greyson] (22x32) at CX + 46: the tier's duo.

THE PLACE. One figure, on the right, where Greyson stood (CX + 46). The carpet column is not free:
tier 2 (Eric) and tier 4 (Matt) stand on it, and bg.py's rule is that neighbouring tiers never
share a column - his antenna would stand in Matt's trainers. On the right he balances the tower's
side figures three and three (Burak, Danny, Liam left; Computah, Mason, Bixby right); left, where
the old robot stood, the lower tower would lean left four to two. As drawn, not mirrored: his
antenna leans in over the carpet and the cannon arm weights the tier's outer edge.
The [greyson] mask stays in masks_clean.txt, untouched and unused, as old REMAP entries stay.

THE MASK. COMPUTAH is frame 0 sampled by menu.py's raw_mask rule (4x4 supersamples per tower pixel,
solid at 34%, bottom-anchored) at Matt's FACTOR 2.75 - the two share the cast's 96 px scale - which
makes him 29x33, then hand-cleaned:
  - the antenna as a round bulb on a thin stalk into the dome (sampled, bulb and stalk merge into
    one wedge)
  - the red eyes ('R', drawn PK) on the 2x2 cells whose supersamples are 75-100% eye red; the row
    below them, at 50%, left black so the eyes stay square
  - his visor as a '+' frame (bg's interior line, N0) - the sprite's own visor keyline, y26..41 -
    with the grille's white dots ('o', WH2) on its row
  - the cannon arm's keyline against his chest as a '+' line, down to where the sprite really opens
    a gap between them (y72), which the sampler keeps
  - the ear pods' lower edge made symmetric
measure() prints how many pixels differ from the raw sample.

THE KEYLINE. His sprite's keyline is #0C111A, not black - measure() prints its share. The tower
draws every member in its own K with the tier's rim light, so it does not carry into the mask.

    python menu_computah.py            # rebuild in memory, prove it, write previews to the scratchpad
    python menu_computah.py --ship     # ...then write masks_clean.txt, bg.py's tier-3 line,
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
SPRITE = os.path.join(K.ASSETS, 'Characters', 'Computah', 'computah_idle.png')

NAME, GONE, TIER = 'computah', 'greyson', 3
FACTOR = 2.75
ANCHOR = 13
X = bg.CX + 46
KEYLINE = (12, 17, 26)                                           # #0C111A
RED = {'ff4436', '93302c'}
EYE_RED = 0.75
COMPUTAH = [
    '...##........................',   # 0  the antenna's bulb
    '..####.......................',   # 1
    '..####.......................',   # 2
    '...####......................',   # 3  the stalk leaves the bulb's lower right
    '.....##.....####.............',   # 4  stalk; the dome's crown
    '......############...........',   # 5
    '......#############..........',   # 6
    '......#++++++++++++#.........',   # 7  the visor's top edge
    '.....##+#RR####RR#+##........',   # 8  red eyes
    '.....##+#RR####RR#+##........',   # 9
    '....###+##########+####......',   # 10 ear pods either side
    '....###+#o#o##o#o#+####......',   # 11 the grille's dots
    '....###+##########+####......',   # 12
    '....###++++++++++++####......',   # 13 the visor's bottom edge
    '.....#################.......',   # 14
    '.........########............',   # 15 chin plate, neck
    '..........######..###........',   # 16
    '..######..############.......',   # 17 shoulders
    '..##############++####.......',   # 18 the cannon arm's keyline against his chest
    '..###############+#######....',   # 19
    '..###############++#######...',   # 20
    '.#################+########..',   # 21
    '.#################+########..',   # 22
    '.#####.###########+##########',   # 23 the robot arm hangs clear
    '#####..###########++#########',   # 24
    '#####..############.#########',   # 25 the cannon opens from his side
    '####...#############.########',   # 26
    '####...#############...######',   # 27
    '####...#####..######...######',   # 28 the muzzle beside his hip
    '......#######.######....####.',   # 29 legs
    '......#######.#######........',   # 30
    '......#######.#######........',   # 31
    '......#######.#######........',   # 32
]
PLACE_OLD = "    ('computah', 3, CX - 46, 7),\n    ('greyson', 3, CX + 46, 11),\n"
PLACE_NEW = ("    # Tier 3 is Computah alone: Greyson left the fight on 2026-09-22. His mask is the redesigned\n"
             "    # robot (computah_idle.png frame 0, see art_source/derived_0923/menu_computah.py), standing\n"
             "    # where Greyson stood; anchor 13 holds sprite x46.75-49.5, where his feet centre.\n"
             "    ('computah', 3, CX + 46, 13),\n")


# ---------------------------------------------------------------------------------------- derive
def frame0():
    return Image.open(SPRITE).convert('RGBA').crop((0, 0, 96, 96))


def sample(factor=FACTOR):
    """menu.sample's rule on his frame 0, with each solid cell's eye-red share."""
    px = frame0().load()
    xs = [x for y in range(96) for x in range(96) if px[x, y][3]]
    ys = [y for y in range(96) for x in range(96) if px[x, y][3]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    tw, th = int(round((x1 - x0) / factor)), int(round((y1 - y0) / factor))
    rows, share = [], []
    for ty in range(th):
        r, s = '', []
        for tx in range(tw):
            hit = red = 0
            for sy in range(M.SS):
                for sx in range(M.SS):
                    X_ = int(x0 + (tx + (sx + 0.5) / M.SS) * factor)
                    Y_ = int(y1 - (th - ty) * factor + ((sy + 0.5) / M.SS) * factor)
                    if 0 <= X_ < 96 and 0 <= Y_ < 96 and px[X_, Y_][3]:
                        hit += 1
                        red += '%02x%02x%02x' % px[X_, Y_][:3] in RED
            solid = hit / float(M.SS * M.SS) >= M.THRESHOLD
            r += '#' if solid else '.'
            s.append(red / float(hit) if solid else 0.0)
        rows.append(r)
        share.append(s)
    return rows, share, x0


def measure():
    im = frame0()
    sheet = Image.open(SPRITE).convert('RGBA')
    f0, sh, bl = K.stats(im, key=KEYLINE), K.stats(sheet, key=KEYLINE), K.stats(im)
    print('computah_idle.png keyline #0C111A: %.1f%% of frame 0 (%d of %d px), %.1f%% of the sheet; pure black %.1f%%'
          % (100 * f0['key'], f0['key_px'], f0['opaque'], 100 * sh['key'], 100 * bl['key']))
    raw, share, x0 = sample()
    assert len(raw) == len(COMPUTAH) and len(raw[0]) == len(COMPUTAH[0]), (len(raw), len(raw[0]))
    assert int((48 - x0) // FACTOR) == ANCHOR
    sil = sum(1 for y in range(len(raw)) for x in range(len(raw[0])) if (raw[y][x] != '.') != (COMPUTAH[y][x] != '.'))
    solid = sum(len(r) - r.count('.') for r in COMPUTAH)
    eyes = {(x, y) for y in range(len(raw)) for x in range(len(raw[0])) if COMPUTAH[y][x] == 'R'}
    cores = {(x, y) for y in range(len(raw)) for x in range(len(raw[0])) if share[y][x] >= EYE_RED}
    print('raw sample at %.2f: %dx%d, anchor column %d; COMPUTAH %dx%d, %d solid pixels; silhouette differs from '
          'the raw sample at %d pixels' % (FACTOR, len(raw[0]), len(raw), ANCHOR, len(COMPUTAH[0]), len(COMPUTAH),
                                           solid, sil))
    print('red eyes: %d pixels, exactly the >=%d%% eye-red cells: %s' % (len(eyes), int(EYE_RED * 100), eyes == cores))
    return sil


# ---------------------------------------------------------------------------------------- build
def use():
    assert len(set(len(r) for r in COMPUTAH)) == 1
    assert set(''.join(COMPUTAH)) <= set('.#+oRy')
    bg.MASKS[NAME] = list(COMPUTAH)
    bg.PLACE[:] = [p for p in bg.PLACE if p[0] != GONE]
    bg.PLACE[:] = [(n, k, (X if n == NAME else ax), (ANCHOR if n == NAME else a)) for (n, k, ax, a) in bg.PLACE]


def box(mask, ax, anchor):
    x0, y1 = ax - anchor, bg.feet_y(TIER)
    return (x0, y1 - len(mask) + 1, x0 + len(mask[0]) - 1, y1)


def in_any(x, y, boxes):
    return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes)


def outside(a, b, boxes):
    pa, pb = a.load(), b.load()
    return [(x, y) for y in range(a.height) for x in range(a.width)
            if pa[x, y] != pb[x, y] and (pa[x, y][3] or pb[x, y][3]) and not in_any(x, y, boxes)]


def changed(a, b):
    pa, pb = a.load(), b.load()
    return [(x, y) for y in range(a.height) for x in range(a.width) if pa[x, y] != pb[x, y]]


def sha(path):
    return hashlib.sha256(K.read_bytes(path)).hexdigest()


# ---------------------------------------------------------------------------------------- previews
def previews(before, after, boxes, start=None):
    up = M.up
    gap = 12
    tower = (bg.CX - 160, 0, bg.CX + 160, 330)
    a, b = up(before.crop(tower), 3), up(after.crop(tower), 3)
    t = Image.new('RGBA', (a.width * 2 + gap, a.height + 20), (10, 10, 12, 255))
    t.paste(a, (0, 20))
    t.paste(b, (a.width + gap, 20))
    d = ImageDraw.Draw(t)
    d.text((6, 4), 'before (live, Matt already shipped)', fill=(230, 230, 235, 255))
    d.text((a.width + gap + 6, 4), 'after: tier 3 is Computah alone', fill=(230, 230, 235, 255))
    p1 = K.preview(t, 'menu_computah_tower_before_after_3x.png')
    z = (bg.CX - 75, 180, bg.CX + 75, 262)
    c, e = up(before.crop(z), 6), up(after.crop(z), 6)
    zz = Image.new('RGBA', (c.width * 2 + gap, c.height), (10, 10, 12, 255))
    zz.paste(c, (0, 0))
    zz.paste(e, (c.width + gap, 0))
    p2 = K.preview(zz, 'menu_computah_tier3_before_after_6x.png')
    diff = after.copy()
    diff.alpha_composite(Image.new('RGBA', diff.size, (0, 0, 0, 150)))
    pd, pb, pa = diff.load(), before.load(), after.load()
    for y in range(diff.height):
        for x in range(diff.width):
            if pb[x, y] != pa[x, y]:
                pd[x, y] = (255, 40, 200, 255)
    dd = ImageDraw.Draw(diff)
    for bx in boxes:
        dd.rectangle([bx[0] - 1, bx[1] - 1, bx[2] + 1, bx[3] + 1], outline=(255, 220, 60, 255))
    p3 = K.preview(up(diff, 2), 'menu_computah_changed_pixels_2x.png')
    out = [p1, p2, p3]
    if start is not None:
        s = up(start.crop(tower), 3)
        w = Image.new('RGBA', (s.width * 2 + gap, s.height + 20), (10, 10, 12, 255))
        w.paste(s, (0, 20))
        w.paste(b, (s.width + gap, 20))
        dw = ImageDraw.Draw(w)
        dw.text((6, 4), 'session start (before Matt and Computah)', fill=(230, 230, 235, 255))
        dw.text((s.width + gap + 6, 4), 'now', fill=(230, 230, 235, 255))
        out.append(K.preview(w, 'menu_tower_session_start_vs_now_3x.png'))
    return out


# ---------------------------------------------------------------------------------------- ship
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
    return nl.join(lines[:i + 1] + COMPUTAH + trailing + tail)


def main(ship=False):
    measure()
    old_masks_text = open(MASKS_TXT, encoding='utf-8', newline='').read()
    old_bg_text = open(BG_PY, encoding='utf-8', newline='').read()
    masks0 = bg.load_masks(MASKS_TXT)
    place0 = {n: (ax, a) for (n, k, ax, a) in bg.PLACE}
    shipped_already = (masks0[NAME] == COMPUTAH and GONE not in place0 and place0[NAME] == (X, ANCHOR))
    live = Image.open(PNG).convert('RGBA')
    live_fx = Image.open(FX_PNG).convert('RGBA')
    png_sha, ase_sha = sha(PNG), sha(ASE)

    comp0, _ = fx.build()
    print('baseline: bg.py + masks_clean.txt as they stand vs the live main_menu_bg.png:',
          K.pixel_diff(M.image(comp0), live) or 'identical')
    assert K.pixel_diff(M.image(comp0), live) is None, 'the live background is not what the pipeline builds - refusing'

    bdir = os.path.join(K.PREVIEWS, 'before_menu_computah')
    before_png = os.path.join(bdir, 'main_menu_bg.png')
    before_masks = os.path.join(bdir, 'masks_clean.txt')
    ref = Image.open(before_png).convert('RGBA') if os.path.exists(before_png) else live
    ref_masks = bg.load_masks(before_masks) if os.path.exists(before_masks) else masks0
    boxes = [box(ref_masks[NAME], bg.CX - 46, 7), box(ref_masks[GONE], bg.CX + 46, 11), box(COMPUTAH, X, ANCHOR)]
    for nm, bx in zip(('old computah', 'old greyson', 'new computah'), boxes):
        print('  %-13s x%d..%d y%d..%d' % (nm, bx[0], bx[2], bx[1], bx[3]))

    use()
    comp, frames = fx.build()
    new = M.image(comp)
    strip = lib.Canvas(bg.W * fx.N, bg.H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * bg.W, 0)
    new_fx = M.image(strip)
    ch = changed(live, new)                                      # proved against the live file;
    bad = outside(live, new, boxes)                              # the backup only feeds the previews
    print('main_menu_bg vs live: %d px changed, %d of them outside those three boxes' % (len(ch), len(bad)))
    fx_d = K.pixel_diff(new_fx, live_fx)
    print('main_menu_bg_fx (12-frame overlay): rebuilt vs live:', fx_d or 'identical (the overlay never touches tier 3)')
    if bad or fx_d:
        raise SystemExit('refusing: a change outside the tier-3 figures, or the fx overlay moved')
    start = os.path.join(K.PREVIEWS, 'before_menu', 'main_menu_bg.png')
    for p in previews(ref, new, boxes, Image.open(start).convert('RGBA') if os.path.exists(start) else None):
        print(p)

    members_c = dict(bg.build()[1])['members']
    members = M.image(members_c)
    work = os.path.join(K.PREVIEWS, 'menu_computah_build')
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
        print('masks_clean.txt and bg.py already carry this tier 3; nothing to write')
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
    assert bg_now.count(place_old) == 1, "bg.py's tier-3 PLACE lines are not where they were"
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
    print('masks_clean.txt: the other %d entries unchanged (%s kept, unused): %s; [computah] is the new mask: %s; '
          'entry order kept: %s' % (len(others), GONE, all(blocks[n] == after[n] for n in others),
                                   after[NAME] == COMPUTAH, list(blocks) == list(after)))
    old_lines = bg_now.splitlines()
    new_lines = open(BG_PY, encoding='utf-8', newline='').read().splitlines()
    print('bg.py: only the two tier-3 PLACE lines changed (replaced by one, with a comment): %s'
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
