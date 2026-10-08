"""FULL POSE SHEETS (after the approved pass, 2026-09-29): every Liam sheet in Scripts/LiamArtLayout.gd
ANIMS (liam_<sheet>.png strips of 96x96, liam.png at (16, 32), anchor point (48, 96)), plus liam_juggle,
liam_leap_shadow and liam_shadow, a contact sheet, GIFs, an in-fight mock of the takeover end state and
anchors.json with every point the code reads. NOTHING here ships (the coordinator ships approved art).

  python le_build_full.py            prints this and writes nothing
  python le_build_full.py --write    writes into art_source/liam_elements/approval/full/ ONLY

Same guard as le_build.py: refuses any write outside this folder, the scratchpad and temp, any write under
Assets/, and any process but Aseprite. Every .aseprite is checked pixel-exact against its .png.
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
sys.path.insert(0, os.path.dirname(HERE))

OUT = os.path.join(HERE, 'approval', 'full')


def sheets():
    import le_full as F
    import le_build as LB
    out = []
    for name, fn, times in F.SHEETS:
        if fn is None:
            frames = [(LB.slimed_sit(), {})]
        else:
            frames = fn()
        assert len(frames) == len(times), (name, len(frames), len(times))
        out.append(dict(name='liam_' + name, key=name, frames=[f[0] for f in frames], points=[f[1] for f in frames],
                        durs=times, tags=[(name, 0, len(frames) - 1)], layer='liam', cell=[96, 96], anchor=[48, 96],
                        perch=name in F.PERCH_SHEETS))
    jf, jinfo = F.juggle()
    out.append(dict(name='liam_juggle', key='juggle', frames=jf, points=[{}] * len(jf),
                    durs=[0.06, 0.08, 0.14, 0.08, 0.08, 0.08, 0.08, 0.07, 0.09, 0.14, 0.4, 0.4],
                    tags=[('launch', 0, 1), ('tumble', 2, 6), ('crash', 7, 9), ('down', 10, 11)], layer='liam',
                    cell=[128, 96], anchor=jinfo['feet'], juggle=jinfo, perch=False))
    leap, ground = F.shadows()
    out.append(dict(name='liam_leap_shadow', key='leap_shadow', frames=leap, points=[{}] * 3, durs=[0.1],
                    tags=[('low', 0, 0), ('mid', 1, 1), ('high', 2, 2)], layer='shadow', cell=[64, 16],
                    anchor=[32, 8], perch=False, shadow=True))
    out.append(dict(name='liam_shadow', key='shadow', frames=ground, points=[{}], durs=[1.0],
                    tags=[('shadow', 0, 0)], layer='shadow', cell=[64, 16], anchor=[32, 8], perch=False, shadow=True))
    return out


def write_sheet(tmp, spec):
    from PIL import Image
    from imgdiff import pixel_diff
    import le_build as LB
    im = LB.strip(spec['frames'])
    n = len(spec['frames'])
    fw = spec['frames'][0].shape[1]
    name = spec['name']
    tpng = os.path.join(tmp, name + '.png')
    tase = os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    lua = os.path.join(tmp, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LB.LUA)
    tags = ';'.join('%s:%d:%d' % (t, a + 1, b + 1) for (t, a, b) in spec['tags'])
    subprocess.run([LB.ASEPRITE, '-b', '--script-param', 'src=' + tpng, '--script-param', 'out=' + tase,
                    '--script-param', 'n=%d' % n, '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%d' % round(t * 1000) for t in spec['durs']),
                    '--script-param', 'layer=' + spec['layer'], '--script-param', 'tags=' + tags,
                    '--script', lua], check=True, capture_output=True)
    back = os.path.join(tmp, name + '_rt.png')
    subprocess.run([LB.ASEPRITE, '-b', tase, '--sheet', back, '--sheet-type', 'horizontal'], check=True,
                   capture_output=True)
    d = pixel_diff(Image.open(tpng), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
        shutil.copyfile(src, os.path.join(OUT, name + ext))
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.path.join(OUT, 'x4', name + '_x4.png'))
    return im


# ------------------------------------------------------------------ GIFs on the real mat
def _mat_crop(box):
    from PIL import Image
    import le_mock as M
    return Image.open(os.path.join(M.CAP, 'arena_nohud.png')).convert('RGBA').crop(box)


def _img(cv):
    from PIL import Image
    import le_rig as R
    return Image.fromarray(R.to_rgba(cv), 'RGBA')


def _up(im, s=3):
    from PIL import Image
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def gif(path, frames, durs):
    frames = [f.convert('RGB').convert('P', palette=1, colors=255) for f in frames]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=[int(d * 1000) for d in durs],
                   loop=0, disposal=2)


def perch_scene(cv, fx=None, pillar_frame=None):
    """Liam's cell standing on the pillar (feet on its stand point), over a crop of the mat, 3x.
    fx: list of (fx canvas, pivot in fx, point in Liam's cell)."""
    import le_pillar as PL
    bg = _mat_crop((960 - 180, 0, 960 + 180, 348 + 40))              # 360 x 388 px: screen top to below the pillar
    ox, oy = 960 - 180, 0
    pil = _up(_img(pillar_frame if pillar_frame is not None else PL.stand_frame(0)))
    bg.alpha_composite(pil, (960 - PL.ANCHOR[0] * 3 - ox, 348 - PL.ANCHOR[1] * 3 - oy))
    lx, ly = 960 - 48 * 3 - ox, 198 - 96 * 3 - oy
    li = _up(_img(cv))
    bg.alpha_composite(li, (lx, ly))
    for (fcv, pivot, pt) in (fx or []):
        f = _up(_img(fcv))
        bg.alpha_composite(f, (int(lx + pt[0] * 3 - pivot[0] * 3), int(ly + pt[1] * 3 - pivot[1] * 3)))
    return bg


def ground_scene(cv, w=110, h=100):
    bg = _mat_crop((960 - w * 3 // 2, 520 - h * 3 + 20, 960 + w * 3 // 2, 520 + 20))
    li = _up(_img(cv))
    bg.alpha_composite(li, (bg.width // 2 - 48 * 3, bg.height - 20 - 96 * 3))
    return bg


def build_gifs(by):
    import le_air as A
    import le_earth as E
    made = []
    # ground loops
    for key in ('laugh', 'staff_pull'):
        s = by[key]
        frames = [ground_scene(f) for f in s['frames']]
        reps = 3 if key == 'laugh' else 1
        gif(os.path.join(OUT, 'gif_liam_%s.gif' % key), frames * reps + ([frames[-1]] if key == 'staff_pull' else []),
            s['durs'] * reps + ([0.8] if key == 'staff_pull' else []))
        made.append('gif_liam_%s.gif' % key)
    # wobble on the pillar (twice round)
    s = by['wobble']
    frames = [perch_scene(f) for f in s['frames']]
    gif(os.path.join(OUT, 'gif_liam_wobble.gif'), frames * 3, s['durs'] * 3)
    made.append('gif_liam_wobble.gif')
    # blast with the gust burst pinned on the staff tip
    s = by['blast']
    burst = [A.gust_burst(k) for k in range(4)]
    frames, durs = [], []
    frames.append(perch_scene(s['frames'][0])); durs.append(s['durs'][0])
    for k, bf in enumerate(burst):
        pose = s['frames'][1] if k < 2 else s['frames'][2]
        pts = s['points'][1 if k < 2 else 2]
        frames.append(perch_scene(pose, fx=[(bf, A.GUST_PIVOT, pts['staff_tip'])]))
        durs.append((0.05, 0.07, 0.08, 0.1)[k])
    frames.append(perch_scene(s['frames'][2])); durs.append(0.4)
    gif(os.path.join(OUT, 'gif_liam_blast.gif'), frames, durs)
    made.append('gif_liam_blast.gif')
    # breathe with the plume pinned on the mouth, the ANIMS order 0,1,2,1,2,1,2,1,2,3
    s = by['breathe']
    plume = [A.cold_breath(k) for k in range(4)]
    order = [0, 1, 2, 1, 2, 1, 2, 1, 2, 3]
    times = [0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2]
    frames = []
    for i, fi in enumerate(order):
        pose, pts = s['frames'][fi], s['points'][fi]
        if fi == 0:
            fx = []
        elif fi == 3:
            fx = [(plume[3], A.BREATH_PIVOT, pts['mouth'])]
        else:
            fx = [(plume[0] if i == 1 else plume[fi], A.BREATH_PIVOT, pts['mouth'])]
        frames.append(perch_scene(pose, fx=fx))
    gif(os.path.join(OUT, 'gif_liam_breathe.gif'), frames, times)
    made.append('gif_liam_breathe.gif')
    # slam with the burst on the staff butt on impact
    s = by['slam']
    frames, durs = [], []
    for k, f in enumerate(s['frames']):
        fx = [(E.slam_burst(0), (16, 15), s['points'][k]['staff_butt'])] if k == 2 else \
             ([(E.slam_burst(1), (16, 15), s['points'][2]['staff_butt'])] if k == 3 else [])
        frames.append(perch_scene(f, fx=fx))
        durs.append(s['durs'][k])
    gif(os.path.join(OUT, 'gif_liam_slam.gif'), frames * 2, durs * 2)
    made.append('gif_liam_slam.gif')
    # fall into downed (ground cell)
    fa, dn = by['fall'], by['downed']
    frames = [ground_scene(f) for f in fa['frames']] + [ground_scene(f) for f in dn['frames']] * 3
    gif(os.path.join(OUT, 'gif_liam_fall_to_downed.gif'), frames, fa['durs'] + dn['durs'] * 3)
    made.append('gif_liam_fall_to_downed.gif')
    return made


# ------------------------------------------------------------------ the takeover end-state mock
def mock_takeover(by, path):
    from PIL import Image
    import numpy as np
    import le_mock as M
    import le_pillar as PL
    nohud, hud, withp = M.load_caps()
    scene = nohud.copy()
    pil = M.up(M.img(PL.stand_frame(0)))
    M.paste_at(scene, pil, (960 - PL.ANCHOR[0] * 3, 348 - PL.ANCHOR[1] * 3))
    shield = M.up(M.img(PL.shield_overlay(0)))
    M.paste_at(scene, shield, (960 - PL.ANCHOR[0] * 3, 348 - PL.ANCHOR[1] * 3))
    li = M.up(M.img(by['perch_idle']['frames'][0]))
    M.paste_at(scene, li, (960 - 48 * 3, 198 - 96 * 3))
    pl, xy = M.player_sprite(nohud, withp)
    M.paste_at(scene, pl, (xy[0] + 190, xy[1] - 250))
    scene = M.finish(scene, nohud, hud)
    M.caption(scene, 'LIAM - TAKEOVER END STATE: parked on the pillar (960,348), perch_idle, pillar shielded, HUD at 0.30, '
                     'no Bixby, player free (plate text is the capture\'s; code swaps it to LIAM)')
    scene.convert('RGB').save(path)
    return path


# ------------------------------------------------------------------ contact sheet and anchors
def contact(specs, path):
    import le_build as LB
    return LB.contact(specs, path)


def anchors(specs):
    import numpy as np
    import le_rig as R
    import le_poses as P
    out = dict(note='FULL POSE SHEETS (texels, scale 3). Cells 96x96 unless stated; liam.png at (16,32); anchor '
                    'point (48,96) = sprite.offset (0,-48). Points are cell texels.',
               liam_png_numbers=dict(black_ratio=0.2819, colours=35, band=[0.2537, 0.3101]),
               perch_box=dict(rect=[P.PERCH_BOX['left'], P.PERCH_BOX['top'], 72, 66]), sheets={})
    for s in specs:
        rows = []
        for i, (cv, pts) in enumerate(zip(s['frames'], s['points'])):
            row = dict(frame=i)
            if not s.get('shadow'):
                b, c, n = R.numbers(cv)
                ys, xs = np.nonzero(cv != '.')
                row.update(black_ratio=round(b, 4), colours=c,
                           drawn_box=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())])
            for k, v in pts.items():
                row[k] = [round(float(v[0]), 1), round(float(v[1]), 1)]
            rows.append(row)
        entry = dict(file=s['name'] + '.png', cell=s['cell'], anchor=s['anchor'], frames=len(s['frames']),
                     times=s['durs'], tags=[dict(name=t, frames=[a, b]) for (t, a, b) in s['tags']],
                     on_pillar=s['perch'], per_frame=rows)
        if 'juggle' in s:
            entry['juggle'] = s['juggle']
            entry['note'] = 'BossJuggled table: launch 0-1, tumble 2-6 (loop), crash 7-9, down 10-11; feet (64,95), ' \
                            'offset (0,-48) like Mason; tumble_centre and top_row measured'
        if s.get('shadow'):
            entry['note'] = 'solid black ellipses; the code sets the alpha (mason_leap_shadow convention)'
        if s['key'] == 'breathe':
            entry['note'] = 'the cold-breath POSE sheet (ANIMS cold_breath): 0 inhale, 1 blow, 2 blow, 3 recover; ' \
                            'play 0,1,2,1,2,1,2,1,2,3; the plume liam_cold_breath.png pins on the mouth point'
        out['sheets'][s['key']] = entry
    # the POINTS table in the code's shape (first frame of each pose, as LiamArtLayout reads it)
    by = {s['key']: s for s in specs}

    def first(key, pt):
        v = by[key]['points'][0].get(pt) or next(p[pt] for p in by[key]['points'] if pt in p)
        return [round(float(v[0]), 1), round(float(v[1]), 1)]
    out['POINTS_for_LiamArtLayout'] = dict(
        staff_tip=dict(perch_idle=first('perch_idle', 'staff_tip'), cast_left=first('cast_left', 'staff_tip'),
                       cast_right=first('cast_right', 'staff_tip'), blast=[round(float(v), 1) for v in by['blast']['points'][1]['staff_tip']]),
        mouth=dict(cold_breath=[round(float(v), 1) for v in by['breathe']['points'][1]['mouth']]),
        staff_butt=dict(slam_rise=[round(float(v), 1) for v in by['slam_rise']['points'][1]['staff_butt']],
                        slam=[round(float(v), 1) for v in by['slam']['points'][2]['staff_butt']]),
        head_top=dict(downed=first('downed', 'head_top')), daze=dict(downed=first('downed', 'daze')))
    out['POINTS_note'] = ('One point per pose as the code reads it today: the blast release frame (1), the breathe blow '
                          'frame (1), the slam_rise and slam impact frames. Per-frame values are under sheets.')
    return out


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    import le_build as LB
    LB.install_guard()
    for d in (os.path.join(HERE, 'approval'), OUT, os.path.join(OUT, 'x4')):
        if not os.path.isdir(d):
            os.mkdir(d)
    specs = sheets()
    d = LB.check_slimed(specs[0]['frames'][0])
    if d:
        raise SystemExit('slimed_sit does not match defeat frame 9: %s' % d)
    print('slimed_sit matches defeat frame 9 exactly (imgdiff)')
    tmp = tempfile.mkdtemp(prefix='le_full_')
    written = []
    for spec in specs:
        im = write_sheet(tmp, spec)
        written.append(spec['name'] + '.png')
        print('wrote %-22s %dx%d (%d frames)' % (spec['name'], im.width, im.height, len(spec['frames'])))
    by = {s['key']: s for s in specs}
    for g in build_gifs(by):
        written.append(g)
        print('wrote', g)
    mock_takeover(by, os.path.join(OUT, 'liam_mock_takeover_end.png'))
    written.append('liam_mock_takeover_end.png')
    print('wrote liam_mock_takeover_end.png')
    contact([s for s in specs], os.path.join(OUT, 'liam_full_contact.png'))
    written.append('liam_full_contact.png')
    a = anchors(specs)
    a['files'] = written
    with open(os.path.join(OUT, 'anchors.json'), 'w') as f:
        json.dump(a, f, indent=1)
    print('wrote anchors.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
