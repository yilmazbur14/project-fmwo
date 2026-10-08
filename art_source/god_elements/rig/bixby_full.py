"""BIXBY'S PUPPET, THE FULL SET: ash-fur twins (approved 2026-10-06) of every sheet the Elemental Wheel plays,
same names, grids and counts as his live sheets, through the approved recipe (bixby_puppet.py, take B).

  - the twin rule: same size, grid, anchor (96, 151) and silhouette; pure-black keyline; every colour mapped.
  - FIRE STAYS FIRE (the plan's default): fire in or from his mouths (the flyby curtain, the perch volley,
    inhale and breath, the impact sparks) keeps its own ember colours exactly and carries no keyline; on the
    frames where he breathes or holds fire his eyes burn EMBER (the roster's take-A glow: #FFD55C / #FF7A2E);
    everywhere else they are the approved rune blue.
  - rings: the roster's all-or-nothing rule per anim (a ring is drawn on an anim only if the tracker finds it
    on every frame of it); the side-view flyby and the juggle carry none.
  - BACK: between the wing roots on his middle head's axis - (96, 72) on hover, (104, 72) on the fly key - tracked per frame; the flyby's set by
    hand on his wing root; the juggle's null.
"""
import math
from ge_common import *
import bixby_puppet as BP

FWB, FHB = 192, 160
TAKE_FUR = 'ash'
EMBER = (hx('FFD55C'), hx('FF7A2E'))

# sheet -> (frame w, frame h, anims {name: frames}) - names and counts from BixbyBeastArtLayout
SHEETS = {
    'bixby_beast': (192, 160, {'hover': [0, 1, 2, 3]}),
    'bixby_beast_fly': (192, 160, {'fly': [0, 1, 2]}),
    'bixby_beast_flyby': (192, 160, {'glide': [0, 1, 2, 3], 'breath': [4, 5, 6, 7]}),
    'bixby_perch': (192, 160, {'perch_land': [0, 1], 'perch': [2, 3], 'volley': [4, 5, 6], 'inhale': [7, 8, 9],
                               'rear_back': [10], 'perch_breath': [11, 12], 'spent': [13], 'release': [14, 15]}),
    'bixby_pound': (192, 160, {'brace': [0, 1], 'pound': [2, 3, 4, 5]}),
    'bixby_beast_land': (192, 160, {'land': [0, 1, 2]}),
    'bixby_beast_recover': (192, 160, {'recover': [0, 1, 2, 3]}),
    'bixby_beast_hit': (192, 160, {'hit': [0, 1]}),
    'bixby_juggle': (256, 256, {'juggle': list(range(12))}),
}
NO_RINGS = {'bixby_beast_flyby', 'bixby_juggle'}
FLYBY_BACK = (82, 60)

FIRE_CORE = {'FFF2B0', 'FFFFFF'}
JET_CORE, JET_REACH = 250, 30      # more white-hot than this in a frame is a breath jet (perch 11-12, the flyby)
FIRE_BODY = {'FFC45A', 'FF8C2E', 'FF8C45', 'E0561A', '9A2A10', 'FFE488', 'DE4E2C'}


def hexmap(src):
    return np.array([['%02X%02X%02X' % tuple(c[:3]) if c[3] else '' for c in row] for row in src])


def fire_mask(src, reach=7):
    """His fire: every pixel of a fire colour 8-connected (through fire colours) to a white-hot core pixel and
    within `reach` texels of one. The fur's flame tips and his tongue share some of the colours but never
    touch a white-hot core, so they stay his body."""
    hm = hexmap(src)
    core = np.isin(hm, list(FIRE_CORE))
    firey = core | np.isin(hm, list(FIRE_BODY))
    if not core.any():
        return np.zeros(core.shape, bool)
    if core.sum() > JET_CORE:
        reach = JET_REACH                 # a breath jet: the whole jet is fire, out to its tattered ends
    from collections import deque
    H, W = core.shape
    dist = np.full(core.shape, 1 << 20, int)
    q = deque()
    for y, x in zip(*np.nonzero(core)):
        dist[y, x] = 0
        q.append((x, y))
    # flood from the cores through fire colours, counting steps (8-connected): connected AND within reach
    while q:
        x, y = q.popleft()
        d = dist[y, x]
        if d >= reach:
            continue
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                u, v = x + dx, y + dy
                if 0 <= u < W and 0 <= v < H and firey[v, u] and dist[v, u] > d + 1:
                    dist[v, u] = d + 1
                    q.append((u, v))
    return dist <= reach


def eye_mask(src):
    hm = hexmap(src)
    return np.isin(hm, ['36C487', '0F4A38', 'B6FFDC'])


def boss_for(sheet, fx, keep=None, frame=None):
    b = BP.boss(TAKE_FUR, fx)
    b.hooks = dict(b.hooks)
    b.hooks['back'] = JB.back_hook('mid_head', 104, 72, fallback=('chest', 'crown'))   # the key (fly f0) has his middle head 8 right of hover's axis: hover (96, 72)
    for k in ('wing_l', 'wing_r'):
        b.hooks.pop(k, None)
    if sheet == 'bixby_juggle':
        b.parts, b.overlays, b.hooks, b.tatter, b.regions = {}, [], {}, [], []
    return b


def treat_frame(sheet, src, f, key, skip_rings=(), back_by_hand=None):
    fire = fire_mask(src)
    fx = BP.detached(src) | BP.streaks(src)
    b = boss_for(sheet, fx)
    rel = 'Bixby/%s.png' % sheet
    fd = {}
    if fire.any():
        ys, xs = np.nonzero(fire)
        cols = sorted({'%02X%02X%02X' % tuple(src[y, x, :3]) for y, x in zip(ys, xs)})
        # the keep region: exactly the fire pixels (a box per pixel row run keeps it tight)
        fd['keep'] = {f: {'boxes': [(int(x), int(y), int(x), int(y)) for y, x in zip(ys, xs)], 'colours': cols}}
    if back_by_hand is not None:
        fd['hooks'] = {f: {'back': (back_by_hand, None)}}
    if fd:
        b.frame_data = {rel: fd}
    im, info = C.treat(b, src, TAKE, key_src=key, sheet_rel=rel, frame_no=f, skip_rings=skip_rings)
    a = np.array(im)
    info['fire_px'] = int(fire.sum())
    info['fx'] = fx | {(int(x), int(y)) for y, x in zip(*np.nonzero(fire))}
    info['src'] = src
    return a, info


def ember_eyes(a, src):
    """On a fire frame his eyes burn ember: the approved rune glow swapped for the roster's take-A ember."""
    m = eye_mask(src)
    g1 = (a[:, :, :3] == np.array(PUP['G1'][:3])).all(axis=2)
    g2 = (a[:, :, :3] == np.array(PUP['G2'][:3])).all(axis=2)
    a[m & g1] = EMBER[0]
    a[m & g2] = EMBER[1]
    return a


def flyby_back(src):
    x, y = FLYBY_BACK
    op = src[:, :, 3] > 0
    if op[y, x]:
        return (x, y)
    near = sorted(((dx * dx + dy * dy, dx, dy) for dy in range(-6, 7) for dx in range(-6, 7) if op[y + dy, x + dx]))
    return (x + near[0][1], y + near[0][2])


EMBER_MIN = 30          # fire pixels in a frame that make it a fire frame (his eyes burn ember)


def plate_back(src):
    """Where the tracker cannot read him: the back from his middle head's headband plate (its top edge, the
    only #EEF4F7 he has), 59 rows under it on his axis - the key frame's own offset (plate top 13, back 72) -
    snapped onto his silhouette; else his key point (96, 72) snapped."""
    hm = hexmap(src)
    ys, xs = np.nonzero(hm == 'EEF4F7')
    op = src[:, :, 3] > 0
    if len(ys):
        # the plate's top edge is his longest run of it: its row, and its middle is his middle head's axis
        rows, counts = np.unique(ys, return_counts=True)
        top = int(rows[np.argmax(counts)])
        row = np.sort(xs[ys == top])
        x, y = int(round((row.min() + row.max()) / 2.0)), top + 59
    else:
        x, y = 96, 72
    x = min(max(x, 0), src.shape[1] - 1)
    y = min(max(y, 0), src.shape[0] - 1)
    if not op[y, x]:
        near = sorted(((dx * dx + dy * dy, dx, dy) for dy in range(-12, 13) for dx in range(-12, 13)
                       if 0 <= y + dy < src.shape[0] and 0 <= x + dx < src.shape[1] and op[y + dy, x + dx]))
        if near:
            x, y = x + near[0][1], y + near[0][2]
    return (x, y)


def build_sheet(sheet):
    fw, fh, anims = SHEETS[sheet]
    rel = 'Bixby/%s.png' % sheet
    n = C.frames_in(rel, fw)
    key = C.frame(BP.SHEET, FWB, FHB, 0)
    if sheet == 'bixby_juggle':
        key = np.zeros((fh, fw, 4), np.uint8)
    srcs = [C.frame(rel, fw, fh, f) for f in range(n)]
    backs = [flyby_back(s) if sheet == 'bixby_beast_flyby' else None for s in srcs]
    first = [treat_frame(sheet, s, f, key, back_by_hand=backs[f]) for f, s in enumerate(srcs)]
    # the BACK on every non-juggle front-view frame from his headband plate (by hand, the roster's rule: the
    # plate is the one thing on him that cannot be mistaken - the tracker slipped 8 texels on the volley frames)
    if sheet not in ('bixby_juggle', 'bixby_beast_flyby'):
        backs = [plate_back(srcs[f]) for f in range(n)]
    # all-or-nothing rings per anim
    found = [set(i.get('rings_drawn', [])) for _a, i in first]
    out, infos = [], []
    for f, s in enumerate(srcs):
        keep = set(found[f])
        if sheet in NO_RINGS:
            keep = set()
        for fr in anims.values():
            if f in fr:
                keep &= set.intersection(*[found[g] for g in fr])
        skip = tuple(sorted(found[f] - keep))
        a, info = treat_frame(sheet, s, f, key, skip_rings=skip + (('head', 'head_l', 'head_r', 'wrist_l', 'wrist_r', 'knee_l', 'knee_r') if sheet in NO_RINGS else ()),
                              back_by_hand=backs[f])
        info['rings_left_off_sheet'] = list(skip)
        info['ember'] = info['fire_px'] >= EMBER_MIN and sheet in ('bixby_beast_flyby', 'bixby_perch')
        if info['ember']:
            a = ember_eyes(a, s)
        out.append(a)
        infos.append(info)
    return out, infos


def audit(frames, infos):
    probs = []
    pal = {tuple(v) for v in PUP.values()} | set(EMBER)
    for f, (a, info) in enumerate(zip(frames, infos)):
        src = info['src']
        if ((a[:, :, 3] > 0) != (src[:, :, 3] > 0)).any():
            probs.append('f%d silhouette differs' % f)
        if ((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).any():
            probs.append('f%d semi-alpha' % f)
        fx = info['fx']
        cols = {tuple(a[y, x]) for y, x in zip(*np.nonzero(a[:, :, 3] > 0)) if (x, y) not in fx}
        if cols - pal:
            probs.append('f%d off-palette %s' % (f, sorted(cols - pal)[:3]))
        for k in ('gaps', 'lone', 'holes', 'bad_keys', 'silhouette', 'edge_black_lost'):
            if info['lint'].get(k):
                probs.append('f%d lint %s %d %s' % (f, k, len(info['lint'][k]), info['lint'][k][:3]))
        if info['unknown']:
            probs.append('f%d unmapped %s' % (f, info['unknown']))
    return probs


def back_points(infos, sheet):
    if sheet == 'bixby_juggle':
        return [None] * len(infos)
    return [None if i['hooks'].get('back') is None else tuple(int(v) for v in i['hooks']['back']) for i in infos]
