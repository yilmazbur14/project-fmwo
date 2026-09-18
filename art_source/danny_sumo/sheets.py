"""Production animation sheets for Danny's transformation.

Every sheet is a horizontal strip, frame 0 leftmost, hframes = N, vframes = 1.

  SMALL FORM   64x64  per frame, drawn at scale 3 (his training-room size)
  EVOLVED FORM 176x144 per frame, drawn at scale 3, anchor = bottom-centre
               (88, 144), figure standing on row 143

The transformation composites the small form into the big frame at (+56, +80),
so both silhouettes swap in place around one anchor.

Usage: python sheets.py <asset-root> [<preview-dir>]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pngio import write_png, upscale          # noqa: E402
from rig import to_pix                         # noqa: E402
import danny_small as SM                       # noqa: E402
import danny_sumo as SU                        # noqa: E402

SW = SH = 64                     # small-form frame
BW, BH = SU.W, SU.H              # 176 x 144
SMALL_OX, SMALL_OY = 56, 80      # small form inside the big frame


# ======================================================== SMALL-FORM SHEETS
# (key, duration ms)
SMALL_SHEETS = {
    'danny_walk': dict(
        frames=[('walk_a', 160), ('walk_pass', 160),
                ('walk_b', 160), ('walk_pass2', 160)],
        loop='0-3'),
    'danny_grip': dict(
        frames=[('reach', 140), ('grip', 280), ('strain', 90)],
        loop='1-2 ping-pong while he strains'),
    'danny_tear': dict(
        frames=[('tear', 260), ('tear_wide', 120), ('shirt_off', 340)],
        loop='once'),
    'danny_flex': dict(
        frames=[('flex_rise', 120), ('flex', 420),
                ('flex_in', 300), ('flex_out', 300)],
        loop='2-3 (the breathing hold); frame 2 is the hand-over frame'),
}

# ======================================================== EVOLVED-FORM SHEETS
AWAKE = dict(eye='awake', mouth='roar', bubble=0, knuck=False)
GUARD = dict(AWAKE, arm='guard')
COCK = dict(AWAKE, arm='cock')
SLAP_LH = dict(AWAKE, arm_l='slap_hi', arm_r='cock')
SLAP_RL = dict(AWAKE, arm_l='cock', arm_r='slap_lo')
SLAP_LL = dict(AWAKE, arm_l='slap_lo', arm_r='cock')
SLAP_RH = dict(AWAKE, arm_l='cock', arm_r='slap_hi')

SUMO_SHEETS = {
    # sleepy idle: the belly swells, the head nods, the bubble grows
    'danny_sumo_idle': dict(frames=[
        (dict(bubble=2), 200),
        (dict(head_dy=1, belly_s=1.012, bubble=2), 180),
        (dict(head_dy=2, belly_s=1.022, bubble=3), 260),
        (dict(head_dy=1, belly_s=1.012, bubble=2), 180),
    ], loop='0-3'),

    # the moment he stops being a joke
    'danny_sumo_wake': dict(frames=[
        (dict(eye='half', mouth='slack', bubble=4, head_dy=1), 140),
        (dict(eye='awake', mouth='slack', bubble=0, head_dy=-1,
              arm='cock', knuck=False), 90),
        (dict(GUARD), 260),
    ], loop='once; frame 2 is identical to danny_sumo_slap frame 0'),

    # the signature: hundred-hand slap
    'danny_sumo_slap': dict(frames=[
        (dict(GUARD), 120),
        (dict(COCK), 100),
        (dict(SLAP_LH), 60),
        (dict(SLAP_RL, head_dy=1), 60),
        (dict(SLAP_LL, head_dy=1), 60),
        (dict(SLAP_RH), 60),
        (dict(GUARD, head_dy=1), 140),
        (dict(GUARD, belly_s=1.012), 200),
    ], loop='2-5 for as long as the flurry runs, then 6-7 to recover'),

    # a heavy step in
    'danny_sumo_step': dict(frames=[
        (dict(arm='swingb', all_dy=-2, bubble=2), 140),
        (dict(arm='swingf', all_dy=-3, dx=3, bubble=2), 90),
        (dict(arm='swingb', all_dy=2, dx=4, belly_s=1.02, bubble=2), 110),
        (dict(arm='hang', dx=2, bubble=2), 160),
    ], loop='0-3 while he walks; ends 4px advanced'),

    # taking one
    'danny_sumo_hit': dict(frames=[
        (dict(eye='wide', mouth='ow', bubble=0, arm='flail',
              dx=-4, head_dy=-2, knuck=False), 90),
        (dict(eye='wide', mouth='ow', bubble=0, arm='flail',
              dx=-1, head_dy=-1, knuck=False), 140),
    ], loop='once, then back to idle'),

    # he does not fall over.  He sits down and goes to sleep.
    'danny_sumo_defeat': dict(frames=[
        (dict(eye='half', mouth='ow', bubble=0, arm='limp',
              head_dy=1, dx=2), 180),
        (dict(eye='half', mouth='slack', bubble=0, arm='limp',
              all_dy=5, head_dy=2), 160),
        (dict(eye='shut', mouth='slack', bubble=0, arm='limp',
              all_dy=10, head_dy=3, leg='sit'), 220),
        (dict(eye='shut', mouth='snore', bubble=3, arm='limp',
              all_dy=11, head_dy=4, leg='sit'), 600),
    ], loop='once, hold on frame 3'),
}


# ============================================================== COMPOSITING
def big_frame(pix, ox=0, oy=0):
    out = [[(0, 0, 0, 0)] * BW for _ in range(BH)]
    for y, row in enumerate(pix):
        ty = y + oy
        if not (0 <= ty < BH):
            continue
        for x, p in enumerate(row):
            tx = x + ox
            if p[3] and 0 <= tx < BW:
                out[ty][tx] = p
    return out


def strip(frames, fw, fh):
    sheet = [[(0, 0, 0, 0)] * (fw * len(frames)) for _ in range(fh)]
    for i, p in enumerate(frames):
        for y in range(fh):
            for x in range(fw):
                sheet[y][i * fw + x] = p[y][x]
    return sheet


def evolve_frames():
    """The three frames the transformation needs, all in the big frame:
      0  small Danny holding the flex (his flex sheet frame 2), composited
      1  the evolved form, awake
      2  the evolved form, landing
    Frames 0 and 1 are what the flash alternates between; the coder drives a
    flat-white treatment over them rather than needing white copies on disk."""
    return [big_frame(to_pix(SM.build('flex_in')), SMALL_OX, SMALL_OY),
            to_pix(SU.build('awake')),
            to_pix(SU.build('land'))]


def build_all():
    out = {}
    for name, sheet in SMALL_SHEETS.items():
        pix = [to_pix(SM.build(k)) for k, _ in sheet['frames']]
        out[name] = (strip(pix, SW, SH), SW, SH, sheet)
    for name, sheet in SUMO_SHEETS.items():
        pix = [to_pix(SU.build('idle', dict(SU.DEFAULT, **sp)))
               for sp, _ in sheet['frames']]
        out[name] = (strip(pix, BW, BH), BW, BH, sheet)
    ev = evolve_frames()
    out['danny_sumo_evolve'] = (
        strip(ev, BW, BH), BW, BH,
        dict(frames=[('small flex hold', 0), ('evolved awake', 0),
                     ('evolved land', 0)],
             loop='driven by the transformation state machine, see the report'))
    return out


if __name__ == '__main__':
    root = sys.argv[1]
    prev = sys.argv[2] if len(sys.argv) > 2 else None
    small_dir = os.path.join(root, 'Assets', 'Characters', 'Danny')
    sumo_dir = os.path.join(small_dir, 'Sumo')
    os.makedirs(sumo_dir, exist_ok=True)
    sheets = build_all()
    for name, (px, fw, fh, meta) in sorted(sheets.items()):
        d = small_dir if name in SMALL_SHEETS else sumo_dir
        w, h = fw * len(meta['frames']), fh
        write_png(os.path.join(d, name + '.png'), w, h, px)
        print('%-24s %4d x %3d  %d frames' % (name, w, h, len(meta['frames'])))
        if prev:
            w2, h2, p2 = upscale(w, h, px, 3, bg='checker')
            write_png(os.path.join(prev, name + '_3x.png'), w2, h2, p2)
