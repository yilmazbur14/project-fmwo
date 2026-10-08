"""APPROVAL PASS (2026-09-29): beast Bixby's Flyby pose - the fly-across fire pass.

    python build.py                    # writes the approval set into art_source/bixby_flyby/approval/
    python build.py --out <folder>     # somewhere else; refused under Assets/ (and outside this folder,
                                       # the scratchpad and temp)
    python build.py --check            # builds in memory, runs the hard-number checks, writes nothing

NOTHING here ships. The guard (installed before anything is written) refuses any write under Assets/,
any write outside this folder, the session scratchpad and the temp folder, and any subprocess but
Aseprite; an Aseprite argument under Assets/ is refused too. Shipping is a separate step after the user
approves: the plan's section 11, step 6.

What it writes (approval/):
  bixby_beast_flyby.png/.aseprite      the sheet: flyby_glide frames 0-3, flyby_breath frames 4-7, 192x160
  bixby_flyby_curtain.png/.aseprite    the optional curtain: 4 frames of 32x48, seamless stacked
  glide_0_1x.png glide_0_3x.png breath_0_1x.png breath_0_3x.png
  mock_1.png                            the projection up, him just entering at the pass line
  mock_2.png                            mid-sweep: the curtain falling from his mouths, the lit floor behind
  contact_3x.png                        every frame and the curtain at 3x, labelled
  flyby.gif                             glide -> breath -> glide, with rough in-betweens (jaws opening)
  contract.json                         every number section 13 asks for, and the checks' results
"""
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fb_common as C          # noqa: E402  (puts the rig on sys.path, read-only)
from PIL import Image, ImageDraw  # noqa: E402

ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
SCRATCH = os.path.join(r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
                       r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\bixby_flyby')
GLIDE_TIMES = [0.08, 0.08, 0.08, 0.08]
BREATH_TIMES = [0.08, 0.08, 0.08, 0.08]
CURTAIN_TIME = 0.06


#THE GUARD

def _norm(p):
    return os.path.normcase(os.path.realpath(os.fspath(p)))


ASSETS = _norm(C.ASSETS)


def under_assets(p):
    rp = _norm(p)
    return rp == ASSETS or rp.startswith(ASSETS + os.sep)


def install_guard(out_dir):
    roots = [_norm(r) for r in (HERE, tempfile.gettempdir(), SCRATCH, out_dir)]
    ase = _norm(ASEPRITE)

    def inside(p):
        if under_assets(p):
            return False
        rp = _norm(p)
        return any(rp == r or rp.startswith(r + os.sep) for r in roots)

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing and not inside(path):
                raise PermissionError('guard: bixby_flyby writes only into %s, the scratchpad or temp, not %s'
                                      % (HERE, path))
        elif event in ('os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir',
                       'shutil.copyfile', 'shutil.move', 'shutil.rmtree'):
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and not inside(a):
                    raise PermissionError('guard: refusing %s on %s' % (event, a))
        elif event == 'subprocess.Popen':
            argv = args[1]
            line = argv if isinstance(argv, str) else subprocess.list2cmdline([os.fspath(a) for a in argv])
            first = line[1:line.index('"', 1)] if line.startswith('"') else line.split(' ')[0]
            if _norm(first) != ase:
                raise PermissionError('guard: bixby_flyby launches only Aseprite, not %s' % first)
            if ASSETS in os.path.normcase(line) or ('assets' + os.sep) in os.path.normcase(line):
                raise PermissionError('guard: an Aseprite argument under Assets')

    sys.addaudithook(hook)


#ASEPRITE (each sheet saved with its clips as tags, then checked to re-export pixel-identical)

LUA = r'''
local src = app.params["src"]
local out = app.params["out"]
local n = tonumber(app.params["n"])
local fw = tonumber(app.params["fw"])
local durs = {}
for d in string.gmatch(app.params["durs"], "[^,]+") do table.insert(durs, tonumber(d)) end
local strip = Image{ fromFile = src }
local fh = strip.height
local spr = Sprite(fw, fh, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = app.params["layer"]
for i = 1, n do
  if i > 1 then spr:newEmptyFrame() end
  local img = Image(fw, fh, ColorMode.RGB)
  img:drawImage(strip, Point(-(i - 1) * fw, 0))
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = durs[i]
end
for t in string.gmatch(app.params["tags"], "[^;]+") do
  local name, a, b = string.match(t, "([^:]+):(%d+):(%d+)")
  local tag = spr:newTag(tonumber(a), tonumber(b))
  tag.name = name
end
spr:saveAs(out)
'''


def write_sprite(tmp, dest, name, strip_im, n, fw, durs, tags, layer):
    from imgdiff import pixel_diff
    assert strip_im.width == n * fw, (name, strip_im.size, n, fw)
    tpng = os.path.join(tmp, name + '.png')
    tase = os.path.join(tmp, name + '.aseprite')
    strip_im.save(tpng)
    lua = os.path.join(tmp, 'mk.lua')
    with open(lua, 'w') as f:
        f.write(LUA)
    tag_s = ';'.join('%s:%d:%d' % t for t in tags)
    subprocess.run([ASEPRITE, '-b', '--script-param', 'src=' + tpng, '--script-param', 'out=' + tase,
                    '--script-param', 'n=%d' % n, '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%d' % int(round(t * 1000)) for t in durs),
                    '--script-param', 'layer=' + layer, '--script-param', 'tags=' + tag_s, '--script', lua],
                   check=True, capture_output=True)
    back = os.path.join(tmp, name + '_rt.png')
    subprocess.run([ASEPRITE, '-b', tase, '--sheet', back, '--sheet-type', 'horizontal'], check=True,
                   capture_output=True)
    d = pixel_diff(Image.open(tpng), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
        with open(src, 'rb') as f:
            data = f.read()
        with open(os.path.join(dest, name + ext), 'wb') as f:
            f.write(data)
    return name + '.png', name + '.aseprite'


#BUILDING

def build_frames():
    import fb_frames as F
    frames = {'glide': [], 'breath': []}
    for clip, br in (('glide', False), ('breath', True)):
        for i in range(4):
            cv, info = F.build(i, br)
            frames[clip].append(dict(image=cv.image(), exits=info['exits'], fire=info['fire'],
                                     head_mask=info['head_mask']))
    return frames


def curtain_frames():
    import fb_fire as FF
    return [C.image(FF.curtain_frame(t), FF.CURTAIN_W, FF.CURTAIN_ROWS) for t in range(FF.FRAMES)]


def strip(images):
    w, h = images[0].size
    out = Image.new('RGBA', (w * len(images), h), (0, 0, 0, 0))
    for i, im in enumerate(images):
        out.alpha_composite(im, (w * i, 0))
    return out


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def on(im, bg=(46, 49, 58, 255)):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


def extents(frames):
    """FINAL_LEAD_PX and FINAL_TRAIL_PX (px), from every frame: the lead over row 86 and the trail."""
    lead = 0
    trail = 0
    for clip in ('glide', 'breath'):
        for f in frames[clip]:
            lx = f['exits'][0][0]
            px = f['image'].load()
            for y in range(C.FH):
                for x in range(C.FW):
                    if px[x, y][3]:
                        if y < C.FLOOR_ROW:
                            lead = max(lead, x - lx)
                        trail = max(trail, lx - x)
    return lead * C.SCALE, trail * C.SCALE


def contact_sheet(frames, curtain, s=3):
    labels = ['glide %d' % i for i in range(4)] + ['breath %d' % i for i in range(4)]
    ims = [f['image'] for f in frames['glide']] + [f['image'] for f in frames['breath']]
    pad, lab = 8, 14
    cols = 4
    fw, fh = C.FW * s, C.FH * s
    cw = 32 * s * 2 + pad
    W = cols * (fw + pad) + pad + cw + pad
    H = 2 * (fh + lab + pad) + pad
    out = Image.new('RGBA', (W, H), (118, 160, 96, 255))
    d = ImageDraw.Draw(out)
    for i, (im, name) in enumerate(zip(ims, labels)):
        x = pad + (i % cols) * (fw + pad)
        y = pad + (i // cols) * (fh + lab + pad)
        d.text((x + 2, y), name, fill=(16, 20, 16, 255))
        out.alpha_composite(up(im, s), (x, y + lab))
        # the floor line (row 86) and the lead exit's column, as thin guides at the frame's edges
        lx = frames['glide' if i < 4 else 'breath'][i % 4]['exits'][0][0]
        for yy in range(y + lab, y + lab + fh, 6):
            out.putpixel((x + lx * s + s // 2, yy), (40, 90, 255, 255))
        for xx in range(x, x + fw, 6):
            out.putpixel((xx, y + lab + C.FLOOR_ROW * s), (255, 255, 255, 255))
    # the curtain, stacked 3 high, frames side by side at half size
    cx = pad + cols * (fw + pad)
    d.text((cx, pad), 'curtain x4 frames, stacked', fill=(16, 20, 16, 255))
    for t, cf in enumerate(curtain):
        x0 = cx + (t % 2) * (32 * 2 + 6)
        y0 = pad + lab + (t // 2) * (48 * 2 * 3 + 10)
        for r in range(3):
            out.alpha_composite(up(cf, 2), (x0, y0 + r * 48 * 2))
    return out


def gif(frames, path, s=2):
    """glide -> breath -> glide on one unbroken wingbeat, with a rough in-between each way: the jaws half
    open and the throats catching, no fire out yet."""
    import fb_frames as F
    bg = (46, 49, 58, 255)
    g = [f['image'] for f in frames['glide']]
    b = [f['image'] for f in frames['breath']]
    half = [F.build(i, breath=False, jaw=12.0, glow=True)[0].image() for i in range(4)]
    states = ['g'] * 8 + ['h'] + ['b'] * 11 + ['h'] + ['g'] * 7
    seq = []
    for n, st in enumerate(states):
        beat = n % 4
        seq.append({'g': g, 'b': b, 'h': half}[st][beat])
    ims = [up(on(im, bg), s).convert('RGB') for im in seq]
    durs = [60 if st == 'h' else 80 for st in states]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=2)


def build(out_dir, write=True):
    import fb_check as K
    import fb_mock as MK
    import fb_frames as F
    frames = build_frames()
    curtain = curtain_frames()
    ok, lines, nums = K.run(frames)
    for line in lines:
        print(line)
    print('HARD CHECKS:', 'PASS' if ok else 'FAIL')
    lead_px, trail_px = extents(frames)
    lead_exit = frames['breath'][0]['exits'][0]
    glide_nums = K.palette_numbers([f['image'] for f in frames['glide']])
    breath_nums = K.palette_numbers([f['image'] for f in frames['breath']])
    curtain_nums = K.palette_numbers(curtain)
    contract = {
        'approval_pass': '2026-09-29',
        'sheet': 'bixby_beast_flyby.png',
        'frame_size': [C.FW, C.FH], 'anchor': list(C.ANCHOR), 'scale': C.SCALE,
        'drawn_facing': 'right; the engine mirrors about the anchor column for flying left',
        'pass_anchor_y': C.PASS_ANCHOR_Y,
        'clips': {
            'flyby_glide': {'frames': [0, 1, 2, 3], 'times': GLIDE_TIMES, 'loop': True},
            'flyby_breath': {'frames': [4, 5, 6, 7], 'times': BREATH_TIMES, 'loop': True},
        },
        'wingbeat': 'glide frame i and breath frame i are the same beat (checked pixel for pixel outside '
                    'the heads and the fire)',
        'FINAL_LEAD_EXIT': [int(lead_exit[0]), int(lead_exit[1])],
        'FINAL_EXITS': {str(4 + i): [[int(x), int(y)] for (x, y) in frames['breath'][i]['exits']] for i in range(4)},
        'FINAL_EXITS_note': 'keyed by sheet frame (4-7 = flyby_breath 0-3); lead exit first, then the middle '
                            'head, then the near head. An exit is where the fire front leaves that maw: its '
                            'column is the fire\'s front edge, its row the maw.',
        'FINAL_LEAD_PX': lead_px,
        'FINAL_TRAIL_PX': trail_px,
        'glide_exits': {str(i): [[int(x), int(y)] for (x, y) in frames['glide'][i]['exits']] for i in range(4)},
        'curtain': {'file': 'bixby_flyby_curtain.png', 'frame': [32, 48], 'frames': len(curtain),
                    'frame_time': CURTAIN_TIME, 'leading_column': 31, 'seamless_stacked': True,
                    'loop': True, 'top_cap': None, 'mirror_for_left': True},
        'palette': {
            'measured_sheet': nums, 'measured_glide': glide_nums, 'measured_breath': breath_nums,
            'measured_curtain': curtain_nums,
            'targets': {'black_pct': 24.6, 'colours': '38-45', 'semi': 0,
                        'live_sheets': {'bixby_beast.png': [38, 25.03], 'bixby_beast_fly.png': [39, 24.62],
                                        'bixby_beast_land.png': [38, 25.18],
                                        'bixby_beast_firebreath.png': [39, 19.27]}},
            'fire': 'Inferno ramp only (bixby_inferno_fx/pal.py): r n N p P Y and white-hot #FFFFFF',
        },
        'hard_checks': {'pass': ok, 'lines': lines},
    }
    if not write:
        print(json.dumps({k: contract[k] for k in ('FINAL_LEAD_EXIT', 'FINAL_EXITS', 'FINAL_LEAD_PX',
                                                   'FINAL_TRAIL_PX')}, indent=1))
        return ok
    install_guard(out_dir)
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    tmp = tempfile.mkdtemp(prefix='bixby_flyby_')
    written = []
    sheet = strip([f['image'] for f in frames['glide']] + [f['image'] for f in frames['breath']])
    written += write_sprite(tmp, out_dir, 'bixby_beast_flyby', sheet, 8, C.FW, GLIDE_TIMES + BREATH_TIMES,
                            [('flyby_glide', 1, 4), ('flyby_breath', 5, 8)], 'flyby')
    written += write_sprite(tmp, out_dir, 'bixby_flyby_curtain', strip(curtain), len(curtain), 32,
                            [CURTAIN_TIME] * len(curtain), [('curtain', 1, len(curtain))], 'curtain')
    for name, im in (('glide_0', frames['glide'][0]['image']), ('breath_0', frames['breath'][0]['image'])):
        im.save(os.path.join(out_dir, name + '_1x.png'))
        up(im, 3).save(os.path.join(out_dir, name + '_3x.png'))
        written += [name + '_1x.png', name + '_3x.png']
    lx, ly = lead_exit
    m1 = MK.compose(frames['glide'][1]['image'], lx, ly, curtain, 1, -0.01, True, 0, player_at=(1470, 700))
    m1.save(os.path.join(out_dir, 'mock_1.png'))
    m2 = MK.compose(frames['breath'][2]['image'], lx, ly, curtain, 1, (660 - 105) / 540.0, True, 2,
                    player_at=(1712, 640))
    m2.save(os.path.join(out_dir, 'mock_2.png'))
    written += ['mock_1.png', 'mock_2.png']
    contact_sheet(frames, curtain).save(os.path.join(out_dir, 'contact_3x.png'))
    gif(frames, os.path.join(out_dir, 'flyby.gif'))
    written += ['contact_3x.png', 'flyby.gif']
    contract['files'] = written
    with open(os.path.join(out_dir, 'contract.json'), 'w') as f:
        json.dump(contract, f, indent=1)
    print('wrote', ', '.join(written + ['contract.json']), 'into', out_dir)
    return ok


def main(argv):
    out = C.APPROVAL
    if '--out' in argv:
        out = os.path.abspath(argv[argv.index('--out') + 1])
    if under_assets(out):
        print('refused: %s is under Assets/. The approval pass never writes there.' % out)
        return 2
    allowed = [_norm(r) for r in (HERE, SCRATCH, tempfile.gettempdir())]
    if not any(_norm(out) == r or _norm(out).startswith(r + os.sep) for r in allowed):
        print('refused: %s is outside art_source/bixby_flyby/, the scratchpad and temp.' % out)
        return 2
    if '--check' in argv:
        return 0 if build(out, write=False) else 1
    return 0 if build(out) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
