"""APPROVAL PASS (2026-09-28): Eric's SWORD-LESS bear-hug charge, for Jordan's attack 3. Nothing ships.

In attack 3 Eric plunges his sword into Josh's portal and it stays there, but his bear-hug charge
(eric_bearhug_v2 f1-f2, the hug_charge anim) is drawn standing beside his planted sword. This makes the
two charge frames without it, off the shipped take-B twin:

  - the planted sword is exactly the prop sheet Assets/Characters/Eric/eric_bearhug_planted_sword_v2.png
    (drawn in his frame space: all 2016 of its pixels are identical in both charge frames), so its
    pixels, dirt included, are what is taken out - and nothing else changes;
  - where the sword stood in front of his aura, the aura is continued behind it: the aura's own
    right side, mirrored across his body's axis (x2 = 253 on f1, 255 on f2, measured off the rows
    where both sides show), keeps only what joins the aura still there, and closes with the twin's
    black keyline. The rest of the sword's footprint becomes air.
  - the result is take-B keys only, no semi-alpha; every pixel outside the sword's footprint is the
    twin's own. The BACK points are the twin's for those frames.

Reads, never writes: the shipped twin (Assets/Characters/Jordan/Puppets/eric/eric_bearhug_v2.png),
the prop sheet, the hooks table, and for the in-context still the puppeteer's take-B sword portal
strips (art_source/jordan_puppeteer/portals/takeB/) and staging (jp_staging, imported read-only).
Writes only into this folder, and only with --write (an audit hook refuses anything else; the only
program it may start is Aseprite, on files in here):

    python jp_portal_charge.py            # print this; writes nothing
    python jp_portal_charge.py --check    # build and audit; writes nothing
    python jp_portal_charge.py --write    # the sheet (.png + .aseprite), previews, compare, still, notes

When approved it ships as Assets/Characters/Jordan/Puppets/eric/eric_portal_charge.png (+ .aseprite),
2 frames of 256x192 on eric_bearhug_v2's layout and feet (128, 191), with its BACK line in the table.
"""
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PUPS = os.path.dirname(HERE)
ART = os.path.dirname(PUPS)
ROOT = os.path.dirname(ART)
TWIN = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'Puppets', 'eric', 'eric_bearhug_v2.png')
PROP = os.path.join(ROOT, 'Assets', 'Characters', 'Eric', 'eric_bearhug_planted_sword_v2.png')
HOOKS = os.path.join(ROOT, 'Scripts', 'JordanPuppetHooks.gd')
PORTALS = os.path.join(ART, 'jordan_puppeteer', 'portals')
STAGING = os.path.join(ART, 'jordan_puppeteer', 'staging')
FW, FH = 256, 192
FRAMES = (1, 2)                      # eric_bearhug_v2's hug_charge
AXIS2 = {1: 253, 2: 255}             # the aura's mirror: x' = AXIS2 - x
XMIN = 60                            # the aura never reached further left than this behind the blade
NAME = 'eric_portal_charge'
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

# ------------------------------------------------------------------ the guard (as in ../concepts)


def _real(p):
    return os.path.normcase(os.path.realpath(os.fspath(p)))


def _inside(p, root):
    rp, r = _real(p), _real(root)
    return rp == r or rp.startswith(r + os.sep)


def _split_cmdline(s):
    out, cur, quoted = [], '', False
    for ch in s:
        if ch == '"':
            quoted = not quoted
        elif ch == ' ' and not quoted:
            if cur:
                out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def install_guard(write_root):
    ase = _real(ASEPRITE)

    def is_path(a):
        return isinstance(a, (str, bytes, os.PathLike))

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and
                       flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
            if writing and (write_root is None or not _inside(path, write_root)):
                raise PermissionError('portal_charge guard: refusing to write %s' % (path,))
        elif event in ('os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir',
                       'os.truncate', 'os.chmod', 'os.symlink', 'os.link', 'shutil.copyfile',
                       'shutil.copytree', 'shutil.move', 'shutil.rmtree'):
            for a in args:
                if is_path(a) and (write_root is None or not _inside(a, write_root)):
                    raise PermissionError('portal_charge guard: refusing %s on %s' % (event, a))
        elif event in ('os.system', 'os.exec', 'os.spawn', 'os.startfile', 'os.posix_spawn'):
            raise PermissionError('portal_charge guard: refusing %s' % event)
        elif event == 'subprocess.Popen':
            if write_root is None:
                raise PermissionError('portal_charge guard: --check launches nothing')
            argv = args[1]
            if isinstance(argv, bytes):
                argv = argv.decode()
            argv = _split_cmdline(argv) if isinstance(argv, str) else [os.fspath(a) for a in argv]
            if not argv or _real(argv[0]) != ase:
                raise PermissionError('portal_charge guard: only Aseprite may run, not %s' % (argv[:1],))
            for a in argv[1:]:
                if is_path(a) and str(a).lower().endswith(('.png', '.aseprite')) and not _inside(a, write_root):
                    raise PermissionError('portal_charge guard: Aseprite may only touch files in here, not %s' % a)

    sys.addaudithook(hook)


# ------------------------------------------------------------------ loading (after the guard)

np = Image = ImageDraw = ImageFont = PAL = C = pixel_diff = ST = None


def load():
    """What build() needs (the ship rig, jp_ship, calls this and build() to rebuild the sheet)."""
    global np, Image, ImageDraw, ImageFont, PAL, C, pixel_diff
    if PUPS not in sys.path:
        sys.path.insert(0, PUPS)
    import numpy as np  # noqa: E402
    from PIL import Image, ImageDraw, ImageFont  # noqa: E402
    import jp_palette as PAL  # noqa: E402
    import jp_core as C  # noqa: E402
    from imgdiff import pixel_diff  # noqa: E402


def load_staging():
    """Only the in-context still needs the puppeteer's staging (the void, the god, the strings)."""
    global ST
    sys.path.insert(0, STAGING)
    import jp_staging as ST  # noqa: E402  (read-only)


def font(size, bold=False):
    try:
        return ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts',
                                               'consolab.ttf' if bold else 'consola.ttf'), size)
    except OSError:
        return ImageFont.load_default()


# ------------------------------------------------------------------ the frames

AURA = ('G1', 'G2')
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def palette():
    return {k: tuple(v[:3]) for k, v in PAL.colours('B').items() if k not in PAL.ALIASES}


def keys_of(fr):
    rgb2key = {v: k for k, v in palette().items()}
    k = np.full(fr.shape[:2], '', dtype='<U2')
    for y, x in zip(*np.nonzero(fr[..., 3])):
        k[y, x] = rgb2key[tuple(int(c) for c in fr[y, x, :3])]
    return k


def image_of(keys):
    a = np.zeros(keys.shape + (4,), np.uint8)
    for key, rgb in palette().items():
        a[keys == key] = rgb + (255,)
    return Image.fromarray(a, 'RGBA')


def n8():
    return [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def without_sword(f, twin, prop):
    """(twin keys, new keys) for twin frame f with the sword taken out and the aura carried on behind it."""
    fr = twin[:, f * FW:(f + 1) * FW]
    k = keys_of(fr)
    H, W = k.shape
    out = k.copy()
    out[prop] = ''
    A = AXIS2[f]
    cand = {}
    for y, x in zip(*np.nonzero(prop)):
        if x < XMIN:
            continue
        m = A - x
        if not 0 <= m < W:
            continue
        key = k[y, m]
        if key in AURA:
            cand[(x, y)] = key
        elif key == 'K' and any(0 <= m + dx < W and 0 <= y + dy < H and k[y + dy, m + dx] in AURA for dx, dy in n8()):
            cand[(x, y)] = 'K'
    # only what joins the aura that is still there
    seed = [(x, y) for (x, y) in cand if any(0 <= x + dx < W and 0 <= y + dy < H and not prop[y + dy, x + dx]
                                             and out[y + dy, x + dx] in AURA for dx, dy in n8())]
    keep, stack = set(seed), list(seed)
    while stack:
        x, y = stack.pop()
        for dx, dy in n8():
            q = (x + dx, y + dy)
            if q in cand and q not in keep:
                keep.add(q)
                stack.append(q)
    for (x, y) in keep:
        out[y, x] = cand[(x, y)]
    # the keyline: a new aura pixel on the edge turns black; an old aura pixel left on the edge by the
    # sword's going gets a black pixel beside it, inside the sword's footprint (so nothing outside changes)
    changed = True
    while changed:
        changed = False
        for y, x in zip(*np.nonzero(prop & np.isin(out, AURA))):
            if any(not (0 <= x + dx < W and 0 <= y + dy < H) or out[y + dy, x + dx] == '' for dx, dy in N4):
                out[y, x] = 'K'
                changed = True
    for y, x in zip(*np.nonzero((~prop) & np.isin(out, AURA))):
        for dx, dy in N4:
            u, v = x + dx, y + dy
            if 0 <= u < W and 0 <= v < H and prop[v, u] and out[v, u] == '':
                out[v, u] = 'K'
    for y, x in zip(*np.nonzero(prop & (out == 'K'))):
        if not any(0 <= x + dx < W and 0 <= y + dy < H and out[y + dy, x + dx] in AURA for dx, dy in n8()):
            out[y, x] = ''
    return k, out


def lint_keys(keys, fx=()):
    wk = C.Work(*keys.shape)
    wk.key = keys.copy()
    return C.lint(wk, fx=set(fx))


def back_points():
    """The twin's BACK points on eric_bearhug_v2 frames 1-2, out of the shipped hooks table."""
    text = open(HOOKS, encoding='utf-8').read()
    m = re.search(r'&"eric_bearhug_v2": \[(.*)\],', text)
    pts = re.findall(r'Vector2\((\d+), (\d+)\)|null', m.group(1))
    allp = [None if a == '' else (int(a), int(b)) for a, b in pts]
    return [allp[f] for f in FRAMES]


def build():
    twin = np.array(Image.open(TWIN).convert('RGBA'))
    prop = np.array(Image.open(PROP).convert('RGBA'))
    src = np.array(Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'Eric', 'eric_bearhug_v2.png')).convert('RGBA'))
    mask = prop[..., 3] > 0
    problems, frames, info = [], [], {'frames': []}
    for f in FRAMES:
        sf = src[:, f * FW:(f + 1) * FW]
        same = ((sf == prop).all(-1) & mask).sum()
        if same != mask.sum():
            problems.append('f%d: the prop is not exactly the sword in the source (%d of %d)' % (f, same, mask.sum()))
        k, out = without_sword(f, twin, mask)
        changed = k != out
        if (changed & ~mask).any():
            problems.append('f%d: %d pixel(s) changed outside the sword' % (f, int((changed & ~mask).sum())))
        # the audit: the palette, no semi-alpha, and no keyline gap, speck or pinhole the twin did not have
        before, after = lint_keys(k), lint_keys(out)
        for kind in ('gaps', 'lone', 'holes', 'bad_keys'):
            new = [p for p in after[kind] if p not in before[kind]]
            if new:
                problems.append('f%d: %d new %s %s' % (f, len(new), kind, new[:4]))
        im = image_of(out)
        a = np.array(im)
        if ((a[..., 3] > 0) & (a[..., 3] < 255)).any():
            problems.append('f%d: semi-alpha' % f)
        frames.append((k, out, im))
        filled = int((mask & (out != '')).sum())
        info['frames'].append({'source_frame': f, 'sword_pixels_removed': int(mask.sum()),
                               'aura_carried_on_behind_it': int((mask & np.isin(out, AURA)).sum()),
                               'keyline_added': int((mask & (out == 'K')).sum()), 'pixels_changed': int(changed.sum()),
                               'drawn_in_the_footprint': filled, 'mirror_axis_x2': AXIS2[f]})
    sheet = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, (_k, _o, im) in enumerate(frames):
        sheet.alpha_composite(im, (i * FW, 0))
    pal = set(palette().values())
    cols = {tuple(c) for c in np.array(sheet)[np.array(sheet)[..., 3] > 0][:, :3].tolist()}
    if cols - pal:
        problems.append('%d colour(s) off the take-B palette' % len(cols - pal))
    info['back'] = back_points()
    info['feet'] = [128, 191]
    info['frame_size'] = [FW, FH]
    return sheet, frames, mask, info, problems


# ------------------------------------------------------------------ previews

BG = (46, 49, 58, 255)
PANEL = (20, 18, 26, 255)
WHITE = (236, 233, 244, 255)
DIM = (150, 146, 170, 255)
MAG = (255, 60, 220, 255)
CYAN = (90, 230, 255, 255)


def up(im, s, box=None):
    im = im.crop(box) if box else im
    base = Image.new('RGBA', im.size, BG)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def union_box(ims, pad=3):
    box = None
    for im in ims:
        b = im.getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return (max(0, box[0] - pad), max(0, box[1] - pad), min(FW, box[2] + pad), min(FH, box[3] + pad))


def preview(frames, s, back):
    ims = [f[2] for f in frames]
    box = union_box(ims)
    tiles = []
    for i, im in enumerate(ims):
        big = up(im, s, box)
        d = ImageDraw.Draw(big)
        bx, by = back[i]
        cx, cy = (bx - box[0] + 0.5) * s, (by - box[1] + 0.5) * s
        r = max(6, int(2.6 * s))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=MAG, width=2)
        lab = 'f%d  (eric_bearhug_v2 f%d without the sword)   BACK %s' % (i, FRAMES[i], list(back[i]))
        tw = int(ImageDraw.Draw(Image.new('RGBA', (4, 4))).textlength(lab, font=font(15, True))) + 12
        t = Image.new('RGBA', (max(big.width, tw), big.height + 26), PANEL)
        t.alpha_composite(big, (0, 26))
        ImageDraw.Draw(t).text((4, 4), lab, fill=WHITE, font=font(15, True))
        tiles.append(t)
    W = sum(t.width for t in tiles) + 10 * (len(tiles) - 1)
    out = Image.new('RGBA', (W, max(t.height for t in tiles) + 30), PANEL)
    ImageDraw.Draw(out).text((4, 6), '%s at %dx, take B (magenta: the BACK point, behind the body)' % (NAME, s),
                             fill=WHITE, font=font(16, True))
    x = 0
    for t in tiles:
        out.alpha_composite(t, (x, 30))
        x += t.width + 10
    return out


def compare(frames, twin_img, mask, s=4):
    rows = []
    for i, (k, out, im) in enumerate(frames):
        f = FRAMES[i]
        tw = twin_img.crop((f * FW, 0, (f + 1) * FW, FH))
        box = union_box([tw, im])
        changed = (k != out)
        panels = []
        for img, lab, boxed in ((tw, 'the shipped twin, eric_bearhug_v2 f%d' % f, False),
                                (im, 'without the sword', False),
                                (im, 'changed: magenta taken out, cyan drawn', True)):
            big = up(img, s, box)
            if boxed:
                # magenta: taken out (air now); cyan: drawn where the sword stood (aura and its keyline)
                d = ImageDraw.Draw(big)
                sub = changed[box[1]:box[3], box[0]:box[2]]
                drawn = (out != '')[box[1]:box[3], box[0]:box[2]]
                ys, xs = np.nonzero(sub)
                for y, x in zip(ys, xs):
                    d.rectangle((x * s, y * s, x * s + s - 1, y * s + s - 1), outline=CYAN if drawn[y, x] else MAG)
            t = Image.new('RGBA', (big.width, big.height + 22), PANEL)
            t.alpha_composite(big, (0, 22))
            ImageDraw.Draw(t).text((3, 3), lab, fill=WHITE, font=font(14))
            panels.append(t)
        W = sum(p.width for p in panels) + 16
        row = Image.new('RGBA', (W, panels[0].height + 26), PANEL)
        n = int(changed.sum())
        ImageDraw.Draw(row).text((3, 3), 'frame %d: %d pixels changed, all of them inside the sword\'s footprint '
                                         '(%d aura carried on behind it, %d keyline)' % (
                                             i, n, int((mask & np.isin(out, AURA)).sum()), int((mask & (out == 'K')).sum())),
                                 fill=(255, 220, 120, 255), font=font(15, True))
        x = 0
        for p in panels:
            row.alpha_composite(p, (x, 26))
            x += p.width + 8
        rows.append(row)
    W = max(r.width for r in rows)
    out = Image.new('RGBA', (W, sum(r.height + 8 for r in rows) + 34), PANEL)
    ImageDraw.Draw(out).text((4, 8), 'Eric\'s charge without his planted sword, against the shipped twin (%dx)' % s,
                             fill=WHITE, font=font(17, True))
    y = 34
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height + 8
    return out


# ------------------------------------------------------------------ the in-context still

def planted_sword():
    """The planted sword prop, in its own colours (props keep theirs), cut at the first row of its dirt,
    and its base point (blade centre x, that row) - as the portals artist places it."""
    im = Image.open(PROP).convert('RGBA')
    px = im.load()
    span = {}
    for y in range(im.height):
        xs = [x for x in range(im.width) if px[x, y][3]]
        if xs:
            span[y] = (min(xs), max(xs))
    ys = sorted(span)
    guard = next(y for y in ys if span[y][1] - span[y][0] >= 30)
    blade = span[guard + 12]
    width = blade[1] - blade[0]
    base = next(y for y in ys if y > guard + 12 and span[y][1] - span[y][0] != width)
    return im.crop((0, 0, im.width, base)), ((blade[0] + blade[1] + 1) / 2.0, base)


def to_screen(p):
    return ((p[0] + 480) / 1.5, (p[1] + 6) / 1.5)


def still(charge_frame, back):
    """1920x1080 in the approved staging (option B, 2 px a texel): Jordan working, Eric's sword planted in
    Josh's take-B sword portal (loop frame 1) at the attack's centre, Eric charging at his start spot on
    Jordan's two blue strings (tied at his back, drawn under him), the player for scale."""
    s = 2
    cv = ST.Canvas(s)
    cv.blit(ST.void(2), 2, (0, 0))
    god, aura, tips = ST.god_frame('control', 1)
    tl = ST.god_tl()
    core = (tl[0] + (ST.L.CORE[0] + 0.5) * 2, tl[1] + (ST.L.CORE[1] + 0.5) * 2)
    cv.blit(ST.RU.frame_image(5), 2, (core[0] - 192, core[1] - 192))
    cv.blit(god, 2, tl)
    cv.add(aura, 2, (tl[0] - ST.G.AURA_PAD * 2, tl[1]))
    centre, start, player = to_screen((960, 921)), to_screen((1154, 930)), to_screen((1020, 1290))
    feet_e = (128, 192)                                      # his feet texel (128, 191), as an edge
    tlx, tly = start[0] - feet_e[0] * s, start[1] - feet_e[1] * s
    hk = (tlx + (back[0] + 0.5) * s, tly + (back[1] + 0.5) * s)
    strings, knots = [], []
    for j, p0 in enumerate(ST.tips_px(tips, 'right', (2, 3))):
        strings.append(ST.S.curve(p0, (hk[0] + (j - 0.5) * 2 * s, hk[1]), 0.7))
        knots.append(p0)
    cv.strings(strings, knots, s)
    L = {layer: Image.open(os.path.join(PORTALS, 'takeB', 'portal_sword_loop_%s.png' % layer)).convert('RGBA')
         for layer in ('back', 'front', 'glow')}
    pw, ph, ax, ay, i = 64, 40, 32, 28, 1
    cut = lambda im: im.crop((i * pw, 0, (i + 1) * pw, ph))  # noqa: E731
    sword, base = planted_sword()

    def portal():
        pos = (centre[0] - ax * s, centre[1] - ay * s)
        cv.blit(cut(L['back']), s, pos)
        cv.blit(sword, s, (centre[0] - base[0] * s, centre[1] - base[1] * s))
        cv.add(cut(L['glow']), s, pos)
        cv.blit(cut(L['front']), s, pos)

    items = [(centre[1], portal),
             (start[1], lambda: cv.blit(charge_frame, s, (tlx, tly))),
             (player[1], lambda: cv.blit(ST.player_up(), s, (player[0] - 16 * s, player[1] - 29 * s)))]
    for _y, fn in sorted(items, key=lambda it: it[0]):
        fn()
    out = cv.im
    d = ImageDraw.Draw(out)
    d.text((24, 18), 'CONCEPT: attack 3, for approval', fill=WHITE, font=font(22, True))
    y = 48
    for ln in ('Eric\'s sword stays planted in Josh\'s take-B sword',
               'portal; he charges the bear hug beside it, sword-less',
               '(eric_portal_charge f0). Staging option B, 2 px a texel:',
               'the portal at the attack\'s centre (world 960, 921), Eric',
               'at his start (world 1154, 930). Jordan\'s blue strings tie',
               'on at his back (behind the body: drawn under him).'):
        d.text((24, y), ln, fill=DIM, font=font(14))
        y += 19
    return out, {'portal_screen': [round(v, 1) for v in centre], 'eric_feet_screen': [round(v, 1) for v in start],
                 'back_hook_screen': [round(v, 1) for v in hk], 'portal': 'takeB portal_sword_loop frame %d' % i}


# ------------------------------------------------------------------ writing

def aseprite(*args):
    subprocess.run([ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def main(argv):
    if not argv or argv[0] not in ('--check', '--write'):
        print(__doc__)
        return 2
    writing = argv[0] == '--write'
    install_guard(HERE if writing else None)
    load()
    sheet, frames, mask, info, problems = build()
    for fi in info['frames']:
        print(fi)
    print('BACK', info['back'])
    if problems:
        print('PROBLEMS:\n  ' + '\n  '.join(problems))
        return 1
    print('audit clean')
    if not writing:
        return 0
    png = os.path.join(HERE, NAME + '.png')
    ase = os.path.join(HERE, NAME + '.aseprite')
    sheet.save(png)
    aseprite(png, '--save-as', ase)
    rt = os.path.join(HERE, '_roundtrip.png')
    aseprite(ase, '--save-as', rt)
    d = pixel_diff(Image.open(png), Image.open(rt))
    os.remove(rt)
    if d:
        raise SystemExit('the .aseprite does not round-trip: ' + d)
    preview(frames, 3, info['back']).save(os.path.join(HERE, NAME + '_3x.png'))
    preview(frames, 6, info['back']).save(os.path.join(HERE, NAME + '_6x.png'))
    twin_img = Image.open(TWIN).convert('RGBA')
    compare(frames, twin_img, mask).save(os.path.join(HERE, NAME + '_vs_twin.png'))
    load_staging()
    im, sinfo = still(frames[0][2], info['back'][0])
    im.save(os.path.join(HERE, NAME + '_in_context.png'))
    info['still'] = sinfo
    info['ship_as'] = 'res://Assets/Characters/Jordan/Puppets/eric/%s.png (+ .aseprite)' % NAME
    info['hooks_line'] = '\t\t&"%s": [%s],' % (NAME, ', '.join('Vector2(%d, %d)' % tuple(p) for p in info['back']))
    with open(os.path.join(HERE, 'notes.json'), 'w', encoding='utf-8') as fh:
        json.dump(info, fh, indent=1)
    print('wrote into', HERE)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
