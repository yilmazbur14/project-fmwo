"""Write the kaiju approval pass into the scratch approval folder (never into the project):

  kaiju_mounted_idle.png / _3x.png / .aseprite      (layers: kaiju, fx, rider)
  kaiju_breath_charge.png / _3x.png / .aseprite
  arena_mockup.png                                    (both poses in the live arena capture, 1920x2160)
  anchors.json                                        (frame + screen anchors, numbers)

Refuses any output folder that resolves into the project tree.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kj_frames2 as F  # noqa: E402
import kj_kaiju2 as KJ  # noqa: E402
import kj_mock as M  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

OUT = K.OUT
CROP = (16, 2, 216, 242)              # working canvas -> delivered frame (200 x 240)
FW, FH = CROP[2] - CROP[0], CROP[3] - CROP[1]
HOME = (330, 800)                     # the architect's home: feet centre on the soles' line, screen px
SCALE = 3


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def to_frame(px):
    return {(x - CROP[0], y - CROP[1]): k for (x, y), k in px.items()
            if CROP[0] <= x < CROP[2] and CROP[1] <= y < CROP[3]}


def fpt(p):
    return (p[0] - CROP[0], p[1] - CROP[1])


def screen(fp, top_left):
    """A frame pixel's centre on screen."""
    return (top_left[0] + SCALE * fp[0] + 1, top_left[1] + SCALE * fp[1] + 1)


def aseprite(*args):
    subprocess.run([K.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def stats_of(px, w, h):
    return K.stats(K.render(px, w, h))


def main():
    if _under(OUT, K.PROJECT):
        raise SystemExit('refusing %s: inside the project' % OUT)
    os.makedirs(OUT, exist_ok=True)
    feet = fpt((int(round(KJ.OX)), KJ.SOLE))
    top_left = (HOME[0] - SCALE * feet[0], HOME[1] - SCALE * feet[1])
    report = {'frame_size': [FW, FH], 'scale': SCALE, 'home_screen': list(HOME),
              'frame_top_left_screen': list(top_left), 'poses': {}}
    tmp = tempfile.mkdtemp(prefix='kj_')
    images = {}
    for name, charge in (('kaiju_mounted_idle', False), ('kaiju_breath_charge', True)):
        final, fx, L = F.layers(charge)
        a = K.audit(final, fx)
        if any(a[k] for k in ('gaps', 'lone', 'holes', 'keys')):
            raise SystemExit('%s fails the audit: %s' % (name, {k: v[:5] for k, v in a.items() if v}))
        fr = to_frame(final)
        if len(fr) != len(final):
            raise SystemExit('%s: %d pixels fall outside the crop' % (name, len(final) - len(fr)))
        im = K.render(fr, FW, FH)
        images[name] = im
        # the layers, each a full-frame PNG, then the layered .aseprite
        ldir = os.path.join(tmp, name)
        os.makedirs(ldir)
        for lname in ('kaiju', 'fx', 'rider'):
            K.render(to_frame(L[lname]), FW, FH).save(os.path.join(ldir, lname + '.png'))
        png = os.path.join(OUT, name + '.png')
        ase = os.path.join(OUT, name + '.aseprite')
        im.save(png)
        lua = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kj_layers.lua')
        aseprite('--script-param', 'dir=' + ldir.replace('\\', '/'), '--script-param', 'layers=kaiju,fx,rider',
                 '--script-param', 'out=' + ase.replace('\\', '/'), '--script', lua.replace('\\', '/'))
        back = os.path.join(tmp, name + '_rt.png')
        aseprite(ase, '--save-as', back)
        d = K.JB.pixel_diff(Image.open(png).convert('RGBA'), Image.open(back).convert('RGBA'))
        if d:
            raise SystemExit('%s.aseprite does not round-trip: %s' % (name, d))
        up = im.resize((FW * SCALE, FH * SCALE), Image.NEAREST)
        up.save(os.path.join(OUT, name + '_3x.png'))
        # numbers
        kaiju_st = stats_of(to_frame(L['kaiju']), FW, FH)
        rider_st = stats_of(to_frame(L['rider']), FW, FH)
        rider_keys = set(L['rider'].values())
        kx = K.bbox(to_frame(L['kaiju']))
        rx = K.bbox(to_frame(L['rider']))
        dx, dy = F.rider_offset()
        seat = fpt(KJ.Ti(*F.SEAT_DESIGN))
        mouth = fpt(KJ.mouth_origin(charge))
        box = fpt((70 + dx, 37 + dy))
        head_top = min(y for (x, y) in to_frame(L['kaiju']) if x >= fpt(KJ.Ti(118, 0))[0])
        report['poses'][name] = {
            'png': png, 'aseprite': ase, 'layers': ['kaiju', 'fx', 'rider'],
            'frame_stats': {k: (round(v, 4) if isinstance(v, float) else v) for k, v in K.stats(im).items()},
            'kaiju_layer_black': round(kaiju_st['black'], 4), 'kaiju_layer_colours': kaiju_st['colours'],
            'rider_layer_black': round(rider_st['black'], 4), 'rider_layer_colours': rider_st['colours'],
            'rider_keys_outside_jordan_40': sorted(rider_keys - K.JORDAN_KEYS),
            'kaiju_bbox_frame': list(kx), 'rider_bbox_frame': list(rx),
            'anchors_frame': {
                'feet_centre_soles': list(feet), 'rider_seat': list(seat), 'mouth_beam_origin': list(mouth),
                'jordan_crown_y': rx[1], 'jordan_box_centre': list(box), 'kaiju_head_top_y': head_top,
            },
            'anchors_screen': {
                'feet_centre_soles': list(HOME), 'rider_seat': list(screen(seat, top_left)),
                'mouth_beam_origin': list(screen(mouth, top_left)),
                'jordan_crown_y': screen((0, rx[1]), top_left)[1],
                'jordan_x_span': [screen((rx[0], 0), top_left)[0], screen((rx[2], 0), top_left)[0] + 2],
                'kaiju_x_span': [screen((kx[0], 0), top_left)[0], screen((kx[2], 0), top_left)[0] + 2],
                'kaiju_head_top_y': screen((0, head_top), top_left)[1],
                'frame_rect': [top_left[0], top_left[1], top_left[0] + FW * SCALE, top_left[1] + FH * SCALE],
            },
            'audit': {k: len(v) for k, v in a.items()},
        }
    # palette across both frames
    cols = set()
    for im in images.values():
        flat = getattr(im, 'get_flattened_data', None)
        cols |= {c for c in (flat() if flat else im.getdata()) if c[3] > 0}
    report['palette_colours_both_frames'] = len(cols)
    report['keyline'] = '#000000'
    live = Image.open(os.path.join(K.ASSETS_JORDAN, 'jordan_idle.png')).convert('RGBA').crop((0, 0, 96, 96))
    report['jordan_live_idle_f0_black'] = round(K.stats(live)['black'], 4)
    # the mockup
    mock(images, report)
    with open(os.path.join(OUT, 'anchors.json'), 'w') as f:
        json.dump(report, f, indent=2)
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps(report, indent=2))


def mock(images, report):
    base_bg = Image.open(os.path.join(M.CAP, 'arena_bg.png')).convert('RGBA')
    player = Image.open(os.path.join(M.CAP, 'arena_player.png')).convert('RGBA')
    # the player sprite, lifted out of its capture by differencing against the bare arena
    pbox = (930, 670, 995, 770)
    pl = Image.new('RGBA', (pbox[2] - pbox[0], pbox[3] - pbox[1]), (0, 0, 0, 0))
    for y in range(pbox[1], pbox[3]):
        for x in range(pbox[0], pbox[2]):
            a, b = player.getpixel((x, y)), base_bg.getpixel((x, y))
            if a != b:
                pl.putpixel((x - pbox[0], y - pbox[1]), a)
    feet_in_pl = (960 - pbox[0], 757 - pbox[1])       # the capture's player feet (body at 960, 718)
    panels = []
    for name, label in (('kaiju_mounted_idle', 'kaiju_mounted_idle'), ('kaiju_breath_charge', 'kaiju_breath_charge')):
        r = report['poses'][name]
        tl = tuple(report['frame_top_left_screen'])
        im = images[name]
        big = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
        canvas = base_bg.copy()
        # a soft contact shadow under the feet (mock only; the game draws its own shadow sprite)
        sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        hx, hy = HOME
        d.ellipse((hx - 230, hy - 26, hx + 200, hy + 22), fill=(20, 40, 15, 90))
        canvas.alpha_composite(sh)
        # the player out in the open ring, y-sorted in front (its feet are below the kaiju's)
        pfeet = (1100, 700)
        canvas.alpha_composite(big, tl)
        canvas.alpha_composite(pl, (pfeet[0] - feet_in_pl[0], pfeet[1] - feet_in_pl[1]))
        a = r['anchors_screen']
        marks = [
            (a['feet_centre_soles'][0], a['feet_centre_soles'][1], 'home / feet (%d, %d)' % tuple(a['feet_centre_soles']), (255, 255, 0, 255)),
            (a['rider_seat'][0], a['rider_seat'][1], 'seat (%d, %d)' % tuple(a['rider_seat']), (255, 140, 0, 255)),
            (a['mouth_beam_origin'][0], a['mouth_beam_origin'][1], 'beam origin (%d, %d)' % tuple(a['mouth_beam_origin']), (0, 255, 255, 255)),
            (pfeet[0], pfeet[1], 'player feet (%d, %d)' % pfeet, (255, 255, 255, 255)),
        ]
        M.annotate(canvas, marks, label='%s  |  3x  |  frame %dx%d at screen (%d, %d)' % (label, FW, FH, tl[0], tl[1]))
        panels.append(canvas)
    out = Image.new('RGBA', (1920, 2160 + 8), (0, 0, 0, 255))
    out.paste(panels[0], (0, 0))
    out.paste(panels[1], (0, 1080 + 8))
    out.save(os.path.join(OUT, 'arena_mockup.png'))


if __name__ == '__main__':
    main()
