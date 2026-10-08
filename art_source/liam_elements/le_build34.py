"""ATTACKS 3-4 DESIGN APPROVAL PASS, v3 (2026-09-29), to ADDENDUM3's art contract (E.3 poses, E.4 FX):
Liam's new poses, the pillar row, the tornados, the fire quake ring, the steam, the lunge / impale / sky
fire / water pieces, four 1920x1080 mocks, GIFs of the elements moving, a contact sheet, x4 upscales and
contract.json (every cell, anchor / pivot, frame count, time and reported point). NOTHING here ships.

  python le_build34.py            prints this and writes nothing
  python le_build34.py --write    writes into art_source/liam_elements/approval_34/ ONLY

The --write run installs le_build's audit hook first: it refuses any file write outside
art_source/liam_elements, the scratchpad and the temp folder, anything under Assets/, and any process
but Aseprite. Every sheet is written as .png + .aseprite; the .aseprite (one frame per cell, row-major,
a tag per row / clip) is exported back and checked pixel-exact (art_source/imgdiff.py) before copying.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))           # art_source (imgdiff)

OUT = os.path.join(HERE, 'approval_34')


# ------------------------------------------------------------------ images
def grid_image(rows):
    from PIL import Image
    import le_rig as R
    fh, fw = rows[0][0].shape
    ncol = max(len(r) for r in rows)
    out = Image.new('RGBA', (fw * ncol, fh * len(rows)), (0, 0, 0, 0))
    for j, r in enumerate(rows):
        for i, cv in enumerate(r):
            assert cv.shape == (fh, fw), (cv.shape, (fh, fw))
            out.paste(Image.fromarray(R.to_rgba(cv), 'RGBA'), (i * fw, j * fh))
    return out


def strip_image(cells):
    return grid_image([cells])


# ------------------------------------------------------------------ the sheets
def _pts(frames):
    return [{k: [round(float(v[0]), 2), round(float(v[1]), 2)] for k, v in p.items()} for _, p in frames]


def sheets():
    import le_a34poses3 as Q
    import le_a34fx as X
    import le_tornado as TN
    import le_row as RW
    specs = []
    # ---- Liam's poses (E.3)
    plays = {'blow': 'once, blow_time 0.9', 'ignite': 'once, ignite_time 0.3', 'channel': 'loop 0.12',
             'vanish': 'once, vanish_time 0.8', 'lunge': 'once, lunge_show 0.12 (coil first, full extension last)',
             'lunge_whiff': 'once, 0.3', 'parried': 'once, 0.3, then downed', 'impale': 'once, 0.4',
             'impale_call': 'loop 0.15', 'water_blast': 'once, 0.3 (release frame 3 starts at 0.15)',
             'teleport': 'once, teleport_time 0.35 (played backward to arrive)'}
    for name, fn, cell, anchor, times, perch, exempt in Q.ALL:
        fr = fn()
        specs.append(dict(name='liam_' + name, kind='pose', rows=[[cv for cv, _ in fr]], durs=times,
                          tags=[(name, 0, len(fr) - 1)], layer='liam', cell=cell, anchor=anchor, perch=perch,
                          exempt=exempt, points=_pts(fr), play=plays[name], doc=(fn.__doc__ or '').strip(),
                          optional=False))
    # ---- the row (rows = variants)
    rise, stand, crumble = RW.sheets()
    for nm, rows, durs, play in (('rise', rise, [0.06, 0.06, 0.07, 0.07, 0.08], 'once over row_rise_time (per pillar)'),
                                 ('stand', stand, [0.2], 'loop (1 frame)'),
                                 ('crumble', crumble, [0.05, 0.06, 0.07, 0.08, 0.1, 0.14], 'once over crumble_time')):
        specs.append(dict(name='liam_row_pillar_' + nm, kind='fx', rows=rows, durs=durs,
                          tags=[('variant%d' % v, v * len(rows[0]), v * len(rows[0]) + len(rows[0]) - 1)
                                for v in range(len(rows))], layer='row', cell=(64, 80), pivot=(32, 72), play=play,
                          optional=False, row_meaning='rows = 3 variants', doc=(getattr(RW, nm).__doc__ or '').strip()))
    # ---- FX
    def fx(name, frames, durs, cell, pivot, play, optional=False, rows=None, row_meaning=None, doc='', tags=None):
        rows = rows if rows is not None else [frames]
        n = len(rows[0])
        if tags is None:
            tags = [(name.replace('liam_', ''), 0, n - 1)] if len(rows) == 1 else \
                [('row%d' % j, j * n, j * n + n - 1) for j in range(len(rows))]
        specs.append(dict(name=name, kind='fx', rows=rows, durs=durs, tags=tags, layer='fx', cell=cell, pivot=pivot,
                          play=play, optional=optional, row_meaning=row_meaning, doc=doc.strip()))
    fx('liam_blow_gust', [X.blow_gust(k) for k in range(6)], [0.08] * 6, (64, 48), (32, 4), 'once, 0.5 at the mouth',
       doc=X.blow_gust.__doc__)
    fx('liam_tornado_spin', [TN.tornado_air(k) for k in range(8)], [0.06] * 8, (48, 112), (24, 108), 'loop 0.06',
       doc=TN.tornado_air.__doc__ + ' ' + TN.__doc__)
    fx('liam_tornado_ignite', [TN.tornado_ignite(k) for k in range(6)], [0.05] * 6, (48, 112), (24, 108),
       'once, 0.3', doc=TN.tornado_ignite.__doc__)
    fx('liam_tornado_fire', [TN.tornado_fire(k) for k in range(8)], [0.06] * 8, (48, 112), (24, 108), 'loop 0.06',
       doc=TN.tornado_fire.__doc__)
    fx('liam_tornado_out', [TN.tornado_die(k) for k in range(6)], [0.1] * 6, (48, 112), (24, 108),
       'once, burnout_time 0.6', doc=TN.tornado_die.__doc__)
    fx('liam_tornado_form', [TN.tornado_form(k) for k in range(6)], [0.066] * 6, (48, 112), (24, 108),
       'once, 0.4 (in place of the scale-in; then spin)', optional=True, doc=TN.tornado_form.__doc__)
    fx('liam_tornado_spew', [TN.tornado_spew(k) for k in range(5)], [0.08] * 5, (48, 112), (24, 108),
       'once, 0.4, instead of the fire loop as each ring leaves (ring on frame 1)', optional=True,
       doc=TN.tornado_spew.__doc__)
    fx('liam_fire_streak', [X.fire_streak(k) for k in range(6)], [0.05] * 6, (24, 12), (20, 6), 'loop 0.05',
       doc=X.fire_streak.__doc__)
    fx('liam_wind_streak', None, [0.05] * 4, (24, 24), (12, 12), 'loop 0.05', optional=True,
       rows=[[X.wind_streak(r, k) for k in range(4)] for r in range(3)], row_meaning='rows 0 / 45 / 90 degrees',
       doc=X.wind_streak.__doc__)
    fx('liam_fire_quake_ring', None, [0.08] * 8, (40, 32), (20, 16), 'loop 0.08; dying rows once over quake_die_time',
       optional=True, rows=X.ring_sheet(8, dying=True),
       row_meaning="rows 0-6 Bixby's tangent buckets, rows 7-13 the same dying",
       doc=X.ring_segment.__doc__ + ' ' + X.ring_dying.__doc__)
    fx('liam_melt_rim', [X.melt_rim(k) for k in range(4)], [0.1] * 4, (16, 16), (8, 8), 'loop 0.1',
       doc=X.melt_rim.__doc__)
    fx('liam_steam_tile', [X.steam_tile(0), X.steam_tile(1)], [1.0], (128, 128), (0, 0),
       'shader tile: frame 0 = layer 1, frame 1 = layer 2 (use the ALPHA)', doc=X.steam_tile.__doc__)
    fx('liam_steam_wisp', [X.steam_wisp(k) for k in range(8)], [0.1] * 8, (16, 32), (8, 31), 'once, 0.8',
       doc=X.steam_wisp.__doc__)
    fx('liam_steam_puff', [X.steam_puff(k) for k in range(7)], [0.05] * 7, (48, 48), (24, 44), 'once, 0.35',
       doc=X.steam_puff.__doc__)
    fx('liam_lunge_wake', [X.lunge_wake(k) for k in range(4)], [0.04] * 4, (48, 24), (47, 12), 'once, 0.15',
       doc=X.lunge_wake.__doc__)
    fx('liam_sky_fire', [X.sky_fire(k) for k in range(6)], [0.06] * 6, (32, 48), (16, 0), 'loop 0.06, stacked',
       optional=True, doc=X.sky_fire.__doc__)
    fx('liam_sky_fire_splash', [X.sky_fire_splash(k) for k in range(6)], [0.06] * 6, (48, 32), (24, 28),
       'loop 0.06', doc=X.sky_fire_splash.__doc__)
    fx('liam_player_flames', [X.player_flames(k) for k in range(8)], [0.06] * 8, (24, 32), (12, 30), 'loop 0.06',
       doc=X.player_flames.__doc__)
    fx('liam_player_embers', [X.player_embers(k) for k in range(8)], [0.08] * 8, (24, 32), (12, 30), 'loop 0.08',
       doc=X.player_embers.__doc__)
    fx('liam_extinguish', [X.extinguish48(k) for k in range(8)], [0.0625] * 8, (48, 48), (24, 40), 'once, 0.5',
       doc=X.extinguish48.__doc__)
    fx('liam_water_jet', [X.water_jet16(k) for k in range(6)], [0.05] * 6, (16, 16), (0, 8), 'loop 0.05, laid along x',
       doc=X.water_jet16.__doc__)
    fx('liam_water_trail', [X.water_trail(k) for k in range(4)], [0.07] * 4, (24, 32), (12, 31), 'loop 0.07',
       doc=X.water_trail.__doc__)
    # optional extras
    fx('liam_lunge_triangle', None, [0.04, 0.05, 0.08, 0.08, 0.08, 0.06], (32, 32), (16, 16),
       'once: 0 spark, 1 pop, 2-4 hold, 5 the lunge', optional=True,
       rows=[[X.triangle_dir(k, d * 45) for k in range(6)] for d in range(8)],
       row_meaning='rows = 8 directions from right, clockwise (0, 45 ... 315 degrees)',
       doc=X.triangle_dir.__doc__ + ' Only if the user picks a drawn red triangle over the parry badge (K1).')
    fx('liam_water_splash', [X.water_head(k) for k in range(6)], [0.05] * 6, (40, 40), (10, 20),
       'loop 0.05 at the jet\'s player end', optional=True, doc=X.water_head.__doc__)
    fx('liam_water_burst', [X.water_muzzle(k) for k in range(5)], [0.04] * 5, (40, 40), (20, 20),
       'once at the staff tip on the release frame', optional=True, doc=X.water_muzzle.__doc__)
    fx('liam_pull_swirl', None, [0.07] * 8, (96, 40), (48, 20), 'loop 0.07 on the floor under each tornado',
       optional=True, rows=[[X.pull_swirl(k, kind='water') for k in range(8)], [X.pull_swirl(k, kind='ice') for k in range(8)]],
       row_meaning='row 0 water (fire stage), row 1 ice spray (spin stage)', doc=X.pull_swirl.__doc__)
    return specs


# ------------------------------------------------------------------ writing
def write_sheet(tmp, spec):
    import le_build as LB
    from PIL import Image
    from imgdiff import pixel_diff
    rows = spec['rows']
    grid = grid_image(rows)
    cells = [c for r in rows for c in r]
    strip = strip_image(cells)
    fh, fw = cells[0].shape
    name = spec['name']
    tpng = os.path.join(tmp, name + '.png')
    tstrip = os.path.join(tmp, name + '_strip.png')
    tase = os.path.join(tmp, name + '.aseprite')
    grid.save(tpng)
    strip.save(tstrip)
    lua = os.path.join(tmp, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LB.LUA)
    tags = ';'.join('%s:%d:%d' % (t, a + 1, b + 1) for (t, a, b) in spec['tags'])
    subprocess.run([LB.ASEPRITE, '-b', '--script-param', 'src=' + tstrip, '--script-param', 'out=' + tase,
                    '--script-param', 'n=%d' % len(cells), '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%d' % round(t * 1000) for t in spec['durs']),
                    '--script-param', 'layer=' + spec['layer'], '--script-param', 'tags=' + tags,
                    '--script', lua], check=True, capture_output=True)
    back = os.path.join(tmp, name + '_rt.png')
    subprocess.run([LB.ASEPRITE, '-b', tase, '--sheet', back, '--sheet-type', 'horizontal'], check=True,
                   capture_output=True)
    d = pixel_diff(Image.open(tstrip), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    # the grid PNG holds exactly the strip's cells
    g = Image.open(tpng)
    ncol = max(len(r) for r in rows)
    for i, _ in enumerate(cells):
        cx, cy = (i % ncol) * fw, (i // ncol) * fh
        a = g.crop((cx, cy, cx + fw, cy + fh))
        b = strip.crop((i * fw, 0, i * fw + fw, fh))
        if pixel_diff(a, b):
            raise SystemExit('%s: grid cell %d differs from the strip' % (name, i))
    for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
        shutil.copyfile(src, os.path.join(OUT, name + ext))
    x4 = grid.resize((grid.width * 4, grid.height * 4), Image.NEAREST)
    x4.save(os.path.join(OUT, 'x4', name + '_x4.png'))
    return grid


# ------------------------------------------------------------------ checks
def _player_mask():
    """The captured player's silhouette at texel scale, feet at (12, 30) of a 24x32 cell."""
    import numpy as np
    import le_mock as M
    nohud, hud, withp = M.load_caps()
    pl, xy = M.player_sprite(nohud, withp)
    a = np.array(pl)[1::3, 1::3, 3] > 0
    ys, xs = np.nonzero(a)
    fx, fy = int(round((xs.min() + xs.max()) / 2.0)), ys.max()
    m = np.zeros((32, 24), bool)
    for y, x in zip(ys, xs):
        X_, Y_ = x - fx + 12, y - fy + 30
        if 0 <= X_ < 24 and 0 <= Y_ < 32:
            m[Y_, X_] = True
    return m


FIRE_KEYS = set('αβγδεζW')


def warm_stats(cells):
    """Of the flame texels (the fire keys), the share that are warm and bright (R-B >= 0.4, value >= 0.6):
    what the steam's glow-through catches."""
    import numpy as np
    import le_rig as R
    tot = warm = 0
    if not any(np.isin(cv, list('αβγδεζ')).any() for cv in cells):
        return None
    for cv in cells:
        m = np.isin(cv, list(FIRE_KEYS))
        tot += int(m.sum())
        for k in FIRE_KEYS:
            c = R.PAL[k]
            if (c[0] - c[2]) / 255.0 >= 0.4 and max(c[:3]) / 255.0 >= 0.6:
                warm += int((cv == k).sum())
    return round(warm / tot, 3) if tot else None


def checks(specs):
    import numpy as np
    import le_rig as R
    import le_poses as P
    out = {}
    box = P.PERCH_BOX
    pm = None
    for s in specs:
        cells = [c for r in s['rows'] for c in r]
        c = {}
        if s['kind'] == 'pose':
            per = []
            for i, cv in enumerate(cells):
                b, n, _ = R.numbers(cv)
                ok = 0.2537 <= b <= 0.3101 and 34 <= n <= 38
                row = dict(frame=i, black=round(b * 100, 2), colours=n,
                           numbers='ok' if ok else ('vanish frame (exempt)' if i in s['exempt'] else 'OUT'))
                if s['perch']:
                    ys, xs = np.nonzero(cv != '.')
                    row['perch_box'] = 'ok' if (len(xs) == 0 or (ys.min() >= box['top'] and xs.min() >= box['left']
                                                                 and xs.max() <= box['right'])) else 'OUT'
                per.append(row)
            c['frames'] = per
        if s['name'].startswith('liam_tornado'):
            bb = []
            for cv in cells:
                band = cv[100:112]
                ys, xs = np.nonzero(band != '.')
                bb.append([int(xs.min()), int(xs.max())] if len(xs) else None)
            c['base_ring_rows_100_111_x_extent'] = bb
        if s['name'] == 'liam_player_flames':
            if pm is None:
                pm = _player_mask()
            cov = [round(float(((cv != '.') & pm).sum()) / pm.sum(), 3) for cv in cells]
            c['player_silhouette_covered'] = cov
            c['player_silhouette_covered_max'] = max(cov)
        w = warm_stats(cells)
        if w is not None and any(k in s['name'] for k in ('fire', 'tornado', 'flames', 'splash', 'streak', 'ring',
                                                            'extinguish', 'embers')):
            c['warm_bright_share_of_flame_texels'] = w
        out[s['name']] = c
    return out


# ------------------------------------------------------------------ the contact sheet
def contact(specs, path):
    from PIL import Image, ImageDraw
    blocks = []
    for s in specs:
        g = grid_image(s['rows'])
        sc = 3 if g.width * 3 <= 2300 else (2 if g.width * 2 <= 2300 else 1)
        if g.height * sc > 1300:
            sc = max(1, 1300 // g.height)
        big = g.resize((g.width * sc, g.height * sc), Image.NEAREST)
        fh, fw = s['rows'][0][0].shape
        lab = '%s%s  (%d x %d cells of %dx%d, %s %s, shown %dx)' % (
            s['name'], '  [optional]' if s.get('optional') else '', len(s['rows'][0]), len(s['rows']), fw, fh,
            'anchor' if s['kind'] == 'pose' else 'pivot', tuple(s.get('anchor') or s.get('pivot')), sc)
        blocks.append((lab, big, fw * sc, fh * sc))
    width = max(2400, max(b[1].width for b in blocks) + 40)
    height = sum(b[1].height + 40 for b in blocks) + 20
    out = Image.new('RGBA', (width, height), (30, 32, 42, 255))
    d = ImageDraw.Draw(out)
    y = 10
    for lab, big, cw, chh in blocks:
        d.text((20, y), lab, fill=(255, 230, 120, 255))
        y += 16
        for yy in range(0, big.height, 12):
            for xx in range(0, big.width, 12):
                c = (58, 62, 78, 255) if ((xx + yy) // 12) % 2 == 0 else (48, 52, 66, 255)
                d.rectangle([20 + xx, y + yy, 20 + min(big.width, xx + 12) - 1, y + min(big.height, yy + 12) - 1], fill=c)
        out.alpha_composite(big, (20, y))
        for x in range(cw, big.width, cw):
            d.line([(20 + x, y), (20 + x, y + big.height - 1)], fill=(255, 0, 255, 110))
        for yy in range(chh, big.height, chh):
            d.line([(20, y + yy), (20 + big.width - 1, y + yy)], fill=(255, 0, 255, 110))
        y += big.height + 24
    out.save(path)
    return path


# ------------------------------------------------------------------ GIFs
def gif(path, frames, durs):
    frames = [f.convert('RGB').convert('P', palette=1, colors=255) for f in frames]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=[int(round(d * 1000)) for d in durs],
                   loop=0, disposal=2)


def _scene_base(floor_kind=None, water_k=3):
    import le_mock as M
    import le_mock34b as MK
    nohud, hud, withp = M.load_caps()
    scene = nohud.copy()
    if floor_kind == 'water':
        MK.floor(scene, water_k=water_k)
    elif floor_kind == 'ice':
        import le_ice as I
        scene.alpha_composite(MK.tiled(I.ice(0)))
    return scene


def build_gifs():
    """The elements moving - each GIF is at the game's scale (3x) over a crop of the real arena."""
    from PIL import Image
    import le_rig as R
    import le_mock as M
    import le_mock34b as MK
    import le_pillar as PL
    import le_row as RW
    import le_tornado as TN
    import le_a34fx as X
    import le_a34poses3 as Q
    import le_full as F
    written = []
    nohud, hud, withp = M.load_caps()

    # 1 the tornado's whole life on the floor: forms on the ice, spins, a spark, ignites (the ice melts),
    #   burns, spews a quake ring, burns, burns out
    ice_bg = _scene_base('ice')
    water_bg = _scene_base('water', 4)
    at = (960, 700)
    win = (at[0] - 200, at[1] - 400, at[0] + 200, at[1] + 90)
    seq = [('form', k, 'ice', 0.066) for k in range(6)] + [('spin', k % 8, 'ice', 0.06) for k in range(16)] + \
          [('ignite', k, 'ice' if k < 2 else 'water', 0.07) for k in range(6)] + \
          [('fire', k % 8, 'water', 0.06) for k in range(16)] + [('spew', k, 'water', 0.08) for k in range(5)] + \
          [('fire', k % 8, 'water', 0.06) for k in range(8)] + [('out', k, 'water', 0.1) for k in range(6)] + \
          [('none', 0, 'water', 0.4)]
    frames, durs = [], []
    ring_r = None
    for i, (st, k, fl, d) in enumerate(seq):
        sc = (ice_bg if fl == 'ice' else water_bg).copy()
        sw = X.pull_swirl(i % 8, kind='ice' if fl == 'ice' else 'water')
        if st not in ('form', 'none', 'out'):
            MK.paste(sc, sw, at, X.SWIRL_PIVOT)
        if st == 'spew':
            ring_r = 60 if k >= 1 else None
        if ring_r is not None:
            MK.ring(sc, at, ring_r, beat=i)
            ring_r += 200 * d
            if ring_r > 200:
                ring_r = None
        cv = {'form': TN.tornado_form, 'spin': TN.tornado_air, 'ignite': TN.tornado_ignite, 'fire': TN.tornado_fire,
              'spew': TN.tornado_spew, 'out': TN.tornado_die}.get(st)
        if cv is not None:
            MK.paste(sc, cv(k), at, TN.PIVOT)
        frames.append(sc.crop(win))
        durs.append(d)
    gif(os.path.join(OUT, 'gif_tornado_life.gif'), frames, durs)
    written.append('gif_tornado_life.gif')

    # 2 the four tornados burning together over the water with their rings racing out (a slice of attack 3)
    frames, durs = [], []
    rad = [60.0, 160.0, 260.0, 110.0]
    for i in range(36):
        sc = water_bg.copy()
        for j, c in enumerate(MK.TORNADO_SPOTS):
            MK.paste(sc, X.pull_swirl((i + j * 2) % 8, kind='water'), c, X.SWIRL_PIVOT)
        for j, c in enumerate(MK.TORNADO_SPOTS):
            r = rad[j]
            if r <= 360:
                MK.ring(sc, c, r, beat=i + j)
            else:
                MK.ring(sc, c, 360, dying=min(7, int((r - 360) / 200 / 0.3 * 8)))
            rad[j] += 200 * 0.06
            if rad[j] > 360 + 60:
                rad[j] = 60.0
        for j, c in sorted(enumerate(MK.TORNADO_SPOTS), key=lambda p: p[1][1]):
            MK.paste(sc, TN.tornado_fire((i + j * 3) % 8), c, TN.PIVOT)
        frames.append(sc.resize((960, 540), Image.NEAREST))
        durs.append(0.06)
    gif(os.path.join(OUT, 'gif_firestorm_rings.gif'), frames, durs)
    written.append('gif_firestorm_rings.gif')

    # 3 the steam: two layers drifting at two speeds, the clear bubble following the player, wisps and a
    #   puff off the wet floor, a fire tornado glowing through
    frames, durs = [], []
    base = water_bg.copy()
    MK.paste(base, X.pull_swirl(0, kind='water'), (1160, 820), X.SWIRL_PIVOT)
    for i in range(24):
        sc = base.copy()
        MK.paste(sc, TN.tornado_fire(i % 8), (1160, 820), TN.PIVOT)
        for j, (x, y) in enumerate(((700, 760), (860, 900), (1000, 640), (1300, 700))):
            k = (i + j * 3) % 12
            if k < 8:
                MK.paste(sc, X.steam_wisp(k), (x, y), (8, 31))
        if 6 <= i < 13:
            MK.paste(sc, X.steam_puff(i - 6), (820, 820), (24, 44))
        p = (840 + i * 6, 780 - i * 2)
        MK.player(sc, nohud, withp, p)
        sc = MK.steam(sc, 0.85, p, drift=((i, 0), (37 + 2 * i, 53 + i)))
        frames.append(sc.crop((560, 520, 1400, 1000)))
        durs.append(0.08)
    gif(os.path.join(OUT, 'gif_steam.gif'), frames, durs)
    written.append('gif_steam.gif')

    # 4 Liam on his pillar: the blow (gust at his mouth), the ignite (fire streaks leaving the tip), channel
    def perch(cv, extra=None, pillar=None):
        sc = nohud.copy()
        MK.row_and_pillar(sc, None if pillar is not None else cv)
        if pillar is not None:
            MK.paste(sc, pillar, (960, 348), PL.ANCHOR)
            MK.paste(sc, cv, MK.LIAM_FEET, (48, 96))
        if extra:
            extra(sc)
        return sc.crop((960 - 330, 0, 960 + 330, 460))
    frames, durs = [], []
    blow = Q.fitted(Q.blow)()
    for k, (cv, pts) in enumerate(blow):
        def ex(sc, k=k, pts=pts):
            if k >= 2:
                mx, my = pts['mouth']
                MK.paste(sc, X.blow_gust(min(5, k - 2 + (k >= 4))), (960 + (mx - 48) * 3, 198 + (my - 96) * 3), (32, 4))
        frames.append(perch(cv, ex))
        durs.append([0.15, 0.2, 0.12, 0.16, 0.14, 0.13][k])
    ign = Q.fitted(Q.ignite)()
    for k, (cv, pts) in enumerate(ign):
        def ex(sc, k=k, pts=pts):
            tx, ty = pts['staff_tip']
            sx, sy = 960 + (tx - 48) * 3, 198 + (ty - 96) * 3
            if k >= 2:
                for j, (x1, y1) in enumerate(MK.TORNADO_SPOTS):
                    f = min(1.0, (k - 1) * 0.3)
                    x, y = sx + (x1 - sx) * f, sy + (y1 - sy) * f
                    ang = math.degrees(math.atan2(y1 - sy, x1 - sx))
                    im = MK.up(X.fire_streak(k % 6)).rotate(-ang, resample=Image.NEAREST, expand=True)
                    sc.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
        frames.append(perch(cv, ex))
        durs.append(0.08)
    ch = Q.fitted(Q.channel)()
    for r in range(3):
        for k, (cv, pts) in enumerate(ch):
            frames.append(perch(cv))
            durs.append(0.12)
    gif(os.path.join(OUT, 'gif_blow_ignite_channel.gif'), frames, durs)
    written.append('gif_blow_ignite_channel.gif')

    # 5 the vanish on the pillar as it sinks to the stump
    frames, durs = [], []
    van = Q.fitted(Q.vanish)()
    for k, (cv, pts) in enumerate(van):
        h = 50 - int(round((50 - 15) * k / 5.0))
        pil = PL.column_at(h)
        sc = nohud.copy()
        MK.row_and_pillar(sc, None, stump=None)
        MK.paste(sc, pil, (960, 348), PL.ANCHOR)
        MK.paste(sc, cv, (960, 198 + (50 - h) * 3), (48, 96))
        MK.paste(sc, X.steam_puff(min(6, k + 1)), (960, 198 + (50 - h) * 3), (24, 44))
        frames.append(sc.crop((960 - 330, 0, 960 + 330, 460)))
        durs.append([0.12, 0.14, 0.14, 0.14, 0.13, 0.13][k])
    frames.append(frames[-1])
    durs.append(0.6)
    gif(os.path.join(OUT, 'gif_vanish.gif'), frames, durs)
    written.append('gif_vanish.gif')

    # 6 attack 4 in full: the badge, the lunge with its wake, the impale, the call, Bixby's fire from the
    #   sky onto the skewered player, the embers, the water blast that puts him out and washes him away,
    #   the teleport
    frames, durs = [], []
    feet = (760, 760)
    pl_at = (feet[0] + 47 * 3 + 20, feet[1] - 19 * 3)

    def ground(cv, cell_anchor, extra=None, player_at=None, fx=None):
        sc = nohud.copy()
        if player_at is not None:
            MK.player(sc, nohud, withp, player_at)
        if cv is not None:
            MK.paste(sc, cv, feet, cell_anchor)
        if extra:
            extra(sc)
        return sc.crop((feet[0] - 260, feet[1] - 470, feet[0] + 420, feet[1] + 90))
    for k in range(6):
        def ex(sc, k=k):
            MK.badge(sc, (feet[0], feet[1]), frame=k % 6)
        frames.append(ground(None, (48, 96), ex, player_at=pl_at))
        durs.append(0.066)
    lg = Q.fitted(Q.lunge)()
    for k, (cv, pts) in enumerate(lg):
        def ex(sc, k=k):
            if k >= 1:
                MK.paste(sc, X.lunge_wake(min(3, k - 1)), (feet[0] - 20, feet[1] - 50), (47, 12))
        frames.append(ground(cv, (48, 96), ex, player_at=pl_at))
        durs.append(0.05)
    imp = Q.fitted(Q.impale)()
    call = Q.fitted(Q.impale_call)()
    seq = [(cv, pts, 0.1, 'imp') for cv, pts in imp] + [(call[i % 2][0], call[i % 2][1], 0.15, 'call') for i in range(4)] + \
          [(call[i % 2][0], call[i % 2][1], 0.06, 'fire') for i in range(18)] + \
          [(call[i % 2][0], call[i % 2][1], 0.08, 'embers') for i in range(4)]
    for i, (cv, pts, d, ph) in enumerate(seq):
        tip = pts['staff_tip']
        held = (feet[0] + (tip[0] - 48) * 3, feet[1] + (tip[1] - 144) * 3)
        def ex(sc, i=i, ph=ph, held=held):
            if ph == 'fire':
                MK.sky_fire_column(sc, held[0], held[1] - 31, frame=i)
                MK.paste(sc, X.sky_fire_splash(i % 6), (held[0], held[1] - 37), (24, 28))
                MK.paste(sc, X.player_flames(i % 8), (held[0], held[1] + 38), (12, 30))
            elif ph == 'embers':
                MK.paste(sc, X.player_embers(i % 8), (held[0], held[1] + 38), (12, 30))
        sc = nohud.copy()
        MK.paste(sc, cv, feet, (48, 144))
        MK.player(sc, nohud, withp, held)
        ex(sc)
        frames.append(sc.crop((feet[0] - 260, feet[1] - 470, feet[0] + 420, feet[1] + 90)))
        durs.append(d)
    last_held = held
    wb = Q.fitted(Q.water_blast)()
    for k, (cv, pts) in enumerate(wb):
        sc = nohud.copy()
        MK.paste(sc, cv, feet, (48, 96))
        MK.player(sc, nohud, withp, last_held)
        if k < 3:
            MK.paste(sc, X.player_embers(k), (last_held[0], last_held[1] + 38), (12, 30))
        if k >= 3:
            tip = wb[3][1]['staff_tip']
            sx, sy = feet[0] + (tip[0] - 48) * 3, feet[1] + (tip[1] - 96) * 3
            tx, ty = last_held
            ang = math.atan2(ty - sy, tx - sx)
            ln = math.hypot(tx - sx, ty - sy)
            jet = MK.up(X.water_jet16(k))
            strip = Image.new('RGBA', (int(ln) + 48, 48))
            for x in range(0, int(ln), 48):
                strip.alpha_composite(jet, (x, 0))
            rot = strip.rotate(-math.degrees(ang), resample=Image.NEAREST, expand=True)
            cxr, cyr = (sx + tx) / 2.0, (sy + ty) / 2.0
            sc.alpha_composite(rot, (int(cxr - rot.width / 2), int(cyr - rot.height / 2)))
            MK.paste(sc, X.water_muzzle(min(4, k - 3)), (sx, sy), (20, 20))
            MK.paste(sc, X.extinguish48(min(7, (k - 3) * 2)), (tx, ty + 38), (24, 40))
        frames.append(sc.crop((feet[0] - 260, feet[1] - 470, feet[0] + 420, feet[1] + 90)))
        durs.append([0.06, 0.06, 0.05, 0.08, 0.08][k])
    # he is washed away (down-right, toward the bottom middle) trailing water; the steam hisses off
    for k in range(8):
        sc = nohud.copy()
        MK.paste(sc, wb[4][0], feet, (48, 96))
        p = (last_held[0] + k * 22, last_held[1] + k * 44)
        MK.paste(sc, X.extinguish48(min(7, 4 + k)), (last_held[0], last_held[1] + 38), (24, 40))
        MK.paste(sc, X.water_trail(k % 4), (p[0], p[1] - 10), (12, 31))
        MK.player(sc, nohud, withp, p)
        frames.append(sc.crop((feet[0] - 260, feet[1] - 470, feet[0] + 420, feet[1] + 90)))
        durs.append(0.06)
    tp = Q.fitted(Q.teleport)()
    for k, (cv, pts) in enumerate(tp):
        sc = nohud.copy()
        MK.paste(sc, cv, feet, (48, 96))
        MK.paste(sc, X.steam_puff(min(6, k + 1)), feet, (24, 44))
        frames.append(sc.crop((feet[0] - 260, feet[1] - 470, feet[0] + 420, feet[1] + 90)))
        durs.append(0.06)
    frames.append(frames[-1])
    durs.append(0.6)
    gif(os.path.join(OUT, 'gif_lunge_impale_water.gif'), frames, durs)
    written.append('gif_lunge_impale_water.gif')

    # 7 the parry and the whiff
    for name, tail in (('parried', Q.fitted(Q.parried)), ('lunge_whiff', Q.fitted(Q.lunge_whiff))):
        frames, durs = [], []
        for k, (cv, pts) in enumerate(lg):
            sc = nohud.copy()
            MK.paste(sc, cv, feet, (48, 96))
            MK.player(sc, nohud, withp, pl_at)
            frames.append(sc.crop((feet[0] - 260, feet[1] - 330, feet[0] + 420, feet[1] + 90)))
            durs.append(0.05)
        tf = tail()
        for k, (cv, pts) in enumerate(tf):
            sc = nohud.copy()
            if name == 'lunge_whiff':
                MK.paste(sc, cv, (feet[0] + 80, feet[1]), (48, 96))
                MK.player(sc, nohud, withp, (pl_at[0] - 40, pl_at[1] + 60))
                if k == 3:
                    MK.paste(sc, X.steam_puff(3), (feet[0] + 80, feet[1]), (24, 44))
            else:
                MK.paste(sc, cv, (feet[0] - 20 * min(k, 2), feet[1]), (48, 96))
                MK.player(sc, nohud, withp, pl_at)
            frames.append(sc.crop((feet[0] - 260, feet[1] - 330, feet[0] + 420, feet[1] + 90)))
            durs.append(0.08)
        if name == 'parried':
            for r in range(2):
                for cv, pts in F.downed():
                    sc = nohud.copy()
                    MK.paste(sc, cv, (feet[0] - 40, feet[1]), (48, 96))
                    MK.player(sc, nohud, withp, pl_at)
                    frames.append(sc.crop((feet[0] - 260, feet[1] - 330, feet[0] + 420, feet[1] + 90)))
                    durs.append(0.12)
        frames.append(frames[-1])
        durs.append(0.5)
        gif(os.path.join(OUT, 'gif_%s.gif' % name), frames, durs)
        written.append('gif_%s.gif' % name)

    # 8 the row rising out from the middle, standing, crumbling
    frames, durs = [], []
    xs = [960 + 108 * k for k in range(-3, 4)]
    for t in range(24):
        sc = nohud.copy()
        for x in sorted(xs, key=lambda v: -abs(v - 960)):
            k = abs(x - 960) // 108
            v = k % 3
            if x == 960:
                cv = PL.rise_frame(min(4, t)) if t < 5 else PL.stand_frame(0)
            else:
                ph = t - k
                cv = None if ph < 0 else (RW.rise(ph, v) if ph < 5 else RW.stand(v))
            if t >= 12:
                ph = t - 12 - (k if x != 960 else 0)
                if x != 960 and ph >= 0:
                    cv = RW.crumble(min(5, ph), v)
            if cv is not None:
                MK.paste(sc, cv, (x, 348), PL.ANCHOR)
        frames.append(sc.crop((960 - 400, 60, 960 + 400, 420)))
        durs.append(0.08 if t < 12 else 0.1)
    frames.append(frames[-1])
    durs.append(0.5)
    gif(os.path.join(OUT, 'gif_row.gif'), frames, durs)
    written.append('gif_row.gif')

    # 9 the burning player close up: flames, embers, the extinguish (4x)
    frames, durs = [], []
    pm = _player_mask()
    import numpy as np
    pl, xy = M.player_sprite(nohud, withp)
    small = np.array(pl)[1::3, 1::3]
    ys, xs_ = np.nonzero(small[..., 3] > 0)
    fx0, fy0 = int(round((xs_.min() + xs_.max()) / 2.0)), ys.max()
    base = Image.new('RGBA', (48, 48), (128, 176, 100, 255))
    base.alpha_composite(Image.fromarray(small, 'RGBA'), (24 - fx0, 40 - fy0))
    for i in range(16):
        f = base.copy()
        f.alpha_composite(Image.fromarray(R.to_rgba(X.player_flames(i % 8)), 'RGBA'), (24 - 12, 40 - 30))
        frames.append(f.resize((192, 192), Image.NEAREST))
        durs.append(0.06)
    for i in range(8):
        f = base.copy()
        f.alpha_composite(Image.fromarray(R.to_rgba(X.player_embers(i)), 'RGBA'), (24 - 12, 40 - 30))
        frames.append(f.resize((192, 192), Image.NEAREST))
        durs.append(0.08)
    for i in range(8):
        f = base.copy()
        f.alpha_composite(Image.fromarray(R.to_rgba(X.extinguish48(i)), 'RGBA'), (0, 0))
        frames.append(f.resize((192, 192), Image.NEAREST))
        durs.append(0.0625)
    frames.append(base.resize((192, 192), Image.NEAREST))
    durs.append(0.4)
    gif(os.path.join(OUT, 'gif_player_fire.gif'), frames, durs)
    written.append('gif_player_fire.gif')
    return written


# ------------------------------------------------------------------ the contract
def contract(specs, chk, files):
    import le_rig as R
    import le_a34 as A
    import le_fire as FI
    import le_a34fx as X
    out = dict(
        pass_='attacks 3-4 design approval, v3 (to ADDENDUM3 E.3/E.4), 2026-09-29', scale=3,
        notes=[
            'Cells and anchors / pivots follow ADDENDUM3 E.3 / E.4 exactly; frame counts are at or above the '
            'minimums and every sheet is read by width (LiamArtLayout.strip_count); times are soft.',
            'Multi-row sheets: rows are variants / directions / tangent buckets as each entry says; the '
            '.aseprite holds the cells row-major, one tag per row.',
            'Points are in cell texels (x right, y down), anchors on the cell bottom-centre edge as the '
            "contract's (48, 96) / (48, 144).",
            'The lunge\'s last staff_tip and the impale\'s first are the same point relative to his feet '
            '(47 right, 19 up), so the skewered player never jumps between sheets.',
        ],
        sheets={}, files=files)
    for s in specs:
        cells = [c for r in s['rows'] for c in r]
        e = dict(file=s['name'] + '.png', cell=list(s['cell']), frames=len(s['rows'][0]), rows=len(s['rows']),
                 times=s['durs'], play=s['play'], optional=bool(s.get('optional')))
        if s['kind'] == 'pose':
            e['anchor'] = list(s['anchor'])
            e['points'] = s['points']
            e['on_the_pillar'] = bool(s['perch'])
        else:
            e['pivot'] = list(s['pivot'])
        if s.get('row_meaning'):
            e['row_meaning'] = s['row_meaning']
        e['what'] = s['doc']
        e['checks'] = chk.get(s['name'], {})
        out['sheets'][s['name']] = e
    lunge = out['sheets']['liam_lunge']['points'][-1]['staff_tip']
    imp = out['sheets']['liam_impale']['points']
    out['sheets']['liam_lunge']['reach_texels'] = round(lunge[0] - 48, 2)
    out['sheets']['liam_impale']['held_tip_px_above_feet'] = round((144 - imp[-1]['staff_tip'][1]) * 3, 1)
    out['sheets']['liam_impale_call']['tip_px_above_feet'] = [
        round((144 - p['staff_tip'][1]) * 3, 1) for p in out['sheets']['liam_impale_call']['points']]
    pal = {}
    for d in (A.FIRE, A.ROCK, A.STEAM, A.FOG, A.TELL, FI.SMOKE, X.WATER_A, X.STEAM_TILE):
        for k, v in d.items():
            pal[k] = '#%02x%02x%02x%s' % (v[0], v[1], v[2], '' if v[3] == 255 else ' a%.2f' % (v[3] / 255.0))
    out['fx_palette_new_keys'] = pal
    return out


# ------------------------------------------------------------------ main
def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    import le_build as LB
    LB.install_guard()
    for d in (OUT, os.path.join(OUT, 'x4')):
        if not os.path.isdir(d):
            os.mkdir(d)
    specs = sheets()
    tmp = tempfile.mkdtemp(prefix='le_34_')
    written = []
    for spec in specs:
        im = write_sheet(tmp, spec)
        written += [spec['name'] + '.png', spec['name'] + '.aseprite']
        print('wrote %-26s %dx%d (%d x %d)' % (spec['name'], im.width, im.height, len(spec['rows'][0]), len(spec['rows'])))
    chk = checks(specs)
    import le_mock34b as MK
    for fn, nm in ((lambda p: MK.mock_firestorm(p, late=False), 'liam_mock_a3_firestorm_mid.png'),
                   (lambda p: MK.mock_firestorm(p, late=True), 'liam_mock_a3_firestorm_full_steam.png'),
                   (MK.mock_lunge_badge, 'liam_mock_a4_badge.png'),
                   (MK.mock_impale, 'liam_mock_a4_impale.png')):
        fn(os.path.join(OUT, nm))
        written.append(nm)
        print('wrote', nm)
    for g in build_gifs():
        written.append(g)
        print('wrote', g)
    contact(specs, os.path.join(OUT, 'liam_a34_contact.png'))
    written.append('liam_a34_contact.png')
    with open(os.path.join(OUT, 'contract.json'), 'w', encoding='utf-8') as f:
        json.dump(contract(specs, chk, written + ['contract.json']), f, indent=1, ensure_ascii=False)
    print('wrote contract.json')
    bad = []
    for name, c in chk.items():
        for fr in c.get('frames', []):
            if fr['numbers'] == 'OUT' or fr.get('perch_box') == 'OUT':
                bad.append((name, fr))
        if c.get('player_silhouette_covered_max', 0) > 0.6:
            bad.append((name, 'player coverage %.2f' % c['player_silhouette_covered_max']))
    print('checks:', 'all pass' if not bad else bad)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
