"""Write kaiju wave 1 into scratch (scratchpad/jordan_kaiju/wave1/), never into the project:

  <sheet>.png        the horizontal strip (frame 0 leftmost), what ships
  <sheet>.aseprite   the same, animated (frame durations), layers 'kaiju' / 'fx' (or one layer for FX sheets),
                     checked to re-export pixel-identical to the strip
  <sheet>_3x.png     a 3x nearest preview on transparent
  gifs/*.gif         the key animations at 2x on the mat
  contact_sheet.png  every sheet, 2x, labelled
  contract.json      frames, times, pivots, per-frame anchors and numbers

    python kjr_export.py            # everything
    python kjr_export.py idle ...   # only sheets whose name contains one of these words
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kj_common as K  # noqa: E402
import kjr as R  # noqa: E402
import kjr_build as B  # noqa: E402
import kjr_fx as FX  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

OUT = os.path.join(K.SCRATCH, 'wave1')
SCALE = 3
HOME = (330, 800)
BODY_SHEETS = ('kaiju_idle', 'kaiju_charge', 'kaiju_rear', 'kaiju_leap', 'kaiju_drop', 'kaiju_stomp',
               'kaiju_stumble', 'kaiju_kneel', 'kaiju_stand', 'kaiju_land')


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def guard(path):
    if _under(path, K.PROJECT):
        raise SystemExit('refusing to write %s: inside the project' % path)
    return path


def render(px, w, h):
    return K.render(px, w, h)


def strip_image(frames, w, h, layer=None):
    im = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        px = f['px']
        if layer == 'kaiju':
            px = {q: k for q, k in px.items() if q not in f['fx']}
        elif layer == 'fx':
            px = {q: k for q, k in px.items() if q in f['fx']}
        im.alpha_composite(render(px, w, h), (i * w, 0))
    return im


def aseprite(*args):
    subprocess.run([K.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def write_sheet(s, tmp):
    name = s['name']
    w, h = s['frame']
    frames = s['frames']
    n = len(frames)
    png = guard(os.path.join(OUT, name + '.png'))
    ase = guard(os.path.join(OUT, name + '.aseprite'))
    strip = strip_image(frames, w, h)
    strip.save(png)
    strip.resize((strip.width * SCALE, strip.height * SCALE), Image.NEAREST).save(
        guard(os.path.join(OUT, name + '_3x.png')))
    ldir = os.path.join(tmp, name)
    os.makedirs(ldir)
    layers = ['kaiju', 'fx'] if s['kind'] in ('body', 'head', 'overlay') else ['art']
    if layers == ['art']:
        strip.save(os.path.join(ldir, 'art.png'))
    else:
        for ln in layers:
            strip_image(frames, w, h, ln).save(os.path.join(ldir, ln + '.png'))
    times = s['times'] or [0.1] * n
    durs = ','.join(str(int(round(1000 * (t if t else 0.3)))) for t in times)
    lua = os.path.join(HERE, 'kjr_layers_anim.lua').replace('\\', '/')
    aseprite('--script-param', 'dir=' + ldir.replace('\\', '/'), '--script-param', 'layers=' + ','.join(layers),
             '--script-param', 'n=%d' % n, '--script-param', 'w=%d' % w, '--script-param', 'h=%d' % h,
             '--script-param', 'durs=' + durs, '--script-param', 'out=' + ase.replace('\\', '/'), '--script', lua)
    back = os.path.join(tmp, name + '_rt.png')
    aseprite(ase, '--sheet', back, '--sheet-type', 'horizontal')
    d = K.JB.pixel_diff(Image.open(png).convert('RGBA'), Image.open(back).convert('RGBA'))
    if d:
        raise SystemExit('%s.aseprite does not round-trip: %s' % (name, d))
    return png, ase


def numbers(s):
    w, h = s['frame']
    rows = []
    for f in s['frames']:
        body = {q: k for q, k in f['px'].items() if q not in f['fx']}
        st = K.stats(render(body, w, h)) if body else {'black': 0.0, 'colours': 0, 'opaque': 0}
        a = K.audit(f['px'], f['fx']) if f['px'] else {'gaps': [], 'lone': [], 'holes': [], 'keys': []}
        rows.append({'black': round(st['black'], 4), 'colours': st['colours'], 'opaque': st['opaque'],
                     'audit': {k: len(v) for k, v in a.items()}})
    return rows


def frame_screen_top_left(pivot):
    return [HOME[0] - SCALE * pivot[0], HOME[1] - SCALE * pivot[1]]


def screen(p, tl):
    return [tl[0] + SCALE * p[0] + 1, tl[1] + SCALE * p[1] + 1]


#PREVIEWS

MAT = (136, 180, 99, 255)


def on_mat(im, s=2):
    b = Image.new('RGBA', im.size, MAT)
    b.alpha_composite(im)
    return b.resize((im.width * s, im.height * s), Image.NEAREST)


def gif(path, frames, durs):
    rgb = [f.convert('RGB') for f in frames]
    rgb[0].save(guard(path), save_all=True, append_images=rgb[1:], duration=[int(d) for d in durs], loop=0,
                optimize=False, disposal=2)


def frame_img(s, i):
    w, h = s['frame']
    return render(s['frames'][i]['px'], w, h)


def place(canvas, im, at):
    canvas.alpha_composite(im, (int(at[0]), int(at[1])))


def beam_strip(length):
    tile = render(FX.beam_body(0), 32, 32)
    out = Image.new('RGBA', (length, 32), (0, 0, 0, 0))
    for x in range(0, length, 32):
        out.alpha_composite(tile, (x, 0))
    return out


def make_gifs(S):
    gdir = guard(os.path.join(OUT, 'gifs'))
    os.makedirs(gdir, exist_ok=True)
    bw, bh = B.BODY

    def seq(names, extra_lift=None):
        fr, du = [], []
        for name in names:
            s = S[name]
            for i, f in enumerate(s['frames']):
                im = Image.new('RGBA', (bw, bh + 40), (0, 0, 0, 0))
                lift = (extra_lift or {}).get((name, i), 0)
                place(im, frame_img(s, i), (0, 40 - lift))
                fr.append(on_mat(im))
                t = s['times'][i] if s['times'] and s['times'][i] else 0.4
                du.append(1000 * t)
        return fr, du
    out = {}
    fr, du = seq(['kaiju_idle'] * 2)
    gif(os.path.join(gdir, 'idle.gif'), fr, du)
    out['idle'] = len(fr)
    lift = {('kaiju_leap', 1): 20, ('kaiju_leap', 2): 40, ('kaiju_drop', 0): 30, ('kaiju_drop', 1): 12}
    fr, du = seq(['kaiju_rear', 'kaiju_leap', 'kaiju_drop', 'kaiju_stomp'], lift)
    du[-1] = 600
    gif(os.path.join(gdir, 'rear_leap_drop_stomp.gif'), fr, du)
    out['rear_leap_drop_stomp'] = len(fr)
    fr, du = seq(['kaiju_stumble', 'kaiju_kneel', 'kaiju_kneel', 'kaiju_stand'])
    gif(os.path.join(gdir, 'stumble_kneel_stand.gif'), fr, du)
    out['stumble_kneel_stand'] = len(fr)
    fr, du = seq(['kaiju_grow'])
    du[-1] = 700
    gif(os.path.join(gdir, 'grow.gif'), fr, du)
    out['grow'] = len(fr)
    fr, du = seq(['kaiju_shrink'])
    du[-1] = 700
    gif(os.path.join(gdir, 'shrink.gif'), fr, du)
    out['shrink'] = len(fr)
    # the breath: the stance body, the head layer on NECK aimed a little down at the ring, the spines
    # counting tail -> neck (0.26 s a row), the flash, then the fire head and the beam
    charge, aim, fire, spines = S['kaiju_charge'], S['kaiju_head_aim'], S['kaiju_head_fire'], S['kaiju_spines']
    neck = charge['frames'][0]['anchors']['NECK']
    hp = aim['pivot']
    ai = B.AIMS.index(0)
    W2 = bw + 200
    fr, du = [], []

    def breath_frame(ci, head_s, hi, sp_i, beam=False):
        im = Image.new('RGBA', (W2, bh), (0, 0, 0, 0))
        place(im, frame_img(charge, ci), (0, 0))
        hx, hy = neck[0] - hp[0], neck[1] - hp[1]
        if beam:
            mouth = head_s['frames'][hi]['anchors']['MOUTH']
            mx, my = hx + mouth[0], hy + mouth[1]
            place(im, beam_strip(int(W2 - mx)), (mx, my - 16))
        place(im, frame_img(head_s, hi), (hx, hy))
        if sp_i:
            place(im, frame_img(spines, sp_i), (0, 0))
        if beam:
            mouth = head_s['frames'][hi]['anchors']['MOUTH']
            place(im, render(FX.beam_mouth(len(fr) % 4), 48, 48), (hx + mouth[0] - 24, hy + mouth[1] - 24))
        return on_mat(im)
    for k in range(0, 8):
        fr.append(breath_frame(k % 2, aim, ai, k))
        du.append(260)
    fr.append(breath_frame(0, aim, ai, 8))
    du.append(150)
    for j in range(6):
        fr.append(breath_frame(j % 2, fire, ai, 7, beam=True))
        du.append(80)
    gif(os.path.join(gdir, 'breath_charge_spines_fire.gif'), fr, du)
    out['breath_charge_spines_fire'] = len(fr)
    # the aims, as a turntable
    fr, du = [], []
    for i in list(range(8)) + list(range(6, 0, -1)):
        im = Image.new('RGBA', (W2, bh), (0, 0, 0, 0))
        place(im, frame_img(charge, 0), (0, 0))
        place(im, frame_img(aim, i), (neck[0] - hp[0], neck[1] - hp[1]))
        fr.append(on_mat(im))
        du.append(180)
    gif(os.path.join(gdir, 'head_aims.gif'), fr, du)
    out['head_aims'] = len(fr)
    return out


def contact(S, order):
    rows = []
    for name in order:
        s = S[name]
        w, h = s['frame']
        sc = 1 if w >= 150 else (2 if w >= 40 else 3)
        ims = [on_mat(frame_img(s, i), sc) for i in range(len(s['frames']))]
        width = sum(i.width for i in ims) + 3 * (len(ims) - 1)
        row = Image.new('RGBA', (max(width, 400), ims[0].height + 16), (20, 20, 24, 255))
        ImageDraw.Draw(row).text((3, 2), '%s  (%dx%d, %d frames)' % (name, w, h, len(ims)), fill=(255, 255, 255))
        x = 0
        for i in ims:
            row.paste(i, (x, 16))
            x += i.width + 3
        rows.append(row)
    W = max(r.width for r in rows)
    H = sum(r.height for r in rows) + 4 * len(rows)
    out = Image.new('RGBA', (W, H), (20, 20, 24, 255))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + 4
    out.save(guard(os.path.join(OUT, 'contact_sheet.png')))
    return out.size


ORDER = ['kaiju_idle', 'kaiju_charge', 'kaiju_head_aim', 'kaiju_head_fire', 'kaiju_spines', 'kaiju_rear',
         'kaiju_leap', 'kaiju_drop', 'kaiju_stomp', 'kaiju_stumble', 'kaiju_kneel', 'kaiju_stand', 'kaiju_land',
         'kaiju_grow', 'kaiju_shrink', 'kaiju_toy', 'kaiju_shadow', 'kaiju_stomp_mark', 'kaiju_stomp_impact',
         'kaiju_beam_body', 'kaiju_beam_mouth', 'kaiju_beam_end', 'kaiju_mouth_charge', 'kaiju_burn_flame',
         'kaiju_burn_out']


def main(argv):
    guard(OUT)
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    S = B.build()
    print('built in %.1fs' % (time.time() - t0))
    tmp = tempfile.mkdtemp(prefix='kjr_')
    approved = R.Rig()
    contract = {
        'scale': SCALE, 'keyline': '#000000',
        'palette': {'kaiju_16': {k: '#%02X%02X%02X' % K.KAIJU_PAL[k][:3] for k in sorted(K.KAIJU_PAL)},
                    'jordan_40': 'the approved Jordan v2 palette (eyes, star, puffs, mouth, mark rim)'},
        'pivot_convention': 'texel coordinates from the frame\'s top-left. A Sprite2D with centered=true needs '
                            'offset = frame_size / 2 - pivot (texels); its position is then the pivot\'s screen '
                            'point. Anchors are given in the same frame texels; screen = position + 3 * '
                            '(anchor - pivot).',
        'home_screen': list(HOME),
        'body_frame': list(B.BODY), 'body_pivot_FEET': list(R.FEET),
        'body_frame_top_left_at_home': frame_screen_top_left(R.FEET),
        'black_target': '14.2% (the approved kaiju layer) +-1.5 at fight size; the grow / shrink / toy sizes '
                        'carry more line by nature and are reported, not held to it',
        'sheets': {},
    }
    written = []
    for name in ORDER:
        s = S[name]
        if argv and not any(a in name for a in argv):
            continue
        png, ase = write_sheet(s, tmp)
        nums = numbers(s)
        entry = {'file': os.path.basename(png), 'aseprite': os.path.basename(ase), 'frame': s['frame'],
                 'frames': len(s['frames']), 'times': s['times'], 'loop': s['loop'], 'pivot': s['pivot'],
                 'kind': s['kind'], 'note': s['note'],
                 'anchors': [f['anchors'] for f in s['frames']], 'numbers': nums}
        if name in BODY_SHEETS or name in ('kaiju_grow', 'kaiju_shrink', 'kaiju_spines'):
            tl = frame_screen_top_left(s['pivot'])
            entry['anchors_screen_at_home_f0'] = {k: screen(v, tl) for k, v in s['frames'][0]['anchors'].items()
                                                  if isinstance(v, list) and len(v) == 2 and
                                                  all(isinstance(c, (int, float)) for c in v)}
        contract['sheets'][name] = entry
        written.append(name)
        print('%-20s %s %2d frames  black %s' % (name, s['frame'], len(s['frames']),
                                                 ' '.join('%.1f' % (100 * r['black']) for r in nums)))
    if not argv:
        contract['gifs'] = make_gifs(S)
        contract['contact_sheet'] = contact(S, ORDER)
    keys = set()
    for name in written:
        for f in S[name]['frames']:
            keys |= set(f['px'].values())
    contract['keys_used'] = ''.join(sorted(keys))
    contract['keys_outside_palette'] = sorted(keys - K.JORDAN_KEYS - set(K.KAIJU_PAL))
    cols = set()
    for name in written:
        w, h = S[name]['frame']
        for f in S[name]['frames']:
            im = render(f['px'], w, h)
            flat = getattr(im, 'get_flattened_data', None)
            cols |= {c for c in (flat() if flat else im.getdata()) if c[3] > 0}
    contract['colours_used'] = len(cols)
    with open(guard(os.path.join(OUT, 'contract.json' if not argv else 'contract_partial.json')), 'w') as f:
        json.dump(contract, f, indent=1)
    shutil.rmtree(tmp, ignore_errors=True)
    print('keys outside the palette:', contract['keys_outside_palette'], ' colours used:', len(cols))
    print('done in %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main(sys.argv[1:])
