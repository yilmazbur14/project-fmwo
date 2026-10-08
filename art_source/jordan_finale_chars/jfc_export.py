"""Write the finale-cutscene character sheets, each PNG with its .aseprite beside it, plus the
previews (a labelled 4x contact sheet and one GIF per beat).

    python jfc_export.py            # build and check everything, print the numbers; writes nothing
    python jfc_export.py --write    # write into THIS folder (sheets) and ./preview (contact + GIFs)
    python jfc_export.py --ship     # ship the three approved sheets into Assets as NEW files only

--write only ever writes inside art_source/jordan_finale_chars/, and refuses any output folder that
resolves (realpath, so 8.3 short names can't slip past) under the project's Assets/.

--ship (approved by the user 2026-09-28: "approve jordans seated sprites and the moustache") writes
exactly six files and nothing else: jordan_seated (.png, .aseprite) into Assets/Characters/Jordan/Room/
and player_moustache and moustache_prop (.png, .aseprite) into Assets/Characters/MainPlayer/. It
refuses if any of the six already exists (each is created exclusively, so nothing can be
overwritten), if a frame fails its checks, or if the fitted tee no longer matches the fight sheets'
refit (jfc_front.check_fit_matches). It runs no Godot import: the editor imports new files on focus.

Sheets written: jordan_seated, player_moustache, moustache_prop (.png + .aseprite). Every .aseprite is
made by Aseprite's CLI from the PNG and re-exported to check it round-trips pixel for pixel
(art_source/imgdiff.pixel_diff: alpha everywhere, colour wherever a pixel shows).
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jfc_base as B  # noqa: E402
import jfc_sheets as S  # noqa: E402
import jfc_player as P  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ASSETS = os.path.join(B.ROOT, 'Assets')
PREVIEW = os.path.join(HERE, 'preview')


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def _guard(folder):
    if _under(folder, ASSETS):
        raise SystemExit('refusing to write under Assets/: %s' % folder)
    if not _under(folder, HERE):
        raise SystemExit('refusing to write outside art_source/jordan_finale_chars/: %s' % folder)


#SHEETS

def write_sheet(name, im, folder):
    """PNG + .aseprite, built in a temp folder and moved into place; returns the round-trip result."""
    _guard(folder)
    tmp = tempfile.mkdtemp(prefix='jfc_')
    tpng, tase = os.path.join(tmp, name + '.png'), os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    subprocess.run([B.ASEPRITE, '-b', tpng, '--save-as', tase], check=True, capture_output=True)
    back = os.path.join(tmp, 'rt.png')
    subprocess.run([B.ASEPRITE, '-b', tase, '--save-as', back], check=True, capture_output=True)
    d = B.pixel_diff(Image.open(tpng), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    os.makedirs(folder, exist_ok=True)
    png, ase = os.path.join(folder, name + '.png'), os.path.join(folder, name + '.aseprite')
    os.replace(tpng, png)
    os.replace(tase, ase)
    back2 = os.path.join(tmp, 'rt2.png')
    subprocess.run([B.ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
    return png, ase, B.pixel_diff(Image.open(png), Image.open(back2))


#PREVIEWS

BGC = (46, 49, 58, 255)          # the rig's preview grey
FLOOR = (74, 62, 58, 255)        # a dim, warm floor for the GIFs (the room is the room artist's)
TXT = (230, 230, 236, 255)
GOLD = (240, 200, 90, 255)


def up(im, s, bg=BGC):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def cells(strip, w, h):
    return [strip.crop((i * w, 0, i * w + w, h)) for i in range(strip.width // w)]


def contact_sheet(seated, player, prop, s=4):
    """Every frame at 4x, labelled, grouped by sheet (Matt's intro contact sheet's layout)."""
    pad, lab, title = 10, 16, 20
    blocks = []

    def block(head, tiles, per_row):
        tw, th = tiles[0][1].width, tiles[0][1].height
        rows = (len(tiles) + per_row - 1) // per_row
        w = per_row * (tw + pad) + pad
        h = title + rows * (th + lab + pad) + pad
        out = Image.new('RGBA', (w, h), (12, 12, 14, 255))
        d = ImageDraw.Draw(out)
        d.text((pad, 4), head, fill=GOLD)
        for i, (name, im) in enumerate(tiles):
            r, c = divmod(i, per_row)
            x, y = pad + c * (tw + pad), title + r * (th + lab + pad)
            d.text((x, y), name, fill=TXT)
            out.paste(im, (x, y + lab))
        return out

    st = [('%d %s' % (i, S.SEATED_NAMES[i]), up(c, s)) for i, c in enumerate(cells(seated, 128, 128))]
    blocks.append(block('jordan_seated.png  11 frames of 128x128, anchor (64,127) = chair floor contact', st, 4))
    pc = []
    for ri, rn in enumerate(P.ROWS):
        for ci, cn in enumerate(P.COLS):
            pc.append(('%s %d %s' % (rn, ci, cn), up(player.crop((ci * 32, ri * 32, ci * 32 + 32, ri * 32 + 32)), s)))
    blocks.append(block('player_moustache.png  8 cols x 4 rows of 32x32 (rows DOWN, UP, LEFT, RIGHT)', pc, 8))
    pr = [('%d %s' % (i, ['level', 'tip right', 'ends up', 'tip left', 'landed'][i]), up(c, s * 2))
          for i, c in enumerate(cells(prop, 16, 16))]
    blocks.append(block('moustache_prop.png  5 frames of 16x16 (shown at 8x), pivot (8,8); f4 lowest texel row 15', pr, 5))
    W = max(b.width for b in blocks)
    H = sum(b.height for b in blocks)
    out = Image.new('RGBA', (W, H), (12, 12, 14, 255))
    y = 0
    for b in blocks:
        out.paste(b, (0, y))
        y += b.height
    return out


def gif(path, frames, durations, s, bg=FLOOR, size=None):
    """frames: RGBA images (same size). Composited on an opaque floor, scaled, looping."""
    ims = []
    for f in frames:
        base = Image.new('RGBA', f.size, bg)
        base.alpha_composite(f)
        big = base.resize((f.width * s, f.height * s), Image.NEAREST).convert('RGB')
        ims.append(big.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=[int(d * 1000) for d in durations],
                loop=0, disposal=1, optimize=False)
    return path


def player_cell(player, rn, cn):
    ri, ci = P.ROWS.index(rn), P.COLS.index(cn)
    return player.crop((ci * 32, ri * 32, ci * 32 + 32, ri * 32 + 32))


def fall_frames(player, prop):
    """The moustache coming off: the player facing right (talk frame without it = 'caught' held
    back), the prop drifting down from his lip to the floor with its flutter, then lying there."""
    W, H = 48, 40
    body = player_cell(player, 'RIGHT', 'caught')
    lip = P.MOUSTACHE_LIP['RIGHT']
    start = (8 + lip[0], 4 + lip[1])          # the lip texel in this little stage
    floor_y = 4 + 28                          # his sole row in the stage
    out, times = [], []
    # hold: on his face
    f = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f.alpha_composite(player_cell(player, 'RIGHT', 'idle'), (8, 4))
    out += [f] * 1
    times += [0.5]
    cells_ = cells(prop, 16, 16)
    seq = [0, 1, 2, 3] * 4
    import math
    n = len(seq)
    for i, k in enumerate(seq):
        t = (i + 1) / float(n)
        y = start[1] + t * (floor_y - 1 - start[1])
        x = start[0] + 3.0 * math.sin(t * math.pi * 3.0) + 2 * t
        f = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        f.alpha_composite(body, (8, 4))
        f.alpha_composite(cells_[k], (int(round(x)) - 8, int(round(y)) - 8))
        out.append(f)
        times.append(0.12)
    f = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    f.alpha_composite(body, (8, 4))
    f.alpha_composite(cells_[4], (int(round(start[0] + 2)) - 8, floor_y - 15))
    out.append(f)
    times.append(1.2)
    return out, times


def facings_frames(player):
    """The moustache on in each facing: idle / talk pairs in DOWN, RIGHT, LEFT, then his back (UP)."""
    out, times = [], []
    for rn in ('DOWN', 'RIGHT', 'LEFT'):
        for _ in range(3):
            out += [player_cell(player, rn, 'idle'), player_cell(player, rn, 'talk')]
            times += [0.22, 0.16]
    out.append(player_cell(player, 'UP', 'idle'))
    times.append(0.8)
    return out, times


def putting_on_frames(player):
    """Turned to the camera: reach, press, done (smug), then back RIGHT to wind up and tap."""
    seq = [('DOWN', 'caught', 0.01)]
    seq = [('UP', 'idle', 0.5), ('DOWN', 'idle', 0.0)]
    out, times = [], []
    order = [('DOWN', 'reach', 0.3), ('DOWN', 'press', 0.35), ('DOWN', 'press', 0.2), ('DOWN', 'done', 0.7),
             ('RIGHT', 'idle', 0.4), ('RIGHT', 'tap_windup', 0.18), ('RIGHT', 'tap', 0.14),
             ('RIGHT', 'tap_windup', 0.12), ('RIGHT', 'tap', 0.3), ('RIGHT', 'idle', 0.5)]
    for rn, cn, t in order:
        out.append(player_cell(player, rn, cn))
        times.append(t)
    return out, times


def stage_mock(seated, player):
    """Both at the cutscene's 3x on a flat floor, the player at Jordan's left elbow (the plan's talk
    spot is on his left): (a) the tap, back view; (b) the friendly talk; then the gag at the camera's
    2x zoom. Placement only illustrates the scale; the room and staging are the coder's."""
    sc = cells(seated, 128, 128)
    W, H = 128, 128
    ax, ay = B.ANCHOR
    # the player's soles 26 texels left of and 19 above the chair's floor contact: his tap glove
    # (RIGHT col 5, texels (23-24, 4-5)) then lands on Jordan's left elbow in frames 0-3
    feet = (ax - 26, ay - 19)
    pcx, psole = 15, 28

    def scene(jframe, pcell, player_front=True):
        f = Image.new('RGBA', (W, H), FLOOR)
        pl = (feet[0] - pcx, feet[1] - psole)
        if not player_front:
            f.alpha_composite(pcell, pl)
        f.alpha_composite(jframe)
        if player_front:
            f.alpha_composite(pcell, pl)
        return f

    a = scene(sc[0], player_cell(player, 'RIGHT', 'tap'))
    b = scene(sc[6], player_cell(player, 'RIGHT', 'idle'))
    c = scene(sc[8], player_cell(player, 'RIGHT', 'caught'))
    big = [x.resize((W * 3, H * 3), Image.NEAREST) for x in (a, b, c)]
    zoom = b.crop((20, 30, 84, 126)).resize((64 * 6, 96 * 6), Image.NEAREST)
    out = Image.new('RGBA', (W * 3 * 3 + zoom.width + 40, max(H * 3, zoom.height) + 24), (12, 12, 14, 255))
    d = ImageDraw.Draw(out)
    labels = ['3x: tap (frames 0 + RIGHT 5)', '3x: friendly (6 + RIGHT 0)', '3x: glare (8 + RIGHT 7)',
              'camera 2x on the gag (= 6x)']
    x = 0
    for i, im in enumerate(big + [zoom]):
        d.text((x + 4, 4), labels[i], fill=TXT)
        out.paste(im, (x, 24))
        x += im.width + 10
    return out


def build_all():
    rows, problems = S.check_seated()
    info, p2 = S.check_player()
    return rows, info, problems + p2


def write_all():
    rows, info, problems = build_all()
    if problems:
        raise SystemExit('not writing; problems:\n  ' + '\n  '.join(problems))
    seated = S.seated_image()
    player = P.sheet_image()
    prop = P.prop_image()
    res = []
    for name, im in (('jordan_seated', seated), ('player_moustache', player), ('moustache_prop', prop)):
        res.append((name,) + write_sheet(name, im, HERE))
    _guard(PREVIEW)
    os.makedirs(PREVIEW, exist_ok=True)
    contact_sheet(seated, player, prop).save(os.path.join(PREVIEW, 'contact_4x.png'))
    sc = cells(seated, 128, 128)
    T = S.SEATED_TIMES
    gif(os.path.join(PREVIEW, 'jordan_gaming.gif'), sc[0:4], T[0:4], 3)
    gif(os.path.join(PREVIEW, 'jordan_turn_friendly.gif'),
        [sc[0], sc[1], sc[4], sc[4], sc[5], sc[6], sc[7], sc[6], sc[7], sc[6], sc[7], sc[6]],
        [0.4, 0.3, 0.45, 0.25, 0.1, 0.25, 0.14, 0.2, 0.14, 0.2, 0.14, 0.9], 3)
    gif(os.path.join(PREVIEW, 'jordan_glare.gif'),
        [sc[6], sc[8], sc[9], sc[8], sc[9], sc[8], sc[9], sc[8], sc[10]],
        [0.6, 0.3, 0.14, 0.2, 0.14, 0.2, 0.14, 0.6, 0.8], 3)
    fr, tm = facings_frames(player)
    gif(os.path.join(PREVIEW, 'player_moustache_facings.gif'), fr, tm, 6)
    fr, tm = putting_on_frames(player)
    gif(os.path.join(PREVIEW, 'player_put_on_and_tap.gif'), fr, tm, 6)
    fr, tm = fall_frames(player, prop)
    gif(os.path.join(PREVIEW, 'moustache_fall.gif'), fr, tm, 6)
    stage_mock(seated, player).save(os.path.join(PREVIEW, 'stage_mock_3x.png'))
    return res


#SHIPPING (the approved sheets, as new files only)

SHIP = {
    'jordan_seated': os.path.join(ASSETS, 'Characters', 'Jordan', 'Room'),
    'player_moustache': os.path.join(ASSETS, 'Characters', 'MainPlayer'),
    'moustache_prop': os.path.join(ASSETS, 'Characters', 'MainPlayer'),
}


def _sha256(path):
    import hashlib
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def _create_new(src, dest):
    """Copy src to dest, which must not exist ('x' mode: an existing file makes this fail, so no file
    can be overwritten even if one appeared after the checks)."""
    with open(src, 'rb') as f:
        data = f.read()
    with open(dest, 'xb') as f:
        f.write(data)


def ship():
    rows, info, problems = build_all()
    if problems:
        raise SystemExit('not shipping; problems:\n  ' + '\n  '.join(problems))
    import jfc_front
    fit = jfc_front.check_fit_matches()
    if fit:
        raise SystemExit('not shipping: the fitted tee no longer matches the fight sheets\' refit (%s)' % fit)
    sheets = {'jordan_seated': S.seated_image(), 'player_moustache': P.sheet_image(),
              'moustache_prop': P.prop_image()}
    targets = []
    for name, folder in SHIP.items():
        if not _under(folder, os.path.join(ASSETS, 'Characters')):
            raise SystemExit('refusing: %s is not under Assets/Characters' % folder)
        for ext in ('.png', '.aseprite'):
            dest = os.path.join(folder, name + ext)
            if os.path.lexists(dest):
                raise SystemExit('refusing: %s already exists (new files only)' % dest)
            targets.append(dest)
    staged = {}
    for name, im in sheets.items():
        tmp = tempfile.mkdtemp(prefix='jfc_ship_')
        tpng, tase = os.path.join(tmp, name + '.png'), os.path.join(tmp, name + '.aseprite')
        im.save(tpng)
        subprocess.run([B.ASEPRITE, '-b', tpng, '--save-as', tase], check=True, capture_output=True)
        back = os.path.join(tmp, 'rt.png')
        subprocess.run([B.ASEPRITE, '-b', tase, '--save-as', back], check=True, capture_output=True)
        d = B.pixel_diff(Image.open(tpng), Image.open(back))
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
        staged[name] = (tpng, tase, tmp)
    out = []
    for name, (tpng, tase, tmp) in staged.items():
        folder = SHIP[name]
        os.makedirs(folder, exist_ok=True)
        png, ase = os.path.join(folder, name + '.png'), os.path.join(folder, name + '.aseprite')
        _create_new(tpng, png)
        _create_new(tase, ase)
        # the shipped files, checked where they landed: the PNG is the build, the .aseprite re-exports to it
        d_png = B.pixel_diff(Image.open(png), sheets[name])
        back2 = os.path.join(tmp, 'rt2.png')
        subprocess.run([B.ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
        d_ase = B.pixel_diff(Image.open(png), Image.open(back2))
        out.append((name, png, ase, d_png, d_ase, _sha256(png), _sha256(ase), Image.open(png).size))
    return out


if __name__ == '__main__':
    if '--ship' in sys.argv:
        for name, png, ase, d_png, d_ase, h_png, h_ase, size in ship():
            print('shipped', png, size, 'png == build:', d_png or 'identical', 'sha256', h_png)
            print('shipped', ase, '.aseprite round-trip:', d_ase or 'identical', 'sha256', h_ase)
    elif '--write' in sys.argv:
        for name, png, ase, d in write_all():
            print('wrote', png, '+ .aseprite, round-trip:', 'identical' if d is None else d)
        print('previews in', PREVIEW)
    else:
        rows, info, problems = build_all()
        for r in rows:
            print('f%-2d %-14s opaque %4d colours %2d black %.3f (him alone %.3f) semi %d lint %s floor row %d x %s' % r)
        print(info)
        print('problems:', problems or 'none', '(bare run: nothing written; --write to write)')
