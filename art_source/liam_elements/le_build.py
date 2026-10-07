"""APPROVAL PASS (2026-09-29): Liam's elements phase - the staff, his key poses, the earth pillar, the
tsunami wave, the gust, attack 2's floor and tremor pieces, two in-fight mocks, a contact sheet and
anchors.json. NOTHING here ships.

  python le_build.py            prints this and writes nothing
  python le_build.py --write    writes into art_source/liam_elements/approval/ ONLY

The --write run installs an audit hook first: it refuses any file write outside this folder, the
scratchpad and the temp folder, any write under Assets/, and any process but Aseprite (which only ever
reads and writes temp files here). Every sheet is written as .png + .aseprite, the .aseprite is exported
back and checked pixel-exact against the .png (art_source/imgdiff.py) before either is copied.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))           # art_source (imgdiff)

OUT = os.path.join(HERE, 'approval')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

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
  img:drawImage(strip, Point(-(i - 1) * fw, 0), 255, BlendMode.SRC)
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = durs[((i - 1) % #durs) + 1]
end
for t in string.gmatch(app.params["tags"], "[^;]+") do
  local name, a, b = string.match(t, "([^:]+):(%d+):(%d+)")
  local tag = spr:newTag(tonumber(a), tonumber(b))
  tag.name = name
end
spr:saveAs(out)
'''


# ------------------------------------------------------------------ the guard
def install_guard():
    import le_view as V
    roots = [HERE, tempfile.gettempdir(), V.SCRATCH]
    roots = [os.path.normcase(os.path.realpath(r)) for r in roots]
    ase = os.path.normcase(os.path.realpath(ASEPRITE))
    assets = os.path.normcase(os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Assets')))

    def inside(p):
        rp = os.path.normcase(os.path.realpath(os.fspath(p)))
        if rp == assets or rp.startswith(assets + os.sep):
            return False
        return any(rp == r or rp.startswith(r + os.sep) for r in roots)

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing and not inside(path):
                raise PermissionError('guard: le_build writes only into %s, the scratchpad or temp, not %s'
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
            if os.path.normcase(os.path.realpath(first)) != ase:
                raise PermissionError('guard: le_build launches only Aseprite, not %s' % first)
            if assets in os.path.normcase(os.path.realpath(line)) or ('assets' + os.sep) in os.path.normcase(line):
                raise PermissionError('guard: an Aseprite argument under Assets')

    sys.addaudithook(hook)


# ------------------------------------------------------------------ sheets
def strip(cvs):
    from PIL import Image
    import le_rig as R
    fw, fh = cvs[0].shape[1], cvs[0].shape[0]
    out = Image.new('RGBA', (fw * len(cvs), fh), (0, 0, 0, 0))
    for i, cv in enumerate(cvs):
        assert cv.shape == (fh, fw), (cv.shape, (fh, fw))
        out.paste(Image.fromarray(R.to_rgba(cv), 'RGBA'), (i * fw, 0))
    return out


def all_sheets():
    """Every approval sheet: name, frames (canvases), durations (s), tags, layer name, notes."""
    import le_rig as R
    import le_staff as S
    import le_posedefs as D
    import le_pillar as PL
    import le_water as W
    import le_air as A
    import le_ice as I
    import le_earth as E
    sheets = []
    staff = [S.upright(24, 68, 11, 1, 63, orb=o) for o in ('neutral', 'water', 'earth', 'air', 'fire')]
    sheets.append(dict(name='liam_staff', frames=staff, durs=[1.0],
                       tags=[('neutral', 0, 0), ('water', 1, 1), ('earth', 2, 2), ('air', 3, 3), ('fire', 4, 4)],
                       layer='staff'))
    poses = [f() for f in D.POSES]
    sheets.append(dict(name='liam_elements_keyposes', frames=[p[0] for p in poses], durs=[1.0],
                       tags=[(p[1]['name'], i, i) for i, p in enumerate(poses)], layer='liam', metas=[p[1] for p in poses]))
    sheets.append(dict(name='liam_slimed_sit', frames=[slimed_sit()], durs=[1.0], tags=[('slimed_sit', 0, 0)],
                       layer='liam'))
    pil = [PL.rise_frame(k) for k in range(5)] + [PL.stand_frame(h) for h in range(6)] + \
          [PL.crumble_frame(k) for k in range(6)]
    sheets.append(dict(name='liam_pillar', frames=pil,
                       durs=[0.08, 0.08, 0.08, 0.1, 0.12] + [1.0] * 6 + [0.08, 0.1, 0.1, 0.12, 0.16, 0.3],
                       tags=[('rise', 0, 4), ('stand', 5, 10), ('crumble', 11, 16)], layer='pillar'))
    sheets.append(dict(name='liam_pillar_shield', frames=[PL.shield_overlay(p) for p in range(4)], durs=[0.09],
                       tags=[('shield', 0, 3)], layer='shield'))
    sheets.append(dict(name='liam_pillar_dust', frames=[PL.dust_frame(k) for k in range(3)], durs=[0.1],
                       tags=[('dust', 0, 2)], layer='dust'))
    sheets.append(dict(name='liam_wave', frames=[W.full_wave(k) for k in range(3)], durs=[0.1],
                       tags=[('wave', 0, 2)], layer='wave'))
    sheets.append(dict(name='liam_wave_crest', frames=[W.crest_strip(k) for k in range(3)], durs=[0.1],
                       tags=[('crest', 0, 2)], layer='crest'))
    sheets.append(dict(name='liam_wave_body', frames=[W.body_tile()], durs=[1.0], tags=[('body', 0, 0)],
                       layer='body'))
    sheets.append(dict(name='liam_wave_edge', frames=[W.wave_edge()], durs=[1.0], tags=[('edge', 0, 0)],
                       layer='edge'))
    sheets.append(dict(name='liam_wave_tell', frames=[W.tell_swell(k) for k in range(3)], durs=[0.15],
                       tags=[('tell', 0, 2)], layer='tell'))
    sheets.append(dict(name='liam_wave_collapse', frames=[W.collapse(k) for k in range(3)], durs=[0.1],
                       tags=[('collapse', 0, 2)], layer='collapse'))
    sheets.append(dict(name='liam_wave_splash', frames=[W.splash(k) for k in range(4)], durs=[0.06, 0.08, 0.08, 0.1],
                       tags=[('splash', 0, 3)], layer='splash'))
    sheets.append(dict(name='liam_gust_burst', frames=[A.gust_burst(k) for k in range(4)], durs=[0.05, 0.07, 0.08, 0.1],
                       tags=[('burst', 0, 3)], layer='burst'))
    sheets.append(dict(name='liam_gust_trail', frames=[A.trail(k) for k in range(3)], durs=[0.07],
                       tags=[('trail', 0, 2)], layer='trail'))
    sheets.append(dict(name='liam_cold_breath', frames=[A.cold_breath(k) for k in range(4)], durs=[0.1, 0.12, 0.12, 0.12],
                       tags=[('start', 0, 0), ('loop', 1, 2), ('end', 3, 3)], layer='breath'))
    sheets.append(dict(name='liam_flood', frames=[I.flood(k) for k in range(6)], durs=[0.2],
                       tags=[('coverage', 0, 5)], layer='flood'))
    sheets.append(dict(name='liam_ice', frames=[I.ice(), I.ice(True)], durs=[0.6], tags=[('ice', 0, 0), ('glint', 1, 1)],
                       layer='ice'))
    sheets.append(dict(name='liam_ice_melt', frames=[I.ice_melt(k) for k in range(3)], durs=[0.33],
                       tags=[('melt', 0, 2)], layer='melt'))
    sheets.append(dict(name='liam_ice_shatter', frames=[I.ice_shatter(k) for k in range(4)], durs=[0.1],
                       tags=[('shatter', 0, 3)], layer='shatter'))
    sheets.append(dict(name='liam_freeze_front', frames=[I.freeze_front(k) for k in range(3)], durs=[0.1],
                       tags=[('front', 0, 2)], layer='front'))
    sheets.append(dict(name='liam_tremor_block', frames=E.block_frames(), durs=E.BLOCK_TIMES,
                       tags=[('tell', 0, 3), ('heave', 4, 6), ('active', 7, 10), ('pulse', 11, 12), ('crumble', 13, 16)],
                       layer='ridge'))
    sheets.append(dict(name='liam_tremor_crack', frames=[E.crack_segment(k) for k in range(3)], durs=[0.1],
                       tags=[('crack', 0, 2)], layer='crack'))
    sheets.append(dict(name='liam_slam_burst', frames=[E.slam_burst(k) for k in range(3)], durs=[0.06, 0.08, 0.1],
                       tags=[('burst', 0, 2)], layer='burst'))
    return sheets


# ------------------------------------------------------------------ slimed_sit (exact crop of defeat frame 9)
DEFEAT_SHEET = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Assets', 'Characters', 'Bixby',
                            'bixby_beast_defeat.png')
DEFEAT_LIAM_FEET = (157, 153)     # frame 9 texel under his centre on the ground line (Bixby ANCHOR convention)
DEFEAT_BIXBY_FEET = (88, 152)
LIAM_X_RANGE = (129, 187)         # frame 9 columns that hold Liam (Bixby ends at 124)
SLIMED_OFFSET = (DEFEAT_LIAM_FEET[0] - 48, DEFEAT_LIAM_FEET[1] - 95)   # frame 9 texel = cell texel + this


def slimed_sit():
    """The 96x96 slimed_sit cell: frame 9's Liam copied texel for texel so the swap is invisible."""
    from PIL import Image
    import numpy as np
    import le_rig as R
    im = Image.open(DEFEAT_SHEET).convert('RGBA')
    f9 = np.array(im.crop((9 * 192, 0, 10 * 192, 160)))
    cv = R.blank(96, 96)
    inv = {}
    for k, v in R.PAL.items():
        if len(k) == 1 and v[3] == 255:
            inv.setdefault(v[:3], k)
    extra = {}
    for y in range(160):
        for x in range(LIAM_X_RANGE[0], LIAM_X_RANGE[1] + 1):
            p = tuple(int(c) for c in f9[y, x])
            if p[3] == 0:
                continue
            key = inv.get(p[:3])
            if key is None:
                key = extra.get(p[:3])
                if key is None:
                    key = chr(0x100 + len(extra))           # a private key for a colour the rig lacks
                    extra[p[:3]] = key
                    R.PAL[key] = p[:3] + (255,)
            cx, cy = x - SLIMED_OFFSET[0], y - SLIMED_OFFSET[1]
            cv[cy, cx] = key
    return cv


def check_slimed(cv):
    """imgdiff: the cell's pixels against frame 9's Liam region, placed back at the offset."""
    from PIL import Image
    import le_rig as R
    from imgdiff import pixel_diff
    im = Image.open(DEFEAT_SHEET).convert('RGBA').crop((9 * 192, 0, 10 * 192, 160))
    ref = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ref.paste(im.crop((LIAM_X_RANGE[0], 0, LIAM_X_RANGE[1] + 1, 160)), (LIAM_X_RANGE[0], 0))
    back = Image.new('RGBA', im.size, (0, 0, 0, 0))
    back.alpha_composite(Image.fromarray(R.to_rgba(cv), 'RGBA'), SLIMED_OFFSET)
    return pixel_diff(ref, back)


# ------------------------------------------------------------------ write one sheet
def write_sheet(tmp, spec):
    from PIL import Image
    from imgdiff import pixel_diff
    im = strip(spec['frames'])
    n = len(spec['frames'])
    fw = spec['frames'][0].shape[1]
    name = spec['name']
    tpng = os.path.join(tmp, name + '.png')
    tase = os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    lua = os.path.join(tmp, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LUA)
    tags = ';'.join('%s:%d:%d' % (t, a + 1, b + 1) for (t, a, b) in spec['tags'])
    subprocess.run([ASEPRITE, '-b', '--script-param', 'src=' + tpng, '--script-param', 'out=' + tase,
                    '--script-param', 'n=%d' % n, '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%d' % round(t * 1000) for t in spec['durs']),
                    '--script-param', 'layer=' + spec['layer'], '--script-param', 'tags=' + tags,
                    '--script', lua], check=True, capture_output=True)
    back = os.path.join(tmp, name + '_rt.png')
    subprocess.run([ASEPRITE, '-b', tase, '--sheet', back, '--sheet-type', 'horizontal'], check=True,
                   capture_output=True)
    d = pixel_diff(Image.open(tpng), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
        shutil.copyfile(src, os.path.join(OUT, name + ext))
    x4 = im.resize((im.width * 4, im.height * 4), Image.NEAREST)
    x4.save(os.path.join(OUT, 'x4', name + '_x4.png'))
    return im


# ------------------------------------------------------------------ contact sheet
def contact(sheets, path):
    from PIL import Image, ImageDraw
    rows = []
    for spec in sheets:
        im = strip(spec['frames'])
        fw, fh = spec['frames'][0].shape[1], spec['frames'][0].shape[0]
        s = 3 if im.width * 3 <= 2300 else (2 if im.width * 2 <= 2300 else 1)
        big = im.resize((im.width * s, im.height * s), Image.NEAREST)
        label = '%s  (%d x %dx%d%s, shown %dx)' % (spec['name'], len(spec['frames']), fw, fh,
                                                    ', tags ' + ' '.join('%s %d-%d' % t for t in spec['tags']), s)
        rows.append((label, big, fw * s, len(spec['frames'])))
    width = max(2400, max(r[1].width for r in rows) + 40)
    height = sum(r[1].height + 44 for r in rows) + 20
    out = Image.new('RGBA', (width, height), (30, 32, 42, 255))
    d = ImageDraw.Draw(out)
    y = 10
    for label, big, cell, n in rows:
        d.text((20, y), label, fill=(255, 230, 120, 255))
        y += 18
        # checker behind each cell so transparency reads
        for i in range(n):
            for yy in range(0, big.height, 12):
                for xx in range(0, cell, 12):
                    c = (58, 62, 78, 255) if ((xx + yy) // 12) % 2 == 0 else (48, 52, 66, 255)
                    d.rectangle([20 + i * cell + xx, y + yy, 20 + i * cell + min(cell, xx + 12) - 1,
                                 y + min(big.height, yy + 12) - 1], fill=c)
        out.alpha_composite(big, (20, y))
        for i in range(1, n):
            d.line([(20 + i * cell, y), (20 + i * cell, y + big.height - 1)], fill=(255, 0, 255, 120))
        y += big.height + 26
    out.save(path)
    return path


# ------------------------------------------------------------------ anchors.json
def anchors(sheets):
    import numpy as np
    import le_rig as R
    import le_poses as P
    import le_pillar as PL
    import le_water as W
    import le_air as A
    ks = next(s for s in sheets if s['name'] == 'liam_elements_keyposes')
    poses = []
    for i, (cv, m) in enumerate(zip(ks['frames'], ks['metas'])):
        ys, xs = np.nonzero(cv != '.')
        b, c, n = R.numbers(cv)
        row = dict(frame=i, name=m['name'], where=m['where'],
                   drawn_box=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                   drawn_width=int(xs.max() - xs.min() + 1),
                   black_ratio=round(b, 4), colours=c)
        for key, label in (('orb', 'staff_tip_orb'), ('mouth', 'mouth'), ('impact', 'staff_butt'),
                           ('daze', 'daze_point'), ('head_top', 'head_top')):
            if key in m:
                row[label] = [round(float(m[key][0]), 1), round(float(m[key][1]), 1)]
        if m['name'].startswith('h_'):
            head = cv[:, 30:80]
            hy = np.nonzero((head == 'k') | (head == 'h') | (head == 'H') | (head == 'r'))[0]
            row['head_top'] = [48, int(hy.min())]
        poses.append(row)
    return dict(
        note='APPROVAL PASS numbers (texels, scale 3). Hard numbers follow PLAN.md section 8.',
        scale=3,
        liam_cells=dict(size=[96, 96], liam_png_at=list(P.BODY), anchor_point=list(P.FEET),
                        feet_texel_row=95, sprite_offset_texels=[0, -48],
                        perch_box=dict(top_row=P.PERCH_BOX['top'], x=[P.PERCH_BOX['left'], P.PERCH_BOX['right']],
                                       why='on the pillar his feet are at screen (960,198): row 30 = screen y 0; '
                                           'x 12..83 = the rope doorway 852..1068')),
        liam_png_numbers=dict(black_ratio=0.2819, colours=35, keyline='#000000'),
        keyposes=poses,
        hand_over=dict(DEFEAT_LIAM_FEET=list(DEFEAT_LIAM_FEET), DEFEAT_BIXBY_FEET=list(DEFEAT_BIXBY_FEET),
                       convention='bixby_beast_defeat.png frame 9 texels (192x160 frame); y is the lowest '
                                  'texel row under the figure, as Bixby ANCHOR (96,151) sits on his lowest row',
                       slimed_sit_offset=list(SLIMED_OFFSET),
                       slimed_sit_rule='defeat frame 9 texel = slimed_sit texel + offset; frame 9 (157,153) = '
                                       'cell (48,95), i.e. the cell anchor point (48,96) is defeat point (157,154)'),
        staff=dict(cell=[24, 68], orb_centre=[11.5, 9.5], butt=[11.5, 63.5], length_butt_to_orb=54,
                   frames=['neutral', 'water', 'earth', 'air', 'fire'],
                   gems='AIR crown, WATER left, FIRE right, EARTH throat; the orb shows the element being bent'),
        pillar=dict(cell=[PL.PW, PL.PH], anchor_floor_line_centre=list(PL.ANCHOR), stand_point=list(PL.STAND),
                    stand_height_texels=PL.ANCHOR[1] - PL.STAND[1],
                    column_x=[PL.COL_X0, PL.COL_X1], top_slab_rows=[PL.TOP_Y0, PL.TOP_Y1],
                    footprint_texels=dict(x=[-18, 18], y=[-16, 0]), drawn_x=[PL.DRAW_X0, PL.DRAW_X1],
                    drawn_width=PL.DRAW_X1 - PL.DRAW_X0 + 1,
                    frames=dict(rise=[0, 4], stand=[5, 10], crumble=[11, 16]),
                    rise_last_equals_stand0=True, runes='6 notches, frame 5+h has 6-h lit (top goes dark first)',
                    rune_rows=list(PL.RUNE_ROWS)),
        pillar_shield=dict(cell=[PL.PW, PL.PH], anchor=list(PL.ANCHOR), frames=4, loop=True),
        pillar_dust=dict(cell=[PL.PW, PL.PH], anchor=list(PL.ANCHOR), frames=3),
        wave=dict(size=[W.WW, W.WH], hit_band_px=[W.WW * 3, W.WH * 3], front_edge_row=W.WH - 1,
                  frames=3, built_from=dict(body_tile=[W.TW, W.BODY_H], crest_strip=[W.TW, W.CREST_H],
                                            tiles_across=3, crest_rows=[W.BODY_H, W.WH - 1]),
                  mirror='allowed', keyline=False),
        wave_edge=dict(size=[W.EDGE_W, W.WH], wave_edge_column=W.EDGE_AT, optional=True,
                       use='at the left wave right end; mirrored for the right wave'),
        wave_tell=dict(size=[W.WW, 24], frames=3, anchor='bottom edge sits on the rope line'),
        wave_collapse=dict(size=[W.WW, W.WH], frames=3),
        wave_splash=dict(size=[32, 32], pivot=[16, 20], frames=4),
        gust_burst=dict(size=[48, 48], pivot_staff_tip=list(A.GUST_PIVOT), frames=4, opens='+y (at the player)'),
        gust_trail=dict(size=[24, 32], pivot=list(A.TRAIL_PIVOT), frames=3, use='on the launched player feet'),
        cold_breath=dict(size=[40, 100], pivot_mouth=list(A.BREATH_PIVOT), frames=4, plume_length=97,
                         max_width=40, tags=dict(start=0, loop=[1, 2], end=3)),
        flood=dict(tile=[64, 64], frames=6, nested=True, semi_transparent=True, flip=False),
        ice=dict(tile=[64, 64], frames=2, notes='frame 1 = glint'),
        ice_melt=dict(tile=[64, 64], frames=3, last_equals='flood frame 5'),
        ice_shatter=dict(tile=[64, 64], frames=4),
        freeze_front=dict(size=[16, 16], pivot=[8, 8], frames=3),
        tremor_block=dict(size=[96, 32], footprint_rows=[8, 31], frames=17,
                          phases=dict(tell=[0, 3], heave=[4, 6], active=[7, 10], pulse=[11, 12], crumble=[13, 16]),
                          tell_colour='earth green 7fd35a with white core (not red, not yellow)',
                          ends_overlap_texels=16),
        tremor_crack=dict(size=[16, 8], pivot=[0, 4], frames=3),
        slam_burst=dict(size=[32, 16], pivot_staff_butt=[16, 15], frames=3),
    )


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    install_guard()
    import le_mock as M
    for d in (OUT, os.path.join(OUT, 'x4')):
        if not os.path.isdir(d):
            os.mkdir(d)
    sheets = all_sheets()
    d = check_slimed(sheets[2]['frames'][0])
    if d:
        raise SystemExit('slimed_sit does not match defeat frame 9: %s' % d)
    print('slimed_sit matches defeat frame 9 exactly (imgdiff)')
    tmp = tempfile.mkdtemp(prefix='le_build_')
    written = []
    for spec in sheets:
        im = write_sheet(tmp, spec)
        written.append(spec['name'] + '.png')
        print('wrote %-26s %dx%d (%d frames)' % (spec['name'], im.width, im.height, len(spec['frames'])))
    for fn, name in ((M.mock_attack1, 'liam_elements_mock_attack1.png'), (M.mock_attack2, 'liam_elements_mock_attack2.png')):
        fn(os.path.join(OUT, name))
        written.append(name)
        print('wrote', name)
    contact(sheets, os.path.join(OUT, 'liam_elements_contact.png'))
    written.append('liam_elements_contact.png')
    a = anchors(sheets)
    a['files'] = written
    with open(os.path.join(OUT, 'anchors.json'), 'w') as f:
        json.dump(a, f, indent=1)
    print('wrote anchors.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
