"""Jordan's room - export and ship.

    python jr_export.py                        # bare run: builds and checks, WRITES NOTHING
    python jr_export.py --out <folder>         # review set into <folder> (never under Assets)
    python jr_export.py --out <folder> --pieces    # ...plus the crumble pieces and the .gd, for review
    python jr_export.py --ship                 # ship into the project (new files only)
    python jr_export.py --ship --replace       # ship over files it shipped before

--out writes the review set:
  layers/room_floor.png ... layers/room_clutter.png   the five 640x360 layers, bottom to top
  jordan_room.aseprite                                 the same five layers, layered
  jordan_room_native.png / jordan_room_1080.png        flattened, 640x360 / 1920x1080
  jordan_room_scale_mock.png, jordan_room_layout.png, jordan_room_layers_sheet.png

--ship writes into the project, and nothing else:
  Assets/Environment/JordanRoom/room_<layer>.png       the five layers (layer = floor, walls,
                                                       furniture, props, clutter)
  Assets/Environment/JordanRoom/jordan_room.aseprite   the layered source
  Assets/Environment/JordanRoom/Pieces/<layer>_<nnn>.png   the crumble pieces, trimmed
  Scripts/JordanRoomPieces.gd                          const PIECES, generated
It refuses to overwrite anything that exists unless --replace is given.

Checks (any failure writes nothing): DB32 only, alpha 0/255 only, floor + walls
opaque over the screen, two builds byte-identical, the layers pixel-identical to
the approved set in approval/layers, the .aseprite reading back pixel-identical,
and every layer's pieces recomposing to that layer with zero difference
(art_source/imgdiff.py) and no pixel in two pieces.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np
from PIL import Image, ImageDraw

from imgdiff import pixel_diff
from jr_lib import to_image, RGB, T, IDX, SCALE, Canvas
import jr_room
import jr_mock
import jr_pieces
from jr_track import recompose
from jr_geom import (WALKABLE, CHAIR_POINT, CHAIR_SPOT, DESK_X0, DESK_X1, FLOOR_Y,
                     DESK_FRONT_Y, DESK_TOP_Y, DOOR_OPEN_X0, DOOR_OPEN_X1, DOOR_X0, DOOR_X1,
                     DOOR_TOP, PC_X0, PC_X1)

PROJECT = os.path.normpath(os.path.join(HERE, '..', '..'))
ASSETS = os.path.realpath(os.path.join(PROJECT, 'Assets'))
SHIP_DIR = os.path.join(PROJECT, 'Assets', 'Environment', 'JordanRoom')
SHIP_GD = os.path.join(PROJECT, 'Scripts', 'JordanRoomPieces.gd')
RES_DIR = 'res://Assets/Environment/JordanRoom/'
APPROVED = os.path.join(HERE, 'approval', 'layers')
ASEPRITE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"


def refuse_assets(path):
    rp = os.path.realpath(path)
    try:
        inside = os.path.commonpath([rp.lower(), ASSETS.lower()]) == ASSETS.lower()
    except ValueError:
        inside = False
    if inside:
        raise SystemExit('refusing to write under Assets without --ship: %s' % rp)
    return rp


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def stats(c):
    a = c.a
    op = a != T
    n = int(op.sum())
    return n, int((a == IDX['K']).sum()), len(set(a[op].tolist()))


def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b', *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('aseprite failed %s\n%s\n%s' % (args, r.stdout, r.stderr))


# ---------------------------------------------------------------- checks
def check_layers(layers, again, comp):
    ok = all(np.array_equal(layers[k].a, again[k].a) for k in layers)
    print('  two builds identical: %s' % ('ok' if ok else 'FAIL'))
    fw = Canvas()
    fw.blit(layers['room_floor'])
    fw.blit(layers['room_walls'])
    holes = int((fw.a == T).sum())
    print('  floor+walls cover the screen: %s (%d holes)' % ('ok' if holes == 0 else 'FAIL', holes))
    ok &= holes == 0 and int((comp.a == T).sum()) == 0
    pal = {tuple(v) for v in RGB.tolist()}
    for name, c in layers.items():
        im = np.array(to_image(c))
        al = set(np.unique(im[:, :, 3]).tolist())
        rgb = im[im[:, :, 3] > 0][:, :3]
        off = {tuple(v) for v in np.unique(rgb, axis=0).tolist()} - pal
        n, black, cols = stats(c)
        approved = os.path.join(APPROVED, name + '.png')
        if os.path.exists(approved):
            d = pixel_diff(to_image(c), Image.open(approved))
            appr = 'identical to the approved layer' if d is None else 'DIFFERS from approved: ' + d
        else:
            d, appr = None, '(no approved copy to compare)'
        good = not off and al <= {0, 255} and d is None
        print('  %-15s %6d px  black %5.1f%%  %2d colours  %s  %s' % (
            name, n, 100.0 * black / max(1, n), cols,
            'palette/alpha ok' if not off and al <= {0, 255} else 'FAIL off-palette %s' % sorted(off)[:3],
            appr))
        ok &= good
    n, black, cols = stats(comp)
    print('  %-15s %6d px  black %5.1f%%  %2d colours' % ('composite', n, 100.0 * black / n, cols))
    return ok


def check_pieces(layers, pieces):
    ok = True
    total = 0
    for name, c in layers.items():
        short = jr_pieces.SHORT[name]
        ps = pieces[short]
        img, cover = recompose(ps)
        d = pixel_diff(Image.fromarray(img, 'RGBA'), to_image(c))
        overlap = int((cover > 1).sum())
        dims = [max(p[3].shape[:2]) for p in ps]
        print('  %-10s %3d pieces  recomposed: %s  overlaps: %d  largest side %d' % (
            short, len(ps), 'zero difference' if d is None else 'DIFF ' + d, overlap, max(dims)))
        ok &= d is None and overlap == 0
        total += len(ps)
    print('  total pieces: %d' % total)
    return ok


# ---------------------------------------------------------------- writers
def piece_paths(pieces):
    """[(layer, index, file name, x, y, rgba)] in the order they are listed."""
    out = []
    for short in ('floor', 'walls', 'furniture', 'props', 'clutter'):
        for i, (_, x0, y0, crop) in enumerate(pieces[short]):
            out.append((short, i, '%s_%03d.png' % (short, i), x0, y0, crop))
    return out


def gd_source(pieces):
    counts = {k: len(v) for k, v in pieces.items()}
    lines = [
        'extends RefCounted',
        '',
        "# Jordan's room, cut for the crumble. GENERATED by art_source/jordan_room/jr_export.py --ship;",
        '# do not edit by hand, rebuild it.',
        '#',
        '# Layer -> its pieces, bottom to top: floor, walls, furniture, props, clutter. Each piece is a',
        '# trimmed PNG of its layer; "at" is the texel where its top-left sits on the 640x360 layer, which',
        '# is drawn from the screen\'s origin at x3 (screen px = at * 3). The pieces of a layer tile it',
        '# exactly: every opaque pixel is in one piece. A whole prop is one piece (props that overlap are',
        '# one piece); floor and walls are ragged chunks of at most 40x40 texels; the monitors\' glow in',
        '# the furniture layer is cut on a grid twice as coarse. Textures are paths, loaded at runtime.',
        '#',
        '# Pieces: floor %d, walls %d, furniture %d, props %d, clutter %d (%d in all).' % (
            counts['floor'], counts['walls'], counts['furniture'], counts['props'],
            counts['clutter'], sum(counts.values())),
        '',
        'const PIECES := {',
    ]
    cur = None
    for (short, i, fname, x0, y0, crop) in piece_paths(pieces):
        if short != cur:
            if cur is not None:
                lines.append('\t],')
            lines.append('\t&"%s": [' % short)
            cur = short
        lines.append('\t\t{"texture": "%sPieces/%s", "at": Vector2(%d, %d)},' % (RES_DIR, fname, x0, y0))
    lines.append('\t],')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def write_pieces(folder, pieces):
    os.makedirs(folder, exist_ok=True)
    for (short, i, fname, x0, y0, crop) in piece_paths(pieces):
        Image.fromarray(crop, 'RGBA').save(os.path.join(folder, fname))


def write_aseprite(layer_dir, out_path):
    aseprite('--script-param', 'dir=' + layer_dir.replace('\\', '/'),
             '--script-param', 'layers=' + ','.join(jr_room.LAYER_ORDER),
             '--script-param', 'out=' + out_path.replace('\\', '/'),
             '--script', os.path.join(HERE, 'jr_layers.lua'))


def check_aseprite(ase, layer_dir, native_png):
    ok = True
    tmp = tempfile.mkdtemp(prefix='jroom_rt_')
    try:
        aseprite('--script-param', 'in=' + ase.replace('\\', '/'),
                 '--script-param', 'dir=' + tmp.replace('\\', '/'),
                 '--script', os.path.join(HERE, 'jr_unpack.lua'))
        for name in jr_room.LAYER_ORDER:
            d = pixel_diff(Image.open(os.path.join(layer_dir, name + '.png')),
                           Image.open(os.path.join(tmp, name + '.png')))
            print('  .aseprite %-15s %s' % (name, 'reads back pixel-identical' if d is None
                                              else 'FAIL ' + d))
            ok &= d is None
        flat = os.path.join(tmp, 'flat.png')
        aseprite(ase.replace('\\', '/'), '--save-as', flat.replace('\\', '/'))
        d = pixel_diff(Image.open(flat), Image.open(native_png))
        print('  .aseprite flattened        %s' % ('equals the composite' if d is None else 'FAIL ' + d))
        ok &= d is None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return ok


def layers_sheet(layers, comp):
    pw, ph, lab = 640, 360, 18
    names = list(layers.keys()) + ['composite']
    sheet = Image.new('RGB', (pw * 2 + 30, (ph + lab + 10) * 3 + 10), (20, 20, 26))
    d = ImageDraw.Draw(sheet)
    chk = Image.new('RGBA', (pw, ph), (0, 0, 0, 255))
    px = chk.load()
    for y in range(ph):
        for x in range(pw):
            if ((x // 8) + (y // 8)) % 2:
                px[x, y] = (38, 38, 46, 255)
    for i, name in enumerate(names):
        c = comp if name == 'composite' else layers[name]
        bg = chk.copy()
        bg.alpha_composite(to_image(c))
        col, row = i % 2, i // 2
        x0, y0 = 10 + col * (pw + 10), 10 + row * (ph + lab + 10)
        d.text((x0, y0), ('%d. ' % (i + 1) if name != 'composite' else '') + name, fill=(230, 230, 240))
        sheet.paste(bg.convert('RGB'), (x0, y0 + lab))
    return sheet


def pieces_sheet(pieces):
    """Every piece pulled apart a little, per layer, for review."""
    sheet = Image.new('RGB', (1300, 5 * 390 + 10), (20, 20, 26))
    d = ImageDraw.Draw(sheet)
    for li, short in enumerate(('floor', 'walls', 'furniture', 'props', 'clutter')):
        y0 = 10 + li * 390
        d.text((10, y0), '%s: %d pieces (spread apart)' % (short, len(pieces[short])),
               fill=(230, 230, 240))
        canvas = Image.new('RGBA', (1280, 360), (12, 10, 18, 255))
        for (_, x, y, crop) in pieces[short]:
            h, w = crop.shape[:2]
            cx, cy = x + w / 2.0, y + h / 2.0
            nx = int(round(cx * 1.9 - w / 2.0 + 10))
            ny = int(round((cy - 180) * 1.0 + 180 - h / 2.0))
            canvas.alpha_composite(Image.fromarray(crop, 'RGBA'), (max(0, nx), max(0, ny)))
        sheet.paste(canvas.convert('RGB'), (10, y0 + 18))
    return sheet


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', help='review folder (never under Assets)')
    ap.add_argument('--pieces', action='store_true', help='with --out: also the pieces and the .gd')
    ap.add_argument('--ship', action='store_true', help='write the shipped files into the project')
    ap.add_argument('--replace', action='store_true', help='with --ship: allow overwriting')
    ap.add_argument('--no-aseprite', action='store_true')
    args = ap.parse_args()
    out = refuse_assets(args.out) if args.out else None

    layers, trackers = jr_room.build(track=True)
    again = jr_room.build()
    comp = jr_room.composite(layers)
    print('layers')
    ok = check_layers(layers, again, comp)
    pieces, labels, _ = jr_pieces.cut(layers, trackers)
    print('pieces')
    ok &= check_pieces(layers, pieces)
    if not ok:
        raise SystemExit('\nCHECKS FAILED - nothing written')

    if not out and not args.ship:
        print('\nbare run: all checks passed, nothing written (use --out <folder> or --ship)')
        return

    stage = tempfile.mkdtemp(prefix='jroom_stage_')
    try:
        # everything is made and checked in a staging folder first
        lay = os.path.join(stage, 'layers')
        os.makedirs(lay)
        for name, c in layers.items():
            to_image(c).save(os.path.join(lay, name + '.png'))
        to_image(comp).save(os.path.join(stage, 'jordan_room_native.png'))
        if not args.no_aseprite:
            write_aseprite(lay, os.path.join(stage, 'jordan_room.aseprite'))
            if not check_aseprite(os.path.join(stage, 'jordan_room.aseprite'), lay,
                                  os.path.join(stage, 'jordan_room_native.png')):
                raise SystemExit('\n.aseprite check failed - nothing written')
        write_pieces(os.path.join(stage, 'Pieces'), pieces)
        with open(os.path.join(stage, 'JordanRoomPieces.gd'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(gd_source(pieces))
        # the staged pieces, read back from disk, must still tile their layers
        for name in layers:
            short = jr_pieces.SHORT[name]
            back = []
            for (s, i, fname, x0, y0, _) in piece_paths(pieces):
                if s == short:
                    back.append((i, x0, y0, np.array(Image.open(os.path.join(stage, 'Pieces', fname)))))
            img, cover = recompose(back)
            d = pixel_diff(Image.fromarray(img, 'RGBA'), Image.open(os.path.join(lay, name + '.png')))
            if d is not None or int((cover > 1).sum()):
                raise SystemExit('staged %s pieces do not recompose: %s' % (short, d))

        if out:
            os.makedirs(os.path.join(out, 'layers'), exist_ok=True)
            for name in layers:
                shutil.copyfile(os.path.join(lay, name + '.png'), os.path.join(out, 'layers', name + '.png'))
            if not args.no_aseprite:
                shutil.copyfile(os.path.join(stage, 'jordan_room.aseprite'),
                                os.path.join(out, 'jordan_room.aseprite'))
            shutil.copyfile(os.path.join(stage, 'jordan_room_native.png'),
                            os.path.join(out, 'jordan_room_native.png'))
            room3 = to_image(comp, SCALE)
            room3.save(os.path.join(out, 'jordan_room_1080.png'))
            jr_mock.scale_mock(room3).save(os.path.join(out, 'jordan_room_scale_mock.png'))
            jr_mock.annotated(room3).save(os.path.join(out, 'jordan_room_layout.png'))
            layers_sheet(layers, comp).save(os.path.join(out, 'jordan_room_layers_sheet.png'))
            if args.pieces:
                if os.path.isdir(os.path.join(out, 'Pieces')):
                    shutil.rmtree(os.path.join(out, 'Pieces'))
                shutil.copytree(os.path.join(stage, 'Pieces'), os.path.join(out, 'Pieces'))
                shutil.copyfile(os.path.join(stage, 'JordanRoomPieces.gd'),
                                os.path.join(out, 'JordanRoomPieces.gd'))
                pieces_sheet(pieces).save(os.path.join(out, 'jordan_room_pieces_sheet.png'))
            print('\nreview set written ->', out)

        if args.ship:
            ship(stage, layers, pieces, args.replace, args.no_aseprite)
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    print('\nlayout (native texels; x3 for screen px)')
    print('  door opening x %d-%d (casing %d-%d, top %d), threshold y %d' % (
        DOOR_OPEN_X0, DOOR_OPEN_X1, DOOR_X0, DOOR_X1, DOOR_TOP, FLOOR_Y))
    print('  desk footprint x %d-%d, y %d-%d; PC x %d-%d' % (DESK_X0, DESK_X1, FLOOR_Y,
                                                              DESK_FRONT_Y - 1, PC_X0, PC_X1))
    print('  CHAIR_POINT %s, chair spot %s' % (CHAIR_POINT, CHAIR_SPOT))


def ship(stage, layers, pieces, replace, no_aseprite):
    """Copy the staged, checked files into the project; verify every copy."""
    plan = []
    for name in layers:
        short = jr_pieces.SHORT[name]
        plan.append((os.path.join(stage, 'layers', name + '.png'),
                     os.path.join(SHIP_DIR, 'room_%s.png' % short)))
    if not no_aseprite:
        plan.append((os.path.join(stage, 'jordan_room.aseprite'),
                     os.path.join(SHIP_DIR, 'jordan_room.aseprite')))
    for (s, i, fname, x0, y0, _) in piece_paths(pieces):
        plan.append((os.path.join(stage, 'Pieces', fname), os.path.join(SHIP_DIR, 'Pieces', fname)))
    plan.append((os.path.join(stage, 'JordanRoomPieces.gd'), SHIP_GD))
    for (_, dst) in plan:
        rp = os.path.realpath(dst)
        allowed = [os.path.realpath(SHIP_DIR), os.path.realpath(SHIP_GD)]
        if not (rp == allowed[1] or os.path.commonpath([rp.lower(), allowed[0].lower()]) ==
                allowed[0].lower()):
            raise SystemExit('refusing to ship outside the room folder: %s' % rp)
    exists = [dst for (_, dst) in plan if os.path.exists(dst)]
    if exists and not replace:
        raise SystemExit('refusing to overwrite %d existing file(s), e.g. %s (use --replace)' %
                         (len(exists), exists[0]))
    os.makedirs(os.path.join(SHIP_DIR, 'Pieces'), exist_ok=True)
    for (src, dst) in plan:
        shutil.copyfile(src, dst)
    bad = [dst for (src, dst) in plan if sha(src) != sha(dst)]
    if bad:
        raise SystemExit('COPY MISMATCH: %s' % bad[:3])
    n_pieces = sum(len(v) for v in pieces.values())
    print('\nshipped %d files (5 layers, %s%d pieces, the .gd), every copy verified by sha256' % (
        len(plan), '' if no_aseprite else '.aseprite, ', n_pieces))
    print('  ->', SHIP_DIR)
    print('  ->', SHIP_GD)
    # and the shipped pieces, read back from the project, tile the shipped layers
    for name in layers:
        short = jr_pieces.SHORT[name]
        back = []
        for (s, i, fname, x0, y0, _) in piece_paths(pieces):
            if s == short:
                back.append((i, x0, y0, np.array(Image.open(os.path.join(SHIP_DIR, 'Pieces', fname)))))
        img, cover = recompose(back)
        d = pixel_diff(Image.fromarray(img, 'RGBA'),
                       Image.open(os.path.join(SHIP_DIR, 'room_%s.png' % short)))
        print('  shipped %-10s %3d pieces recomposed vs shipped room_%s.png: %s' % (
            short, len(back), short, 'zero difference' if d is None and not int((cover > 1).sum())
            else 'FAIL %s' % d))


if __name__ == '__main__':
    main()
