"""Ship Josh's ride sheets (anims_ride.py): mount, glide, drop_bomb, dismount.

    python export_ride.py preview OUTDIR     # contact sheet + GIFs + numbers, writes no assets
    python export_ride.py ship OUTDIR        # also writes each PNG (in one go) and its .aseprite,
                                             # and checks the .aseprite re-exports pixel-identical

Numbers printed per sheet: opaque pixels, colours (and any not in lib.PAL), black ratio, keyline
colour, sole rows per frame. Layout numbers: RIDE_HEADROOM, HAND_BOMB, the drawn extent.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import anims_ride as R                                           # noqa: E402
import lib                                                       # noqa: E402
from imgdiff import pixel_diff                                   # noqa: E402
from PIL import Image, ImageDraw                                 # noqa: E402

ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh'))
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

# name: frame times, as FINAL_ANIMS plays them (the last repeats), and whether it loops
TIMES = {
    'josh_mount': ([0.16, 0.13, 0.2], False),
    'josh_glide': ([0.11, 0.11, 0.11, 0.11], True),
    'josh_drop_bomb': ([0.09, 0.08, 0.13], False),
    'josh_dismount': ([0.12, 0.16, 0.24], False),
}
ORDER = ['josh_mount', 'josh_glide', 'josh_drop_bomb', 'josh_dismount']
GLIDER_FRAME_TIME = 0.11
MOUNT_GROW = 0.4          # JoshCardsStateMachine.mount_grow_time, TRANS_BACK ease-out
DISMOUNT_SHRINK = 0.15    # JoshCardsDismount.GLIDER_SHRINK, TRANS_QUAD ease-in
BG = (30, 32, 40, 255)


#MEASURING

def frames(im):
    return [im.crop((80 * i, 0, 80 * i + 80, 80)) for i in range(im.width // 80)]


def px_list(im):
    flat = getattr(im, 'get_flattened_data', None)
    return list(flat() if flat else im.getdata())


def numbers(name, im):
    pal = set(lib.PAL.values())
    px = [c for c in px_list(im) if c[3]]
    cols = set(px)
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    out = {
        'opaque': len(px), 'colours': len(cols), 'off_palette': sorted(c for c in cols if c not in pal),
        'black': black / max(1, len(px)),
        'semi': sum(1 for c in px if c[3] != 255),
        'soles': [], 'tops': [], 'extent': [],
    }
    for f in frames(im):
        rows = [y for y in range(80) for x in range(80) if f.getpixel((x, y))[3]]
        cols_ = [x for y in range(80) for x in range(80) if f.getpixel((x, y))[3]]
        out['soles'].append(max(rows))
        out['tops'].append(min(rows))
        out['extent'].append((min(cols_), min(rows), max(cols_), max(rows)))
    return out


def solid_bbox(f, min_blob=12):
    """Bounding box of the drawn texels ignoring any connected blob smaller than min_blob px (a stray
    glint or spark), for the layout's BODY_DRAWN."""
    seen, keep = set(), set()
    opaque = {(x, y) for y in range(80) for x in range(80) if f.getpixel((x, y))[3]}
    for p in opaque:
        if p in seen:
            continue
        blob, stack = [], [p]
        seen.add(p)
        while stack:
            q = stack.pop()
            blob.append(q)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    r = (q[0] + dx, q[1] + dy)
                    if r in opaque and r not in seen:
                        seen.add(r)
                        stack.append(r)
        if len(blob) >= min_blob:
            keep.update(blob)
    xs = [p[0] for p in keep]
    ys = [p[1] for p in keep]
    return min(xs), min(ys), max(xs), max(ys)


def hand_bomb():
    """Centre of the bomb card drawn on drop_bomb frame 1 (its face, border and keyline)."""
    c, _ = R.bomb_card_f1()
    xs = [p[0] for p in c]
    ys = [p[1] for p in c]
    return (sum(xs) / len(xs), sum(ys) / len(ys)), (min(xs), min(ys), max(xs), max(ys))


#PREVIEWS

def ease_back_out(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def glider_scaled(gframe, s, scale):
    """The glider at node scale s about his feet anchor, for a preview drawn at `scale`: returns
    (image, top-left) in preview pixels, or None when it is too small to draw."""
    if s <= 0.02:
        return None
    w = max(1, int(round(64 * scale * s)))
    h = max(1, int(round(28 * scale * s)))
    img = gframe.resize((w, h), Image.NEAREST)
    # glider texel (gx, gy) is Josh texel (gx + 7, gy + 70) at full size; the anchor is (40, 79)
    ox = (40 + s * (7 - 40)) * scale
    oy = (79 + s * (70 - 79)) * scale
    return img, (int(round(ox)), int(round(oy)))


def timeline(name):
    """(duration, josh frame, glider frame, glider scale) steps for one play of an animation."""
    times, loop = TIMES[name]
    n = len(times)
    # a loop plays three times, so its 4 frames and the glider's 3 line up again at the seam; a
    # one-shot holds its last frame a moment
    plays = 3 if loop else 1
    times = times * plays
    n = len(times)
    total = sum(times) if loop else sum(times) + 0.4
    starts = [sum(times[:i]) for i in range(n)]
    cuts = set(starts) | {total}
    t = 0.0
    while t < total:
        cuts.add(round(t, 4))
        t += GLIDER_FRAME_TIME
    if name == 'josh_mount':
        cuts |= {round(i * 0.04, 4) for i in range(11)}
    if name == 'josh_dismount':
        cuts |= {0.05, 0.1, 0.15}
    keep = sorted(set(starts) | {total})
    for c in sorted(c for c in cuts if c <= total):
        if all(abs(c - k) >= 0.02 for k in keep):
            keep.append(c)
    cuts = sorted(keep)
    steps = []
    for a, b in zip(cuts, cuts[1:]):
        fi = max(i for i in range(n) if starts[i] <= a + 1e-9) % len(TIMES[name][0])
        gi = int((a + 1e-6) / GLIDER_FRAME_TIME) % 3
        if name == 'josh_mount':
            s = ease_back_out(min(1.0, a / MOUNT_GROW))
        elif name == 'josh_dismount':
            s = max(0.0, 1.0 - (a / DISMOUNT_SHRINK) ** 2)
        else:
            s = 1.0
        steps.append((b - a, fi, gi, s))
    return steps


def gif(name, im, path, scale=3):
    gl = R.glider_frames()
    fr = frames(im)
    out, durs = [], []
    W, H = 80 * scale, 100 * scale
    for dur, fi, gi, s in timeline(name):
        canvas = Image.new('RGBA', (W, H), BG)
        g = glider_scaled(gl[gi], s, scale)
        if g:
            canvas.alpha_composite(g[0], g[1])
        canvas.alpha_composite(fr[fi].resize((80 * scale, 80 * scale), Image.NEAREST), (0, 0))
        out.append(canvas.convert('RGB'))
        durs.append(max(10, int(round(dur * 1000))))
    # merge identical neighbours
    merged, mdurs = [out[0]], [durs[0]]
    for f, d in zip(out[1:], durs[1:]):
        if px_list(f) == px_list(merged[-1]):
            mdurs[-1] += d
        else:
            merged.append(f)
            mdurs.append(d)
    merged[0].save(path, save_all=True, append_images=merged[1:], duration=mdurs, loop=0,
                   disposal=1, optimize=False)


def contact(sheets, path, scale=4):
    """Every frame at 4x on a dark background, riding frames standing on the glider card."""
    gl = R.glider_frames()
    cw, ch = 84, 112
    cols = max(im.width // 80 for im in sheets.values())
    W = cw * cols * scale + 16
    H = (ch * len(ORDER)) * scale + 16
    out = Image.new('RGBA', (W, H), BG)
    d = ImageDraw.Draw(out)
    for r, name in enumerate(ORDER):
        im = sheets[name]
        times, _ = TIMES[name]
        for i, f in enumerate(frames(im)):
            cell = Image.new('RGBA', (80, 100), (0, 0, 0, 0))
            if i in R.RIDING.get(name, []):
                cell.alpha_composite(gl[[0, 1, 2, 1][i % 4]], R.GLIDER_AT)
            cell.alpha_composite(f, (0, 0))
            x = 8 + i * cw * scale
            y = 8 + r * ch * scale
            out.alpha_composite(cell.resize((80 * scale, 100 * scale), Image.NEAREST), (x, y + 12 * scale))
            ride = 'ride' if i in R.RIDING.get(name, []) else 'ground'
            d.text((x + 4, y + 4), '%s  f%d  %.2fs  %s' % (name, i, times[i], ride), fill=(230, 230, 230))
    out.save(path)


#SHIPPING

def ship_one(name, im):
    png = os.path.join(ASSETS, name + '.png')
    ase = os.path.join(ASSETS, name + '.aseprite')
    tmp = os.path.join(tempfile.mkdtemp(), name + '.png')
    im.save(tmp)
    # replace the shipped PNG in one step, so the game never sees a half-written sheet
    os.replace(tmp, png)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    d2 = pixel_diff(Image.open(png), im)
    return png, ase, d, d2


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'out_ride')
    os.makedirs(out, exist_ok=True)
    sheets = {n: R.sheet(n) for n in ORDER}
    bad = 0
    for name in ORDER:
        im = sheets[name]
        st = numbers(name, im)
        print('%-15s %d frames  opaque %d  colours %d  black %.1f%%  keyline #000000  semi-alpha %d'
              % (name, im.width // 80, st['opaque'], st['colours'], 100 * st['black'], st['semi']))
        if st['off_palette']:
            print('   OFF-PALETTE colours:', st['off_palette'])
            bad += 1
        print('   soles (lowest row) per frame:', st['soles'], '  top row per frame:', st['tops'])
        for i, f in enumerate(frames(im)):
            print('   f%d drawn %s  solid %s' % (i, st['extent'][i], solid_bbox(f)))
        gif(name, im, os.path.join(out, name + '.gif'))
        lib.upscale(lib.on_bg(im), 6).save(os.path.join(out, name + '_6x.png'))
    contact(sheets, os.path.join(out, 'contact_4x.png'))
    # layout numbers
    riding = [(n, i) for n in ORDER for i in R.AT_HEIGHT.get(n, [])]
    tops = [numbers(n, sheets[n])['tops'][i] for n, i in riding]
    solid_tops = [solid_bbox(frames(sheets[n])[i])[1] for n, i in riding]
    top = min(tops)
    print('RIDE_HEADROOM: top drawn row of the riding frames %d -> %.1f px above the anchor row '
          '(solid body top row %d -> %.1f px)' % (top, (79 - top) * 3.0, min(solid_tops),
                                                  (79 - min(solid_tops)) * 3.0))
    (cx, cy), box = hand_bomb()
    print('HAND_BOMB: bomb card centre on drop_bomb f1 = (%.1f, %.1f) -> Vector2(%d, %d); card box %s'
          % (cx, cy, round(cx), round(cy), box))
    allb = [solid_bbox(f, min_blob=40) for n in ORDER for f in frames(sheets[n])]
    raw = [numbers(n, sheets[n])['extent'] for n in ORDER]
    raw = [e for es in raw for e in es]
    print('DRAWN EXTENT: bodies without streaks/glints x %d..%d y %d..%d -> Rect2(%d, %d, %d, %d); '
          'raw incl. speed lines and glints x %d..%d y %d..%d' % (min(b[0] for b in allb), max(b[2] for b in allb),
                                  min(b[1] for b in allb), max(b[3] for b in allb),
                                  min(b[0] for b in allb), min(b[1] for b in allb),
                                  max(b[2] for b in allb) - min(b[0] for b in allb) + 1,
                                  max(b[3] for b in allb) - min(b[1] for b in allb) + 1,
                                  min(e[0] for e in raw), max(e[2] for e in raw),
                                  min(e[1] for e in raw), max(e[3] for e in raw)))
    if mode == 'ship':
        for name in ORDER:
            png, ase, d, d2 = ship_one(name, sheets[name])
            print('wrote %s and %s  round trip: %s  png vs build: %s'
                  % (png, os.path.basename(ase), d or 'identical', d2 or 'identical'))
            bad += bool(d) + bool(d2)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
