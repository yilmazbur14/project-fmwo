"""Builds the full Nugget Fastball set into scratchpad/mason_fastball/full/out/ (SCRATCH ONLY).

Refuses any output under the project's Assets/ (realpath-checked: 8.3 short names are on for this drive).
Reads Assets only for reference numbers. Every .aseprite is round-tripped through Aseprite's own sheet export
and must match its PNG pixel for pixel (imgdiff.pixel_diff, which checks colour as well as alpha).
    python build_full.py
"""
import json
import os
import subprocess
import sys
from collections import Counter
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
for sub in ('rig', 'lt', ''):
    sys.path.insert(0, os.path.join(HERE, sub))

from PIL import Image                 # noqa: E402
import rig                            # noqa: E402
import pitch as PT                    # noqa: E402
import broken as BR                   # noqa: E402
import projectile as PJ               # noqa: E402
import fx as FX                       # noqa: E402
import home_run_fx as HRF             # noqa: E402
from imgdiff import pixel_diff        # noqa: E402

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
ASSETS = os.path.realpath(PROJ + 'Assets')
OUT = os.path.realpath(os.path.join(HERE, '..', 'out'))
APPROVAL = os.path.realpath(os.path.join(HERE, '..', '..', 'approval'))
TMP = os.path.join(HERE, '_ase')
ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)


def guard(p):
    if os.path.realpath(p).lower().startswith(ASSETS.lower()):
        raise SystemExit('REFUSING to write under Assets/: ' + p)
    return p


def hx(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def grid_img(g):
    im = Image.new('RGBA', (len(g[0]), len(g)), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(g):
        for x, v in enumerate(row):
            if v is None:
                continue
            if isinstance(v, str):
                px[x, y] = hx(v)
            elif v[3]:
                px[x, y] = tuple(v)
    return im


def canvas_img(c):
    im = Image.new('RGBA', (c.w, c.h), (0, 0, 0, 0))
    px = im.load()
    for y in range(c.h):
        for x in range(c.w):
            if c.p[y][x]:
                px[x, y] = hx(c.p[y][x])
    return im


def strip(frames):
    w, h = frames[0].size
    s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.alpha_composite(f, (i * w, 0))
    return s


LUA = open(os.path.join(HERE, 'make_ase.lua')).read() if os.path.exists(os.path.join(HERE, 'make_ase.lua')) else None
LUA_PATH = os.path.join(TMP, 'make_ase.lua')
open(LUA_PATH, 'w').write(r'''
local specPath = app.params["spec"]
local lines = {}
for line in io.lines(specPath) do
  if #line > 0 then table.insert(lines, line) end
end
local function split(s, sep)
  local out = {}
  for piece in string.gmatch(s, "([^" .. sep .. "]+)") do table.insert(out, piece) end
  return out
end
local head = split(lines[1], "|")
local outPath, W, H, layerName = head[1], tonumber(head[2]), tonumber(head[3]), head[4]
local spr = Sprite(W, H, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = layerName
local frameLines, tagLines = {}, {}
for i = 2, #lines do
  if string.sub(lines[i], 1, 4) == "TAG|" then table.insert(tagLines, lines[i])
  else table.insert(frameLines, lines[i]) end
end
for f, fl in ipairs(frameLines) do
  local parts = split(fl, "|")
  local frame
  if f == 1 then frame = spr.frames[1] else frame = spr:newEmptyFrame() end
  frame.duration = tonumber(parts[1]) / 1000.0
  spr:newCel(layer, frame, Image{ fromFile = parts[2] }, Point(0, 0))
end
for _, tl in ipairs(tagLines) do
  local parts = split(tl, "|")
  local tag = spr:newTag(tonumber(parts[3]), tonumber(parts[4]))
  tag.name = parts[2]
end
spr:saveAs(outPath)
spr:close()
''')

LOG = []


def ship(name, frames, durations, tags, layer=None):
    s = strip(frames)
    alphas = {p[3] for p in s.get_flattened_data()}
    assert alphas <= {0, 255}, (name, 'partial alpha', alphas)
    s.save(guard(os.path.join(OUT, name + '.png')))
    s.resize((s.width * 3, s.height * 3), Image.NEAREST).save(guard(os.path.join(OUT, name + '_3x.png')))
    w, h = frames[0].size
    ase = guard(os.path.join(OUT, name + '.aseprite'))
    lines = ['%s|%d|%d|%s' % (ase.replace('\\', '/'), w, h, layer or name)]
    for i, (f, d) in enumerate(zip(frames, durations)):
        fp = os.path.join(TMP, '%s_f%02d.png' % (name, i)).replace('\\', '/')
        f.save(fp)
        lines.append('%d|%s' % (d, fp))
    for tname, a, b in tags:
        lines.append('TAG|%s|%d|%d' % (tname, a, b))
    spec = os.path.join(TMP, name + '_spec.txt')
    open(spec, 'w').write('\n'.join(lines) + '\n')
    if os.path.exists(ase):
        os.remove(ase)
    r = subprocess.run([ASEPRITE, '-b', '--script-param', 'spec=' + spec, '--script', LUA_PATH],
                       capture_output=True, text=True)
    assert os.path.exists(ase), (name, r.stdout, r.stderr)
    back = os.path.join(TMP, name + '_roundtrip.png')
    if os.path.exists(back):
        os.remove(back)
    subprocess.run([ASEPRITE, '-b', ase, '--sheet', back, '--sheet-type', 'horizontal'], capture_output=True, text=True)
    d = pixel_diff(Image.open(back).convert('RGBA'), s)
    assert d is None, (name, 'aseprite round trip', d)
    LOG.append('%-24s %4dx%-3d %2d x %dx%d   .aseprite round trip identical' % (name, s.width, s.height, len(frames), w, h))
    return s


# ----------------------------------------------------------------------------- measuring
MASON = PROJ + 'Assets/Characters/Mason/'


def colours(im):
    return Counter(p[:3] for p in im.get_flattened_data() if p[3])


APPROVED = set(colours(Image.open(MASON + 'mason_sheet.png').convert('RGBA'))) | \
    set(colours(Image.open(MASON + 'nugget_meteor.png').convert('RGBA')))


def audit(name, f, xlim=None):
    px = list(f.get_flattened_data())
    op = [p for p in px if p[3]]
    blk = sum(1 for p in op if p[:3] == (0, 0, 0))
    c = colours(f)
    W, H = f.size
    edge = sum(1 for y in range(H) for x in range(W) if f.getpixel((x, y))[3] and (x in (0, W - 1) or y == 0))
    foreign = sorted('#%02X%02X%02X' % k for k in c if k not in APPROVED)
    xs = [x for y in range(H) for x in range(W) if f.getpixel((x, y))[3]]
    feet = sum(1 for x in range(W) if f.getpixel((x, H - 1))[3])
    ok = 0.215 <= blk / len(op) <= 0.29 and 13 <= len(c) <= 21 and not edge and not foreign and feet
    if xlim:
        ok = ok and min(xs) >= xlim[0] and max(xs) <= xlim[1]
    assert ok, (name, blk / len(op), len(c), edge, foreign, feet, min(xs), max(xs))
    return {'black_ratio': round(blk / len(op), 3), 'colours': len(c), 'opaque_px': len(op),
            'semi_alpha': 0, 'edge_px': edge, 'x_span': [min(xs), max(xs)], 'feet_row_px': feet}


def head_of(pose):
    return rig.make_ctx(dict(rig.NEUTRAL, **pose)).head


def body_px(t):
    """a frame texel -> MasonCharacterBody-local px (MasonArtLayout.frame_local, unflipped)"""
    return [round((t[0] - 32) * 3, 2), round((t[1] - 32) * 3, 2)]


def comb_top(img, hxy):
    hx_, hy_ = hxy
    ys = [y for y in range(64) for x in range(21 + hx_, 43 + hx_) if 0 <= x < 64 and img.getpixel((x, y))[3]]
    return min(ys)


def T(x, y):
    return [round(float(x), 2), round(float(y), 2)]


# ----------------------------------------------------------------------------- 1. mason_pitch
pitch_imgs = [grid_img(PT.render(p)) for _, p in PT.FRAMES]
appr = Image.open(os.path.join(APPROVAL, 'mason_windup_release.png')).convert('RGBA')
for i, k in ((3, 0), (4, 1)):
    d = pixel_diff(pitch_imgs[i], appr.crop((k * 64, 0, k * 64 + 64, 64)))
    assert d is None, ('approved frame changed', i, d)
LOG.append('mason_pitch frames 3 (SET) and 4 (RELEASE) == approved approval-pass frames, pixel for pixel')
PITCH_MS = [600, 250, 300, 300, 60, 350, 100, 100, 200, 200, 300, 350, 120, 150, 180]
ship('mason_pitch', pitch_imgs, PITCH_MS,
     [('fastball', 1, 6), ('fake_pump', 7, 8), ('changeup', 9, 12), ('bonk', 13, 15)], 'mason')

frames_contract = []
TELL_SIDE_BODY = [150.0, 10.0]
TELL_SIDE = T(32 + 150 / 3.0, 32 + 10 / 3.0)
NUGGET = {0: (54.0, 43.5), 2: (56.5, 21.0), 3: (53.5, 7.0), 4: (10.5, 56.5), 6: (23.5, 51.5), 7: (54.5, 27.0),
          10: (55.0, 54.5), 11: (11.5, 36.5)}
for k, nm in ((8, 'change_a'), (9, 'change_b')):
    p = dict(PT.FRAMES)[nm]
    c = rig.make_ctx(dict(rig.NEUTRAL, **p))
    dx = p['body'][0]
    hx_ = dx + rig.rh(p['shear'] * 23) + p['head'][0]
    NUGGET[k] = (45.5 + hx_, 29.5)
for i, (name, pose) in enumerate(PT.FRAMES):
    a = audit('pitch_' + name, pitch_imgs[i])
    hxy = head_of(pose)
    entry = dict(index=i, name=name.upper(), shown_ms=PITCH_MS[i], feet=T(32, 63),
                 head_hit=T(31.5 + hxy[0], 11 + hxy[1]), head_offset=list(hxy), audit=a)
    if i in NUGGET:
        entry['nugget_drawn_at'] = T(*NUGGET[i])
    if i in (3, 6, 7, 10):
        top = comb_top(pitch_imgs[i], hxy)
        entry['tell_over_comb'] = T(31.5 + hxy[0], top - 2)
        entry['tell_side'] = TELL_SIDE
    if i in (4, 11):
        entry['release_hand'] = T(*NUGGET[i])
    if i in (3, 6, 7):
        entry['hand'] = T(*NUGGET[i])
    frames_contract.append(entry)

# ----------------------------------------------------------------------------- 2. mason_broken
broken_imgs = [grid_img(BR.render(p)) for _, p in BR.FRAMES]
BROKEN_MS = [100, 120, 140, 120, 350, 350, 120]
ship('mason_broken', broken_imgs, BROKEN_MS, [('knockdown', 1, 4), ('dazed', 5, 6), ('twitch', 7, 7)], 'mason')
broken_contract = []
for i, (name, pose) in enumerate(BR.FRAMES):
    a = audit('broken_' + name, broken_imgs[i], (6, 58))
    hxy = head_of(pose)
    top = comb_top(broken_imgs[i], hxy)
    broken_contract.append(dict(index=i, name=name.upper(), shown_ms=BROKEN_MS[i], feet=T(32, 63),
                                head=T(31.5 + hxy[0], top - 3), head_offset=list(hxy), audit=a))

# ----------------------------------------------------------------------------- 3. balls (the approved scheme)
spin = [grid_img(g) for g in PJ.spin_frames()]
streak = [grid_img(g) for g in PJ.streak_frames()]
change = [grid_img(g) for g in PJ.changeup_frames()]
for nm, fr in (('nugget_fastball', spin), ('nugget_fastball_streaks', streak), ('nugget_changeup_trail', change)):
    d = pixel_diff(strip(fr), Image.open(os.path.join(APPROVAL, nm + '.png')).convert('RGBA'))
    assert d is None, (nm, 'differs from the approved sheet', d)
DIRS = ['e', 'se', 's', 'sw', 'w', 'nw', 'n', 'ne']
ship('nugget_fastball', spin, [50] * 4, [('spin', 1, 4)])
ship('nugget_fastball_streaks', streak, [60] * 16, [('streak_' + d, i * 2 + 1, i * 2 + 2) for i, d in enumerate(DIRS)])
ship('nugget_changeup_trail', change, [110] * 16, [('trail_' + d, i * 2 + 1, i * 2 + 2) for i, d in enumerate(DIRS)])
LOG.append('nugget_fastball / _streaks / nugget_changeup_trail == the approved sheets, pixel for pixel')
half = []
for f in spin:
    bb = f.getbbox()
    half.append(((bb[2] - bb[0]) / 2.0, (bb[3] - bb[1]) / 2.0))
hw = max(h[0] for h in half)
hh = max(h[1] for h in half)
mean_half = sum((h[0] + h[1]) / 2.0 for h in half) / len(half)

# ----------------------------------------------------------------------------- 4. FX
bonk = [grid_img(g) for g in FX.bonk_frames()]
ship('nugget_bonk', bonk, [60] * 5, [('bonk', 1, 5)])
puffs = [grid_img(g) for g in FX.puff_frames()]
ship('nugget_puff', puffs, [70] * 3, [('puff', 1, 3)])
hr = [canvas_img(c) for c in HRF.frames()]
HR_MS = [50, 60, 60, 300, 60, 60]
ship('home_run', hr, HR_MS, [('pop', 1, 3), ('hold', 4, 4), ('glint', 5, 6)])
pips = [canvas_img(c) for c in HRF.pips()]
ship('home_run_pips', pips, [100, 100], [])
hr_boxes = []
for f in hr:
    bb = f.getbbox()
    hr_boxes.append([bb[0], bb[1], bb[2], bb[3]])

contract = {
    'note': 'Texels on UNFLIPPED frames (drawn throwing toward screen-left). body_px = MasonArtLayout.frame_local '
            '= ((x-32)*3, (y-32)*3). The approval-pass badge placement (tell_side, body +(150, 10)) clears the boss '
            'bar at his home spot; tell_over_comb is the plan placement (2 texels over his comb top, open sky above).',
    'mason_pitch': {
        'texture': 'mason_pitch.png', 'hframes': 15, 'frame_size': [64, 64], 'feet': [32, 63],
        'frames': frames_contract,
        'tell_side_body_px': TELL_SIDE_BODY,
        'release_hand_body_px': {str(e['index']): body_px(e['release_hand']) for e in frames_contract if 'release_hand' in e},
        'hand_body_px': {str(e['index']): body_px(e['hand']) for e in frames_contract if 'hand' in e},
        'head_hit_body_px': {str(e['index']): body_px(e['head_hit']) for e in frames_contract},
        'tell_over_comb_body_px': {str(e['index']): body_px(e['tell_over_comb']) for e in frames_contract if 'tell_over_comb' in e},
    },
    'mason_broken': {
        'texture': 'mason_broken.png', 'hframes': 7, 'frame_size': [64, 64], 'feet': [32, 63],
        'intro_frames': [0, 1, 2, 3], 'intro_times': [0.10, 0.12, 0.14, 0.12],
        'loop_frames': [4, 5], 'loop_time': 0.35, 'twitch_frame': 6,
        'x_limits': [6, 58],
        'frames': broken_contract,
        'heads': {str(e['index']): e['head'] for e in broken_contract},
        'heads_body_px': {str(e['index']): body_px(e['head']) for e in broken_contract},
    },
    'ball': {
        'scheme': 'spin_streaks',
        'nugget_fastball': {'hframes': 4, 'frame_size': [32, 32], 'centre': [16, 16], 'frame_time': 0.05},
        'nugget_fastball_streaks': {'hframes': 16, 'frame_size': [48, 48], 'centre': [24, 24],
                                    'frame': 'direction * 2 + flicker', 'directions': DIRS, 'frame_time': 0.06},
        'nugget_changeup_trail': {'hframes': 16, 'frame_size': [48, 48], 'centre': [24, 24],
                                  'frame': 'direction * 2 + flicker', 'directions': DIRS, 'frame_time': 0.11,
                                  'spin': 'nugget_fastball.png at half rate (0.10 s a frame)'},
        'drawn_half_size_texels': [hw, hh], 'drawn_half_size_px_at_3x': [hw * 3, hh * 3],
        'suggested_radius_px': round(mean_half * 3, 1),
    },
    'nugget_bonk': {'hframes': 5, 'frame_size': [32, 32], 'pivot': [16, 16], 'frame_time': 0.06, 'placed_on': 'head_hit'},
    'nugget_puff': {'hframes': 3, 'frame_size': [8, 8], 'pivot': [4, 4], 'frame_time': 0.07},
    'home_run': {'hframes': 6, 'frame_size': [128, 40], 'pivot': [64, 40], 'frame_times': [t / 1000.0 for t in HR_MS],
                 'drawn_boxes': hr_boxes, 'baseline_row': HRF.BASE},
    'home_run_pips': {'hframes': 2, 'frame_size': [12, 12], 'frames': ['empty', 'filled']},
}
json.dump(contract, open(guard(os.path.join(OUT, 'contract.json')), 'w'), indent=1)

for line in LOG:
    print(line)
print('ball drawn half-size (texels, max over spin):', hw, hh, ' mean', round(mean_half, 2))
print('home_run drawn boxes:', hr_boxes)
for e in frames_contract:
    a = e['audit']
    print('pitch %2d %-15s ratio %.3f colours %2d head_hit %s %s' % (
        e['index'], e['name'], a['black_ratio'], a['colours'], e['head_hit'],
        ' '.join('%s=%s' % (k, e[k]) for k in ('tell_over_comb', 'release_hand', 'hand') if k in e)))
for e in broken_contract:
    a = e['audit']
    print('broken %d %-11s ratio %.3f colours %2d head %s x-span %s' % (
        e['index'], e['name'], a['black_ratio'], a['colours'], e['head'], a['x_span']))
