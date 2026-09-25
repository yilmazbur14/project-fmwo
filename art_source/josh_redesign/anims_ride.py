"""Josh's RIDE sheets in the approved redesign: mount, glide, drop_bomb, dismount.

80x80 frames facing right (the code mirrors glide and drop_bomb while he flies left). Riding frames
stand him with his soles on row 75, so the glider card - a separate sprite drawn behind him, top
surface at y=76, spanning x 14..63 - sits under his boots. Ground frames put his soles on row 79 like
every other sheet.

Everything is built from the approved parts in josh3.py (head, hat, collar, chest, waistcoat, lapels,
fan, near hand) - moved, sheared or re-aimed with capsule() - plus the pieces only a rider needs (bent
legs, side-on boots, a skirt streaming like a flag, open hands, the bomb card and its glow). The
standing frames (mount 0, dismount 2) are the approved frame 0 with one layer swapped or an effect
added. Nothing in josh3.py or lib.py is edited; pose() and approved() take lib.patch spans for any
later hand touch-up.

    python export_ride.py preview OUTDIR   # numbers, contact sheet and GIFs
    python export_ride.py ship OUTDIR      # also writes the PNGs and .aseprite files
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import josh3                                                        # noqa: E402
import lib                                                          # noqa: E402
from josh3 import capsule                                           # noqa: E402
from lib import Canvas, amap, fill, paint, rim                      # noqa: E402

RIDE_SOLE = 75
GROUND_SOLE = 79


#MOVING PARTS

def mv(px, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in px.items()}


def hshear(px, y0, per, sign=1):
    """Lean: rows above y0 shift sideways one pixel for every `per` rows above it (sign +1 leans
    right, -1 left). Rows at or below y0 stay."""
    return {(x + lean_at(y, y0, per, sign), y): k for (x, y), k in px.items()}


def lean_at(y, y0, per, sign=1):
    return sign * ((y0 - y + per - 1) // per) if y < y0 else 0


def iline(pts):
    """A polyline through (rounded) points, as a list of pixels. lib.line needs whole numbers."""
    pts = [(int(round(x)), int(round(y))) for x, y in pts]
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out += lib.line(x0, y0, x1, y1)
    return out


def under(cv, part):
    """Put a part's pixels only where nothing is drawn yet (effects behind the figure)."""
    for q, k in part.items():
        if 0 <= q[0] < cv.w and 0 <= q[1] < cv.h and q not in cv.px:
            cv.px[q] = k


#APPROVED LAYERS

def torso_top():
    """The approved coat shoulders, lapels, waistcoat and ascot, cut at the waist (row 59). The collar
    goes with the head, and the skirt below the waist is re-drawn per pose."""
    cv = Canvas()
    for c in josh3.coat_panels():
        cv.stamp(c)
    cv.stamp(josh3.vest())
    lib.patch(cv.px, josh3.CHEST)
    lib.patch(cv.px, josh3.VEST_HEM)
    px = {p: k for p, k in cv.px.items() if p[1] <= 59}
    # close the cut under both coat panels: every shape keeps its keyline
    for x in list(range(28, 38)) + list(range(47, 56)):
        if (x, 59) in px or (x - 1, 59) in px or (x + 1, 59) in px:
            px[(x, 60)] = 'k'
    return px


def approved_layers():
    """josh3.build_frame(False)'s stamps as named layers - the body up to the waistcoat hem, then the
    far arm, head, hat, near arm, fan and near hand as (part, outline) stamps - so a standing pose
    can swap one layer (the far arm) and keep the rest pixel-identical."""
    cv = Canvas()
    for c in josh3.collar():
        cv.stamp(c)
    cv.stamp(josh3.coat_back())
    for leg in josh3.legs():
        cv.stamp(leg)
    for b in josh3.boots():
        cv.stamp(b, outline=False)
    for c in josh3.coat_panels():
        cv.stamp(c)
    cv.stamp(josh3.vest())
    lib.patch(cv.px, josh3.CHEST)
    sk = josh3.skirt()
    for q in [q for q in cv.px if 56 <= q[1] <= 71 and 24 <= q[0] <= 58]:
        del cv.px[q]
    cv.px.update(sk)
    lib.patch(cv.px, josh3.VEST_HEM)
    body = dict(cv.px)
    return {
        'body': body,
        'far_arm': josh3.far_arm(),
        'head': josh3.head(),
        'hat': josh3.hat(),
        'near_arm': [(p, True) for p in josh3.near_arm()],
        'fan': amap(josh3.FAN, 6, 34),
        'near_hand': amap(josh3.NEAR_HAND, 14, 40),
    }


#RIDER PARTS

def leg_shape(hip, knee, ankle, r=(2.7, 2.4, 2.0), cap=True):
    """A trouser leg bent at the knee as ONE shape (so no keyline cuts across the knee), lit from the
    upper left, with the kneecap catching the light."""
    p = fill(capsule(hip, knee, r[0], r[1]) | capsule(knee, ankle, r[1], r[2]), 'N')
    rim(p, 's', -1, 0)
    rim(p, 's', 0, -1)
    rim(p, 'n', 1, 0)
    rim(p, 'n', 0, 1)
    if cap:
        kx, ky = int(round(knee[0])), int(round(knee[1]))
        for q in ((kx, ky - 1), (kx - 1, ky - 1), (kx, ky)):
            if q in p and p[q] in 'Ns':
                p[q] = 'S'
    return p


# A boot seen from the side, toe to the right: shaft, instep, toe cap, sole. Soles on its last-but-one
# row, the keyline under them on the last.
BOOT_SIDE = [
    ".kkkkk.....",
    "kmlljk.....",
    "klljjik....",
    "kljjjjikkk.",
    "kljjjjjjjik",
    "khhhhhhhhhk",
    ".kkkkkkkkk.",
]


def boot(x, sole_y):
    """BOOT_SIDE with its sole keyline on row sole_y."""
    return amap(BOOT_SIDE, x, sole_y - len(BOOT_SIDE) + 1)


# Hands: fingerless crimson gloves, bare fingertips, keylined inside the map.
HAND_FWD = [          # knife hand pointing ahead, fingertips bare
    ".kkkk...",
    "kTRRRkkk",
    "kRRRRdddk",
    "kVRRRkkk.",
    ".kVVk....",
    "..kk.....",
]
HAND_CARD = [        # a card pinched up between two fingers, reaching ahead (the card goes on top)
    "..k.k..",
    ".kdkdk.",
    "kTRkRRk",
    "kRRRRVk",
    "kVRRRVk",
    ".kVVVk.",
    "..kkk..",
]
FIST = [             # the approved fist (josh3.far_arm's hand)
    ".kkk..",
    "kRTRk.",
    "kRRRVk",
    "kVRRVk",
    ".kVVk.",
]
HAND_BACK = [         # open hand trailing back, palm down
    "..kkkk.",
    ".kTRRRk",
    "kdkRRRk",
    "kddRRVk",
    ".kdkVVk",
    "..k.kk.",
]


def sleeve(p0, p1, p2, lit=True, cuff=True):
    """A duster sleeve from shoulder p0 through elbow p1 to wrist p2: the near arm lit, the far arm
    in its shadow tones, a gold cuff at the wrist. Returns the stamps back to front."""
    base, top, low = ('9', '0', '8') if lit else ('8', '9', '7')
    up = fill(capsule(p0, p1, 2.4, 2.1), base)
    rim(up, top, 0, -1)
    rim(up, low, 0, 1)
    fo = fill(capsule(p1, p2, 2.1, 1.9), base)
    rim(fo, top, 0, -1)
    rim(fo, low, 0, 1)
    if cuff:
        paint(fo, capsule(p2, p2, 1.9, 1.9), 'o')
    return [up, fo]


def flag_tail(x_root=38, x_tip=5, top_root=51, bot_root=63, top_tip=47, bot_tip=55,
              amp=1.8, lam=14.0, phase=0.0, sweep=7, slant=0.35, lining=True):
    """The duster's skirt streaming back like a flag. Its edges undulate with one travelling wave
    (advance `phase` to make it flap) and the light runs in bands across the flow, slanted along the
    wave crests: cream highlight, base, shadow and fold. The crimson lining shows under the gold hem,
    a pixel on the crests and three where the cloth curls under. The trailing edge is cut on a
    diagonal, the top point furthest back, like a pennant."""
    part = {}
    span = float(x_root - x_tip)
    cols = {}
    for x in range(x_tip, x_root + 1):
        t = (x_root - x) / span
        w = amp * (0.3 + 0.7 * t)
        base_ang = 2 * math.pi * (x_root - x) / lam - phase
        off = w * math.sin(base_ang)
        cols[x] = (top_root + (top_tip - top_root) * t + off,
                   bot_root + (bot_tip - bot_root) * t + off, base_ang)
    for x, (top, bot, base_ang) in cols.items():
        y0, y1 = int(round(top)), int(round(bot))
        mid = (y0 + y1) / 2.0
        h = max(1, y1 - y0)
        kept = 0
        for y in range(y0, y1 + 1):
            f = (y - y0) / h
            if x < x_tip + sweep * f and not (kept < 2 and x - x_tip < 3):
                continue
            kept += 1
            ang = base_ang + slant * (y - mid) * 2 * math.pi / lam
            c = math.cos(ang)
            key = '0' if c > 0.62 else ('9' if c > -0.05 else ('8' if c > -0.6 else '7'))
            if c < -0.88 and y > mid:
                key = '6'                              # the deepest fold, down by the hem
            part[(x, y)] = key
    if lining:
        for x, (top, bot, base_ang) in cols.items():
            y1 = int(round(bot))
            c = math.cos(base_ang)
            lw = 1 if c > 0.3 else (2 if c > -0.4 else 3)
            ys = [y for y in range(y1 - lw + 1, y1 + 1) if (x, y) in part]
            for y in ys:
                part[(x, y)] = 'R'
            if ys:
                if lw == 3 and len(ys) == 3:
                    part[(x, ys[-1])] = 'v'
                    part[(x, ys[-2])] = 'V'
                elif lw >= 2:
                    part[(x, ys[-1])] = 'V'
                yo = ys[0] - 1
                if (x, yo) in part and part[(x, yo)] not in 'RVv':
                    part[(x, yo)] = 'o' if c > -0.4 else 'G'
    rim(part, '0', 0, -1, only='9')
    return part


#EFFECTS

def sparkle(x, y, big=False):
    """A four-point glint: white core, gold arms (longer when big)."""
    out = {(x, y): 'W'}
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out[(x + dx, y + dy)] = 'Y'
        if big:
            out[(x + 2 * dx, y + 2 * dy)] = 'O'
    return out


def speed_lines(lines):
    """Wind streaks behind him: (x, y, length) runs, faint at their trailing (left) end and bright
    at the leading one, so they read as air going past rather than as a ruled line."""
    out = {}
    for (x, y, ln) in lines:
        for i in range(ln):
            u = i / max(1, ln - 1)
            out[(x + i, y)] = '0' if u > 0.85 else ('9' if u > 0.45 else '8')
    return out


def impact_dashes(segs):
    """Short dust streaks flung out from an impact: pale where they start, fading outward."""
    out = {}
    for a, b in segs:
        path = iline([a, b])
        for i, q in enumerate(path):
            out[q] = '0' if i == 0 else ('9' if i < len(path) - 1 else '8')
    return out


#THE RIDING POSE

# Where the approved torso lands on a rider: sheared one pixel every two rows above the waist, then
# moved so the waist sits over the back of the card and the neck leans out over the front knee.
LEAN_PER = 2
TORSO_AT = (-3, 3)
NECK_ROW = 39

# Arm specs: (shoulder, elbow, wrist, hand map, hand map origin), given for bob 0.
ARM_FWD = ((56, 47), (61, 53), (66, 54), HAND_CARD, (66, 50))
ARM_TRAIL = ((39, 47), (31, 43), (24, 38), HAND_BACK, (17, 34))


def front_card(bob=0, glint=False, at=(70.5, 51)):
    """The card pinched in his leading hand: a plain one, cream with a red pip, keylined, tipped
    forward (its bottom centre at `at` for bob 0). glint puts a white catch-light on its top
    corner."""
    c = josh3.card(at[0], at[1] + bob, 28, w=6, h=8, pip=['R'], face='0', border='8')
    rim(c, '9', 1, 0, only='0')
    out = [(c, True)]
    if glint:
        top = min(c, key=lambda q: (q[1], -q[0]))
        out.append((sparkle(top[0] + 1, top[1] - 1), False))
    return out


def clear_of(cv, part, gap=1):
    """Lay a free-floating effect (wind streaks) only where it keeps `gap` px of air round
    everything already drawn, so it never reads as attached to him."""
    drawn = set(cv.px)
    for (x, y), k in part.items():
        if not (0 <= x < cv.w and 0 <= y < cv.h):
            continue
        if all((x + dx, y + dy) not in drawn
               for dx in range(-gap, gap + 1) for dy in range(-gap, gap + 1)):
            cv.px[(x, y)] = k


def pose(bob=0, torso=TORSO_AT, per=LEAN_PER, phase=0.0, front=ARM_FWD, back=ARM_TRAIL,
         tail=None, legs=None, boots=((51, RIDE_SOLE), (19, RIDE_SOLE)), face=None,
         extras_back=(), extras_front=(), patches=(), wind=None):
    """A rider (or any pose built the same way): skirt, legs, boots, collar, the sheared approved
    torso, far arm, head and hat, near arm, effects, wind. bob lowers everything above the knees; arm
    specs are given for bob 0; tail overrides flag_tail's arguments (False for none); extras are
    stamps behind (drawn only where empty) / in front of him; face swaps the head map (e.g. a wink);
    patches are lib.patch spans applied last; wind streaks go in last, clear of everything."""
    tdx, tdy = torso[0], torso[1] + bob
    hdx = tdx + lean_at(NECK_ROW, 59, per)
    hdy = tdy
    cv = Canvas()
    for part in extras_back:
        under(cv, part)
    if tail is not False:
        spec = dict(tail or {})
        spec.setdefault('phase', phase)
        for key, dflt in (('top_root', 51), ('bot_root', 63), ('top_tip', 47), ('bot_tip', 55)):
            spec[key] = spec.get(key, dflt) + bob
        cv.stamp(flag_tail(**spec))
    L = legs or {}
    cv.stamp(leg_shape(*L.get('front', ((45, 61 + bob), (55, 63 + bob), (55, 69)))))
    cv.stamp(leg_shape(*L.get('back', ((38, 62 + bob), (30, 66 + bob), (24, 69)))))
    for (bx, sole) in boots:
        cv.stamp(boot(bx, sole), outline=False)
    for c in josh3.collar():
        cv.stamp(mv(c, hdx, hdy))
    cv.stamp(mv(hshear(torso_top(), 59, per), tdx, tdy), outline=False)
    if front:
        s, e, w, hand, at = front
        for p in sleeve(_b(s, bob), _b(e, bob), _b(w, bob), lit=False):
            cv.stamp(p)
        if hand:
            cv.stamp(amap(hand, at[0], at[1] + bob), outline=False)
    cv.stamp(mv(face or josh3.head(), hdx, hdy))
    for part, o in josh3.hat():
        cv.stamp(mv(part, hdx, hdy), outline=o)
    if back:
        s, e, w, hand, at = back
        for p in sleeve(_b(s, bob), _b(e, bob), _b(w, bob), lit=True):
            cv.stamp(p)
        if hand:
            cv.stamp(amap(hand, at[0], at[1] + bob), outline=False)
    for part, outline in extras_front:
        cv.stamp(part, outline=outline)
    for p in patches:
        lib.patch(cv.px, p)
    if wind:
        clear_of(cv, speed_lines(wind))
    return cv


def _b(p, bob):
    return (p[0], p[1] + bob)


#EFFECTS THAT NEED THE CARD

def hot_card(bx, by, angle, w=7, h=10):
    """The bomb card in his fingers: cream face, gold border, a red pip, keylined, with the fuse's
    glow hugging the keyline (gold) and a few orange sparks off its corners. Returns (card, glow),
    the glow to be laid only where nothing else is."""
    c = josh3.card(bx, by, angle, w=w, h=h, pip=['.R.', 'RRR', '.R.'], face='0', border='o')
    body = set(c)
    ring = set()
    for (x, y) in body:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body:
                ring.add(q)
    glow = {}
    for (x, y) in ring:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body and q not in ring:
                glow[q] = 'O'
    # orange sparks off the four corners
    xs = sorted(glow, key=lambda q: q[0] + q[1])
    for q in (xs[0], xs[-1]):
        glow[q] = 'r'
    ys = sorted(glow, key=lambda q: q[0] - q[1])
    for q in (ys[0], ys[-1]):
        glow[q] = 'r'
    return c, glow


def smear(pts, width=2, keys='Y09'):
    """A motion smear along a polyline: brightest at its end (where the hand is now), thinning and
    cooling toward its start."""
    path = iline(pts)
    out = {}
    n = len(path)
    for i, (x, y) in enumerate(path):
        t = i / max(1, n - 1)
        k = keys[0] if t > 0.75 else (keys[1] if t > 0.4 else keys[2])
        wv = max(0, int(round(width * t)))
        for d in range(-wv, wv + 1):
            out[(x + d, y)] = k if abs(d) < wv or wv == 0 else keys[min(2, keys.index(k) + 1)]
    return out


#FRAMES

# Streaks per glide frame, moving back past him frame to frame.
GLIDE_WIND = [
    [(0, 28, 9), (3, 63, 11), (0, 69, 7)],
    [(0, 31, 7), (0, 61, 12), (5, 67, 6)],
    [(1, 26, 8), (0, 64, 10), (2, 70, 8)],
    [(0, 30, 10), (2, 60, 9), (0, 67, 8)],
]


def glide(i):
    bob = [0, 1, 1, 0][i]
    return pose(bob=bob, phase=i * math.pi / 2, wind=GLIDE_WIND[i],
                extras_front=front_card(bob, glint=(i == 0)))


HAND_PINCH = [        # two fingertips pinching a card above the glove
    ".k.k.",
    "kdkdk",
    "kRkRk",
    "kTRRR",
    "kRRRV",
    ".kVVk",
    "..kk.",
]
HAND_SPREAD = [       # fingers flung open after a release
    "k.k.k..",
    "dkdkdk.",
    "kdRdRk.",
    ".kTRRRk",
    ".kRRRVk",
    "..kVVk.",
    "...kk..",
]


def bomb_card_f1():
    """The bomb card just off his fingertips on drop_bomb frame 1: its centre is HAND_BOMB, where the
    fight spawns the falling bomb."""
    return hot_card(13, 69, 30)


def drop_bomb(i):
    bob = [0, 1, 1][i]
    extras_back, extras_front = [], []
    if i == 0:
        # wound up: the trailing arm high behind him, the card burning between two fingers
        back = ((39, 47), (33, 41), (27, 35), HAND_PINCH, (24, 30))
        c, glow = hot_card(26, 30, -18)
        extras_front.append((c, True))
        extras_back.append(glow)
    elif i == 1:
        # the whip: arm flung down and back, the card just off the fingertips in the clear under the
        # coat (its centre is HAND_BOMB), a smear down the arc the arm swept
        back = ((39, 48), (32, 54), (25, 58), HAND_SPREAD, (18, 55))
        c, glow = bomb_card_f1()
        extras_front.append((c, True))
        extras_back += [glow, smear([(24, 31), (17, 37), (13, 45), (14, 52), (19, 57)], 2)]
    else:
        # recoil: the arm bounces back up toward the riding pose, the card's trail streaking
        # away down-left behind it
        back = ((39, 47), (32, 47), (26, 43), HAND_SPREAD, (19, 39))
        extras_back.append(smear([(15, 62), (11, 68), (7, 74)], 1, keys='OoG'))
        for (sx, sy, big) in ((6, 70, True), (14, 71, False)):
            extras_back.append(sparkle(sx, sy, big))
    # the whip throws the skirt up out of the arm's way
    tail = [None, dict(top_tip=43, bot_tip=50), dict(top_tip=45, bot_tip=53)][i]
    return pose(bob=bob, phase=i * math.pi / 2, back=back, tail=tail, extras_back=extras_back,
                extras_front=front_card(bob) + extras_front, wind=GLIDE_WIND[i])


def approved(far=None, extras_back=(), extras_front=(), fan=True, bob=0, patches=()):
    """The approved standing frame, optionally with the far arm swapped out (far = list of
    (part, outline)) and effects added. bob lowers everything above the boots."""
    L = approved_layers()
    cv = Canvas()
    for part in extras_back:
        under(cv, part)
    body = dict(L['body'])
    if bob:
        body = {(x, y + (bob if y < 72 else 0)): k for (x, y), k in body.items()}
    cv.px.update(body)
    for part, o in (far if far is not None else L['far_arm']):
        cv.stamp(mv(part, 0, bob), outline=o)
    cv.stamp(mv(L['head'], 0, bob))
    for part, o in L['hat']:
        cv.stamp(mv(part, 0, bob), outline=o)
    for part, o in L['near_arm']:
        cv.stamp(mv(part, 0, bob), outline=o)
    if fan:
        cv.stamp(mv(L['fan'], 0, bob), outline=False)
    cv.stamp(mv(L['near_hand'], 0, bob), outline=False)
    for part, outline in extras_front:
        cv.stamp(part, outline=outline)
    for p in patches:
        lib.patch(cv.px, p)
    return cv


def mount(i):
    if i == 0:
        # the glider card just flicked at the floor in front of him: far arm flung down and forward,
        # fingers open, the card's gold trail and the flash where it hit
        far = [(p, True) for p in sleeve((51, 43), (57, 49), (61, 55), lit=False)]
        far.append((amap(HAND_SPREAD, 60, 54), False))
        streak = smear([(64, 62), (61, 69), (58, 75)], 1, keys='OoG')
        return approved(far=far, extras_back=[streak, sparkle(58, 76, big=True), sparkle(65, 72)])
    if i == 1:
        # stepping up: the front boot on the card (sole row 75), the back one still on the floor
        legs = {'front': ((45, 60), (52, 61), (51, 69)), 'back': ((38, 61), (35, 67), (34, 73))}
        tail = dict(x_root=38, x_tip=15, top_root=51, bot_root=65, top_tip=50, bot_tip=59,
                    amp=1.2, lam=18.0, sweep=6, phase=1.0)
        front = ((54, 46), (59, 41), (63, 37), FIST, (61, 32))
        back = ((37, 47), (31, 52), (35, 57), FIST, (34, 55))
        return pose(torso=(-2, 1), per=3, legs=legs, boots=((48, RIDE_SOLE), (30, GROUND_SOLE)),
                    tail=tail, front=front, back=back,
                    extras_back=[sparkle(28, 77), sparkle(61, 72)])
    # aboard: the riding pose, held while the card lifts him straight up, so no speed lines
    return pose(extras_front=front_card(0, glint=True))


def dismount(i):
    if i == 0:
        # the card hits the floor under him: crouched hard on it, coat thrown up by the stop
        legs = {'front': ((45, 64), (55, 66), (55, 70)), 'back': ((38, 65), (30, 68), (24, 70))}
        tail = dict(top_tip=41, bot_tip=49, amp=1.8, phase=0.0, x_tip=7, sweep=6)
        front = ((56, 47), (62, 52), (66, 55), HAND_CARD, (66, 51))
        back = ((39, 47), (32, 55), (26, 61), HAND_BACK, (19, 57))
        # dust kicked off both ends of the card as it slams down
        dust = impact_dashes([((13, 73), (9, 70)), ((12, 69), (9, 66)),
                              ((66, 73), (70, 70)), ((67, 69), (70, 66))])
        return pose(bob=3, legs=legs, tail=tail, front=front, back=back,
                    extras_back=[dust], extras_front=front_card(3, at=(70.5, 52)))
    if i == 1:
        # stepped off onto the floor: a low landing, arms out, the skirt settling behind
        legs = {'front': ((45, 66), (53, 68), (53, 73)), 'back': ((38, 67), (31, 70), (27, 73))}
        tail = dict(x_root=38, x_tip=8, top_root=56, bot_root=69, top_tip=57, bot_tip=64,
                    amp=1.5, lam=15.0, sweep=6, phase=1.5)
        front = ((55, 51), (60, 57), (64, 62), HAND_FWD, (65, 59))
        back = ((38, 51), (31, 47), (25, 42), HAND_BACK, (18, 38))
        return pose(torso=(-2, 7), per=4, legs=legs, boots=((50, GROUND_SOLE), (21, GROUND_SOLE)),
                    tail=tail, front=front, back=back,
                    extras_back=[sparkle(18, 77), sparkle(63, 77)])
    # up again with the fan back in his hand
    return approved(extras_front=[(sparkle(9, 33, big=True), False), (sparkle(24, 31), False)])


SHEETS = {
    'josh_mount': (mount, 3),
    'josh_glide': (glide, 4),
    'josh_drop_bomb': (drop_bomb, 3),
    'josh_dismount': (dismount, 3),
}
# Frames shown while he is up at riding height (the rest of the riding frames play on the floor:
# mount 1 before the rise starts, dismount 0 after the landing). These set RIDE_HEADROOM.
AT_HEIGHT = {
    'josh_mount': [2],
    'josh_glide': [0, 1, 2, 3],
    'josh_drop_bomb': [0, 1, 2],
}
# Frames that stand on the glider (a sole on row 75).
RIDING = {
    'josh_mount': [1, 2],
    'josh_glide': [0, 1, 2, 3],
    'josh_drop_bomb': [0, 1, 2],
    'josh_dismount': [0],
}


def sheet(name):
    from PIL import Image
    fn, n = SHEETS[name]
    out = Image.new('RGBA', (80 * n, 80), (0, 0, 0, 0))
    for i in range(n):
        out.alpha_composite(fn(i).image(), (80 * i, 0))
    return out


#PREVIEW

# Glider texel (gx, gy) sits on Josh texel (gx + 7, gy + 70): FINAL_GLIDER offset (-3, 15) px at 3x
# from his feet anchor (40, 79), pivot (32, 14).
GLIDER_AT = (7, 70)


def glider_frames():
    from PIL import Image
    g = Image.open(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh', 'Cards',
                                'josh_glider.png')).convert('RGBA')
    return [g.crop((i * 64, 0, i * 64 + 64, 28)) for i in range(3)]


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'out_ride')
    os.makedirs(out, exist_ok=True)
    for name in SHEETS:
        im = sheet(name)
        im.save(os.path.join(out, name + '.png'))
        lib.upscale(lib.on_bg(im), 5).save(os.path.join(out, name + '_5x.png'))
        print(name, lib.stats(im))
