"""Danny's fight sheets (the user's brief of 2026-09-24): build, lint, measure, anchor, preview, ship.

    python fight_export.py              build and lint every sheet, print the numbers. Writes NOTHING.
    python fight_export.py --preview    also the previews, into the scratch folder (DANNY_FIGHT_PREVIEW)
    python fight_export.py --ship       also into Assets/Characters/Danny/Sumo/: each PNG and its .aseprite,
                                        built in a temp folder, saved as .aseprite by the Aseprite CLI,
                                        exported back and compared pixel for pixel (art_source/imgdiff.py)
                                        BEFORE anything lands, then compared again where it landed.
    --only NAME[,NAME]                  just those sheets
    --replace                           allow overwriting a sheet this script shipped before

It only ever writes the nine names in fight_sheets.SHEETS; it refuses any other name, so the approved
sheets (idle, wake, slap, step, hit, defeat, evolve, juggle) can never be touched from here. A lint
failure or a round-trip difference stops it before anything lands.

Lint, per frame, against the approved sheets:
  palette     only Danny's approved 26 colours, pure-black keyline, no semi-alpha
  craft       no keyline gaps (a fill pixel touching transparency), no pinholes, no stray pixels,
              nothing cut by the frame's border (the floor row may carry only keyline)
  contract    grounded frames sit on the floor row; airborne ones say so
  numbers     black share and colour count, beside the approved range (14.6-16.9%, 26)
  ramps       the darker half of each main ramp (skin, both knits) as a share, against the approved
              sheets, so a turned or relit frame cannot drown in shadow unnoticed
"""
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
AS = os.path.dirname(HERE)
ROOT = os.path.dirname(AS)

from PIL import Image, ImageDraw  # noqa: E402

import fight as FT  # noqa: E402
import fight_sheets as FS  # noqa: E402
import sumo_lib as L  # noqa: E402

K = FT.K
imgdiff = FT._load('imgdiff', os.path.join(AS, 'imgdiff.py'))

SUMO = os.path.join(ROOT, 'Assets', 'Characters', 'Danny', 'Sumo')
APPROVED = ('danny_sumo_idle', 'danny_sumo_wake', 'danny_sumo_slap', 'danny_sumo_step', 'danny_sumo_hit',
            'danny_sumo_defeat')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
SCRATCH = os.environ.get('DANNY_FIGHT_PREVIEW', os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\danny_anims'))
BG = (46, 49, 58, 255)
FAMILIES = {'skin': '1234567', 'lknit': 'uvwx', 'dknit': 'UVBX'}
MAIN = ('skin', 'lknit', 'dknit')
DEEP_TOL = 0.12
BLACK_RANGE = (0.146, 0.169)      # the approved sheets' per-frame range


def rgb(k):
    return L.PAL[k][:3]


FAM_RGB = {fam: [rgb(k) for k in keys] for fam, keys in FAMILIES.items()}
PALETTE = {v[:3] for v in L.PAL.values()}


# ------------------------------------------------------------------ THE APPROVED NUMBERS
def approved_stats():
    frames = []
    for name in APPROVED:
        im = Image.open(os.path.join(SUMO, name + '.png')).convert('RGBA')
        for i in range(im.width // 176):
            f = im.crop((176 * i, 0, 176 * i + 176, 144))
            flat = f.get_flattened_data() if hasattr(f, 'get_flattened_data') else f.getdata()
            frames.append([p for p in flat if p[3]])
    allpx = [p for fr in frames for p in fr]
    black = [sum(1 for p in fr if p[:3] == (0, 0, 0)) / len(fr) for fr in frames]
    cols = [len({p[:3] for p in fr}) for fr in frames]
    return dict(palette={p[:3] for p in allpx}, black=(min(black), max(black)), colours=(min(cols), max(cols)),
                deep=deep_shares(Counter(p[:3] for p in allpx)), n=len(frames))


def deep_shares(c):
    out = {}
    for fam, cols in FAM_RGB.items():
        tones = [c.get(v, 0) for v in cols]
        n = sum(tones)
        if n < 40:
            continue
        half = (len(cols) - 1) / 2.0
        out[fam] = sum(t for i, t in enumerate(tones) if i < half) / n
    return out


# ------------------------------------------------------------------ ONE FRAME
def frame_map(sheet, spec):
    """The frame's key map in the sheet frame's own coordinates."""
    w, h = FS.SHEETS[sheet]['size']
    ox = 0 if 'side' in spec else (w - 176) // 2
    oy = FS.SHEETS[sheet]['oy']
    return {(x + ox, y + oy): k for (x, y), k in FS.frame_px(spec).items() if 0 <= x + ox < w and 0 <= y + oy < h}, \
        (ox, oy)


def airborne(sheet, name):
    return sheet == 'danny_sumo_headbutt' and name in ('flight_a', 'flight_b', 'bonk', 'recoil')


def turned(spec):
    """Frames with a part lit for a turn (a lolled head, the rocking / squashed tuck, the side view
    posed through its joints): the ones the ramp check guards."""
    if 'tuck' in spec or 'side' in spec:
        return True
    return bool(dict(FT.DEFAULT, **spec)['head_tilt'])


def lint_frame(sheet, name, px, src, spec=None):
    w, h = FS.SHEETS[sheet]['size']
    fails, notes = [], []
    cols = Counter(rgb(k) for k in px.values())
    semi = sum(1 for k in px.values() if L.PAL[k][3] != 255)
    if semi:
        fails.append('%d semi-alpha pixels' % semi)
    off = set(cols) - src['palette']
    if off:
        fails.append('off-palette %s' % sorted('#%02X%02X%02X' % v for v in off))
    gaps = [q for q, k in px.items() if k != 'k' and any((q[0] + dx, q[1] + dy) not in px for dx, dy in K.N4)]
    if gaps:
        fails.append('%d keyline gaps (first %s)' % (len(gaps), sorted(gaps)[:3]))
    holes = K.pinholes(px)
    if holes:
        fails.append('%d pinholes (first %s)' % (len(holes), sorted(holes)[:3]))
    lone = K.orphans(px)
    if lone:
        fails.append('%d stray pixels (first %s)' % (len(lone), sorted(lone)[:3]))
    cut = [q for q, k in px.items() if k != 'k' and (q[0] in (0, w - 1) or q[1] in (0, h - 1))]
    if cut:
        fails.append('%d pixels cut by the border' % len(cut))
    edge = [q for q in px if q[0] in (0, w - 1) or q[1] == 0]
    if edge:
        fails.append('%d pixels on the frame edge' % len(edge))
    low = max(y for (x, y) in px)
    if not airborne(sheet, name) and low != h - 1:
        fails.append('lowest row %d, not the floor row %d' % (low, h - 1))
    n = sum(cols.values())
    black = cols.get((0, 0, 0), 0) / n
    deep = deep_shares(Counter(rgb(k) for k in px.values()))
    for fam in MAIN:
        if fam in deep and fam in src['deep'] and abs(deep[fam] - src['deep'][fam]) > DEEP_TOL:
            msg = '%s deep %.1f%% vs %.1f%%' % (fam, 100 * deep[fam], 100 * src['deep'][fam])
            if spec is None or turned(spec):
                fails.append(msg)
            else:
                notes.append(msg + ' (unturned: what the pose covers, not a relight)')
    return dict(fails=fails, notes=notes, black=black, colours=len(cols), deep=deep, opaque=n, low=low)


# ------------------------------------------------------------------ ANCHORS
def anchors(sheet, name, spec, px, off):
    """The texels the coder needs, in the sheet frame's coordinates."""
    w, h = FS.SHEETS[sheet]['size']
    ox, oy = off
    out = {}
    low = max(y for (x, y) in px)
    row = sorted(x for (x, y) in px if y == low)
    out['bottom_centre'] = (w // 2, h - 1)
    if sheet == 'danny_sumo_spit':
        out['mouth'] = mouth_texel(spec, ox, oy)
    if 'tuck' in spec:
        out['rear_contact'] = (88 + ox, low)
    if sheet == 'danny_sumo_push':
        s = dict(FT.DEFAULT, **spec)
        if s['arms'] == ('push', 'push'):
            bx, by = s['body']
            pl = (s['push_at'] or {}).get(1, (66.0, 112.0, 1.15))
            left = (int(round(pl[0] + bx + ox)), int(round(pl[1] + by + oy)))
            right = (int(round(175 - pl[0] + bx + ox)), int(round(pl[1] + by + oy)))
            out['hand_l'], out['hand_r'] = left, right
            out['hands_mid'] = ((left[0] + right[0]) // 2, left[1] + int(round(6 * pl[2])))
    if 'side' in spec:
        out.update(side_anchors(spec, px))
    else:
        out['crown'] = crown_texel(spec, px, ox, oy)
    if sheet == 'danny_sumo_sleep':
        cx, cy = out['crown']
        out['zs'] = (cx - 2, cy - 5)
    out['bbox'] = K.bbox(px)
    return out


def head_offset(spec):
    """The head's (dx, dy) from its approved place, and its tilt."""
    if 'tuck' in spec:
        import fight_tuck as TK
        t = dict(TK.DEFAULT, **spec['tuck'])
        xf = t['xf'] or TK.Xf()
        hx, hy = xf((87.5, 30.0))
        return int(round(hx - 87.5)) + t['head'][0], int(round(hy - 30.0)) + t['head'][1], 0.0
    s = dict(FT.DEFAULT, **spec)
    return s['body'][0] + s['head_dx'], s['body'][1] + s['head_dy'], s['head_tilt']


def crown_texel(spec, px, ox, oy):
    """The top of the beanie: the highest drawn texel in the column over the crown's peak (the
    head's own top, turned with the head when it lolls)."""
    dx, dy, tilt = head_offset(spec)
    top = (87.5 + dx, 2.5 + dy)
    if tilt:
        top = FT.rot_pt(top, tilt, (87.5 + dx, 50.0 + dy))
    x = int(round(top[0])) + ox
    ys = [y for (qx, y) in px if qx == x and y <= top[1] + oy + 6]
    return (x, min(ys) if ys else int(round(top[1])) + oy)


def box_without_bubble(spec, off):
    """The body's box with the sleep bubble and the drool left out: what the hurtbox should cover."""
    sp = dict(spec, bubble=0, drool=False, pop=False)
    ox, oy = off
    pxx = {(x + ox, y + oy): k for (x, y), k in FS.frame_px(sp).items()}
    return K.bbox(pxx)


def mouth_texel(spec, ox, oy):
    s = dict(FT.DEFAULT, **spec)
    dx = s['body'][0] + s['head_dx']
    dy = s['body'][1] + s['head_dy']
    rows = len(FT.anim.MOUTHS[s['mouth']])
    y = 43 + 1 + (rows - 2) / 2.0
    p = (87.5 + dx, y + dy)
    if s['head_tilt']:
        p = FT.rot_pt(p, s['head_tilt'], (87.5 + dx, 50.0 + dy))
    return (int(round(p[0] + ox)), int(round(p[1] + oy)))


def side_anchors(spec, px):
    """The headbutt's HEAD point (the leading texel of the beanie, where the hit lands) and the body
    box (every drawn texel)."""
    import fight_side as SD
    sp = spec['side']
    pz = SD.Pose(sp)
    neck = pz.neck((0.0, 0.0))
    ang = pz.neck.angle()
    hx = SD.J(ang, neck)
    crown = [hx(p) for p in SD.H_CROWN] + [hx(p) for p in SD.H_FACE]
    shift_y = 0
    if spec.get('ground'):
        raw = SD.build(sp)[0].px
        shift_y = 143 - max(y for (x, y) in raw)
    lead = max(crown, key=lambda p: p[0])
    return {'head_point': (int(round(lead[0])) + 1, int(round(lead[1])) + shift_y)}


# ------------------------------------------------------------------ BUILD
def build(names):
    out = {}
    for sheet in names:
        cfg = FS.SHEETS[sheet]
        w, h = cfg['size']
        frames = []
        for (name, spec, ms) in cfg['frames']:
            px, off = frame_map(sheet, spec)
            frames.append(dict(name=name, spec=spec, ms=ms, px=px, off=off))
        im = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            im.alpha_composite(FT.image_of(f['px'], w, h), (w * i, 0))
        out[sheet] = dict(frames=frames, image=im, size=(w, h))
    return out


def ship_one(im, name, replace):
    assert name in FS.SHEETS, name
    png = os.path.join(SUMO, name + '.png')
    ase = os.path.join(SUMO, name + '.aseprite')
    if (os.path.exists(png) or os.path.exists(ase)) and not replace:
        raise SystemExit('%s already exists; pass --replace to overwrite it (nothing written)' % name)
    tmp = tempfile.mkdtemp()
    png_t = os.path.join(tmp, name + '.png')
    ase_t = os.path.join(tmp, name + '.aseprite')
    back = os.path.join(tmp, 'rt.png')
    im.save(png_t)
    subprocess.run([ASEPRITE, '-b', png_t, '--save-as', ase_t], check=True, capture_output=True)
    subprocess.run([ASEPRITE, '-b', ase_t, '--save-as', back], check=True, capture_output=True)
    d = imgdiff.pixel_diff(Image.open(png_t), Image.open(back))
    if d:
        raise SystemExit('%s: round trip differs before shipping: %s' % (name, d))
    shutil.copyfile(png_t, png)
    shutil.copyfile(ase_t, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
    return png, ase, imgdiff.pixel_diff(Image.open(png), Image.open(back2)), imgdiff.pixel_diff(Image.open(png), im)


# ------------------------------------------------------------------ PREVIEWS
def strip_3x(sheet, data):
    w, h = data['size']
    fr = data['frames']
    s, pad, lab = 3, 10, 26
    W = len(fr) * (w * s + pad) + pad
    H = h * s + 2 * pad + lab
    out = Image.new('RGBA', (W, H), (24, 25, 31, 255))
    d = ImageDraw.Draw(out)
    for i, f in enumerate(fr):
        x0, y0 = pad + i * (w * s + pad), pad + lab
        cell = Image.new('RGBA', (w, h), BG)
        cell.alpha_composite(FT.image_of(f['px'], w, h))
        out.alpha_composite(cell.resize((w * s, h * s), Image.NEAREST), (x0, y0))
        d.line((x0, y0 + h * s, x0 + w * s - 1, y0 + h * s), fill=(90, 200, 210, 255))
        d.text((x0 + 2, 6), 'f%d %s  %d ms' % (i, f['name'], f['ms']), fill=(225, 225, 235, 255))
    return out


def gif_3x(path, data, bg=BG):
    w, h = data['size']
    ims = []
    for f in data['frames']:
        cell = Image.new('RGBA', (w, h), bg)
        cell.alpha_composite(FT.image_of(f['px'], w, h))
        ims.append(cell.resize((w * 3, h * 3), Image.NEAREST).convert('RGB').convert('P', palette=Image.ADAPTIVE,
                                                                                         colors=255))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=[f['ms'] for f in data['frames']], loop=0,
                disposal=1, optimize=False)


KEY_FRAMES = [('danny_sumo_spit', 3), ('danny_sumo_jump', 1), ('danny_sumo_air', 0), ('danny_sumo_slam', 1),
              ('danny_sumo_sleep', 2), ('danny_sumo_sleep_hit', 0), ('danny_sumo_headbutt', 2),
              ('danny_sumo_push', 1), ('danny_sumo_block', 0)]


def game_contact(built):
    """One key frame of every sheet at 3x game scale on the arena mat, the player beside it at 3x
    for size (their feet on the same floor line)."""
    mat = Image.open(os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')).convert('RGBA')
    mat3 = mat.resize((mat.width * 3, mat.height * 3), Image.NEAREST)
    player = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')).convert('RGBA')
    p_back = player.crop((0, 32, 32, 64)).resize((96, 96), Image.NEAREST)
    cw, ch = 720, 560
    cols = 3
    rows = (len(KEY_FRAMES) + cols - 1) // cols
    out = Image.new('RGBA', (cols * cw, rows * ch), BG)
    d = ImageDraw.Draw(out)
    for i, (sheet, fi) in enumerate(KEY_FRAMES):
        if sheet not in built:
            continue
        data = built[sheet]
        w, h = data['size']
        f = data['frames'][fi]
        cx, cy = (i % cols) * cw, (i // cols) * ch
        win = mat3.crop((360, 90, 360 + cw, 90 + ch)).copy()
        ground = ch - 40
        big = FT.image_of(f['px'], w, h).resize((w * 3, h * 3), Image.NEAREST)
        ax = cw // 2 - 60 if w <= 176 else cw // 2
        lift = 0
        if sheet in ('danny_sumo_air', 'danny_sumo_jump') and 'tuck' in f['spec']:
            lift = 120                                   # the code lifts him; shown in the air
        win.alpha_composite(big, (ax - (w // 2) * 3, ground - h * 3 - lift))
        win.alpha_composite(p_back, (cw - 150, ground - 90))
        out.alpha_composite(win, (cx, cy))
        d.text((cx + 8, cy + 6), '%s  f%d %s' % (sheet, fi, f['name']), fill=(255, 255, 255, 255))
    return out


# ------------------------------------------------------------------ MAIN
def main():
    args = sys.argv[1:]
    ship, preview, replace = '--ship' in args, '--preview' in args, '--replace' in args
    names = list(FS.SHEETS)
    if '--only' in args:
        names = [n for n in args[args.index('--only') + 1].split(',') if n]
        for n in names:
            assert n in FS.SHEETS, n
    if ship:
        bad = [(n, d) for n, d in FT.check_same() if d]
        print('fight.build == anim.build_frame on every approved frame: %s' % ('yes' if not bad else bad))
        if bad:
            raise SystemExit('the approved frames no longer rebuild; nothing shipped')
    src = approved_stats()
    print('approved sheets: %d frames, black %.1f-%.1f%%, %d-%d colours; deep: %s' % (
        src['n'], 100 * src['black'][0], 100 * src['black'][1], src['colours'][0], src['colours'][1],
        '  '.join('%s %.1f%%' % (f, 100 * src['deep'][f]) for f in MAIN)))
    built = build(names)
    fatal = 0
    for sheet in names:
        data = built[sheet]
        w, h = data['size']
        cfg = FS.SHEETS[sheet]
        print('\n%s  %d x %d frames, hframes %d, sheet %dx%d  -- %s' % (sheet, w, h, len(data['frames']),
                                                                        data['image'].width, h, cfg['note']))
        for i, f in enumerate(data['frames']):
            r = lint_frame(sheet, f['name'], f['px'], src, f['spec'])
            a = anchors(sheet, f['name'], f['spec'], f['px'], f['off'])
            f['lint'], f['anchors'] = r, a
            fatal += len(r['fails'])
            flag = '' if BLACK_RANGE[0] - 0.01 <= r['black'] <= BLACK_RANGE[1] + 0.01 else ' (black outside the band)'
            print('  f%d %-9s %4d ms  black %5.1f%%  col %2d  deep %s%s  %s' % (
                i, f['name'], f['ms'], 100 * r['black'], r['colours'],
                ' '.join('%s %.0f' % (k[0], 100 * v) for k, v in r['deep'].items() if k in MAIN), flag,
                '; '.join(r['fails']) or 'clean') + (('  [note: ' + '; '.join(r['notes']) + ']') if r['notes'] else ''))
            print('       anchors: ' + '  '.join('%s %s' % (k, v) for k, v in a.items()))
        if sheet == 'danny_sumo_sleep':
            boxes = [box_without_bubble(f['spec'], f['off']) for f in data['frames']]
            u = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
            print('  SLEEP_BOX (union over the loop, bubble and drool left out; x0, y0, x1, y1 inclusive): %s' % (u,))
        if sheet == 'danny_sumo_headbutt':
            fl = [f['anchors']['bbox'] for f in data['frames'] if f['name'].startswith('flight')]
            u = (min(b[0] for b in fl), min(b[1] for b in fl), max(b[2] for b in fl), max(b[3] for b in fl))
            print('  flight body box (union of the flight loop; x0, y0, x1, y1 inclusive): %s' % (u,))
        if sheet == 'danny_sumo_jump':
            print('  lift-off: f2 (the tuck) is the first frame off the mat; f0-f1 have the feet on the floor row')
    print('\n%d fatal findings' % fatal)
    if preview or ship:
        os.makedirs(SCRATCH, exist_ok=True)
        for sheet in names:
            strip_3x(sheet, built[sheet]).save(os.path.join(SCRATCH, sheet + '_3x.png'))
            gif_3x(os.path.join(SCRATCH, sheet + '_3x.gif'), built[sheet])
            built[sheet]['image'].save(os.path.join(SCRATCH, sheet + '.png'))
        if len(names) == len(FS.SHEETS):
            game_contact(built).save(os.path.join(SCRATCH, 'danny_fight_contact_game_scale.png'))
        print('previews in', SCRATCH)
    if fatal:
        raise SystemExit('lint failed; nothing shipped')
    if ship:
        for sheet in names:
            png, ase, d2, d3 = ship_one(built[sheet]['image'], sheet, replace)
            print('wrote %s (+ .aseprite): .aseprite -> .png %s; shipped vs build %s' % (
                os.path.basename(png), d2 or 'pixel-identical', d3 or 'pixel-identical'))
            if d2 or d3:
                raise SystemExit(1)
    elif not preview:
        print('(nothing written: --preview for previews, --ship for Assets/Characters/Danny/Sumo/)')


if __name__ == '__main__':
    main()
