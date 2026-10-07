"""Build every wave-2 sheet in memory (same structure as kjr_build). Nothing here writes a file."""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kjr as R  # noqa: E402
import kjr_render as RR  # noqa: E402
import kjr_poses2 as P2  # noqa: E402
import kjr_fx2 as F2  # noqa: E402
from kjr_build import BODY, fr  # noqa: E402

TIMES2 = {
    'kaiju_roar': ([0.10, 0.10, 0.15, 0.15, 0.15, 0.15], False),
    'kaiju_roar_spines': ([0.10, 0.10, 0.15, 0.15, 0.15, 0.15], False),
    'kaiju_bow': ([0.10] * 4, False),
    'kaiju_hit': ([0.08, 0.14], False),
    'kaiju_tail_windup': ([0.13] * 3, False),
    'kaiju_tail_spin': ([0.0875] * 8, False),
    'kaiju_tail_arc': (None, False),
    'kaiju_collapse': ([0.08, 0.10, 0.12, None], False),
    'kaiju_down': ([0.30] * 2, True),
    'kaiju_puff': ([0.06] * 6, False),
}


def sheet(name, frame, pivot, frames, kind='body', note=''):
    times, loop = TIMES2[name]
    return {'name': name, 'frame': list(frame), 'pivot': list(pivot), 'frames': frames, 'times': times,
            'loop': loop, 'kind': kind, 'note': note}


def body(pose, opt):
    kw = dict(opt)
    if kw.pop('jaw_from_pose', False):
        kw['jaw'] = pose.get('jaw', (0.0,))[0]
    roar = kw.pop('roar', False)
    smear = kw.pop('smear', 0)
    px, fx, info = RR.render_body(pose, **kw)
    px = dict(px)
    fx = set(fx)
    if roar and info.get('MOUTH'):
        m, n = info['MOUTH'], info['NECK']
        a = math.atan2(m[1] - n[1], m[0] - n[0]) + math.radians(28)     # fan them into the frame
        d = (math.cos(a), math.sin(a))
        ln = 1.0
        arcs = F2.roar_arcs(m, (d[0] / ln, d[1] / ln), roar if isinstance(roar, int) else 1, px)
        for q, k in arcs.items():
            if 0 <= q[0] < BODY[0] and 0 <= q[1] < BODY[1]:
                px[q] = k
                fx.add(q)
    if smear:
        extra = F2.smear(px, smear)
        extra.update(F2.tail_smear(info['FEET'], R.BASE_SC, smear))
        for q, k in extra.items():
            if 0 <= q[0] < BODY[0] and 0 <= q[1] < BODY[1] and q not in px:
                px[q] = k
                fx.add(q)
    return px, fx, info


def body_sheets():
    out = {}
    notes = {
        'kaiju_roar': 'intro, Phase B and the player\'s defeat; f1-f5 carry the sound arcs (fx layer). For the '
                      'Phase B roar draw kaiju_roar_spines over it (normal blend): every plate flashing',
        'kaiju_bow': 'the head lowered for the remount; RIDER_SEAT per frame (it drops with the head)',
        'kaiju_hit': 'a funko blast at its legs: the near foot kicked up, eyes squeezed shut',
        'kaiju_tail_windup': 'HIP is the tell anchor (the yellow ring)',
        'kaiju_tail_spin': 'one full turn: f0 facing right, f1-f2 turning through the front (squashed, smeared), '
                           'f3 facing left (drawn turned, not mirrored by code), f4-f5 turning through the back, '
                           'f6-f7 facing right again. Smear streaks and the tail\'s blur are on the fx layer',
        'kaiju_collapse': 'the Break: knees buckle, over backwards, down on its rump (eyes shut), f3 == kaiju_down f0',
        'kaiju_down': 'sitting, swirl eyes, the head lolling; loop',
    }
    for name, frames in P2.sheets().items():
        fs = []
        for i, (pose, opt) in enumerate(frames):
            o = dict(opt)
            if o.get('roar'):
                o['roar'] = i
            px, fx, info = body(pose, o)
            fs.append(fr(px, fx, info))
        out[name] = sheet(name, BODY, R.FEET, fs, note=notes.get(name, ''))
    return out


def roar_spines():
    """Overlay frames for kaiju_roar: every plate lit, flashing white on alternate frames."""
    fs = []
    allg = {g: 1.0 for g in range(R.N_GROUPS)}
    for i, (pose, opt) in enumerate(P2.sheets()['kaiju_roar']):
        jaw = pose.get('jaw', (0.0,))[0]
        base, _, _ = RR.render_body(pose, jaw=jaw)
        px, fx, info = RR.render_body(pose, jaw=jaw, glow=allg, flash=(i % 2 == 1), halo=True)
        over = {q: c for q, c in px.items() if base.get(q) != c}
        fxs = {q for q in over if q in fx or q not in base}
        fs.append(fr(over, fxs, {'FLASH': i % 2 == 1}))
    return sheet('kaiju_roar_spines', BODY, R.FEET, fs, kind='overlay',
                 note='OPTIONAL overlay for kaiju_roar (same frame, same pivot), normal blend: every plate lit, '
                      'white-hot on odd frames. For the Phase B roar only')


def tail_arc_sheet():
    fs = []
    for k in range(16):
        px, pivot, lost = F2.tail_arc(k)
        fs.append(fr(px, set(px), {'ANGLE_DEG': k * 22.5, 'PIVOT_FEET': list(pivot), 'clipped_px': lost}))
    return sheet('kaiju_tail_arc', (F2.ARC_W, F2.ARC_H), [0, 0], fs, kind='fx_add',
                 note='additive floor swoosh. Frame k = the tail\'s leading edge at k * 22.5 deg round the feet '
                      '(0 = screen right, 90 = toward the camera, clockwise), its trail behind. Each frame has '
                      'its own PIVOT_FEET (the ellipse centre, often outside the frame): put that on the kaiju\'s '
                      'FEET. Outer edge = the (520, 230) px band ellipse')


def puff_sheet():
    fs = [fr(F2.puff96(i), set(F2.puff96(i)), {}) for i in range(6)]
    return sheet('kaiju_puff', (F2.PUFF, F2.PUFF), [48, 48], fs, kind='fx',
                 note='96x96 pink-gold puff and star, centred on its pivot; the grow / shrink / funko pop language')


def build():
    S = body_sheets()
    S['kaiju_roar_spines'] = roar_spines()
    S['kaiju_tail_arc'] = tail_arc_sheet()
    S['kaiju_puff'] = puff_sheet()
    return S
