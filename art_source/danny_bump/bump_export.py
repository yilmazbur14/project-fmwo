"""Danny's belly bump / on-his-back / worm splash / rope impact / big slam approval pass: build, lint, measure,
anchor, and (only when asked) write.

    python bump_export.py              build and lint every sheet, print the numbers and anchors. WRITES NOTHING.
    python bump_export.py --preview    also previews, GIFs and the arena mock into the scratch folder (BUMP_PREVIEW)
    python bump_export.py --write      also the approval folder, art_source/danny_bump/approval/: each sheet's PNG and
                                       .aseprite (saved by the Aseprite CLI and read back, compared texel for texel
                                       with art_source/imgdiff.py before anything lands, and again where it landed),
                                       the 3x previews, the GIFs and the 1920x1080 mock
    --only NAME[,NAME]                 just those sheets

It never writes into Assets, project.godot or a scene: every path it writes is checked (realpath, so an 8.3 short name
can't slip past) to be inside the approval folder or the scratch folder, and it refuses anything else. A lint
failure stops it before anything is written.

Lint, per frame. Body sheets, against the approved sumo sheets: only Danny's approved 26 colours, a pure-black
keyline, no semi-alpha, no keyline gaps (a fill texel touching transparency), no pinholes, no stray texels,
nothing cut by the frame's border, grounded frames on the floor row; the black share and colour count beside the
approved range. FX sheets, against his approved FX: only the FX palette (plus the arena rope's own black and white
for the rope), alpha only 255 / 168 / 96, nothing on the frame's border.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
AS = os.path.dirname(HERE)
ROOT = os.path.dirname(AS)
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw  # noqa: E402

import bump_rig as R  # noqa: E402
import bump_sheets as S  # noqa: E402
import bump_fx as X  # noqa: E402

K = R.K
imgdiff = R.FT._load('imgdiff', os.path.join(AS, 'imgdiff.py'))

APPROVAL = os.path.join(HERE, 'approval')
SCRATCH = os.environ.get('BUMP_PREVIEW', os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\danny_bump\out'))
SUMO = os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'Sumo')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
APPROVED = ('danny_sumo_idle', 'danny_sumo_slam', 'danny_sumo_headbutt', 'danny_sumo_push', 'danny_sumo_sleep')
BG = (46, 49, 58, 255)
FX_ALPHAS = {255, 168, 96}


# ------------------------------------------------------------------ WRITE GUARD
def _real(p):
    return os.path.normcase(os.path.realpath(p))


def guard(path):
    """Every write goes through here: inside the approval folder or the scratch folder, never anywhere else."""
    rp = _real(path)
    for ok in (APPROVAL, SCRATCH):
        root = _real(ok)
        if rp == root or rp.startswith(root + os.sep):
            if 'assets' in rp.split(os.sep):
                break
            return path
    raise SystemExit('REFUSED to write %s (only %s or %s)' % (path, APPROVAL, SCRATCH))


def save(im, path, **kw):
    guard(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, **kw)


# ------------------------------------------------------------------ THE APPROVED NUMBERS
def approved_stats():
    frames = []
    sizes = {'danny_sumo_headbutt': (224, 144)}
    for name in APPROVED:
        im = Image.open(os.path.join(SUMO, name + '.png')).convert('RGBA')
        fw, fh = sizes.get(name, (176, 144))
        for i in range(im.width // fw):
            f = im.crop((fw * i, 0, fw * i + fw, fh))
            flat = f.get_flattened_data() if hasattr(f, 'get_flattened_data') else f.getdata()
            frames.append([p for p in flat if p[3]])
    allpx = [p for fr in frames for p in fr]
    black = [sum(1 for p in fr if p[:3] == (0, 0, 0)) / len(fr) for fr in frames]
    cols = [len({p[:3] for p in fr}) for fr in frames]
    return dict(palette={p[:3] for p in allpx}, black=(min(black), max(black)), colours=(min(cols), max(cols)),
                n=len(frames))


# ------------------------------------------------------------------ BODY SHEETS
def rgb(k):
    return R.L.PAL[k][:3]


def lint_body(sheet, name, spec, px, src):
    w, h = S.SHEETS[sheet]['size']
    fails = []
    cols = Counter(rgb(k) for k in px.values())
    off = set(cols) - src['palette']
    if off:
        fails.append('off-palette %s' % sorted('#%02X%02X%02X' % v for v in off))
    if any(R.L.PAL[k][3] != 255 for k in px.values()):
        fails.append('semi-alpha')
    gaps = [q for q, k in px.items() if k != 'k' and any((q[0] + dx, q[1] + dy) not in px for dx, dy in K.N4)]
    if gaps:
        fails.append('%d keyline gaps (first %s)' % (len(gaps), sorted(gaps)[:3]))
    holes = K.pinholes(px)
    if holes:
        fails.append('%d pinholes (first %s)' % (len(holes), sorted(holes)[:3]))
    lone = K.orphans(px)
    if lone:
        fails.append('%d stray texels (first %s)' % (len(lone), sorted(lone)[:3]))
    edge = [q for q in px if q[0] in (0, w - 1) or q[1] == 0]
    if edge:
        fails.append('%d texels on the frame edge' % len(edge))
    low = max(y for (x, y) in px)
    if spec.get('ground', True) and low != h - 1:
        fails.append('lowest row %d, not the floor row %d' % (low, h - 1))
    n = sum(cols.values())
    return dict(fails=fails, black=cols.get((0, 0, 0), 0) / n, colours=len(cols), opaque=n)


def body_anchors(sheet, i, name, spec, px, off):
    """The texels the coder asked for, in the sheet frame's coordinates."""
    w, h = S.SHEETS[sheet]['size']
    ox, oy = off
    out = {'bottom_centre': (w // 2, h - 1)}
    bb = K.bbox(px)
    out['bbox'] = bb
    if 'side' in spec:
        sp = dict(R.DEFAULT, **spec['side'])
        pz = R.SD.Pose({k: v for k, v in sp.items() if k in R.SD.DEFAULT})
        ang = pz.neck.angle()
        hx = R.J(ang, pz.neck((0.0, 0.0)))
        crown_pts = [hx(p) for p in R.SD.H_CROWN]
        top = min(crown_pts, key=lambda p: p[1])
        cx = int(round(top[0])) + ox
        ys = [y for (x, y) in px if x == cx and y <= int(round(top[1])) + oy + 6]
        out['crown'] = (cx, min(ys) if ys else int(round(top[1])) + oy)
        head = [hx(p) for p in R.SD.H_CROWN + R.SD.H_FACE]
        hp = min(head, key=lambda p: p[1])
        out['head_top'] = (int(round(hp[0])) + ox, int(round(hp[1])) + oy - 1)     # its keyline, stars left out
        # the head's direction: where the face points (the profile faces head-local +x)
        fx, fy = hx((30.0, -6.0))
        nx, ny = hx((0.0, -6.0))
        out['face_dir'] = (round(fx - nx, 2), round(fy - ny, 2))
        if sheet == 'danny_sumo_bump':
            bf = R.belly_xf(sp['belly'])
            T = pz.torso
            ys_ = [T(bf(p) if bf else p)[1] for p in ((40.0, -40.0), (40.0, -6.0))]
            y0, y1 = int(min(ys_)) + oy, int(max(ys_)) + oy
            band = [(x, y) for (x, y) in px if y0 <= y <= y1]
            front = max(band, key=lambda q: (q[0], -abs(q[1] - (y0 + y1) / 2.0)))
            out['belly_front'] = front
    else:
        out['crown'] = (w // 2, min(y for (x, y) in px if abs(x - w // 2) <= 2))
    if sheet == 'danny_sumo_back':
        out['ground_point'] = (int(round(w / 2.0)), h - 1)
    return out


def body_px_no_stars(sheet, spec):
    sp = dict(spec)
    sp.pop('stars', None)
    return S.frame_map(sheet, sp)[0]


def build_body(names):
    out = {}
    for sheet in names:
        cfg = S.SHEETS[sheet]
        w, h = cfg['size']
        frames = []
        for (name, spec, ms) in cfg['frames']:
            px, off, full = S.frame_map(sheet, spec)
            clipped = len(full) - len(px)
            frames.append(dict(name=name, spec=spec, ms=ms, px=px, off=off, clipped=clipped))
        im = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            im.alpha_composite(R.FT.image_of(f['px'], w, h), (w * i, 0))
        out[sheet] = dict(frames=frames, image=im, size=(w, h), note=cfg['note'], kind='body')
    return out


# ------------------------------------------------------------------ FX SHEETS
def fx_palette():
    pal = {v[:3] for v in X.pal.PAL.values()}
    return pal | {(0, 0, 0), (255, 255, 255)}


def lint_fx(sheet, im, w, h):
    fails = []
    px = [p for p in (im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()) if p[3]]
    off = {p[:3] for p in px} - fx_palette()
    if off:
        fails.append('off-palette %s' % sorted('#%02X%02X%02X' % v for v in off))
    alphas = {p[3] for p in px}
    if alphas - FX_ALPHAS:
        fails.append('alphas %s' % sorted(alphas))
    a = im.getchannel('A')
    rope = {(0, 0, 0), (255, 255, 255)}
    for x in range(w):
        for y in (0, h - 1):
            # the rope sheet's rope runs off its top and bottom edges on purpose: it joins the arena's rope there
            if a.getpixel((x, y)) and not (sheet == 'danny_rope_impact' and im.getpixel((x, y))[:3] in rope):
                fails.append('texels on the top/bottom edge at %s' % ((x, y),))
                break
        else:
            continue
        break
    for y in range(h):
        if a.getpixel((0, y)) or a.getpixel((w - 1, y)):
            fails.append('texels on the left/right edge')
            break
    return dict(fails=fails, colours=len({p for p in px}), opaque=len(px), alphas=sorted(alphas))


def build_fx(names):
    out = {}
    for sheet in names:
        cfg = X.FX_SHEETS[sheet]
        w, h = cfg['size']
        frs = cfg['frames']()
        ims = [X.pal.to_image(fr) for fr in frs]
        for im in ims:
            assert im.size == (w, h), (sheet, im.size)
        strip = Image.new('RGBA', (w * len(ims), h), (0, 0, 0, 0))
        for i, im in enumerate(ims):
            strip.paste(im, (i * w, 0))
        frames = [dict(name='f%d' % i, ms=cfg['ms'][i], image=im) for i, im in enumerate(ims)]
        out[sheet] = dict(frames=frames, image=strip, size=(w, h), note=cfg['note'], kind='fx', pivot=cfg['pivot'])
    return out


# ------------------------------------------------------------------ PREVIEW STRIPS
def strip_3x(sheet, data, s=3, bg=BG):
    w, h = data['size']
    fr = data['frames']
    pad, lab = 10, 26
    out = Image.new('RGBA', (len(fr) * (w * s + pad) + pad, h * s + 2 * pad + lab), (24, 25, 31, 255))
    d = ImageDraw.Draw(out)
    for i, f in enumerate(fr):
        x0, y0 = pad + i * (w * s + pad), pad + lab
        cell = Image.new('RGBA', (w, h), bg)
        cell.alpha_composite(f['image'] if data['kind'] == 'fx' else R.FT.image_of(f['px'], w, h))
        out.alpha_composite(cell.resize((w * s, h * s), Image.NEAREST), (x0, y0))
        d.line((x0, y0 + h * s, x0 + w * s - 1, y0 + h * s), fill=(90, 200, 210, 255))
        d.text((x0 + 2, 6), 'f%d %s  %d ms' % (i, f['name'], f['ms']), fill=(225, 225, 235, 255))
    return out


# ------------------------------------------------------------------ ASEPRITE ROUND TRIP
def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('aseprite %s failed: %s %s' % (args, r.stdout, r.stderr))


def write_sheet(im, name):
    """PNG + .aseprite into the approval folder: built in a temp folder, the .aseprite read back and compared
    texel for texel before anything lands, then compared again where it landed."""
    png = guard(os.path.join(APPROVAL, name + '.png'))
    ase = guard(os.path.join(APPROVAL, name + '.aseprite'))
    tmp = tempfile.mkdtemp()
    png_t, ase_t, back = os.path.join(tmp, name + '.png'), os.path.join(tmp, name + '.aseprite'), os.path.join(tmp, 'rt.png')
    im.save(png_t)
    aseprite(png_t, '--save-as', ase_t)
    aseprite(ase_t, '--save-as', back)
    d = imgdiff.pixel_diff(Image.open(png_t), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite round trip differs before writing: %s' % (name, d))
    os.makedirs(APPROVAL, exist_ok=True)
    shutil.copyfile(png_t, png)
    shutil.copyfile(ase_t, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    aseprite(ase, '--save-as', back2)
    d2 = imgdiff.pixel_diff(Image.open(png), Image.open(back2))
    d3 = imgdiff.pixel_diff(Image.open(png), im)
    shutil.rmtree(tmp, ignore_errors=True)
    return d2, d3


# ------------------------------------------------------------------ MAIN
def main():
    args = sys.argv[1:]
    write, preview = '--write' in args, '--preview' in args
    body_names = list(S.SHEETS)
    fx_names = list(X.FX_SHEETS)
    if '--only' in args:
        only = [n for n in args[args.index('--only') + 1].split(',') if n]
        body_names = [n for n in body_names if n in only]
        fx_names = [n for n in fx_names if n in only]
    bad = [(n, same) for n, same in R.check_same() if not same]
    print('bump_rig.build_side == the approved fight_side.build on every headbutt frame: %s' % ('yes' if not bad else bad))
    if bad:
        raise SystemExit('the approved side view no longer rebuilds; nothing written')
    src = approved_stats()
    print('approved sheets (%s): %d frames, black %.1f-%.1f%%, %d-%d colours, palette %d' % (
        ', '.join(APPROVED), src['n'], 100 * src['black'][0], 100 * src['black'][1], src['colours'][0],
        src['colours'][1], len(src['palette'])))
    built = build_body(body_names)
    built.update(build_fx(fx_names))
    fatal = 0
    report = {}
    for sheet in body_names:
        data = built[sheet]
        w, h = data['size']
        print('\n%s  %d frames of %dx%d, sheet %dx%d  -- %s' % (sheet, len(data['frames']), w, h,
                                                               data['image'].width, h, data['note']))
        for i, f in enumerate(data['frames']):
            r = lint_body(sheet, f['name'], f['spec'], f['px'], src)
            if f['clipped']:
                r['fails'].append('%d texels outside the frame' % f['clipped'])
            a = body_anchors(sheet, i, f['name'], f['spec'], f['px'], f['off'])
            f['lint'], f['anchors'] = r, a
            fatal += len(r['fails'])
            print('  f%-2d %-9s %4d ms  black %5.1f%%  col %2d  %s' % (
                i, f['name'], f['ms'], 100 * r['black'], r['colours'], '; '.join(r['fails']) or 'clean'))
            print('       ' + '  '.join('%s %s' % (k, v) for k, v in a.items()))
        if sheet == 'danny_sumo_back':
            boxes, stars = [], []
            for f in data['frames']:
                if not f['name'].startswith('daze'):
                    continue
                bare = body_px_no_stars(sheet, f['spec'])
                boxes.append(K.bbox(bare))
                stars.append(K.bbox([q for q in f['px'] if q not in bare]))
            u = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
            data['back_box'] = u
            print('  BACK_BOX (the daze loop, stars left out; x0, y0, x1, y1 inclusive): %s' % (u,))
            data['stars_box'] = (min(b[0] for b in stars), min(b[1] for b in stars), max(b[2] for b in stars),
                                 max(b[3] for b in stars))
            print('  daze stars box (union over the loop): %s' % (data['stars_box'],))
        report[sheet] = data
    for sheet in fx_names:
        data = built[sheet]
        w, h = data['size']
        print('\n%s  %d frames of %dx%d, sheet %dx%d, pivot %s  -- %s' % (
            sheet, len(data['frames']), w, h, data['image'].width, h, data['pivot'], data['note']))
        for i, f in enumerate(data['frames']):
            r = lint_fx(sheet, f['image'], w, h)
            f['lint'] = r
            fatal += len(r['fails'])
            print('  f%-2d %4d ms  colours %2d  texels %5d  alphas %s  %s' % (
                i, f['ms'], r['colours'], r['opaque'], r['alphas'], '; '.join(r['fails']) or 'clean'))
    print('\n%d fatal findings' % fatal)
    if fatal:
        raise SystemExit('lint failed; nothing written')
    if not (preview or write):
        print('(nothing written: --preview for the scratch folder, --write for %s)' % APPROVAL)
        return
    import bump_mock as M
    dest = APPROVAL if write else SCRATCH
    for sheet, data in built.items():
        save(strip_3x(sheet, data), os.path.join(dest, 'preview', sheet + '_3x.png'))
        if not write:
            save(data['image'], os.path.join(dest, sheet + '.png'))
    M.make_all(built, dest, save)
    if write:
        for sheet, data in built.items():
            d2, d3 = write_sheet(data['image'], sheet)
            print('wrote %s.png + .aseprite: .aseprite -> .png %s; written vs build %s' % (
                sheet, d2 or 'texel-identical', d3 or 'texel-identical'))
            if d2 or d3:
                raise SystemExit(1)
    print('written into', dest)


if __name__ == '__main__':
    main()
