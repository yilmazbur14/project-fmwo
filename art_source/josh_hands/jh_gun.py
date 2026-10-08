"""The card hands as FINGER GUNS for Josh's Wild Cards, cut to the addendum's art contract (scratchpad
josh_hands/PLAN_addendum_gun.md, "Art contract for the Gun Hands"). Built from the approved take-A rig:
the same cards, keyline, light, palette and scale, in the same 128x128 frame with the same pivot
(64, 70) as every hand clip, so the one hand sprite only switches clip.

The gun is seen from the side like the user's photo: palm to the camera, index and middle fingers out
together as the barrel, thumb up as the hammer, ring and pinky curled into the palm, the wrist and its
wine cuff (the spade badge) at the back. DRAWN AS THE RIGHT SIDE'S HAND, pointing LEFT into the ring;
the left side's is the code's mirror. Every card keeps its approved name (fan0-3, p/r/m/i 0-2, thumb0-2,
cuff, pin), so the fold from the hover hand into the gun moves each card to its new place.

THE MUZZLE (GUN_MUZZLE) is the corner point (30, 70): the beam's centre line is row 70, the pivot row,
so the beam row is the hand node's own y; the fingertips end at column 30. It is the same on idle,
charge and fire frame 0 (fire frame 0 turns the hand about the muzzle, so the tips stay on it).

Clips (GUN_CLIPS: frame times; totals are the contract's):
  gun_form    6  0.40  0 = hover frame 0 exactly; 1-4 each card travels, turns and resizes to its gun
                       place; 5 = gun_idle frame 0 exactly. Played reversed, it unfolds.
  gun_idle    4  0.10 each, loop: a one-texel bob, the hammer thumb twitching
  gun_charge  4  0.08 each, loop: the hammer cocked, a glow at the fingertips pulsing up
  gun_fire    4  0.35  0 = the shot (the hand kicks up about the muzzle, flashing); 1-2 the recoil
                       back; 3 settled, held while the beam is live
"""
import math

import jh_lib as H
import jh_cards as C
import jh_hand as HD
import jh_anims as A
from jh_hand import Facet, rot, add

FW, FH = A.FW, A.FH
PX, PY = A.PX, A.PY
MUZZLE = (30, 70)                           # corner coordinates in the frame (GUN_MUZZLE)
MX = MUZZLE[0] - PX                         # the muzzle, pivot-relative (texels): (-34, 0)
MY = MUZZLE[1] - PY

GUN_CLIPS = {
    'gun_form': [0.05, 0.06, 0.07, 0.07, 0.07, 0.08],
    'gun_idle': [0.1, 0.1, 0.1, 0.1],
    'gun_charge': [0.08, 0.08, 0.08, 0.08],
    'gun_fire': [0.05, 0.08, 0.1, 0.12],
}
GUN_LOOPS = {'gun_idle', 'gun_charge'}
GUN_ORDER = ['gun_form', 'gun_idle', 'gun_charge', 'gun_fire']
GUN_HOLD = {'gun_fire': 3}

# The gun, pivot-relative texels, built outward from the muzzle (MX, MY): x right, y down.
S = 0.92 * HD.S                             # the fingers: the approved hand's cards, a touch shorter
GX = MX + 4.0                               # the hand is laid out from here so the fingertips end on MX
KNUCKLE = {'i': (GX + 27.5, MY - 4.4), 'm': (GX + 28.5, MY + 4.4),
           'r': (GX + 26.5, MY + 6.0), 'p': (GX + 30.5, MY + 8.5)}
BARREL = {'i': (11.0, 8.5, 7.3), 'm': (11.5, 8.8, 7.9)}     # before S
PALM_C = (GX + 37.0, MY - 4.5)              # the top card of the palm's deck
PALM_WH = (19.0, 25.0)
THUMB_BASE_G = (GX + 39.5, MY - 15.0)
CUFF_C = (GX + 51.0, MY - 1.5)
CUFF_WH = (9.0, 18.0)
WRIST_G = (GX + 49.0, MY - 1.5)             # the recoil turns about here


def _dir(deg):
    a = math.radians(deg)
    return (math.cos(a), math.sin(a))


def _chain(name, part, start, angles, lengths, widths, z0, bias, dots=None, tuck=False):
    """Cards along a bent chain from `start`: card k runs along angles[k] for lengths[k] (texels); the
    card nearer the knuckle is stamped on top (shingled toward the tip)."""
    pts = [start]
    p = start
    for a, ln in zip(angles, lengths):
        p = add(p, _dir(a), ln)
        pts.append(p)
    out = []
    n = len(lengths)
    for k in range(n - 1, -1, -1):
        (w0, w1) = widths[k]
        bk = 2.5 if k == 0 else 2
        fw = 1.5 if k < n - 1 else 0
        cs = C.seg(pts[k], pts[k + 1], w0, w1, bk, fw)
        out.append(Facet(z0 + (n - 1 - k), cs, bias=bias[k], name='%s%d' % (name, k), part=part,
                         dot=(dots[k] if dots else None), tip=(k == n - 1)))
    return out


def gun_pose(thumb=-88.0, cock=0.0, bob=0.0):
    """The gun's cards (pivot-relative, screen space). thumb: the hammer's angle (-90 straight up, more
    leans it back); cock: pulls it further back; bob: the whole hand's rise (texels)."""
    F = []
    fw = [(8.8, 8.4), (8.4, 7.8), (7.8, 7.0)]
    # ring and pinky: out from the knuckle, down, and the tip tucked in behind the palm; only the first
    # two cards of each show, as the grip's knuckles under the barrel
    for key, lens, z0, fi in (('p', (5.0, 3.5, 4.0), 110, 0), ('r', (6.0, 4.5, 4.5), 114, 1)):
        a0 = 162.0
        a1 = a0 - 80.0
        a2 = a1 - 90.0
        chain = _chain(key, 'finger%d' % fi, KNUCKLE[key], [a0, a1, a2], lens,
                       [(7.4, 7.0), (7.0, 6.4), (6.4, 6.0)], z0, [0.4, 0.7, 1.0],
                       dots=[(0.25, 0.7, HD.SUITS[fi]), None, None])
        for f in chain:
            if f.name.endswith('2'):
                f.z = 90 + fi
        F += chain
    # the palm: his deck squared up, edges stepping down and back, the top card face up (big diamond)
    for n in range(4):
        k = 3 - n
        cx, cy = PALM_C[0] + 1.5 * k, PALM_C[1] + 1.2 * k
        cs = C.seg((cx, cy - PALM_WH[1] / 2.0), (cx, cy + PALM_WH[1] / 2.0), PALM_WH[0], PALM_WH[0])
        F.append(Facet(100 + n, cs, pip=HD.SUITS[n] if n == 3 else None, pip_uv=(0.5, 0.5) if n == 3 else None,
                       bias=-0.2 + 0.25 * k, name='fan%d' % n, part='fan'))
    # the barrel: the middle finger under, the index over it, both straight out to the muzzle
    for key, z0, fi, bias in (('m', 120, 2, 0.35), ('i', 130, 3, 0.0)):
        lens = [v * S for v in BARREL[key]]
        F += _chain(key, 'finger%d' % fi, KNUCKLE[key], [180.0, 180.0, 180.0], lens, fw, z0,
                    [0.1 + bias, 0.3 + bias, 0.5 + bias],
                    dots=[(0.25, 0.7, HD.SUITS[fi % 4]), (0.25, 0.7, HD.SUITS[(fi + 1) % 4]), None])
    # the thumb: the hammer, up from the top of the palm
    ta = thumb + cock * 16.0
    F += _chain('thumb', 'thumb', THUMB_BASE_G, [ta, ta - 6.0 + cock * 4.0, ta - 12.0 + cock * 6.0],
                (10.0, 8.5, 7.0), [(9.6, 9.2), (9.2, 8.2), (8.2, 7.2)], 150, [0.15, 0.3, 0.45],
                dots=[(0.25, 0.7, 'heart'), None, None])
    # the cuff across the wrist, standing up (the forearm runs off to the right), and his badge on it
    cx, cy = CUFF_C
    cw, ch = CUFF_WH
    F.append(Facet(160, [(cx - cw / 2, cy - ch / 2 + 1), (cx + cw / 2, cy - ch / 2), (cx + cw / 2, cy + ch / 2),
                         (cx - cw / 2, cy + ch / 2 - 1)], side='back', bias=0.2, name='cuff', part='cuff'))
    F.append(Facet(200, [(cx - 1, cy - 1), (cx + 1, cy - 1), (cx + 1, cy + 1), (cx - 1, cy + 1)], name='pin',
                   part='pin'))
    if bob:
        F = HD.shift(F, 0.0, bob)
    return F


def turned(F, deg, about, dx=0.0):
    """The whole gun turned by deg (positive = clockwise on screen, the barrel kicking up when turned
    about the muzzle) about a point, then moved dx texels (the recoil back)."""
    out = []
    for f in F:
        cs = []
        for (x, y) in f.cs:
            xr, yr = rot((x - about[0], y - about[1]), deg)
            cs.append((xr + about[0] + dx, yr + about[1]))
        out.append(f.copy(cs=cs))
    return out


# ------------------------------------------------------------------ the fold (hover <-> gun)

def screen_hover(i=0):
    """The delivered hover frame's cards in screen space (the right side's hand: mirrored and relit),
    pivot-relative, so they can be mixed with the gun's."""
    out = []
    for f in A.hand_at(A.hover_pose(i)):
        cs = [(-x, y) for (x, y) in f.cs]
        cs = [cs[3], cs[2], cs[1], cs[0]]
        uv = (1.0 - f.pip_uv[0], f.pip_uv[1]) if f.pip_uv else None
        dot = (1.0 - f.dot[0], f.dot[1], f.dot[2]) if f.dot else None
        out.append(f.copy(cs=cs, pip_uv=uv, dot=dot))
    return out


def _params(f):
    a, b, c, d = f.cs
    s0 = ((a[0] + d[0]) / 2.0, (a[1] + d[1]) / 2.0)
    s1 = ((b[0] + c[0]) / 2.0, (b[1] + c[1]) / 2.0)
    return s0, s1, math.hypot(a[0] - d[0], a[1] - d[1]), math.hypot(b[0] - c[0], b[1] - c[1])


def _lerp_angle(a0, a1, t):
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    return a0 + d * t


def morph(F0, F1, t):
    """Each card from its place in F0 to its place in F1 (matched by name): its middle travels, its long
    axis turns the short way round, its two ends change width; its stacking follows F1 past half-way."""
    by = {f.name: f for f in F1}
    out = []
    e = t * t * (3 - 2 * t)
    for f in F0:
        g = by.get(f.name)
        if g is None:
            continue
        s0a, s1a, w0a, w1a = _params(f)
        s0b, s1b, w0b, w1b = _params(g)
        ca = ((s0a[0] + s1a[0]) / 2.0, (s0a[1] + s1a[1]) / 2.0)
        cb = ((s0b[0] + s1b[0]) / 2.0, (s0b[1] + s1b[1]) / 2.0)
        la = math.hypot(s1a[0] - s0a[0], s1a[1] - s0a[1])
        lb = math.hypot(s1b[0] - s0b[0], s1b[1] - s0b[1])
        aa = math.atan2(s1a[1] - s0a[1], s1a[0] - s0a[0])
        ab = math.atan2(s1b[1] - s0b[1], s1b[0] - s0b[0])
        c = (ca[0] + (cb[0] - ca[0]) * e, ca[1] + (cb[1] - ca[1]) * e)
        ang = _lerp_angle(aa, ab, e)
        L = la + (lb - la) * e
        u = (math.cos(ang), math.sin(ang))
        s0 = (c[0] - u[0] * L / 2.0, c[1] - u[1] * L / 2.0)
        s1 = (c[0] + u[0] * L / 2.0, c[1] + u[1] * L / 2.0)
        cs = C.seg(s0, s1, w0a + (w0b - w0a) * e, w1a + (w1b - w1a) * e)
        src = g if e >= 0.5 else f
        out.append(src.copy(cs=cs, z=g.z if e >= 0.5 else f.z))
    return out


# ------------------------------------------------------------------ effects drawn with the hand

def tip_glow(fx, r, phase):
    """The fingertip glow of the charge: a hot bead on the muzzle in his wine and cream (never the
    lanes' gold), a ring of crimson round it. Pivot-relative texels, centred just past the tips."""
    cx, cy = MX - 1.5, MY - 0.5
    for y in range(int(cy - r) - 2, int(cy + r) + 3):
        for x in range(int(cx - r) - 2, int(cx + r) + 3):
            d = math.hypot(x - cx, y - cy)
            if d > r + 1.0:
                continue
            a = math.atan2(y - cy, x - cx)
            if d <= r * 0.45:
                k = 'W'
            elif d <= r * 0.75:
                k = '0'
            elif d <= r:
                k = 'T' if math.sin(3 * a - phase * 2 * math.pi) > 0 else 'R'
            else:
                k = 'V'
            fx[(x, y)] = k


def _frame(cards, over=None, glow='faint', tone=0.0, rings=0, dy=0):
    return A.Frame(cards, over=over, glow=glow, dy=dy, tone=tone, rings=rings)


def clip_frames(name):
    if name == 'gun_form':
        H0 = screen_hover(0)
        G = gun_pose()
        out = [_frame(H0, glow='faint', dy=A.HOVER_BOB[0])]
        for t in (0.2, 0.4, 0.6, 0.8):
            out.append(_frame(morph(H0, G, t), glow='faint'))
        out.append(clip_frames('gun_idle')[0])
        return out
    if name == 'gun_idle':
        out = []
        for i, (bob, th) in enumerate(((0.0, -88.0), (-1.0, -85.0), (-1.0, -88.0), (0.0, -91.0))):
            out.append(_frame(gun_pose(thumb=th, bob=bob), glow='faint'))
        return out
    if name == 'gun_charge':
        out = []
        G = gun_pose(thumb=-88.0, cock=1.0)
        for i, r in enumerate((2.0, 2.8, 3.6, 4.2)):
            over = {}
            tip_glow(over, r, i / 4.0)
            out.append(_frame(G, over=over, glow='mid', tone=-0.4 if i % 2 else 0.0))
        return out
    if name == 'gun_fire':
        out = []
        # 0: the shot - the barrel stays on the muzzle, the hammer thumb falls forward, the palm and cuff
        #    jolt back a texel and the whole hand flashes
        F0 = gun_pose(thumb=-102.0)
        F0 = [f if f.part.startswith('finger') and f.name[0] in 'im' else
              f.copy(cs=[(x + 1.5, y - 1.0) for (x, y) in f.cs]) for f in F0]
        out.append(_frame(F0, glow='mid', tone=-1.0))
        # 1-2: the recoil - the barrel kicks up about the wrist and the hand slides back; 3: settled
        for deg, dx, th, tone in ((6.0, 3.0, -96.0, -0.4), (3.0, 1.5, -92.0, 0.0), (0.0, 0.0, -88.0, 0.0)):
            F = turned(gun_pose(thumb=th), deg, WRIST_G, dx)
            out.append(_frame(F, glow='mid' if deg else 'faint', tone=tone))
        return out
    raise KeyError(name)


def render(fr):
    """(px, glow) for a gun frame: the cards are already in screen space, lit from the upper left about
    the gun's palm."""
    keep = list(HD.LIGHT_ORIGIN)
    HD.LIGHT_ORIGIN[0], HD.LIGHT_ORIGIN[1] = PALM_C[0] - 2.0, PALM_C[1] + 6.0
    try:
        return A.render_frame(fr, mirror=False)
    finally:
        HD.LIGHT_ORIGIN[0], HD.LIGHT_ORIGIN[1] = keep


def render_any(clip, fr, i):
    """gun_form's first frame is the approved hover frame 0 drawn exactly as its sheet draws it."""
    if clip == 'gun_form' and i == 0:
        return A.render_frame(A.clip_frames('hover')[0])
    return render(fr)


def tips(px_frame):
    """The fingertips' leftmost column and the barrel's rows in a rendered frame (for the checks)."""
    return min(x for (x, y) in px_frame)
