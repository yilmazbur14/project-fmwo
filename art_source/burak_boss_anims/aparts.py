"""Posable pieces for the fight set, all from the approved rig's own parts and shading: an arm (coat
sleeve pushed up, gold-edged cuff, bare forearm), fists and hands, the cutlass with its brass hilt,
the flintlock, and the flintlock tucked in his sash. Coordinates are the approved frame's; a drawer
maps them through the Pose (bob, frame offset) when it stamps.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import akit  # noqa: E402,F401
import burak as B  # noqa: E402
from kit import amap, capsule, cylinder, ellipse, fill, line, poly, rim  # noqa: E402,F401

SH_L, SH_R = (31.5, 53.0), (64.5, 53.0)          # the approved sleeves' roots


def unit(dx, dy):
    L = math.hypot(dx, dy) or 1.0
    return dx / L, dy / L


def ang(p, deg, r):
    a = math.radians(deg)
    return (p[0] + math.cos(a) * r, p[1] + math.sin(a) * r)


def arm(F, shoulder, elbow, wrist, lit=True, cuff=True):
    """Sleeve, cuff, forearm, in the approved arms' radii and ramps. `lit`: the sword arm (screen
    left) is lit, the pistol arm (screen right) sits a tone darker, as on the approved frames."""
    F.body(B.sleeve(shoulder, elbow, 4.6, 3.9, lit_side=lit))
    ux, uy = unit(wrist[0] - elbow[0], wrist[1] - elbow[1])
    if cuff:
        F.body(B.cuff_d((elbow[0] + ux * 0.8, elbow[1] + uy * 0.8), (ux, uy), 1.5, 4.0))
    keys = ('3', '2', '4', '5') if lit else ('4', '3', '5', '6')
    F.body(B.limb([((elbow[0] + ux * 2.3, elbow[1] + uy * 2.3), wrist, 2.8, 2.6)], *keys))


def fist(c, d=(1.0, 0.0), lit=True, r=3.4):
    """A fist round a grip: a rounded mass, lit on its upper left, knuckle creases across it."""
    cx, cy = c
    p = fill(ellipse(cx, cy, r, r * 0.92), '3' if lit else '4')
    rim(p, '2' if lit else '3', -1, 0)
    rim(p, '2' if lit else '3', 0, -1, only='3' if lit else '4')
    rim(p, '4' if lit else '5', 1, 0)
    rim(p, '5', 0, 1, only='34')
    ux, uy = d
    nx, ny = -uy, ux
    for t in (-1.2, 0.2, 1.6):                      # finger creases, across the grip
        q = (int(round(cx + nx * t + ux * 1.0)), int(round(cy + ny * t + uy * 1.0)))
        if q in p:
            p[q] = '5'
    return p


def open_hand(c, d, lit=True, r=3.2):
    """A limp or gesturing open hand: palm, thumb off one side, fingers out along d."""
    cx, cy = c
    ux, uy = d
    shape = ellipse(cx, cy, r, r) | ellipse(cx + ux * 2.0 - uy * 2.0, cy + uy * 2.0 + ux * 2.0, 1.6, 1.6)
    shape |= capsule((cx, cy), (cx + ux * 3.6, cy + uy * 3.6), 2.3, 1.7)
    p = fill(shape, '3' if lit else '4')
    rim(p, '2' if lit else '3', -1, 0)
    rim(p, '2' if lit else '3', 0, -1, only='3' if lit else '4')
    rim(p, '4' if lit else '5', 1, 0)
    rim(p, '5', 0, 1, only='34')
    return p


def point_hand(c, d, lit=True, r=3.1, reach=4.2):
    """A fist with the index finger out along d, riding the fist's upper side: pointing."""
    cx, cy = c
    ux, uy = unit(*d)
    nx, ny = -uy, ux
    if ny > 0:
        nx, ny = -nx, -ny                            # n points up: the finger rides the top
    b = (cx + ux * (r - 1.0) + nx * 1.1, cy + uy * (r - 1.0) + ny * 1.1)
    t = (b[0] + ux * reach, b[1] + uy * reach)
    shape = ellipse(cx, cy, r, r * 0.92) | capsule(b, t, 1.25, 1.05)
    p = fill(shape, '3' if lit else '4')
    rim(p, '2' if lit else '3', -1, 0)
    rim(p, '2' if lit else '3', 0, -1, only='3' if lit else '4')
    rim(p, '4' if lit else '5', 1, 0, only='3' if lit else '4')
    rim(p, '5', 0, 1, only='34')
    for s in (0.6, 2.0):                             # the curled fingers' creases under the pointer
        q = (int(round(cx + ux * 1.2 - nx * s)), int(round(cy + uy * 1.2 - ny * s)))
        if q in p:
            p[q] = '5'
    return p


# A hand pointing straight out to screen right, seen from the thumb side: the fist of curled fingers,
# the thumb laid over the index finger's root, the index finger out, a dark crease under its root.
# Shade-side ramp (the screen-right arm). The fist's centre is at (2.5, 3.5).
POINT_R = [
    "..33.......",
    ".3443333333",
    "34444444445",
    "44446k.....",
    "44444k.....",
    "44445......",
    ".4455......",
]


# The same hand turned up, the finger raised (to his temple: "Think!"); the finger on the hand's
# inner side, the curled fingers to its right, a crease between. The fist's centre is at (2.5, 6.5).
POINT_U = [
    ".33...",
    ".34...",
    ".34...",
    ".34...",
    "334k..",
    "34444.",
    "344445",
    "344455",
    ".4455.",
]


def point_hand_u(c):
    x0, y0 = int(round(c[0] - 2.5)), int(round(c[1] - 6.5))
    return amap(POINT_U, x0, y0)


def point_hand_r(c):
    """POINT_R placed with its fist's centre at c. Stamp it with outline='soft' so the crease's own
    black stays one pixel."""
    x0, y0 = int(round(c[0] - 2.5)), int(round(c[1] - 3.5))
    return amap(POINT_R, x0, y0)


def cutlass(F, guard, tip, bow=2.2, hilt=True):
    """The cutlass anywhere, any angle: blade from the guard to the tip, then the brass hilt."""
    F.body(B.cutlass(guard, tip, bow=bow))
    if not hilt:
        return
    gx, gy = guard
    ux, uy = unit(tip[0] - gx, tip[1] - gy)
    nx, ny = -uy, ux
    grip = fill(capsule((gx, gy), (gx - ux * 6.0, gy - uy * 6.0), 1.4, 1.4), '9')
    rim(grip, '0', -1, 0)
    rim(grip, '7', 1, 0)
    F.body(grip)
    shell = fill(capsule((gx - nx * 2.8, gy - ny * 2.8), (gx + nx * 2.8, gy + ny * 2.8), 1.3, 1.3), 'O')
    rim(shell, 'G', 1, 0)
    rim(shell, 'G', 0, 1)
    F.body(shell)
    pom = fill(ellipse(gx - ux * 7.0, gy - uy * 7.0, 1.6, 1.6), 'O')
    rim(pom, 'G', 1, 0)
    F.body(pom)


def knuckle_bow(F, guard, tip, side=1.0):
    """The brass D-guard arcing from the shell round the fist to the pommel, drawn over the fist."""
    gx, gy = guard
    ux, uy = unit(tip[0] - gx, tip[1] - gy)
    nx, ny = -uy * side, ux * side
    pts = [(gx + nx * 2.6, gy + ny * 2.6), (gx - ux * 3.2 + nx * 4.4, gy - uy * 3.2 + ny * 4.4),
           (gx - ux * 6.8 + nx * 1.6, gy - uy * 6.8 + ny * 1.6)]
    bw = {}
    for a, b in zip(pts, pts[1:]):
        for q in capsule(a, b, 0.75, 0.75):
            bw[q] = 'o'
    F.body(bw)


def pistol(F, breech, barrel_dir, grip_dir, **kw):
    for part in B.pistol_parts(breech, barrel_dir, grip_dir, **kw):
        F.body(part)


def pistol_sash(F):
    """The flintlock tucked through his sash on his left hip (screen right), grip up and forward,
    barrel down along his thigh, when that hand is busy."""
    for part in B.pistol_parts((58.5, 67.5), (0.25, 1.0), (-0.35, -1.0), barrel_len=8.5, grip_len=4.5,
                               bell_len=4.5, r_bar=1.9, r_bell=3.9, mouth_tip=0.5):
        F.body(part)


def leg(F, hip, knee, ankle, toe, lit=True, planted=False):
    """A posed leg under the coat: the trouser thigh from hip to knee, then the tall black boot, its
    turned-down cuff at the knee and the foot. Shaded against the fixed light, like the approved legs.
    planted: the leg ignores the body's vertical bob (a foot on the ground stays on the ground);
    planted='abs': it ignores the bob altogether, every point is given in the frame's own terms."""
    if planted:
        frame = F
        keep_x = planted != 'abs'

        class _G:
            def body(self, part, outline=True, owner=None, extra=(0, 0)):
                frame.put(part, (frame.P.bob[0] if keep_x else 0) + extra[0], extra[1], outline, owner)
        F = _G()
    th = fill(capsule(hip, knee, 3.4, 3.1), '9')
    cylinder(th, hip, knee, 3.4, '0987' if lit else '9877', (0.55, 0.15, -0.3))
    F.body(th)
    sh = fill(capsule(knee, ankle, 3.9, 3.5), 'r')
    cylinder(sh, knee, ankle, 3.9, 'utrq', (0.6, 0.25, -0.2))
    ft = fill(capsule(ankle, toe, 3.3, 2.6), 'r')
    cylinder(ft, ankle, toe, 3.3, 'utrq', (0.6, 0.25, -0.2))
    ux, uy = unit(ankle[0] - knee[0], ankle[1] - knee[1])
    cuff = fill(capsule((knee[0] - ux * 0.3, knee[1] - uy * 0.3), (knee[0] + ux * 2.6, knee[1] + uy * 2.6), 4.9, 4.7), 't')
    cylinder(cuff, knee, ankle, 4.9, 'utrq', (0.5, 0.1, -0.3))
    F.body(ft)
    F.body(sh)
    F.body(cuff)
