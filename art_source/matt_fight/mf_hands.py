"""Hands for the fight body set, drawn like the intro's (mi_hands): the rig's skin ramp, lit from the
upper left, every finger split by a keyline. (rows, anchor): the anchor is the map pixel that sits on
the arm's attach point, 3 px past the wrist along the forearm.
"""
import mf_base  # noqa: F401
from mf_base import B

# Cupped round his mouth like a megaphone: each hand a chunky curled mitten standing either side of
# the mouth, palm turned in, the fingertips curling over toward the mouth at the top, the heel of the
# hand bulging in at the bottom, finger creases ticked on the outside. Lit upper left; the forearm
# arrives from below and outside. Big enough to break the jaw's silhouette at game scale.
MEGA_L = ([
    # 012345678
    "..kkkkk..",   # 0
    ".k11122k.",   # 1  index finger on top, its tip curling in toward the mouth
    "k1112222k",   # 2
    "kkkkkkkk.",   # 3  crease
    "k1122223k",   # 4  middle finger
    "k112223k.",   # 5
    "kkkkkkk..",   # 6  crease
    "k122333k.",   # 7  ring finger
    "kkkkkkk..",   # 8  crease
    "k122334k.",   # 9  little finger
    ".kk2334k.",   # 10 heel of the hand
    "...kkkk..",   # 11
], (4, 11))
MEGA_R = ([
    # 012345678
    "..kkkkk..",   # 0
    ".k12233k.",   # 1
    "k1222334k",   # 2
    ".kkkkkkkk",   # 3
    "k1223334k",   # 4
    ".k223334k",   # 5
    "..kkkkkkk",   # 6
    ".k223344k",   # 7
    "..kkkkkkk",   # 8
    ".k233444k",   # 9
    ".k2344kk.",   # 10
    "..kkkk...",   # 11
], (4, 11))

def _cone(length=14, mouth_h=6, open_h=12):
    """The cupped hands in profile: a cone lying on its side, narrow at his lips (left end) and
    flaring to the opening (right end), keylined all round. The back of the near hand shows, lit
    along the top; two finger separations run along its length; the opening's rim shows the
    shaded palms inside. Built from its geometry so the edges stay straight."""
    rows = []
    mid = open_h / 2.0
    grid = {}
    for x in range(length):
        t = x / float(length - 1)
        half = (mouth_h + (open_h - mouth_h) * t) / 2.0
        top = int(round(mid - half))
        bot = int(round(mid + half))
        for y in range(top, bot + 1):
            v = (y - top) / float(max(1, bot - top))
            if y in (top, bot) or x in (0, length - 1):
                k = 'k'
            elif 2 <= x <= length - 4 and (abs(v - 0.36) < 0.08 or abs(v - 0.68) < 0.08):
                k = 'k'
            elif x >= length - 3:
                k = '4' if v < 0.5 else '5'
            else:
                k = '1' if v < 0.25 else ('2' if v < 0.55 else ('3' if v < 0.8 else '4'))
            grid[(x, y)] = k
    h = int(round(open_h)) + 1
    for y in range(h):
        rows.append(''.join(grid.get((x, y), '.') for x in range(length)))
    return rows


# drawn by hand from that geometry: single-pixel finger separations, lit top, palms in the opening
MEGA_CONE = ([
    # 0123456789012345
    "............kkkk",   # 0  the opening's top rim
    "........kkkk114k",   # 1
    "...kkkkk1111114k",   # 2  top edge, rising to the opening
    "kkk111111122224k",   # 3  the back of the near hand
    "k12kkkkkkkkkk24k",   # 4  finger separation
    "k22222222222224k",   # 5
    "k23kkkkkkkkkk35k",   # 6  finger separation
    "kkk333333333335k",   # 7
    "...kkkkk4444445k",   # 8  bottom edge, falling to the opening
    "........kkkk445k",   # 9
    "............kkkk",   # 10
], (2, 8))

HANDS = {'MEGA_L': MEGA_L, 'MEGA_R': MEGA_R, 'MEGA_CONE': MEGA_CONE}


def check():
    bad = []
    for n, (rows, a) in HANDS.items():
        bad += B.check_map(rows, len(B.rows_of(rows)[0]), n)
    return bad


if __name__ == '__main__':
    print(check())
