"""Build every wave-1 sheet in memory: frames as {pixel: key} on their sheet's frame, the effect pixels,
per-frame anchors, times. Nothing here writes a file (kjr_export does, into scratch only)."""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kjr as R  # noqa: E402
import kjr_render as RR  # noqa: E402
import kjr_poses as PZ  # noqa: E402
import kjr_fx as FX  # noqa: E402

BODY = (R.FW, R.FH)
TOY_W, TOY_H = 32, 32
TOY_FEET = (12, 27)
GROW = [12, 18, 26, 36, 48, 60, 72, 84, 94, 100]
SHRINK = [100, 84, 60, 40, 24, 15, 12, 12]
AIMS = [-60, -40, -20, 0, 20, 40, 65, 90]
JAW_AIM, JAW_FIRE = 7.0, 24.0
CHARGE_GLOW = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0}
SPARKS = [(48, 150), (44, 128), (52, 108), (40, 140), (47, 163), (60, 96), (72, 84)]

TIMES = {
    'kaiju_idle': ([0.16] * 6, True), 'kaiju_charge': ([0.20] * 2, True),
    'kaiju_head_aim': (None, False), 'kaiju_head_fire': (None, False), 'kaiju_spines': (None, False),
    'kaiju_rear': ([0.12, 0.12, 0.13, 0.13], False), 'kaiju_leap': ([0.10] * 3, False),
    'kaiju_drop': ([0.11] * 2, False), 'kaiju_stomp': ([0.05, 0.10, None], False),
    'kaiju_stumble': ([0.07, 0.08, 0.10, 0.10, None], False), 'kaiju_kneel': ([0.30] * 2, True),
    'kaiju_stand': ([0.12] * 3, False), 'kaiju_land': ([0.06, 0.10, 0.14], False),
    'kaiju_grow': ([0.12] * 10, False), 'kaiju_shrink': ([0.11] * 8, False), 'kaiju_toy': ([0.10] * 4, False),
    'kaiju_shadow': (None, False),
    'kaiju_stomp_mark': ([0.10] * 6, False), 'kaiju_stomp_impact': ([0.05, 0.06, 0.07, 0.08, 0.10, None], False),
    'kaiju_beam_body': ([0.05] * 4, True), 'kaiju_beam_mouth': ([0.05] * 4, True),
    'kaiju_beam_end': ([0.05] * 4, True), 'kaiju_mouth_charge': ([0.08] * 6, False),
    'kaiju_burn_flame': ([0.08] * 6, True), 'kaiju_burn_out': ([0.10] * 4, False),
}


def body_frame(pose, opt):
    kw = dict(opt)
    if kw.pop('jaw_from_pose', False):
        kw['jaw'] = pose.get('jaw', (0.0,))[0]
    return RR.render_body(pose, **kw)


def sheet(name, frame, pivot, frames, kind='body', note=''):
    times, loop = TIMES[name]
    return {'name': name, 'frame': list(frame), 'pivot': list(pivot), 'frames': frames, 'times': times,
            'loop': loop, 'kind': kind, 'note': note}


def fr(px, fx=(), anchors=None):
    return {'px': px, 'fx': set(fx), 'anchors': anchors or {}}


def build_body_sheets(only=None):
    out = {}
    for name, frames in PZ.sheets().items():
        if only and name not in only:
            continue
        fs = []
        for pose, opt in frames:
            px, fx, info = body_frame(pose, opt)
            fs.append(fr(px, fx, info))
        note = ''
        if name == 'kaiju_charge':
            note = ('the breath stance with the head taken off: draw kaiju_head_aim / kaiju_head_fire over it with '
                    'their NECK pivot on this sheet\'s NECK, then kaiju_spines over both (normal blend)')
        if name == 'kaiju_stumble':
            note = 'Jordan leaves the seat on f1; f4 == kaiju_kneel f0'
        if name == 'kaiju_drop':
            note = 'f0 shows the stomping (far, screen-right) foot\'s sole with the gold star sticker'
        out[name] = sheet(name, BODY, R.FEET, fs, note=note)
    return out


def spines_sheet():
    """Overlay frames for kaiju_charge: f0 none, f1..f7 rows 0..k-1 lit (tail first), f8 all flashing.
    Each frame holds only the pixels that change on kaiju_charge f0 (plus the halo and sparks)."""
    base, _, _ = RR.render_body(PZ.charge(0), head=False)
    fs = []
    for k in range(9):
        if k == 0:
            fs.append(fr({}, (), {'ROWS_LIT': 0}))
            continue
        if k < 8:
            glow = {g: 1.0 for g in range(k)}
            px, fx, info = RR.render_body(PZ.charge(0), head=False, glow=glow, halo=True,
                                          spark_pts=SPARKS[:max(0, k - 2)])
        else:
            px, fx, info = RR.render_body(PZ.charge(0), head=False, glow=CHARGE_GLOW, flash=True, halo=True,
                                          spark_pts=SPARKS)
        over = {q: c for q, c in px.items() if base.get(q) != c}
        fxs = {q for q in over if q in fx or q not in base}
        fs.append(fr(over, fxs, {'ROWS_LIT': min(k, 7), 'FLASH': k == 8, 'SPINE_ROWS': info['SPINE_ROWS']}))
    return sheet('kaiju_spines', BODY, R.FEET, fs, kind='overlay',
                 note='overlay for kaiju_charge (same frame and pivot). Draw with NORMAL blend: it replaces the '
                      'plate pixels it covers (opaque), its halo and sparks sit outside the body.')


def head_sheets():
    raw = {}
    for name, jaw, flare in (('kaiju_head_aim', JAW_AIM, False), ('kaiju_head_fire', JAW_FIRE, True)):
        raw[name] = [RR.render_head(a, jaw, glow=True, flare=flare) for a in AIMS]
    xs, ys = [], []
    for frames in raw.values():
        for px, fx, info in frames:
            xs += [x for (x, y) in px]
            ys += [y for (x, y) in px]
    x0, y0 = min(xs) - 1, min(ys) - 1
    w, h = max(xs) - x0 + 2, max(ys) - y0 + 2
    pivot = (RR.HEAD_PIVOT[0] - x0, RR.HEAD_PIVOT[1] - y0)
    out = {}
    for name, frames in raw.items():
        fs = []
        for (px, fx, info), aim in zip(frames, AIMS):
            sh = {(x - x0, y - y0): k for (x, y), k in px.items()}
            sfx = {(x - x0, y - y0) for (x, y) in fx}
            an = {'AIM_DEG': aim, 'NECK': list(pivot),
                  'MOUTH': [info['MOUTH'][0] - x0, info['MOUTH'][1] - y0],
                  'SEAT_ON_HEAD': [info['SEAT_ON_HEAD'][0] - x0, info['SEAT_ON_HEAD'][1] - y0]}
            fs.append(fr(sh, sfx, an))
        out[name] = sheet(name, (w, h), pivot, fs, kind='head',
                          note='head layer: frame i aims %s deg (0 = the approved head, + turns it down / '
                               'clockwise); put its NECK pivot on kaiju_charge NECK. MOUTH = the beam origin.' % AIMS)
    return out


def scaled(pct, feet=R.FEET, size=BODY):
    sc = R.BASE_SC * pct / 100.0
    return RR.render_body({}, sc=sc, feet=feet, size=size)


def toy_px(i):
    sc = R.BASE_SC * 0.12
    pose = [{}, PZ.toy_crouch(), PZ.toy_hop(), PZ.toy_land()][i]
    px, fx, info = RR.render_body(pose, sc=sc, feet=TOY_FEET, size=(TOY_W, TOY_H), floor=(i != 2))
    return px, info


def grow_sheet():
    fs = []
    for i, pct in enumerate(GROW):
        if pct == 100:
            px, fx, info = scaled(100)
            fs.append(fr(px, fx, dict(info, SIZE_PCT=pct)))
            continue
        px, fx, info = scaled(pct)
        amount = 1.0 - i / 9.0
        rmax = 3 + 7 * min(1.0, pct / 48.0)
        puff = FX.puffs_round(px, amount * (1.0 if i < 6 else 0.4), seed=40 + i, rmin=2.0, rmax=rmax,
                              stars=1 if i < 7 else 0, sparks=4 if i < 8 else 3,
                              cover=0.0 if i < 3 else 0.55, out_by=[7, 6, 4][i] if i < 3 else 0.0)
        if i >= 7:
            puff = {q: k for q, k in puff.items() if k in ('W', 'Q')}       # only sparkles left
        px2 = dict(px)
        fxs = set(fx)
        for q, k in puff.items():
            if 0 <= q[0] < BODY[0] and 0 <= q[1] < BODY[1]:
                px2[q] = k
                fxs.add(q)
        fs.append(fr(px2, fxs, dict(info, SIZE_PCT=pct)))
    return sheet('kaiju_grow', BODY, R.FEET, fs,
                 note='baked sizes %s%%, anchored on FEET; pink-gold puffs and gold stars are effects (fx layer); '
                      'f0 is the toy; f9 == kaiju_idle f0' % GROW)


def shrink_sheet():
    fs = []
    for i, pct in enumerate(SHRINK):
        px, fx, info = scaled(pct)
        if i == 7:
            fs.append(fr(px, fx, dict(info, SIZE_PCT=pct)))
            continue
        amount = [0.25, 0.45, 0.65, 0.8, 0.95, 1.0, 0.7][i]
        rmax = [6, 7, 8, 8, 7, 7, 6][i]
        puff = FX.puffs_round(px, amount, seed=70 + i, rmin=2.5, rmax=rmax, cover=0.9 if i >= 4 else 0.55,
                              stars=1 if i in (5, 6) else 0, sparks=3)
        if i == 6:
            # the puff thrown off: a ring round the toy, open in the middle (the summon pop's last beat)
            ring_c = FX.puff_cloud([(R.FEET[0] + 18 * math.cos(a / 8.0 * 2 * math.pi),
                                     R.FEET[1] - 12 + 11 * math.sin(a / 8.0 * 2 * math.pi), 3.5)
                                    for a in range(8)])
            puff = dict(ring_c)
            puff.update(FX.star(R.FEET[0], R.FEET[1] - 30, big=True))
            for d in ((-24, -26), (22, -32), (-30, 2)):
                puff.update(FX.sparkle(R.FEET[0] + d[0], R.FEET[1] + d[1], 1))
        px2 = dict(px)
        fxs = set(fx)
        for q, k in puff.items():
            if 0 <= q[0] < BODY[0] and 0 <= q[1] < BODY[1]:
                px2[q] = k
                fxs.add(q)
        fs.append(fr(px2, fxs, dict(info, SIZE_PCT=pct)))
    return sheet('kaiju_shrink', BODY, R.FEET, fs,
                 note='sizes %s%% on FEET with the puff; f7 is the toy (== kaiju_toy f0 placed on FEET)' % SHRINK)


def toy_sheet():
    fs = []
    for i in range(4):
        px, info = toy_px(i)
        fs.append(fr(px, (), {'FEET': list(TOY_FEET)}))
    return sheet('kaiju_toy', (TOY_W, TOY_H), TOY_FEET, fs,
                 note='the vinyl toy (the kaiju at 12%%): sit, crouch, hop, land; pivot = its feet. f0 is the '
                      'same drawing as kaiju_grow f0 / kaiju_shrink f7')


def fx_sheets():
    out = {}

    def mk(name, fn, n, size, pivot, note='', kind='fx'):
        fs = [fr(fn(i), set(fn(i))) for i in range(n)]
        out[name] = sheet(name, size, pivot, fs, kind=kind, note=note)
    mk('kaiju_stomp_mark', FX.stomp_mark, 6, (FX.MARK_W, FX.MARK_H), FX.MARK_PIVOT,
       'f0-1 tracking flicker (a toed foot shadow), f2 high, f3 mid, f4 low, f5 landed. Rim = the (50, 35)-texel '
       'ellipse round the pivot on every frame')
    mk('kaiju_stomp_impact', FX.stomp_impact, 6, (FX.IMP_W, FX.IMP_H), FX.IMP_PIVOT,
       'pivot on FOOT_IMPACT; floor layer; f5 = the cracks (hold)')
    mk('kaiju_beam_body', FX.beam_body, 4, (32, 32), (0, 16),
       '32x32 horizontal tile: repeat it along the beam (x), rotate the strip by code. Hit band 90 px = 30 texels; '
       'the drawn beam is rows 2..29 (28 texels = 84 px) with its glow edge')
    mk('kaiju_beam_mouth', FX.beam_mouth, 4, (48, 48), (24, 24), 'centred on MOUTH, drawn above the body')
    mk('kaiju_beam_end', FX.beam_end, 4, (48, 48), (28, 24),
       'the splash where the beam meets the rope; the beam arrives from the left (rotate with the beam)')
    mk('kaiju_mouth_charge', FX.mouth_charge, 6, (32, 32), (16, 16), 'additive, centred on MOUTH', kind='fx_add')
    mk('kaiju_burn_flame', FX.burn_flame, 6, (FX.FL_W, FX.FL_H), (8, 23),
       'upright blue flame, pivot bottom-centre; place every 36 px along the burn line, never rotated, phase-offset')
    mk('kaiju_burn_out', FX.burn_out, 4, (FX.FL_W, FX.FL_H), (8, 23), 'the dying ember, same pivot as the flame')
    sh = FX.shadow()
    out['kaiju_shadow'] = sheet('kaiju_shadow', (FX.SH_W, FX.SH_H), FX.SH_PIVOT, [fr(sh, set())], kind='shadow',
                                note='solid black; the game sets its alpha. Pivot sits on the kaiju\'s FEET')
    return out


def build(only=None):
    sheets = {}
    want = (lambda n: only is None or n in only)
    sheets.update(build_body_sheets(only))
    if want('kaiju_spines'):
        sheets['kaiju_spines'] = spines_sheet()
    if want('kaiju_head_aim') or want('kaiju_head_fire'):
        sheets.update(head_sheets())
    if want('kaiju_grow'):
        sheets['kaiju_grow'] = grow_sheet()
    if want('kaiju_shrink'):
        sheets['kaiju_shrink'] = shrink_sheet()
    if want('kaiju_toy'):
        sheets['kaiju_toy'] = toy_sheet()
    for n, s in fx_sheets().items():
        if want(n):
            sheets[n] = s
    return sheets
