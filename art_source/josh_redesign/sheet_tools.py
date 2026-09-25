"""Assembling, measuring, shipping and previewing Josh's ground sheets."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import lib                                                         # noqa: E402
from PIL import Image                                              # noqa: E402

ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh'))
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
SCRATCH = os.environ.get('JOSH_PREVIEW', os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\josh_sheets\ground'))
WIP = os.environ.get('JOSH_WIP', os.path.join(os.path.dirname(os.path.dirname(SCRATCH)), 'jg'))
DARK = (26, 27, 33, 255)


def to_image(px, w=80, h=80):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), lib.PAL[k])
    return im


def strip(frames):
    ims = [f if isinstance(f, Image.Image) else to_image(f) for f in frames]
    out = Image.new('RGBA', (80 * len(ims), 80), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        out.alpha_composite(im, (80 * i, 0))
    return out


def stats(im):
    return lib.stats(im)


def rows_used(im, n):
    out = []
    for f in range(n):
        fr = im.crop((80 * f, 0, 80 * f + 80, 80))
        out.append(fr.getbbox(alpha_only=True))
    return out


def ship(name, im, nframes):
    """Write Assets/Characters/Josh/<name>.png in one go (temp file + replace), save the .aseprite
    beside it, and check the .aseprite re-exports pixel-identical."""
    from imgdiff import pixel_diff
    png = os.path.join(ASSETS, name + '.png')
    ase = os.path.join(ASSETS, name + '.aseprite')
    assert im.size == (80 * nframes, 80), im.size
    tmp_dir = tempfile.mkdtemp()
    tmp_png = os.path.join(tmp_dir, name + '.png')
    im.save(tmp_png)
    tmp_ase = os.path.join(tmp_dir, name + '.aseprite')
    subprocess.run([ASEPRITE, '-b', tmp_png, '--save-as', tmp_ase], check=True, capture_output=True)
    back = os.path.join(tmp_dir, 'rt.png')
    subprocess.run([ASEPRITE, '-b', tmp_ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(tmp_png), Image.open(back))
    if d:
        raise SystemExit('%s: aseprite round trip differs: %s' % (name, d))
    os.replace(tmp_png, png)
    os.replace(tmp_ase, ase)
    # and the shipped pair, read back from where they landed
    back2 = os.path.join(tmp_dir, 'rt2.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
    d2 = pixel_diff(Image.open(png), Image.open(back2))
    return png, ase, d2


GLIDER_AT = (7, 70)          # glider texel (gx, gy) sits on Josh texel (gx + 7, gy + 70)


def glider_frames():
    g = Image.open(os.path.join(ASSETS, 'Cards', 'josh_glider.png')).convert('RGBA')
    return [g.crop((i * 64, 0, i * 64 + 64, 28)) for i in range(3)]


def on_glider(im, gi=0):
    """A strip with the glider card drawn behind each frame (for the riding sheets' previews)."""
    gl = glider_frames()
    out = Image.new('RGBA', (im.width, 100), (0, 0, 0, 0))
    for f in range(im.width // 80):
        out.alpha_composite(gl[(gi + f) % 3], (80 * f + GLIDER_AT[0], GLIDER_AT[1]))
    out.alpha_composite(im, (0, 0))
    return out


def contact(sheets, scale=4, pad=6, label_h=0, riding=(), times=None):
    """All frames of all sheets at `scale` on a dark background, one sheet per row, each frame
    labelled; the riding sheets stand on the glider card."""
    from PIL import ImageDraw
    w = max(im.width for _, im in sheets)
    cell_h = 100 + 2 * pad + 4
    out = Image.new('RGBA', ((w + 2 * pad) * scale, len(sheets) * cell_h * scale), DARK)
    d = ImageDraw.Draw(out)
    y = 0
    for name, im in sheets:
        ride = name in riding
        strip_im = on_glider(im) if ride else im
        big = lib.upscale(strip_im, scale)
        out.alpha_composite(big, (pad * scale, y + (pad + 4) * scale))
        for f in range(im.width // 80):
            x = (pad + 80 * f) * scale
            t = ''
            if times and name in times:
                tt = times[name]
                t = '  %.2fs' % tt[min(f, len(tt) - 1)]
            d.text((x + 4, y + 6), '%s f%d%s  %s' % (name, f, t, 'ride' if ride else 'ground'),
                   fill=(225, 225, 230, 255))
            if f:
                for yy in range(y + (pad + 4) * scale, y + (pad + 84) * scale, 3):
                    out.putpixel((x, yy), (70, 72, 84, 255))
        y += cell_h * scale
    return out


def gif(im, nframes, times, path, scale=3, riding=False, loops=1, seq=None):
    """One play of the animation at `scale` on a dark background (a looping one plays `loops`
    times, or give the (frame, seconds) sequence). A riding sheet stands on the glider, whose own
    three frames cycle every 0.11 s."""
    gl = glider_frames() if riding else None
    if seq is None:
        seq = [(i, times[min(i, len(times) - 1)]) for i in range(nframes)] * loops
    # cut the timeline wherever Josh or the glider changes frame
    cuts, t = [0.0], 0.0
    for _, d in seq:
        t += d
        cuts.append(round(t, 4))
    total = t
    if riding:
        g = 0.11
        while g < total:
            cuts.append(round(g, 4))
            g += 0.11
    cuts = sorted(set(cuts))
    starts = [sum(d for _, d in seq[:k]) for k in range(len(seq))]
    frames, durs = [], []
    H = 100 if riding else 80
    for a, b in zip(cuts, cuts[1:]):
        k = max(j for j in range(len(seq)) if starts[j] <= a + 1e-9)
        f = seq[k][0]
        bg = Image.new('RGBA', (80, H), DARK)
        if riding:
            bg.alpha_composite(gl[int((a + 1e-6) / 0.11) % 3], GLIDER_AT)
        bg.alpha_composite(im.crop((80 * f, 0, 80 * f + 80, 80)), (0, 0))
        frames.append(lib.upscale(bg, scale).convert('RGB'))
        durs.append(max(20, int(round((b - a) * 1000))))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1,
                   optimize=False)


def inspect(frames, path, s=8, cols=None):
    """Frames side by side, gridded at s, for looking at."""
    ims = [f if isinstance(f, Image.Image) else to_image(f) for f in frames]
    cols = cols or len(ims)
    rows = (len(ims) + cols - 1) // cols
    tile = 80 * s
    out = Image.new('RGBA', (cols * (tile + 8), rows * (tile + 8)), (10, 10, 12, 255))
    for i, im in enumerate(ims):
        g = lib.grid(im, s)
        out.paste(g, ((i % cols) * (tile + 8), (i // cols) * (tile + 8)))
    out.save(path)


def plain(frames, path, s=4, bg=(46, 49, 58, 255), riding=False):
    ims = [f if isinstance(f, Image.Image) else to_image(f) for f in frames]
    H = 100 if riding else 80
    out = Image.new('RGBA', (80 * len(ims), H), bg)
    if riding:
        gl = glider_frames()
        for i in range(len(ims)):
            out.alpha_composite(gl[i % 3], (80 * i + GLIDER_AT[0], GLIDER_AT[1]))
    for i, im in enumerate(ims):
        out.alpha_composite(im, (80 * i, 0))
    lib.upscale(out, s).save(path)
