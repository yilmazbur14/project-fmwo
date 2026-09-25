"""Build bixby_spin_slow.png (24 frames of 192x160), check it, measure it against the fast loop, and
render the previews.

    python slow_export.py            # SAFE: sheet, numbers and previews into the scratchpad only
    python slow_export.py --write    # ALSO writes Assets/Characters/Bixby/bixby_spin_slow.png and
                                     # .aseprite beside it, round-trip checked with imgdiff.pixel_diff

Never touches bixby_spin.png or any other sheet.
"""
import math
import os
import subprocess
import sys
from collections import Counter

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slow_spin as SS  # noqa: E402  (puts bixby_redesign and art_source on the path)
from pal import PAL  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
BIXBY = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby')
OLD = os.path.join(BIXBY, 'bixby_spin.png')
OUT_PNG = os.path.join(BIXBY, 'bixby_spin_slow.png')
OUT_ASE = os.path.join(BIXBY, 'bixby_spin_slow.aseprite')
ASEPRITE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'
SCRATCH = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
           'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/bixby_spin_slow/')
FW, FH = 192, 160
BG = (46, 49, 58, 255)
FRAME_S = 0.125               # 5 degrees every 0.125 s = 40 degrees a second
FLOOR_FLATTEN = 0.36          # BixbyCombinedArtLayout.FLOOR_FLATTEN


def strip(frames):
    out = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f, (i * FW, 0))
    return out


def old_frame(i):
    return Image.open(OLD).convert('RGBA').crop((i * FW, 0, (i + 1) * FW, FH))


def numbers(im):
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    cnt = Counter(px)
    return dict(opaque=len(px), colours=len(cnt), black=100.0 * cnt.get((0, 0, 0, 255), 0) / max(1, len(px)),
                semi=sum(1 for c in px if c[3] < 255), cnt=cnt)


def on(im, bg=BG):
    g = Image.new('RGBA', im.size, bg)
    g.alpha_composite(im)
    return g


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


#CHECKS

def check(frames):
    bad = 0
    # the loop closes: the frame after the last is frame 0
    d = pixel_diff(SS.frame(SS.N).image(), frames[0])
    print('frame %d (one past the last) vs frame 0: %s' % (SS.N, d or 'pixel-identical'))
    bad += d is not None
    # only palette colours, no semi-alpha, keyline pure black
    pal = set(PAL.values())
    for k, f in enumerate(frames):
        n = numbers(f)
        off = [c for c in n['cnt'] if c not in pal]
        if off or n['semi']:
            print('frame %d: %d off-palette colours, %d semi-alpha' % (k, len(off), n['semi']))
            bad += 1
    # every maw core sits on its anchor's texel, with the whole maw drawn round it unless a nearer
    # head (or the column, for a head going round behind it) is in front of it
    maw = {}
    for r, row in enumerate(SS.rig_spin.MAW):
        for c, ch in enumerate(row):
            if ch != '.':
                maw[(c - SS.rig_spin.MAW_C[0], r - SS.rig_spin.MAW_C[1])] = PAL[ch]
    hidden = []
    for k, f in enumerate(frames):
        px = f.load()
        for az, x, y, near in SS.anchors(k):
            X, Y = SS.maw_pixel(x, y)
            got = sum(1 for (dx, dy), c in maw.items()
                      if 0 <= X + dx < FW and 0 <= Y + dy < FH and px[X + dx, Y + dy] == c)
            if got != len(maw):
                hidden.append((k, az, got, len(maw)))
    for k, az, got, tot in hidden:
        print('  frame %2d maw at %5.1f: %d of %d maw texels showing' % (k, az, got, tot))
    print('maws fully drawn on their anchors: %d of %d' % (3 * len(frames) - len(hidden), 3 * len(frames)))
    return bad


def measure(frames):
    print('\n%-18s %7s %8s %8s' % ('', 'opaque', 'colours', 'black %'))
    old = []
    for i in (2, 3, 4, 5):
        n = numbers(old_frame(i))
        old.append(n)
        print('%-18s %7d %8d %8.2f' % ('old loop frame %d' % i, n['opaque'], n['colours'], n['black']))
    ob = sum(n['black'] for n in old) / 4.0
    oc = sum(n['colours'] for n in old) / 4.0
    new = [numbers(f) for f in frames]
    for k, n in enumerate(new):
        print('%-18s %7d %8d %8.2f' % ('new frame %d' % k, n['opaque'], n['colours'], n['black']))
    nb = [n['black'] for n in new]
    nc = [n['colours'] for n in new]
    print('\nold loop: black %.2f%% (%.2f-%.2f), colours %d-%d, mean %.1f' % (
        ob, min(n['black'] for n in old), max(n['black'] for n in old),
        min(n['colours'] for n in old), max(n['colours'] for n in old), oc))
    print('new loop: black %.2f%% (%.2f-%.2f), colours %d-%d, mean %.1f' % (
        sum(nb) / len(nb), min(nb), max(nb), min(nc), max(nc), sum(nc) / len(nc)))
    print('+/-10%% window: black %.2f-%.2f%%, colours %.1f-%.1f' % (ob * 0.9, ob * 1.1, oc * 0.9, oc * 1.1))
    ok = all(ob * 0.9 <= b <= ob * 1.1 for b in nb) and all(oc * 0.9 <= c <= oc * 1.1 for c in nc)
    sh = numbers(strip(frames))
    print('whole new sheet: colours %d, black %.2f%%;  every frame inside the window: %s' % (
        sh['colours'], sh['black'], ok))
    return ok


#PREVIEWS

def previews(frames, sh):
    os.makedirs(SCRATCH, exist_ok=True)
    sh.save(SCRATCH + 'bixby_spin_slow_scratch.png')
    # 1. every frame at 4x, one strip
    up(on(sh), 4).save(SCRATCH + 'strip_4x.png')
    # (and the same as a 6 x 4 grid, which is easier to look at)
    cols, gap = 6, 4
    rows = (len(frames) + cols - 1) // cols
    grid = Image.new('RGBA', (cols * (FW + gap) - gap, rows * (FH + gap) - gap), (18, 17, 22, 255))
    for k, f in enumerate(frames):
        grid.alpha_composite(on(f), ((k % cols) * (FW + gap), (k // cols) * (FH + gap)))
    up(grid, 2).save(SCRATCH + 'grid_2x.png')
    # 2. the old loop's frame 2 beside the new frame 0
    pair = Image.new('RGBA', (2 * FW + 6, FH), (18, 17, 22, 255))
    pair.alpha_composite(on(old_frame(2)), (0, 0))
    pair.alpha_composite(on(frames[0]), (FW + 6, 0))
    up(pair, 4).save(SCRATCH + 'old2_vs_new0_4x.png')
    # 3. the loop at 40 degrees a second, 3x (game scale), and a copy with the maw anchors marked
    gif(frames, SCRATCH + 'loop_40dps_3x.gif')
    gif([mark(f, k) for k, f in enumerate(frames)], SCRATCH + 'loop_40dps_anchors_3x.gif', s=1)
    up(on(mark(frames[0], 0)), 2).save(SCRATCH + 'anchors_frame0_6x.png')


def gif(frames, path, s=3, times=None):
    """times in seconds per frame. GIF delays are whole centiseconds, so 0.125 s is written as
    alternating 12 and 13 cs with the rounding carried over: the loop keeps its true 40 deg/s."""
    ims = [up(on(f), s).convert('RGB') for f in frames]
    times = times or [FRAME_S] * len(ims)
    durs, t = [], 0.0
    for dt in times:
        durs.append(10 * (int(round((t + dt) * 100)) - int(round(t * 100))))
        t += dt
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=2)


def beam_angle(az):
    r = math.radians(az)
    return math.atan2(math.sin(r) * FLOOR_FLATTEN, math.cos(r))


def mark(f, k, s=3):
    """Frame k at 3x with each maw anchor marked where the game puts the beam: a cross at the exact
    point, and a ray the way the beam fires (cyan near the camera, magenta far)."""
    im = up(on(f), s)
    d = ImageDraw.Draw(im)
    for az, x, y, near in SS.anchors(k):
        col = (60, 240, 255, 255) if near else (255, 70, 220, 255)
        X, Y = x * s, y * s
        a = beam_angle(az)
        d.line([(X, Y), (X + math.cos(a) * 16 * s, Y + math.sin(a) * 16 * s)], fill=col, width=1)
        d.line([(X - 4, Y), (X + 4, Y)], fill=col)
        d.line([(X, Y - 4), (X, Y + 4)], fill=col)
    d.text((4, 4), 'frame %d  (%s)' % (k, ', '.join('%g' % a[0] for a in SS.anchors(k))), fill=(255, 255, 255, 255))
    return im


def joins(frames, entry=22, exit_=1):
    """spin_up (old 0, 1) -> the new loop from `entry`, once round -> leave after `exit_` -> spin_down
    (old 6, 7), as the fight would play it at 40 degrees a second."""
    seq = [(old_frame(0), 0.11), (old_frame(1), 0.09)]
    k = entry
    for _ in range(SS.N):
        seq.append((frames[k], FRAME_S))
        k = (k + 1) % SS.N
    while True:
        seq.append((frames[k], FRAME_S))
        if k == exit_:
            break
        k = (k + 1) % SS.N
    seq += [(old_frame(6), 0.2), (old_frame(7), 0.3)]
    gif([f for f, _ in seq], SCRATCH + 'joins_entry%d_exit%d_3x.gif' % (entry, exit_),
        times=[t for _, t in seq])
    # and the join frames side by side at 4x: old 1 | entry, and exit | old 6
    row = Image.new('RGBA', (4 * FW + 3 * 4 + 12, FH), (18, 17, 22, 255))
    for i, im in enumerate([old_frame(1), frames[entry], frames[exit_], old_frame(6)]):
        row.alpha_composite(on(im), (i * (FW + 4) + (12 if i >= 2 else 0), 0))
    up(row, 3).save(SCRATCH + 'joins_3x.png')


#WRITING

def aseprite_roundtrip(png, ase):
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True)
    back = SCRATCH + '_roundtrip.png'
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True)
    return pixel_diff(Image.open(png), Image.open(back))


if __name__ == '__main__':
    frames = SS.frames()
    sh = strip(frames)
    print('bixby_spin_slow: %d frames of %dx%d, %d degrees a frame, sheet %dx%d' % (
        len(frames), FW, FH, SS.STEP, sh.width, sh.height))
    bad = check(frames)
    ok = measure(frames)
    previews(frames, sh)
    joins(frames)
    print('\nMOUTH_ANCHORS for bixby_spin_slow.png:')
    print(SS.table())
    if '--write' in sys.argv:
        if bad or not ok:
            sys.exit('not writing: the checks above failed')
        sh.save(OUT_PNG)                                  # one save
        print('\nwrote', OUT_PNG)
        d = aseprite_roundtrip(OUT_PNG, OUT_ASE)
        print('wrote', OUT_ASE, '- aseprite round trip:', d or 'pixel-exact')
        back = pixel_diff(Image.open(OUT_PNG), sh)
        print('written png vs built sheet:', back or 'pixel-exact')
