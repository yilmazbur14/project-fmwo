"""Body poses for player_uppercut (final). Authored as explicit segments so columns can't drift:
POSE = {y: [(x, 'run'), ...]} in standard 32x32 player-frame coordinates (grounded feet bottom y=28).
render(name, R) -> 48x64 Canvas with the pose lifted R rows (frame = std + (8, 32 - R))."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import Canvas, PAL


def head(hx, hy, chin='d', face=True):
    """profile head block, 5 wide x 6 tall, top-left (hx, hy), facing right"""
    rows = [(hx + 1, 'ccc'), (hx, 'ccccc'), (hx, 'eeeee'), (hx, 'ceeee')]
    if face:
        rows += [(hx, 'dbbbb'), (hx, 'dbbb' + chin)]
    return {hy + i: [r] for i, r in enumerate(rows)}


def merge(*parts):
    out = {}
    for p in parts:
        for y, segs in p.items():
            out.setdefault(y, []).extend(segs)
    return out


def px(points, ch):
    """list of (x, y) single pixels of one colour"""
    out = {}
    for x, y in points:
        out.setdefault(y, []).append((x, ch))
    return out


def seg(d):
    return d


# ---------------------------------------------------------------- CHARGE CROUCH
CROUCH_BODY = merge(
    head(17, 8, chin='.'),
    {12: [(22, 'aa')], 13: [(22, 'aa')]},            # guard glove
    {
        14: [(15, 'dbbbbbbdd')],
        15: [(14, 'bddbbbbbdd')],
        16: [(13, 'bdddbdbdddd')],
        17: [(12, 'bd'), (15, 'dbbdbbdd')],
        18: [(11, 'gaa'), (15, 'dbbbbbd')],
        19: [(11, 'aaf'), (16, 'dbbbb')],
        20: [(11, 'ff'), (15, 'fgagaga')],
        21: [(13, 'faaaaaaaa')],
        22: [(12, 'faaaaffaaaa')],
        23: [(11, 'gaaaaf'), (19, 'aaaaa')],
        24: [(10, 'gaaaf'), (20, 'aaaa')],
        25: [(10, 'bd'), (20, 'dbb')],
        26: [(9, 'bd'), (21, 'dbb')],
        27: [(8, 'ccc'), (21, 'cccc')],
        28: [(7, 'ccc'), (21, 'ccccc')],
    })
# tails whip up and back from the knot at (16, 9); three loop variants
CROUCH_TAILS = [
    px([(16, 9), (15, 8), (14, 8), (13, 7), (15, 10), (14, 10), (13, 11), (12, 11)], 'e'),
    px([(16, 9), (15, 8), (14, 7), (13, 7), (12, 6), (15, 10), (14, 11), (13, 11)], 'e'),
    px([(16, 9), (15, 9), (14, 8), (13, 8), (12, 7), (15, 10), (14, 10), (13, 10), (12, 11)], 'e'),
]

# ---------------------------------------------------------------- LAUNCH
LAUNCH = merge(
    head(16, 2),
    {0: [(22, 'gga')], 1: [(22, 'gaaa')], 2: [(22, 'aaaf')],   # rising fist
     3: [(21, 'bd')], 4: [(21, 'bd')], 5: [(21, 'bd')], 6: [(21, 'bd')], 7: [(21, 'bd')]},
    px([(15, 3), (14, 4), (13, 5), (12, 6)], 'e'),                   # tails streaming down-back
    {
        8: [(15, 'dbbbbbbd')],
        9: [(13, 'ffdbbbbbbd')],
        10: [(13, 'ffdbdbdbdd')],
        11: [(14, 'dbbdbbd')],
        12: [(15, 'dbbbbb')],
        13: [(16, 'dbbb')],
        14: [(15, 'fgagag')],
        15: [(14, 'faaaaaaa')],
        16: [(13, 'faaaaaaaaa')],
        17: [(12, 'gaaaaffaaaadb')],
        18: [(11, 'gaaaaf'), (19, 'aaaadbb')],
        19: [(10, 'gaaaf'), (20, 'ddbbb')],
        20: [(10, 'bdf'), (20, 'dbb')],
        21: [(9, 'bd'), (20, 'dbb')],
        22: [(8, 'bd'), (20, 'ccc')],
        23: [(8, 'bd'), (20, 'cc')],
        24: [(7, 'bd')],
        25: [(7, 'bd')],
        26: [(6, 'bd')],
        27: [(6, 'ccc')],
        28: [(5, 'ccc')],
    })

# ---------------------------------------------------------------- RISE 1 (3/4 front, arm angling up)
RISE1 = merge(
    {-3: [(21, 'gg')], -2: [(20, 'gaaa')], -1: [(20, 'aaaf')], 0: [(19, 'bdaf')],
     1: [(19, 'bd')], 2: [(18, 'bd')]},
    {3: [(14, 'ccc'), (18, 'bd')], 4: [(13, 'ccccc'), (18, 'bd')], 5: [(13, 'eeeee'), (18, 'bd')],
     6: [(13, 'dbbbb'), (18, 'bd')], 7: [(13, 'dbbbbd')], 8: [(14, 'dbbd')]},
    px([(12, 5), (11, 6), (11, 7), (10, 8), (10, 9)], 'e'),
    {
        9: [(12, 'dbbbbbbd')],
        10: [(11, 'dbbbbbbbd')],
        11: [(11, 'dbdbdbdbd')],
        12: [(11, 'dbbdbbdff')],
        13: [(11, 'dbbbbbbff')],
        14: [(12, 'dbbbbbd')],
        15: [(13, 'dbbbd')],
        16: [(12, 'fgagagf')],
        17: [(11, 'faaaaaaa')],
        18: [(11, 'faaaaaaaaa')],
        19: [(11, 'gaaaaaaaaadb')],
        20: [(11, 'gaaaafaaaadbb')],
        21: [(12, 'gaaf'), (20, 'dbb')],
        22: [(13, 'bd'), (20, 'dbb')],
        23: [(13, 'bd'), (21, 'ccc')],
        24: [(13, 'bd')],
        25: [(12, 'bd')],
        26: [(12, 'bd')],
        27: [(12, 'cc')],
        28: [(13, 'c')],
    })

# ---------------------------------------------------------------- RISE 2 (profile, the classic silhouette)
RISE2 = merge(
    {-3: [(18, 'gga')], -2: [(18, 'gaa')], -1: [(18, 'aaf')],
     0: [(18, 'bd')], 1: [(18, 'bd')], 2: [(18, 'bd')], 3: [(18, 'bd')], 4: [(18, 'bd')],
     5: [(18, 'bd')], 6: [(18, 'bd')], 7: [(18, 'bd')], 8: [(18, 'bd')]},
    head(13, 3),
    px([(12, 5), (11, 6), (10, 7), (10, 8), (9, 9)], 'e'),
    {
        9: [(12, 'dbbbbbbd')],
        10: [(11, 'dbbbbbbdd')],
        11: [(11, 'dbdbdbddd')],
        12: [(11, 'dbbdbbdaa')],
        13: [(11, 'dbbbbbbaa')],
        14: [(12, 'dbbbbb')],
        15: [(13, 'dbbb')],
        16: [(12, 'fgagag')],
        17: [(11, 'faaaaaaaa')],
        18: [(11, 'faaaaaaaaaa')],
        19: [(11, 'gaaaaaaaaaadb')],
        20: [(11, 'gaaaafaaaaadbb')],
        21: [(12, 'gaaf'), (21, 'dbb')],
        22: [(13, 'bd'), (21, 'dbb')],
        23: [(13, 'bd'), (22, 'cc')],
        24: [(13, 'bd'), (22, 'ccc')],
        25: [(13, 'bd')],
        26: [(13, 'bd')],
        27: [(13, 'cc')],
        28: [(14, 'c')],
    })

# ---------------------------------------------------------------- RISE 3 (turning away, 3/4 back)
RISE3 = merge(
    {-3: [(17, 'gga')], -2: [(17, 'gaa')], -1: [(17, 'aaf')],
     0: [(17, 'bd')], 1: [(17, 'bd')], 2: [(17, 'bd')], 3: [(17, 'bd')], 4: [(17, 'bd')],
     5: [(17, 'bd')], 6: [(17, 'bd')], 7: [(17, 'bd')], 8: [(17, 'bd')]},
    {3: [(13, 'ccc')], 4: [(12, 'ccccc')], 5: [(12, 'eeeee')], 6: [(12, 'ccccd')],
     7: [(12, 'cccdb')], 8: [(13, 'cdbb')]},
    px([(11, 5), (10, 6), (10, 7), (9, 8), (9, 9)], 'e'),
    {
        9: [(12, 'bbbbbd')],
        10: [(11, 'bbbdbbbdd')],
        11: [(10, 'ffbdbbbdbd')],
        12: [(10, 'ffbbbdbbbd')],
        13: [(11, 'bbbbdbbd')],
        14: [(12, 'bbbdbd')],
        15: [(13, 'bbbd')],
        16: [(12, 'gagagf')],
        17: [(11, 'aaaaaaaf')],
        18: [(11, 'aaaaaaaaaf')],
        19: [(11, 'aaaaaaaaaadb')],
        20: [(11, 'gaaaafaaaadbb')],
        21: [(12, 'gaaf'), (20, 'dbb')],
        22: [(13, 'bd'), (20, 'dbb')],
        23: [(13, 'bd'), (21, 'ccc')],
        24: [(13, 'bd')],
        25: [(13, 'bd')],
        26: [(13, 'bd')],
        27: [(13, 'cc')],
        28: [(14, 'c')],
    })

# ---------------------------------------------------------------- APEX (full stretch)
APEX = merge(
    {-4: [(17, 'gga')], -3: [(17, 'gaa')], -2: [(17, 'aaf')],
     -1: [(17, 'bd')], 0: [(17, 'bd')], 1: [(17, 'bd')], 2: [(17, 'bd')], 3: [(17, 'bd')],
     4: [(17, 'bd')], 5: [(17, 'bd')], 6: [(17, 'bd')], 7: [(17, 'bd')]},
    {2: [(13, 'ccc')], 3: [(12, 'ccccc')], 4: [(12, 'eeeee')], 5: [(12, 'ccccd')],
     6: [(12, 'cccdb')], 7: [(13, 'cdbb')]},
    px([(11, 4), (10, 3), (10, 2), (9, 1), (11, 5), (10, 5), (9, 6), (8, 6)], 'e'),     # tails lift as he slows
    {
        8: [(12, 'bbbbbd')],
        9: [(11, 'bbbdbbbdd')],
        10: [(11, 'bbbdbbbdbd')],
        11: [(11, 'bdbbdbbbd')],
        12: [(11, 'bbbdbbbbd')],
        13: [(10, 'fbbbbbbd')],
        14: [(10, 'ff'), (13, 'bbbd')],
        15: [(10, 'ff'), (12, 'gagagf')],
        16: [(11, 'aaaaaaaf')],
        17: [(11, 'aaaaaaaaf')],
        18: [(11, 'aaaaaaaaf')],
        19: [(12, 'gaaafaaf')],
        20: [(13, 'bdddbd')],
        21: [(13, 'bd'), (17, 'bd')],
        22: [(13, 'bd'), (17, 'bd')],
        23: [(14, 'bd'), (17, 'bd')],
        24: [(14, 'bd'), (17, 'bd')],
        25: [(14, 'cc'), (17, 'cc')],
        26: [(15, 'c'), (17, 'c')],
    })

# ---------------------------------------------------------------- FALL (unwinding, dropping back)
FALL = merge(
    {2: [(16, 'gg')], 3: [(15, 'gaaa')], 4: [(15, 'aaaf')], 5: [(16, 'bd')], 6: [(16, 'bd')],
     7: [(16, 'bd')], 8: [(16, 'bd')], 9: [(16, 'bd')]},
    head(11, 4),
    px([(10, 5), (9, 4), (9, 3), (8, 2), (8, 1), (10, 4), (10, 3), (11, 2), (11, 1)], 'e'),   # tails stream up
    {
        10: [(10, 'dbbbbbbd')],
        11: [(9, 'dbbbbbbdd')],
        12: [(9, 'dbdbdbddd')],
        13: [(9, 'dbbdbbdd')],
        14: [(6, 'ff'), (9, 'dbbbbbbd')],
        15: [(6, 'ffdd'), (10, 'dbbbbb')],
        16: [(11, 'dbbb')],
        17: [(10, 'fgagag')],
        18: [(9, 'faaaaaaaa')],
        19: [(9, 'faaaaaaaaadb')],
        20: [(9, 'gaaaaaaaaadbb')],
        21: [(10, 'gaaaf'), (16, 'aaadbb')],
        22: [(11, 'aadb'), (18, 'dbb')],
        23: [(12, 'dbb'), (18, 'ccc')],
        24: [(12, 'dbb'), (18, 'cc')],
        25: [(13, 'ccc')],
        26: [(13, 'cc')],
    })

# ---------------------------------------------------------------- LAND (crouch, guard back up)
LAND_BODY = merge(
    head(16, 8, chin='.'),
    {12: [(21, 'aa')], 13: [(21, 'aa')]},
    {
        14: [(14, 'dbfffbdd')],
        15: [(13, 'dbbfffbdd')],
        16: [(13, 'dbdbdbddd')],
        17: [(13, 'dbbdbbdd')],
        18: [(13, 'dbbbbbbd')],
        19: [(14, 'dbbbbb')],
        20: [(14, 'fgagag')],
        21: [(13, 'faaaaaaa')],
        22: [(12, 'faaaaaaaaa')],
        23: [(11, 'gaaaaffaaaaa')],
        24: [(10, 'gaaaf'), (18, 'aaaaa')],
        25: [(10, 'gbd'), (19, 'dbb')],
        26: [(9, 'bd'), (20, 'dbb')],
        27: [(8, 'ccc'), (20, 'cccc')],
        28: [(7, 'cccc'), (20, 'ccccc')],
    })
LAND_TAILS = px([(15, 9), (14, 10), (13, 11), (12, 12), (14, 9), (13, 9)], 'e')

POSES = {
    'CROUCH': merge(CROUCH_BODY, CROUCH_TAILS[0]),
    'CROUCH_B': merge(CROUCH_BODY, CROUCH_TAILS[1]),
    'CROUCH_C': merge(CROUCH_BODY, CROUCH_TAILS[2]),
    'LAUNCH': LAUNCH, 'RISE1': RISE1, 'RISE2': RISE2, 'RISE3': RISE3, 'APEX': APEX,
    'FALL': FALL, 'LAND': merge(LAND_BODY, LAND_TAILS),
}


def body_canvas(name, R=0, dx=0):
    c = Canvas(48, 64)
    for y, segs in POSES[name].items():
        for x, run in segs:
            for i, ch in enumerate(run):
                if ch == '.':
                    continue
                c.set(8 + x + i + dx, 32 + y - R, PAL[ch])
    return c


def render(name, R=0):
    return body_canvas(name, R)
