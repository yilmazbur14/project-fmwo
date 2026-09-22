"""Computah redesign - the "robot Mega Man" pass.  Solo boss 2, beam only.

WHAT CHANGES
The chassis grows a proper armour suit: a wide domed helmet with side ear-pods that
wraps the same dark faceplate, and ONE ARM IS NOW A CANNON.  The other arm stays the
stubby segmented robot arm he already had.  Purple stops being a trim accent and
becomes the ARMOUR colour - helmet, pauldron, cannon shell, boots, chest bezel - over
the cool grey shell, which becomes the inner suit.  That is the same two-value
structure the reference gets out of its two blues, in Computah's own palette.

WHAT IS KEPT
The bent antenna with its glowing ball, the dark faceplate with red LED eyes and the
wide toothy grin, the chest plate with its four cells, the grey shell ramp and the
purple.  Those are what stop him reading as somebody else's blue robot.  The cells no
longer mean "battery charge" - Greyson is gone and there is nothing to recharge him -
they are the beam capacitor now, and they fill as the shot charges.  That turns the
retired mechanic's art into the attack's loudest tell.

FRAME
96x96, feet on row 95 - Greyson's old frame, which is free now.  Two reasons.  The
braced pose is 66 texels wide before any muzzle FX, so rendered at 64 it runs from
column 1 to column 62 with nothing left for recoil, a muzzle flash or an overshoot;
and as the sole boss he is no longer the small half of a pair.  He does get bigger:
crown to feet goes from 44 texels (132 px at SCALE 3) to 73 (219 px), against
Greyson's 86 (258 px).  That is a real character-size change, not just headroom, and
it is the part of this to push back on if it is unwanted - the rig is written in
96-space and scaled by K, so `python computah_mm.py <dir> 64` re-renders the same
drawing small, and holding the body to ~55 texels inside the 96 frame would keep his
old on-screen size while still giving the cannon its reach.

POSES
  idle        standing key frame, cannon hanging forward-down
  charge      the braced charge off the reference: two-handed brace, cannon level,
              deep wide stance leaning back off the recoil, tracking the player
  ready       THE LOCK.  Aim has stopped following - he snaps upright and square, the
              antenna goes rigid, the off hand leaves the barrel for the breech, the
              soft charge collapses to a white-hot spiked point.  This has to read in
              peripheral vision in 0.45 s, so every delta is silhouette, not colour.

  python computah_mm.py <outdir> [frame_size]
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "greyson_computah"))
from pixlib import Canvas, Ellipse, Capsule, Poly, RoundRect, Union, Clip  # noqa: E402

FRAME = 96
K = 1.0                    # set by _set_frame(); 96-space -> frame-space

OUTLINE = "#0C111A"        # the keyline every shipped Computah sheet already uses

PAL = {
    # inner suit / chassis - the shipped ramp, untouched
    "shell":  ["#F2F8FF", "#CEDCEA", "#A6B8CC", "#8091A8", "#5E6C82", "#3F4A5C"],
    # armour plate - the shipped 5-tone purple, untouched, just used over far more
    "armour": ["#C892F2", "#A063DC", "#7C3BB4", "#592687", "#391555"],
    # recesses: joints, the cannon bore, vents
    "dark":   ["#6C7A8E", "#536174", "#3C4757", "#2A3341", "#1A212C"],
    "glass":  ["#2B3444", "#222A38", "#1A202B", "#131821", "#0D1118"],
}

# THE BATTERY, on his chest.  The chase clock IS the battery, so its state has to be
# readable three ways at once - how many of the four cells are lit, what colour they
# are, and how brightly the antenna ball and the eyes glow.  A colour swap alone
# would keep four lit cells and lose the count.
#
# ON THE SHEETS THAT CARRY ROWS, ROW 0 IS FULL: `frame = charge_state * 4 + cycle`.
# The overload attack's own charge sheet runs the OPPOSITE way round (row 0 barely
# charged, row 2 white-hot).  Two sheets on one character with opposite conventions
# is a real trap, so both say which way they go where they are defined.
CHARGE = {
    #        lit cells, bright,      mid,       dark,      glow,      eye
    "full": (4, "#A9FFB4", "#4FE066", "#1F9A38", "#2A7A3C", "#FF4436"),
    "half": (2, "#FFE9A8", "#FFC33E", "#C9820F", "#7A5A18", "#E0392C"),
    "low":  (1, "#FFC0A6", "#FF6A4E", "#C32A1C", "#7A2418", "#C42C22"),
    "dead": (0, "#6E7A8C", "#4A5668", "#333D4C", "#232A36", "#5A2420"),
}
CHARGE_ROWS = ("full", "half", "low")
CHARGE_CYCLE = 4

# The beam's own states.  These are NOT battery states: the beam is charged by the
# attack, the battery is spent by the chase, and they must never be confused on the
# chest.  `lock` is the blown-out capacitor on the frame the aim stops moving.
CORE = {
    "chg":  (3, "#A9FFB4", "#4FE066", "#1F9A38", "#2A7A3C", "#FF4436"),
    "lock": (4, "#E6FFE9", "#A9FFB4", "#4FE066", "#A9FFB4", "#FFF0D2"),
    # The capacitor state the approved idle key frame happens to be drawn in.  Kept
    # only so golden/ has something exact to regress against - the shipped idle
    # sheet's row 0 is FULL, four green cells, per the contract above.
    "key":  (1, "#A9FFB4", "#4FE066", "#1F9A38", "#2A7A3C", "#FF4436"),
}
BEAM_CORE = "#E6FFE9"
BEAM_HI = "#A9FFB4"
BEAM_MID = "#4FE066"
BEAM_DK = "#1F9A38"


def _set_frame(n):
    global FRAME, K
    FRAME = int(n)
    K = FRAME / 96.0


# ---------------------------------------------------------------------------
# 96-space shape constructors
# ---------------------------------------------------------------------------
def E(cx, cy, rx, ry, round_r=None):
    return Ellipse(cx * K, cy * K, rx * K, ry * K,
                   None if round_r is None else round_r * K)


def CAP(p0, p1, r0, r1=None, round_r=None):
    return Capsule((p0[0] * K, p0[1] * K), (p1[0] * K, p1[1] * K), r0 * K,
                   None if r1 is None else r1 * K,
                   None if round_r is None else round_r * K)


def RR(x0, y0, x1, y1, r=4.0, round_r=5.0):
    return RoundRect(x0 * K, y0 * K, x1 * K, y1 * K, r * K, round_r * K)


def PO(pts, round_r=7.0):
    return Poly([(x * K, y * K) for x, y in pts], round_r * K)


def PX(x, y):
    return (int(round(x * K)), int(round(y * K)))


def SPAN(x0, x1, y):
    """The integer pixel run from 96-space x0..x1 on 96-space row y."""
    a, b = int(round(x0 * K)), int(round(x1 * K))
    yy = int(round(y * K))
    return [(x, yy) for x in range(a, b + 1)]


# ---------------------------------------------------------------------------
# the face plate.  Generated, not typed, so it can be checked for symmetry and
# resized with the frame without a second copy drifting out of step.
# ---------------------------------------------------------------------------
def face_grid(w, h, ew, eh, inset, mouth_rows=4, squint=0, turn=0):
    """`turn` > 0 squeezes the far (left) eye and slides the mouth toward the side
    he faces, which is what a three-quarter head looks like at this size."""
    g = [["V"] * w for _ in range(h)]
    g[0] = ["v"] * w
    g[h - 1] = ["v"] * w

    def eye(sx, width, top, height):
        for j in range(height + 2):
            for i in range(width + 2):
                x, y = sx - 1 + i, top - 1 + j
                if not (0 <= x < w and 1 <= y < h - 1):
                    continue
                edge = i in (0, width + 1) or j in (0, height + 1)
                g[y][x] = "G" if edge else "R"

    top = 2 + squint
    lw = max(2, ew - 2 * turn)
    eye(inset + (ew - lw), lw, top, eh - squint)
    eye(w - inset - ew, ew, top, eh - squint)

    mt = h - 1 - mouth_rows - 1
    m0, m1 = 2 + max(0, turn), w - 3 - max(0, -turn)
    for x in range(m0, m1 + 1):
        g[mt][x] = "M" if (x in (m0, m1) or turn) else "V"
    for j in range(1, mouth_rows):
        for x in range(m0 + (1 if j == mouth_rows - 1 else 0),
                       m1 + 1 - (1 if j == mouth_rows - 1 else 0)):
            g[mt + j][x] = "M"
    # single-pixel teeth, stepped out from the centre line in mirrored pairs so the
    # grin stays symmetric whatever width the plate is
    mid = (m0 + m1) / 2.0
    ty = mt + mouth_rows - 2
    n = 0
    while True:
        d = 1.5 + 3.0 * n
        lo, hi = int(round(mid - d)), int(round(mid + d))
        if lo <= m0 or hi >= m1:
            break
        g[ty][lo] = g[ty][hi] = "t"
        n += 1
    return ["".join(r) for r in g]


def _check(grid, symmetric):
    """A front-on plate must mirror exactly; a turned one must not pretend to."""
    cls = {"v": "g", "V": "g", "G": "e", "R": "e", "M": "m", "t": "t"}
    bad = []
    w = len(grid[0])
    for j, row in enumerate(grid):
        if len(row) != w:
            bad.append("row %d is %d wide, not %d" % (j, len(row), w))
    if not symmetric:
        return bad
    for j, row in enumerate(grid):
        for i in range(w // 2):
            if cls.get(row[i]) != cls.get(row[w - 1 - i]):
                bad.append("row %d col %d/%d %r/%r"
                           % (j, i, w - 1 - i, row[i], row[w - 1 - i]))
    return bad


def _face(c, grid, ox, oy, cc, mood="calm"):
    eye = cc[5]
    chars = {
        "v": ("dark", 0), "V": ("glass", 1), "M": ("glass", 4), "t": "#D8E4F2",
        "G": _mix(eye, "#101820", 0.45), "R": eye,
    }
    if mood == "angry":
        chars["G"] = _mix(eye, "#FFD8A0", 0.30)
    if mood == "lock":                      # blown out: the aim has stopped moving
        chars["G"] = "#FFD9A0"
        chars["R"] = "#FFFFFF"
        chars["t"] = "#FFFFFF"
    if mood == "hit":                       # the instant of the punch
        chars["G"] = "#FFD9A0"
        chars["R"] = "#FFFFFF"
    if mood == "dim":                       # venting, low on power
        chars["G"] = _mix(eye, "#101820", 0.72)
        chars["R"] = _mix(eye, "#101820", 0.45)
    if mood == "dead":
        chars["G"] = "#2A2430"
        chars["R"] = "#5E2A26"
        chars["t"] = "#7E8A99"
    if mood == "ember":
        chars["G"] = "#3A2226"
        chars["R"] = "#B8392C"
        chars["t"] = "#7E8A99"
    c.stamp(grid, int(round(ox * K)), int(round(oy * K)), chars)


# ---------------------------------------------------------------------------
# the head
# ---------------------------------------------------------------------------
def _helmet(c, cx, cy, rx, ry, jaw, chin, pods, pod_y, vent=1):
    """A wide domed helmet shell over the boxy face housing he already had.

    The armour is not a band across the crown: it wraps DOWN THE SIDES to `chin`, so
    the faceplate sits in a helmet window.  That plus the ear-pods and the cannon is
    the whole Mega Man read - the face inside the window is unchanged Computah.
    jaw = (half width, top offset, bottom offset) from cy.
    """
    dome = E(cx, cy, rx, ry)
    box = RR(cx - jaw[0], cy + jaw[1], cx + jaw[0], cy + jaw[2], r=6.0, round_r=7.0)
    skull = Union([dome, box], k=1.6 * K, round_r=8.0 * K)
    c.add(skull, "shell", prio=10)

    cap = Clip(skull, PO([(-40, -90), (150, -90), (150, chin), (-40, chin)]))
    c.add(cap, "armour", prio=11, bias=2)
    c.contour(cap, width=1.4, delta=3, mats=("shell",))
    c.shade_px(SPAN(cx - rx - 1, cx + rx + 1, chin - 1), 2, "armour")

    # the crown ridge: a raised band running front-to-back over the top of the shell
    ridge = Clip(E(cx + vent * 2.0, cy - ry * 0.34, rx * 0.66, ry * 0.86),
                 PO([(-40, -90), (150, -90), (150, cy - ry * 0.46),
                     (-40, cy - ry * 0.46)]))
    c.add(ridge, "armour", prio=12, bias=1)
    c.contour(ridge, width=1.0, delta=2, mats=("armour",))

    # the forehead vent slashed into the leading edge of the shell
    if vent:
        s = 1 if vent > 0 else -1
        for n in range(3):
            c.shade_px([PX(cx + s * (rx * 0.30 + n * 2.6 + i * 0.9),
                           cy - ry * 0.58 + i * 1.0) for i in range(5)],
                       2, "armour")

    # ear-pods.  Half of each hangs out past the dome; after the cannon this is the
    # loudest new thing in the silhouette.
    if pods[0]:
        _pod(c, cx - rx + 1.6, cy + pod_y, pods[0], -1)
    if pods[1]:
        _pod(c, cx + rx - 1.6, cy + pod_y, pods[1], 1)
    return skull


def _pod(c, px, py, r, side):
    c.add(E(px, py, r, r * 1.12), "armour", prio=14, bias=2)
    c.add(E(px, py, r * 0.62, r * 0.66), "shell", prio=15, bias=-1)
    c.add(E(px + side * 0.5, py, r * 0.42, max(r * 0.15, 1.0)), "dark",
          prio=16, flat=3)


# ---------------------------------------------------------------------------
# the cannon.  Radius profile read off the reference: pauldron ball, a pinched
# waist, the swelling barrel body, a narrowed neck, then the muzzle flare.
# ---------------------------------------------------------------------------
PROFILE = ((0.00, 1.00), (0.18, 0.66), (0.34, 0.94), (0.56, 1.06),
           (0.72, 0.70), (0.86, 0.80), (1.00, 1.06))


def _cannon(c, sh, muzzle, r, prio=16):
    """Returns the muzzle-face centre in FRAME pixels - this is C_MUZZLE."""
    ax, ay = muzzle[0] - sh[0], muzzle[1] - sh[1]
    L = math.hypot(ax, ay) or 1.0
    ax, ay = ax / L, ay / L
    px, py = -ay, ax

    def at(t):
        return (sh[0] + ax * L * t, sh[1] + ay * L * t)

    gun = Union([CAP(at(t0), at(t1), r * k0, r * k1)
                 for (t0, k0), (t1, k1) in zip(PROFILE, PROFILE[1:])],
                k=1.4 * K, round_r=7.0 * K)
    c.add(gun, "armour", prio=prio, bias=2)
    c.contour(gun, width=1.5, delta=3, mats=("shell", "armour"), below_prio=prio)

    # hard segment rings at the two pinches
    for t, kk in ((0.20, 0.76), (0.76, 0.78)):
        bx, by = at(t)
        rr = r * kk + 1.6
        c.shade_px([PX(bx + px * u, by + py * u)
                    for u in [q * 0.4 - rr for q in range(int(rr * 5) + 1)]],
                   2, "armour")
    # a lit spine along the top of the barrel and a dark belly under it
    for q in range(40):
        t = 0.26 + q * 0.019
        bx, by = at(t)
        rr = r * 0.70
        c.shade_px([PX(bx - px * rr, by - py * rr)], -2, "armour")
        c.shade_px([PX(bx + px * rr, by + py * rr)], 2, "armour")

    face = (muzzle[0] + ax * 0.6, muzzle[1] + ay * 0.6)
    c.add(E(face[0], face[1], r * 0.68, r * 0.68), "dark", prio=prio + 2, flat=4)
    c.add(E(face[0] - ax * 1.2 - 0.7, face[1] - ay * 1.2 - 0.7,
            r * 0.38, r * 0.38), "dark", prio=prio + 3, flat=2)
    c.contour(E(face[0], face[1], r * 0.68, r * 0.68), width=1.3, delta=-2,
              mats=("armour",))
    return face


# ---------------------------------------------------------------------------
# body parts
# ---------------------------------------------------------------------------
def _antenna(c, pts, ball, cc, prio=1):
    for i in range(len(pts) - 1):
        c.add(CAP(pts[i], pts[i + 1], 2.6 - i * 0.22, 2.3 - i * 0.22), "shell",
              prio=prio)
    bx, by, br = ball
    hi, mid = cc[1], cc[2]
    bxp, byp, brp = bx * K, by * K, br * K
    for dy in range(-int(brp) - 1, int(brp) + 2):
        for dx in range(-int(brp) - 1, int(brp) + 2):
            if dx * dx + dy * dy <= brp * brp:
                c.raw_px([(int(round(bxp)) + dx, int(round(byp)) + dy)],
                         hi if (dx <= 0 and dy <= 0) else mid)


def _arm(c, sh, elbow, wrist, hand_r, r0, r1, r2, prio=6, cap=None, gauntlet=False):
    """`gauntlet` armours the FOREARM in purple.  An arm that crosses the body in
    shell grey vanishes into the torso and the leg behind it whatever you do with
    tone; changing the hue is the only thing that reliably keeps it readable, and it
    is what the reference does on the bracing arm too.  The mitt stays grey so it
    still separates from the purple barrel it grips."""
    upper = CAP(sh, elbow, r0, r1)
    lower = CAP(elbow, wrist, r1 + (0.6 if gauntlet else 0.0), r2)
    c.add(Union([upper, lower], k=1.6 * K), "shell", prio=prio)
    if gauntlet:
        c.add(lower, "armour", prio=prio + 1, bias=2)
        c.contour(lower, width=1.5, delta=3, mats=("shell", "armour"),
                  below_prio=prio + 1)
        c.contour(upper, width=1.4, delta=3, mats=("shell", "armour"),
                  below_prio=prio)
    hand = E(wrist[0], wrist[1], hand_r, hand_r * 0.92)
    c.add(hand, "shell", prio=prio + 2, bias=-1 if gauntlet else 0)
    if gauntlet:
        c.contour(hand, width=1.4, delta=3, mats=("shell", "armour"),
                  below_prio=prio + 2)
    if cap:
        c.add(E(cap[0], cap[1], cap[2], cap[3]), "armour", prio=prio + 3, bias=2)
    c.shade_px(SPAN(elbow[0] - 2, elbow[0] + 2, elbow[1]), 2, "shell")
    c.shade_px(SPAN(wrist[0] - 3, wrist[0] + 3, wrist[1] + 2), 2, "shell")
    c.shade_px(SPAN(wrist[0] - 3, wrist[0] + 3, wrist[1] - 4), 3, "shell")
    c.shade_px(SPAN(wrist[0] - 3, wrist[0] + 1, wrist[1] - 2), -2, "shell")


def _leg(c, hip, knee, ankle, foot, prio=4, far=False, r=(7.0, 6.0, 5.2)):
    """`far` puts the limb behind: a step darker all over, so a wide stance does not
    collapse into one white mass the way it does when both legs share a tone."""
    limb = Union([CAP(hip, knee, r[0], r[1]), CAP(knee, ankle, r[1], r[2])],
                 k=1.6 * K)
    c.add(limb, "shell", prio=prio, bias=2 if far else 0)
    c.add(RR(foot[0], foot[1], foot[2], foot[3], r=5.0, round_r=6.0), "armour",
          prio=prio + 1, bias=3 if far else 2)
    if not far:
        c.contour(limb, width=1.4, delta=3, mats=("shell", "armour"),
                  below_prio=prio)
    c.shade_px(SPAN(knee[0] - 3, knee[0] + 3, knee[1] - 1), 2, "shell")
    c.shade_px(SPAN(foot[0] + 1, foot[2] - 1, foot[1] + 2), 2, "armour")
    c.shade_px(SPAN(foot[0], foot[2], foot[3] - 1), 3, "armour")
    c.shade_px(SPAN(foot[0], foot[2], foot[3]), 4, "armour")


def _torso(c, quad, collar, pelvis=None, prio=3):
    body = PO(quad, round_r=9.0)
    c.add(body, "shell", prio=prio)
    c.add(Clip(RR(collar[0], collar[1], collar[2], collar[3], r=3.0, round_r=4.0),
               body), "armour", prio=prio + 1, bias=2)
    if pelvis:
        hips = Clip(RR(pelvis[0], pelvis[1], pelvis[2], pelvis[3],
                       r=5.0, round_r=6.0), body)
        c.add(hips, "armour", prio=prio + 1, bias=2)
        c.contour(hips, width=1.3, delta=3, mats=("shell",))
    top = (quad[0][1] + quad[1][1]) / 2.0
    left = min(quad[0][0], quad[3][0])
    right = max(quad[1][0], quad[2][0])
    for n in range(2):
        y = collar[3] + 3 + n * 7
        if y < quad[2][1] - 3:
            c.shade_px([PX(left + 3, y), PX(right - 3, y)], 2, "shell")
    return top, left, right


def _capacitor(c, cx, cy, cc, cell_w=4, gap=3, bh=8.0, prio=20, blaze=False):
    """The four-cell chest plate.  It used to be the battery gauge; it is the beam
    capacitor now and it fills as the shot charges, which is half the attack's tell."""
    lit, hi, mid, dk, glow, _eye = cc
    step = cell_w + gap
    span = step * 4 - gap
    bez = RR(cx - span / 2.0 - 2.2, cy - bh, cx + span / 2.0 + 2.2, cy + bh,
             r=3.0, round_r=4.0)
    c.add(bez, "armour", prio=prio, bias=2)
    c.contour(bez, width=1.3, delta=3, mats=("shell",), below_prio=prio)
    half = max(2, int(round((bh - 2.4) * K)))
    ix = int(round((cx - span / 2.0) * K))
    cw = max(2, int(round(cell_w * K)))
    st = max(cw + 1, int(round(step * K)))
    cyp = int(round(cy * K))
    c.add(RR(cx - span / 2.0 - 1.4, cy - bh + 2.4, cx + span / 2.0 + 1.0,
             cy + bh - 2.4, r=1.5, round_r=2.0), "glass", prio=prio + 1)
    for i in range(4):
        on = i < lit
        for x in range(ix + i * st, ix + i * st + cw):
            for y in range(cyp - half, cyp + half + 1):
                if on:
                    col = hi if y <= cyp - half + 1 else (mid if y <= cyp + 1 else dk)
                    if x == ix + i * st + cw - 1 and y > cyp - half + 1:
                        col = dk
                else:
                    col = "#46536A" if y <= cyp else "#333E52"
                c.raw_px([(x, y)], col)
    lo, hy = cyp - half - 1, cyp + half + 1
    right = ix + 3 * st + cw
    for x in range(ix - 1, right + 1):
        c.raw_px([(x, lo), (x, hy)], glow)
    for y in range(lo, hy + 1):
        c.raw_px([(ix - 1, y), (right, y)], glow)
    if blaze:
        for x in range(ix - 2, right + 2):
            c.raw_px([(x, lo - 1), (x, hy + 1)], BEAM_HI)


# ---------------------------------------------------------------------------
# muzzle effects
# ---------------------------------------------------------------------------
def _blob(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if 0 <= x < c.w and 0 <= y < c.h:
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    c.raw_px([(x, y)], col)


def _ring(c, cx, cy, rx, ry, t, col):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if not (0 <= x < c.w and 0 <= y < c.h):
                continue
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if 1.0 - t <= d <= 1.0:
                c.raw_px([(x, y)], col)


def _charge_sphere(c, cx, cy, r, back, muzzle=None):
    """The shot the reference draws: a stack of energy rings climbing out of the
    muzzle into a ball with a bright off-centre core and a swirl, plus flame trails
    streaming backwards over the cannon arm."""
    cx, cy, r = cx * K, cy * K, r * K
    bx, by = back
    px, py = -by, bx

    # the throat: energy widening out of the bore into the ball.  The reference has a
    # stack of rings here, but at this size they land inside the ball and vanish - a
    # cone says the same thing and survives the pixel count.
    if muzzle:
        mx, my = muzzle[0] * K, muzzle[1] * K
        n = max(3, int(round(math.hypot(cx - mx, cy - my))))
        for t in range(n + 1):
            f = t / float(n)
            ex, ey = mx + (cx - mx) * f, my + (cy - my) * f
            half = r * (0.20 + 0.62 * f)
            for u in range(-int(half), int(half) + 1):
                c.raw_px([(int(round(ex - py * u)), int(round(ey + px * u)))],
                         BEAM_HI if abs(u) > half * 0.45 else BEAM_CORE)

    # the ball: dark rim, mid body, a bright core pushed toward the light, a swirl
    _blob(c, cx, cy, r, r, BEAM_DK)
    _blob(c, cx, cy, r - 1.2, r - 1.2, BEAM_MID)
    kx, ky = cx - r * 0.26, cy - r * 0.28
    _blob(c, kx, ky, r * 0.62, r * 0.62, BEAM_HI)
    _blob(c, kx, ky, r * 0.30, r * 0.30, BEAM_CORE)
    for t in range(22):
        a = math.pi * 0.55 + t * 0.235
        rr = r * (0.26 + t * 0.020)
        c.raw_px([(int(round(kx + math.cos(a) * rr)),
                   int(round(ky + math.sin(a) * rr * 0.94)))],
                 BEAM_MID if t % 4 else BEAM_DK)
    c.raw_px([(int(round(cx + r * 0.46)), int(round(cy + r * 0.44)))], BEAM_HI)

    # flame trails: solid near the ball, tapering to single pixels
    for i, (off, length) in enumerate(((-0.92, 26), (-0.34, 16), (0.38, 22),
                                       (0.94, 14))):
        sx = cx + px * off * r + bx * r * 0.30
        sy = cy + py * off * r + by * r * 0.30
        n = max(4, int(length * K))
        for t in range(n):
            f = t / float(n)
            w = 3 if f < 0.20 else (2 if f < 0.46 else (1 if f < 0.74 else 0))
            ax = sx + bx * t + px * off * r * f * 0.45
            ay = sy + by * t + py * off * r * f * 0.45
            if f > 0.82 and (t + i) % 2:
                continue
            for u in range(-w, w + 1):
                c.raw_px([(int(round(ax - py * u)), int(round(ay + px * u)))],
                         BEAM_HI if f < 0.42 else BEAM_MID)


def _lock_flare(c, cx, cy, r, back):
    """THE LOCK.  The soft ball collapses into a hard white point with four rigid
    spikes and a snapped-shut ring - deliberately nothing like the charge blob, so
    the change reads at the edge of vision."""
    cx, cy, r = cx * K, cy * K, r * K
    for y in range(int(cy - r) - 2, int(cy + r) + 3):
        for x in range(int(cx - r) - 2, int(cx + r) + 3):
            if not (0 <= x < c.w and 0 <= y < c.h):
                continue
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d < r * 0.46:
                c.raw_px([(x, y)], BEAM_CORE)
            elif d < r * 0.62:
                c.raw_px([(x, y)], BEAM_HI)
            elif r * 0.90 <= d <= r * 1.06:       # the snapped ring
                c.raw_px([(x, y)], BEAM_HI if (x + y) % 2 else BEAM_MID)
    bx, by = back
    px, py = -by, bx
    for dx, dy, n in ((bx, by, 1.90), (-bx, -by, 1.30), (px, py, 1.75),
                      (-px, -py, 1.75)):
        for t in range(int(r * n)):
            f = t / float(r * n)
            w = 0 if f > 0.55 else 1
            for u in range(-w, w + 1):
                c.raw_px([(int(round(cx + dx * t - dy * u)),
                           int(round(cy + dy * t + dx * u)))],
                         BEAM_CORE if f < 0.35 else BEAM_HI)
    # the four corner ticks of the lock reticle
    for sx in (-1, 1):
        for sy in (-1, 1):
            ox, oy = cx + sx * r * 1.32, cy + sy * r * 1.32
            for t in range(int(3 * K) + 2):
                c.raw_px([(int(round(ox - sx * t)), int(round(oy))),
                          (int(round(ox)), int(round(oy - sy * t)))], BEAM_CORE)


def _mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    out = []
    for i in (0, 2, 4):
        av, bv = int(a[i:i + 2], 16), int(b[i:i + 2], 16)
        out.append(int(av * (1 - t) + bv * t))
    return "#%02x%02x%02x" % tuple(out)


def _keyline(c, gap=1):
    """Ink a 1px black line on the LOWER side of every overlap.

    Greyson, drawn at this same 96x96, carries 20-24% pure keyline per frame; the
    shipped 64x64 Computah carries 21-25%.  A bigger frame does not get there on its
    outer border alone - the border is perimeter and the body is area, so its share
    falls with scale.  The house style makes it up in INTERIOR line, and this is that
    pass: wherever a part sits on top of another, the one underneath gets a black
    edge, which is also what stops a crossed arm melting into the leg behind it.
    """
    ink = []
    for y in range(c.h):
        for x in range(c.w):
            if c.mat[y][x] is None or c.locked[y][x] or c.raw[y][x] is not None:
                continue
            p = c.prio[y][x]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if not (0 <= xx < c.w and 0 <= yy < c.h):
                    continue
                if c.mat[yy][xx] is not None and c.prio[yy][xx] - p >= gap:
                    ink.append((x, y))
                    break
    c.raw_px(ink, OUTLINE)
    return len(ink)


def _finish(c, gap=2):
    c.occlude(strength=2, reach=1)
    c.rim(1, mats=("shell", "armour"))
    c.despeckle()
    _keyline(c, gap)
    return c


FACE_FRONT = face_grid(28, 14, ew=4, eh=4, inset=4, mouth_rows=4)
FACE_BLINK = face_grid(28, 14, ew=4, eh=4, inset=4, mouth_rows=4, squint=2)
FACE_SCOWL = face_grid(28, 14, ew=4, eh=4, inset=4, mouth_rows=4, squint=1)
FACE_TURN = face_grid(24, 13, ew=4, eh=4, inset=3, mouth_rows=4, turn=1)
FACE_LOCK = face_grid(24, 13, ew=4, eh=4, inset=3, mouth_rows=4, turn=1, squint=1)


# ---------------------------------------------------------------------------
# damage and failure effects, carried over from the shipped sheets
# ---------------------------------------------------------------------------
def _sparks(c, ox, oy, pts):
    """Electrical arcs.  Drawn as little crosses, not single pixels - at 96 a lone
    pixel of spark disappears into the keyline and reads as dirt."""
    for i, (dx, dy) in enumerate(pts):
        col = "#FFF6C8" if i % 2 else "#8CD8FF"
        x, y = PX(ox + dx, oy + dy)
        c.raw_px([(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)], col)
        c.raw_px([(x + 1 if i % 2 else x - 1, y - 1)], "#F2F8FF")


def _steam(c, ox, oy, phase=0):
    """Vent plume: three puffs climbing and spreading, each a lit cap over a shaded
    body so it reads as volume and not as dirt.

    Cool grey, never green.  Green is the beam, and a vent that glowed would read as
    a charge - exactly the wrong thing on the frames that ARE the punish window."""
    for n, (dx, dy, r, hi, lo) in enumerate((
            (0.0, -5.0, 3.6, "#CEDCEA", "#8091A8"),
            (3.5, -12.0, 4.6, "#A6B8CC", "#5E6C82"),
            (6.5, -20.0, 3.4, "#8091A8", "#3F4A5C"))):
        # Round the CENTRE once and step in whole pixels from there.  Rounding
        # every (centre + offset) instead looks equivalent and is not: a centre on
        # .5 plus Python's banker's rounding maps two neighbouring offsets onto one
        # column and skips the next, and the puff comes out as vertical stripes.
        cx, cy = PX(ox + dx + phase * 1.2 * (n + 1),
                    oy + dy - phase * 1.8 * (n + 1))
        rr = r * K
        for y in range(int(-rr) - 1, int(rr) + 2):
            for x in range(int(-rr) - 1, int(rr) + 2):
                if (x + 0.3) ** 2 + (y + 0.3) ** 2 <= rr * rr:
                    c.raw_px([(cx + x, cy + y)],
                             hi if (x <= 0 and y <= 0) else lo)


def _dust(c, ox, oy):
    """A low, wide kick of mat dust.  Flat and spreading sideways, not climbing like
    the vent steam - one is an impact and the other is heat, and they must not look
    like the same effect."""
    for dx, dy, rx, ry, hi, lo in ((0, 0, 5.0, 2.0, "#A6B8CC", "#5E6C82"),
                                   (7, -3, 3.6, 1.6, "#8091A8", "#3F4A5C"),
                                   (-6, -2, 3.0, 1.4, "#8091A8", "#3F4A5C")):
        cx, cy = PX(ox + dx, oy + dy)
        for y in range(int(-ry) - 1, int(ry) + 2):
            for x in range(int(-rx) - 1, int(rx) + 2):
                if (x / rx) ** 2 + (y / ry) ** 2 <= 1.0:
                    c.raw_px([(cx + x, cy + y)], hi if y <= 0 else lo)


def _speed(c):
    """Motion streaks behind the chase, the same read the shipped run sheet had."""
    for (x0, x1, y, col) in ((6, 21, 33, "#5E6C82"), (2, 15, 41, "#8091A8"),
                             (5, 20, 50, "#8091A8"), (0, 14, 57, "#5E6C82"),
                             (3, 17, 65, "#5E6C82")):
        c.raw_px(SPAN(x0, x1, y), col)
        c.raw_px(SPAN(x0 + 3, x1, y + 1), col)


# ===========================================================================
# The idle breath.  Everything above the hips rises and falls; the boots never move.
# Frame 0 is the approved key frame, so its offset has to be exactly zero - golden/
# holds the approved PNGs and regress.py fails if it ever stops matching.
IDLE_BOB = (0.0, -1.6, -3.0, -1.6)


def build_idle(k=0, charge="full"):
    """Standing loop.  Near-frontal so the chest plate reads, head and cannon canted
    to his right - the side the layout says he faces.

    The SHEET is this four-frame cycle emitted three times, once per battery state,
    so `frame = charge_state * 4 + cycle_frame` with ROW 0 = FULL.  The battery costs
    no extra drawing: only the cells, the antenna ball and the eye colour change."""
    d = IDLE_BOB[k]
    cc = CHARGE[charge] if isinstance(charge, str) else charge
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)

    _antenna(c, [(38, 25 + d), (30, 18 + d), (24.0, 13.5 + d)],
             (21.0, 11.4 + d, 4.0), cc)

    c.add(RR(41, 46 + d, 54, 57 + d * 0.6, r=3.0, round_r=4.0), "shell", prio=2)
    _torso(c, [(28.0, 55.0 + d), (67.0, 55.0 + d), (62.0, 79.0 + d * 0.3),
               (33.0, 79.0 + d * 0.3)],
           (29.0, 53.5 + d, 68.0, 60.5 + d * 0.8),
           pelvis=(30.0, 69.5 + d * 0.4, 66.0, 80.0 + d * 0.3))

    _leg(c, (39.5, 75 + d * 0.35), (37.5, 83), (37.0, 89),
         (27.5, 86.5, 46.0, 95.0), prio=4)
    _leg(c, (55.5, 75 + d * 0.35), (57.5, 83), (58.0, 89),
         (49.5, 86.5, 68.0, 95.0), prio=4)

    _arm(c, (25.5, 60.0 + d), (19.0, 70.0 + d * 0.6), (16.8, 80.5 + d * 0.25),
         hand_r=5.3, r0=5.8, r1=4.9, r2=4.2, prio=6,
         cap=(25.6, 58.5 + d, 7.8, 6.9))

    _cannon(c, (65.0, 59.0 + d), (83.0, 77.5 + d * 0.3), r=8.0, prio=16)
    _capacitor(c, 47.5, 66.0 + d * 0.7, cc, cell_w=3, gap=3, bh=6.4)

    _helmet(c, 47.0, 33.5 + d, rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
            chin=41.5 + d, pods=(6.0, 6.0), pod_y=5.5, vent=1)
    _face(c, FACE_BLINK if k == 2 else FACE_FRONT, 33.0, 27.0 + d, cc)
    return _finish(c)


# The chase.  Four poses: contact, passing, contact on the other leg, passing.
# Each entry is (near leg, far leg), each leg (hip, knee, ankle, foot).  The torso is
# deliberately SHORT here - a standing torso leaves about fifteen rows of leg below
# the pelvis and no stride fits in that, which is why the first cut read as a robot
# shuffling on the spot.
RUN_LEGS = (
    ((((52, 71), (61, 79), (63, 88), (55, 86.5, 75, 95))),
     (((44, 71), (33, 79), (26, 86), (16, 84.0, 36, 93)))),
    ((((51, 69), (55, 79), (55, 89), (47, 87.5, 67, 95))),
     (((45, 69), (40, 78), (37, 85), (27, 83.0, 47, 92)))),
    ((((51, 71), (42, 79), (35, 87), (25, 85.0, 45, 94))),
     (((46, 71), (57, 77), (62, 83), (54, 81.0, 74, 90)))),
    ((((51, 69), (53, 79), (53, 89), (45, 87.5, 65, 95))),
     (((45, 69), (49, 78), (51, 84), (41, 82.0, 61, 91)))),
)
# (normal arm shoulder/elbow/wrist, cannon shoulder, cannon muzzle)
RUN_ARMS = (
    ((31, 56), (20, 62), (16, 71), (67, 56), (88, 65)),
    ((31, 55), (24, 63), (23, 73), (67, 55), (89, 60)),
    ((31, 54), (29, 62), (33, 69), (67, 54), (85, 70)),
    ((31, 55), (24, 63), (23, 73), (67, 55), (88, 63)),
)
RUN_ANT = (([(40, 24), (30, 20), (22, 18)], (19.0, 16.6)),
           ([(40, 22), (31, 17), (24, 14)], (21.0, 12.6)),
           ([(40, 24), (30, 21), (22, 20)], (19.0, 18.6)),
           ([(40, 22), (31, 18), (24, 16)], (21.0, 14.6)))
RUN_BOB = (0.0, -2.5, 0.0, -2.5)


def build_run(k=0, charge="full"):
    """The chase.  He leans hard into it and the cannon rides forward and high - the
    weapon leads, which is what says `beam boss closing` rather than `robot jogging`.
    The off arm stays grey here: it is out at his side, not crossing the body, so it
    does not need the gauntlet that keeps it readable in the braced poses."""
    d = RUN_BOB[k]
    cc = CHARGE[charge] if isinstance(charge, str) else charge
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    _speed(c)

    ant, ball = RUN_ANT[k]
    _antenna(c, [(x, y + d) for x, y in ant], (ball[0], ball[1] + d, 4.0), cc)

    near, far = RUN_LEGS[k]
    _leg(c, far[0], far[1], far[2], far[3], prio=4, far=True)

    c.add(RR(45, 43 + d, 58, 53 + d * 0.6, r=3.0, round_r=4.0), "shell", prio=2)
    _torso(c, [(32.0, 52.0 + d), (71.0, 48.0 + d), (66.0, 70.0 + d * 0.3),
               (36.0, 73.0 + d * 0.3)],
           (32.5, 47.5 + d, 72.0, 54.5 + d * 0.8),
           pelvis=(34.0, 63.0 + d * 0.4, 69.0, 74.0 + d * 0.3))

    _leg(c, near[0], near[1], near[2], near[3], prio=6)

    a = RUN_ARMS[k]
    _arm(c, (a[0][0], a[0][1] + d), (a[1][0], a[1][1] + d * 0.6),
         (a[2][0], a[2][1] + d * 0.25), hand_r=5.3, r0=5.8, r1=4.9, r2=4.2,
         prio=9, cap=(a[0][0] + 0.2, a[0][1] - 1.5 + d, 7.8, 6.9))

    _cannon(c, (a[3][0], a[3][1] + d), (a[4][0], a[4][1] + d * 0.4), r=8.0,
            prio=16)
    _capacitor(c, 51.0, 59.5 + d * 0.7, cc, cell_w=3, gap=3, bh=6.0)

    _helmet(c, 51.0, 29.0 + d, rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
            chin=37.0 + d, pods=(6.0, 6.0), pod_y=5.5, vent=1)
    _face(c, FACE_SCOWL, 37.0, 22.5 + d, cc, mood="angry")
    return _finish(c)


def build_hit(k=0):
    """Taking a punch: head snapped back, arms flung, the chassis arcing.  Three
    frames, played once, so the recoil has to be legible on frame 0 alone."""
    cc = CHARGE["full"]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    t = (-6.0, -3.0, -0.8)[k]            # how far back he is driven
    s = (7.5, 4.0, 1.2)[k]               # how far the limbs are flung

    _antenna(c, [(38 + t, 25), (30 + t * 2.0, 18), (24.0 + t * 2.6, 14)],
             (21.0 + t * 2.8, 12.0, 4.0), cc)

    c.add(RR(41 + t * 0.6, 46, 54 + t * 0.6, 57, r=3.0, round_r=4.0), "shell",
          prio=2)
    _torso(c, [(28.0 + t * 0.7, 55.0), (67.0 + t * 0.7, 55.0), (62.0, 79.0),
               (33.0, 79.0)],
           (29.0 + t * 0.7, 53.5, 68.0 + t * 0.7, 60.5),
           pelvis=(30.0, 69.5, 66.0, 80.0))

    _leg(c, (39.5, 75), (36.5, 83), (35.5, 89), (25.5, 86.5, 44.0, 95.0), prio=4)
    _leg(c, (55.5, 75), (58.5, 83), (59.5, 89), (51.5, 86.5, 70.0, 95.0), prio=4)

    _arm(c, (25.5 + t * 0.4, 60.0), (17.5 - s * 0.5, 67.0 - s),
         (14.0 - s * 0.8, 75.0 - s * 1.4), hand_r=5.3, r0=5.8, r1=4.9, r2=4.2,
         prio=6, cap=(25.6 + t * 0.4, 58.5, 7.8, 6.9))

    _cannon(c, (65.0 + t * 0.4, 59.0), (86.0 + s * 0.4, 72.0 - s * 1.6), r=8.0,
            prio=16)
    _capacitor(c, 47.5 + t * 0.4, 66.0, cc, cell_w=3, gap=3, bh=6.4)

    _helmet(c, 47.0 + t, 33.5, rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
            chin=41.5, pods=(6.0, 6.0), pod_y=5.5, vent=1)
    _face(c, (FACE_BLINK, FACE_SCOWL, FACE_FRONT)[k], 33.0 + t, 27.0, cc,
          mood="hit" if k == 0 else "calm")
    _finish(c)
    if k == 0:
        _sparks(c, 47, 24, ((-12, -3), (-9, -6), (-14, -8), (11, -3), (14, -6),
                            (9, -8), (-3, -9), (3, -11)))
    return c


def build_charge(fx=True):
    """The braced charge off the reference: both hands on the weapon, cannon level at
    chest height, stance wide and deep, weight back off the recoil."""
    cc = CORE["chg"]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)

    _antenna(c, [(28, 26), (18, 19), (10.5, 14.5)], (7.8, 12.6, 4.0), cc)

    # rear leg folded deep and back and a tone darker; front leg planted forward
    _leg(c, (31.0, 72.0), (18.5, 79.5), (14.5, 88.0), (3.5, 86.5, 23.0, 95.0),
         prio=4, far=True)
    _leg(c, (44.0, 72.5), (52.5, 81.0), (53.0, 88.0), (42.0, 86.5, 63.0, 95.0),
         prio=6)

    c.add(RR(33.5, 44.0, 42.0, 53.0, r=3.0, round_r=4.0), "shell", prio=2)
    _torso(c, [(25.0, 51.0), (46.0, 48.5), (50.0, 72.0), (28.5, 74.5)],
           (25.5, 48.5, 47.0, 52.5), pelvis=(26.5, 65.5, 51.5, 75.5))

    # the bracing arm crosses the body, so it is drawn lifted and cut out of it
    _arm(c, (29.5, 55.0), (35.5, 68.0), (48.5, 68.5), hand_r=5.4,
         r0=6.2, r1=5.2, r2=4.6, prio=9, cap=(29.0, 53.5, 7.8, 7.2),
         gauntlet=True)

    face = _cannon(c, (43.0, 58.0), (69.0, 59.5), r=8.2, prio=16)

    # the bracing mitt clamps the barrel from underneath, drawn OVER it
    grip = E(54.5, 67.0, 5.9, 5.3)
    c.add(grip, "shell", prio=22, bias=-1)
    c.contour(grip, width=1.5, delta=3, mats=("armour", "shell"), below_prio=22)
    c.shade_px(SPAN(51.5, 58.0, 69.5), 2, "shell")
    c.shade_px(SPAN(51.5, 58.0, 67.5), 2, "shell")
    c.shade_px(SPAN(52.0, 55.5, 63.5), -2, "shell")

    _capacitor(c, 36.0, 59.5, cc, cell_w=3, gap=3, bh=6.2, prio=24)

    _helmet(c, 31.5, 33.0, rx=18.5, ry=13.0, jaw=(10.0, 3.0, 14.0), chin=40.0,
            pods=(6.2, 3.4), pod_y=5.0, vent=1)
    _face(c, FACE_TURN, 21.0, 26.5, cc, mood="angry")

    _finish(c)
    if fx:
        _charge_sphere(c, 80.0, 60.0, 11.0, back=(-1.0, 0.0), muzzle=face)
        c.raw_px([(int(round(face[0] * K)) + dx, int(round(face[1] * K)) + dy)
                  for dx in (0, 1, 2) for dy in (-2, -1, 0, 1, 2)], BEAM_CORE)
    return c


def build_ready(fx=True):
    """THE LOCK - the frame the whole attack hangs on.  Everything that changes from
    `charge` is silhouette: he snaps upright out of the crouch, the antenna goes
    rigid, the bracing arm leaves the barrel and clamps the breech, and the soft ball
    collapses into a hard spiked point.  Colour only seconds it."""
    cc = CORE["lock"]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)

    # antenna bolt upright - the single loudest silhouette change
    _antenna(c, [(32, 19), (31, 12), (30.5, 8)], (30.0, 6.4, 4.2), cc)

    # knees locked, both feet rooted, the stance narrower than the crouch
    _leg(c, (33.5, 70.0), (25.0, 80.0), (22.0, 88.0), (11.0, 86.5, 30.0, 95.0),
         prio=4, far=True)
    _leg(c, (46.5, 70.5), (53.0, 80.0), (53.5, 88.0), (43.0, 86.5, 63.0, 95.0),
         prio=6)

    c.add(RR(36.0, 39.0, 44.5, 48.0, r=3.0, round_r=4.0), "shell", prio=2)
    _torso(c, [(29.0, 46.0), (50.0, 45.0), (52.5, 70.0), (31.0, 72.0)],
           (29.5, 43.5, 51.0, 47.5), pelvis=(30.0, 63.5, 54.0, 73.0))

    # the off arm has left the weapon: elbow tucked, fist clamped on the breech
    _arm(c, (32.5, 52.5), (31.5, 68.5), (43.5, 62.0), hand_r=5.4,
         r0=6.2, r1=5.2, r2=4.6, prio=9, cap=(32.2, 51.0, 7.8, 7.2),
         gauntlet=True)

    face = _cannon(c, (45.5, 54.5), (70.0, 54.5), r=8.2, prio=16)

    _capacitor(c, 38.0, 55.0, cc, cell_w=3, gap=3, bh=6.2, prio=24, blaze=True)

    _helmet(c, 33.5, 29.0, rx=18.5, ry=13.0, jaw=(10.0, 3.0, 14.0), chin=36.0,
            pods=(6.2, 3.4), pod_y=5.0, vent=1)
    _face(c, FACE_LOCK, 23.0, 22.5, cc, mood="lock")

    _finish(c)
    if fx:
        _lock_flare(c, 79.0, 54.5, 8.6, back=(1.0, 0.0))
        c.raw_px([(int(round(face[0] * K)) + dx, int(round(face[1] * K)) + dy)
                  for dx in (0, 1, 2) for dy in (-2, -1, 0, 1, 2)], BEAM_CORE)
    return c


# The discharge.  Muzzle, shoulder and body kick BACK along the barrel, which is why
# the muzzle point has to be per frame - a beam pinned to one fixed point detaches
# from the barrel on the recoil frame.  FIRE_RIG feeds both the drawing and
# muzzle_points(), so they cannot drift apart.
FIRE_RIG = (       # (cannon shoulder, muzzle, body shift, head shift, blast)
    ((47.5, 54.0), (73.0, 54.0), 1.5, 1.0, 13.0),
    ((35.0, 57.0), (57.0, 59.0), -10.0, -14.0, 7.0),
    ((42.0, 55.5), (65.0, 56.0), -3.5, -5.5, 3.5),
)


def build_fire(k=0, fx=True):
    """Discharge.  Frame 0 is the shot leaving, 1 is peak recoil with the barrel
    driven back into the shoulder and the whole chassis rocked off it, 2 is the
    settle with the first of the vent steam."""
    sh, mz, bx, hx, blast = FIRE_RIG[k]
    cc = CORE["lock"] if k == 0 else CHARGE["full"]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)

    _antenna(c, [(32 + bx, 19), (31 + bx * 2.2, 12), (30.5 + bx * 3.0, 8.5)],
             (30.0 + bx * 3.2, 7.0, 4.2), cc)

    # rear leg takes the recoil, front leg skids
    _leg(c, (33.5 + bx * 0.5, 70.0), (25.0 + bx * 0.3, 80.0), (22.0, 88.0),
         (11.0, 86.5, 30.0, 95.0), prio=4, far=True)
    _leg(c, (46.5 + bx * 0.5, 70.5), (53.0 + bx * 0.6, 80.0),
         (53.5 + bx * 0.4, 88.0), (43.0 + bx * 0.4, 86.5, 63.0 + bx * 0.4, 95.0),
         prio=6)

    c.add(RR(36.0 + bx, 39.0, 44.5 + bx, 48.0, r=3.0, round_r=4.0), "shell",
          prio=2)
    _torso(c, [(29.0 + bx, 46.0), (50.0 + bx, 45.0), (52.5 + bx * 0.3, 70.0),
               (31.0 + bx * 0.3, 72.0)],
           (29.5 + bx, 43.5, 51.0 + bx, 47.5),
           pelvis=(30.0 + bx * 0.3, 63.5, 54.0 + bx * 0.3, 73.0))

    _arm(c, (32.5 + bx, 52.5), (31.5 + bx * 1.2, 68.5), (43.5 + bx, 62.0),
         hand_r=5.4, r0=6.2, r1=5.2, r2=4.6, prio=9,
         cap=(32.2 + bx, 51.0, 7.8, 7.2), gauntlet=True)

    face = _cannon(c, sh, mz, r=8.2, prio=16)
    _capacitor(c, 38.0 + bx, 55.0, cc, cell_w=3, gap=3, bh=6.2, prio=24,
               blaze=k == 0)

    _helmet(c, 33.5 + hx, 29.0, rx=18.5, ry=13.0, jaw=(10.0, 3.0, 14.0),
            chin=36.0, pods=(6.2, 3.4), pod_y=5.0, vent=1)
    _face(c, FACE_LOCK, 23.0 + hx, 22.5, cc,
          mood="lock" if k == 0 else "angry")

    _finish(c)
    if k == 2:
        _steam(c, 56, 44, phase=0)
    if fx:
        _muzzle_blast(c, face, blast, back=(1.0, 0.0), hot=k == 0)
    return c


def _muzzle_blast(c, face, r, back, hot=True):
    """The flash at the barrel: a radial star blown off the bore, squashed along the
    barrel axis so it reads as coming OUT rather than as a ball sitting there.

    Deliberately not a beam.  The beam is its own node hung on C_MUZZLE_FIRE, and
    drawing one here would double it and fix its length to whatever I guessed."""
    fx, fy, r = face[0] * K, face[1] * K, r * K
    if r < 1.5:
        return
    bx, by = back
    px, py = -by, bx
    for y in range(int(fy - r) - 2, int(fy + r) + 3):
        for x in range(int(fx - r) - 2, int(fx + r) + 3):
            if not (0 <= x < c.w and 0 <= y < c.h):
                continue
            ax = (x + 0.5 - fx) * bx + (y + 0.5 - fy) * by      # along the barrel
            cr = (x + 0.5 - fx) * px + (y + 0.5 - fy) * py      # across it
            d = math.hypot(ax / 1.35, cr)                       # squashed ellipse
            if d > r:
                continue
            if d < r * 0.40:
                c.raw_px([(x, y)], BEAM_CORE)
            elif d < r * 0.68:
                c.raw_px([(x, y)], BEAM_HI if hot else BEAM_MID)
            elif (x + y) % 2 == 0:
                c.raw_px([(x, y)], BEAM_MID)
    # the spikes off the bore, longest straight down the barrel
    for n in range(9):
        a = n * (math.pi / 4.5)
        reach = r * (2.0 if n == 0 else (0.9 + 0.7 * abs(math.cos(a))))
        for t in range(int(reach)):
            f = t / max(reach, 1.0)
            if f > 0.55 and (t + n) % 2:
                continue
            dx = bx * math.cos(a) - py * math.sin(a)
            dy = by * math.cos(a) + px * math.sin(a)
            c.raw_px([(int(round(fx + dx * t)), int(round(fy + dy * t)))],
                     BEAM_CORE if f < 0.3 else BEAM_HI)


def build_recover(k=0):
    """The vent.  This is the punish window, so it must not read as any kind of
    wind-up: he is DOWN on one knee with the barrel planted muzzle-first on the mat,
    head below the chest, cells nearly out and cool grey steam - never green - coming
    off the shoulder.  A separate C_DOWN_BODY_BOX is swapped in for these frames, so
    the silhouette deliberately sits in a much lower band than any standing pose."""
    cc = CHARGE["full"] if k else CORE["chg"]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    d = (-13.0, 0.0, 0.0, 0.0)[k]             # frame 0 is still on the way down
    puff = (0, 0, 0, 1)[k]

    _antenna(c, [(26, 46 + d), (18, 44 + d), (11, 46 + d)],
             (8.0, 47.4 + d, 4.0), cc)

    # rear knee down on the mat, front knee up with the foot planted flat
    _leg(c, (34.0, 80.0 + d * 0.4), (23.0, 90.0 + d * 0.2), (18.0, 93.0),
         (9.0, 90.0, 27.0, 95.0), prio=4, far=True)
    _leg(c, (45.0, 82.0 + d * 0.4), (63.0, 84.0 + d * 0.3), (61.0, 92.0),
         (51.0, 89.0, 71.0, 95.0), prio=6)

    c.add(RR(31.0, 60.0 + d, 39.0, 68.0 + d * 0.6, r=3.0, round_r=4.0), "shell",
          prio=2)
    _torso(c, [(26.0, 67.0 + d), (48.0, 65.0 + d), (51.0, 84.0 + d * 0.2),
               (28.0, 86.0 + d * 0.2)],
           (26.5, 64.5 + d, 49.0, 68.5 + d),
           pelvis=(27.0, 78.0 + d * 0.2, 52.0, 88.0))

    _arm(c, (29.5, 71.0 + d * 0.8), (26.0, 84.0 + d * 0.3), (34.0, 90.0),
         hand_r=5.2, r0=6.0, r1=5.0, r2=4.4, prio=9,
         cap=(29.3, 69.5 + d * 0.8, 7.6, 7.0), gauntlet=True)

    # the barrel laid across the raised knee while it cools - a weapon at rest.  It
    # is deliberately NOT pointed anywhere: this frame is an invitation, not a threat
    _cannon(c, (45.0, 72.0 + d * 0.7), (76.0, 76.0 + d * 0.2), r=8.2, prio=16)
    _capacitor(c, 35.5, 73.0 + d * 0.7, cc, cell_w=3, gap=3, bh=5.6, prio=24)

    _helmet(c, 30.0, 50.0 + d, rx=17.0, ry=12.0, jaw=(9.5, 3.0, 14.0),
            chin=56.0 + d, pods=(6.0, 3.2), pod_y=4.6, vent=1)
    _face(c, FACE_TURN, 19.5, 43.5 + d, cc, mood="dim" if k else "angry")

    _finish(c)
    if k:
        _steam(c, 52, 62, phase=puff)
        _steam(c, 70, 66, phase=1 - puff)
    return c


# The collapse and the floor loop.  Frames 0-2 put him down, 3-4 are the twitch the
# punish window sits on, and playing 2-1-0 brings him back up, which is the hand-over
# the shipped drop sheet was built around and the state machine still expects.
def _floor(c, cc, dy=0.0, arms_up=False, eyes="dead", smoke=False, spark=None,
           armless=False):
    """Him on the mat: chassis sat down where he stood, head lolled back over the
    shoulder, the cannon flopped out across the floor."""
    _antenna(c, [(25, 60 + dy), (17, 57 + dy), (10, 59 + dy)],
             (7.0, 60.4 + dy, 4.0), cc)

    # knees folded up on his left, so the right of the frame is clear for the
    # cannon to lie out along the mat - which is what makes this read as sprawled
    # rather than as a crouch
    _leg(c, (34.0, 86 + dy * 0.2), (24.0, 91), (18.0, 94),
         (8.0, 91.0, 26.0, 95.0), prio=4, far=True)
    _leg(c, (40.0, 87 + dy * 0.2), (30.0, 92), (26.0, 94),
         (16.0, 91.5, 34.0, 95.0), prio=6)

    c.add(RR(27.0, 76 + dy, 35.0, 83 + dy * 0.6, r=3.0, round_r=4.0), "shell",
          prio=2)
    _torso(c, [(22.0, 80 + dy), (46.0, 77 + dy), (54.0, 93), (20.0, 94)],
           (22.5, 77.5 + dy, 47.0, 82.0 + dy), pelvis=(22.0, 87.0, 54.0, 95.0))

    if arms_up:
        _arm(c, (25.0, 83 + dy * 0.6), (16.0, 73), (11.0, 63), hand_r=5.2,
             r0=5.8, r1=4.9, r2=4.2, prio=9, cap=(24.8, 81.5 + dy * 0.6, 7.4, 6.8),
             gauntlet=True)
        if armless:
            _stump(c, 46.0, 82 + dy * 0.6, spray=0.8)
        else:
            _cannon(c, (44.0, 82 + dy * 0.6), (68.0, 62.0), r=7.8, prio=16)
    else:
        _arm(c, (25.0, 84 + dy * 0.6), (18.0, 90), (13.0, 94), hand_r=5.2,
             r0=5.8, r1=4.9, r2=4.2, prio=9, cap=(24.8, 82.5 + dy * 0.6, 7.4, 6.8),
             gauntlet=True)
        if armless:
            _stump(c, 48.0, 84 + dy * 0.6, spray=0.8)
        else:
            _cannon(c, (46.0, 84 + dy * 0.6), (80.0, 92.0), r=7.8, prio=16)
    _capacitor(c, 32.5, 85 + dy * 0.3, cc, cell_w=3, gap=3, bh=5.4, prio=24)

    _helmet(c, 26.0, 66.0 + dy, rx=16.5, ry=11.5, jaw=(9.0, 3.0, 13.0),
            chin=71.5 + dy, pods=(5.8, 3.0), pod_y=4.4, vent=1)
    _face(c, FACE_LOCK, 16.0, 59.5 + dy, cc, mood=eyes)

    _finish(c)
    if smoke:
        _steam(c, 58, 76 + dy)
    if spark:
        _sparks(c, spark[0], spark[1],
                ((-14, -4), (-17, 0), (-13, 4), (14, -4), (17, 0), (13, 4),
                 (-9, -10), (9, -10), (0, 11)))


def build_drop(k=0):
    """Knocked off his feet.  0 faltering, 1 the knees going with the arms flung up,
    2 landed, 3-4 the floor twitch the punish window loops on."""
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    if k == 0:
        # Faltering mid-stride.  Built on RUN FRAME 2 and sagged, not on the idle:
        # this frame is handed straight over from the chase when the battery runs
        # out, and a standing pose here would pop the moment it cut in.  Last red
        # cell, eyes going dim, no speed streaks - he has stopped closing.
        cc = CHARGE["low"]
        sag = 7.0
        _antenna(c, [(40, 24 + sag), (30, 23 + sag), (22, 26 + sag)],
                 (19.0, 27.6 + sag, 4.0), cc)
        _leg(c, (46, 71 + sag * 0.5), (57, 79 + sag * 0.2), (60, 87),
             (52.0, 85.0, 72.0, 94.0), prio=4, far=True)
        c.add(RR(45, 43 + sag, 58, 53 + sag * 0.6, r=3.0, round_r=4.0), "shell",
              prio=2)
        _torso(c, [(32.0, 52.0 + sag), (71.0, 48.0 + sag),
                   (66.0, 70.0 + sag * 0.3), (36.0, 73.0 + sag * 0.3)],
               (32.5, 47.5 + sag, 72.0, 54.5 + sag * 0.8),
               pelvis=(34.0, 63.0 + sag * 0.4, 69.0, 74.0 + sag * 0.3))
        _leg(c, (51, 71 + sag * 0.5), (43, 80 + sag * 0.2), (37, 88),
             (27.0, 86.0, 47.0, 95.0), prio=6)
        _arm(c, (31, 54 + sag), (28, 64 + sag * 0.6), (31, 73 + sag * 0.25),
             hand_r=5.3, r0=5.8, r1=4.9, r2=4.2, prio=9,
             cap=(31.2, 52.5 + sag, 7.8, 6.9))
        _cannon(c, (67, 54 + sag), (84, 74 + sag * 0.4), r=8.0, prio=16)
        _capacitor(c, 51.0, 59.5 + sag * 0.7, cc, cell_w=3, gap=3, bh=6.0)
        _helmet(c, 51.0, 29.0 + sag, rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
                chin=37.0 + sag, pods=(6.0, 6.0), pod_y=5.5, vent=1)
        _face(c, FACE_BLINK, 37.0, 22.5 + sag, cc, mood="dim")
        return _finish(c)
    if k == 1:
        _floor(c, CHARGE["dead"], dy=-10.0, arms_up=True, eyes="dim",
               spark=(30, 80))
        return c
    _floor(c, CHARGE["dead"], dy=(0.0, -1.0, 0.0)[k - 2],
           eyes=("dead", "ember", "dead")[k - 2])
    return c


def build_defeat(k=0):
    """Scrapped for this fight: two staggering frames, then down and smoking.  The
    last frame holds forever, so it has to look final standing still."""
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    if k < 2:
        cc = CHARGE["low" if k == 0 else "dead"]
        t = (-5.0, -9.0)[k]
        _antenna(c, [(38 + t, 28 + k * 4), (30 + t * 2, 23 + k * 6),
                     (24.0 + t * 2.6, 20 + k * 8)],
                 (21.0 + t * 2.8, 18.4 + k * 9, 4.0), cc)
        c.add(RR(41 + t * 0.6, 49 + k * 3, 54 + t * 0.6, 60 + k * 3, r=3.0,
                 round_r=4.0), "shell", prio=2)
        _torso(c, [(28.0 + t * 0.7, 58.0 + k * 3), (67.0 + t * 0.7, 58.0 + k * 3),
                   (62.0, 81.0), (33.0, 81.0)],
               (29.0 + t * 0.7, 56.5 + k * 3, 68.0 + t * 0.7, 63.5 + k * 3),
               pelvis=(30.0, 72.0, 66.0, 82.0))
        _leg(c, (39.5, 77), (35.0, 85), (33.0, 91), (23.0, 88.5, 43.0, 95.0),
             prio=4, far=True)
        _leg(c, (55.5, 77), (60.0, 85), (61.0, 91), (53.0, 88.5, 73.0, 95.0),
             prio=6)
        _arm(c, (25.5 + t * 0.4, 63.0), (16.0, 70.0 + k * 4),
             (12.0, 79.0 + k * 4), hand_r=5.3, r0=5.8, r1=4.9, r2=4.2, prio=6,
             cap=(25.6 + t * 0.4, 61.5, 7.8, 6.9))
        _cannon(c, (65.0 + t * 0.4, 62.0), (86.0, 79.0 + k * 5), r=8.0, prio=16)
        _capacitor(c, 47.5 + t * 0.4, 69.0 + k * 3, cc, cell_w=3, gap=3, bh=6.4)
        _helmet(c, 47.0 + t, 36.5 + k * 4, rx=21.0, ry=13.0,
                jaw=(11.5, 4.0, 16.5), chin=44.5 + k * 4, pods=(6.0, 6.0),
                pod_y=5.5, vent=1)
        _face(c, FACE_BLINK, 33.0 + t, 30.0 + k * 4, cc,
              mood="hit" if k == 0 else "dim")
        _finish(c)
        _sparks(c, 47 + int(t), 66 + k * 3,
                ((-18, -5), (-21, 0), (-17, 5), (18, -5), (21, 0), (17, 5),
                 (-12, -11), (12, -11), (0, 12)))
        return c
    _floor(c, CHARGE["dead"], dy=(-4.0, 0.0, 0.0)[k - 2],
           eyes=("ember", "dead", "dead")[k - 2],
           smoke=k > 2, spark=(30, 84) if k == 2 else None)
    return c


# ===========================================================================
# THE UPPERCUT
# ===========================================================================
# 0-2 wind (a Shoryuken load: the cannon drops across his body and the plant shows
# in the legs), 3-5 the rise, 6-7 the fall, 8-9 the punishable loop, and
# `uppercut_up` plays 7 then 6 to get him back on his feet.
#
# FRAMES 6-9 SIT IN THE SAME VERTICAL BAND AS computah_drop's down frames, because
# the same down hurtbox is swapped in for them.  checks.py measures both and fails if
# they drift apart; 6 is only lifted enough to read as the bounce.
UP_RIG = (
    # (head cx, head cy, torso quad, collar, pelvis, cannon shoulder, muzzle,
    #  off arm sh/elbow/wrist, near leg, far leg, glow)
    #
    # The barrel drops to his RIGHT HIP and rises straight up that same side.  The
    # first cut cocked it across his body, where the torso hid it completely and the
    # load read as a crouch with a green smudge; on the punching side the whole swing
    # stays outside the silhouette.
    (40, 38, [(30, 56), (52, 54), (55, 76), (33, 78)], (30.5, 53.5, 53, 58),
     (32, 68, 56, 79), (50, 58), (66, 78), ((33, 60), (29, 72), (37, 78)),
     ((47, 76), (58, 84), (57, 92), (47, 90, 67, 95)),
     ((36, 76), (26, 84), (22, 92), (12, 90, 32, 95)), 4.0),
    (40, 41, [(30, 59), (52, 57), (55, 78), (33, 80)], (30.5, 56.5, 53, 61),
     (32, 71, 56, 81), (49, 61), (63, 83), ((33, 63), (29, 75), (37, 81)),
     ((47, 78), (59, 85), (58, 93), (48, 91, 68, 95)),
     ((36, 78), (25, 85), (21, 93), (11, 91, 31, 95)), 7.0),
    (41, 43, [(31, 61), (53, 59), (56, 80), (34, 82)], (31.5, 58.5, 54, 63),
     (33, 73, 57, 83), (48, 63), (60, 87), ((34, 65), (30, 77), (38, 83)),
     ((48, 80), (60, 86), (59, 94), (49, 92, 69, 95)),
     ((37, 80), (24, 86), (20, 94), (10, 92, 30, 95)), 10.0),
    (40, 33, [(32, 51), (54, 49), (55, 72), (33, 74)], (32.5, 48.5, 55, 53),
     (33, 64, 56, 75), (50, 54), (70, 38), ((33, 56), (28, 68), (37, 73)),
     ((48, 72), (56, 82), (54, 91), (44, 89, 64, 95)),
     ((38, 72), (30, 82), (26, 90), (16, 88, 36, 94)), 9.0),
    (37, 31, [(31, 49), (53, 47), (52, 72), (30, 74)], (31.5, 46.5, 54, 51),
     (31, 63, 53, 75), (49, 47), (62, 20), ((31, 50), (25, 62), (33, 70)),
     ((45, 72), (51, 84), (51, 93), (41, 91, 61, 95)),
     ((36, 72), (28, 83), (23, 91), (13, 89, 33, 95)), 7.0),
    (34, 30, [(29, 48), (51, 47), (50, 71), (28, 72)], (29.5, 45.5, 52, 50),
     (29, 62, 51, 73), (47, 45), (56, 18), ((29, 49), (22, 60), (29, 69)),
     ((43, 70), (49, 83), (50, 92), (40, 90, 60, 95)),
     ((34, 70), (26, 82), (21, 90), (11, 88, 31, 94)), 6.0),
)


def build_uppercut(k=0):
    cc = CHARGE["full"]
    if k >= 6:
        c = Canvas(FRAME, FRAME, PAL, OUTLINE)
        _floor(c, CHARGE["full" if k == 6 else "half"],
               dy=(-2.0, 0.0, 0.0, -1.0)[k - 6],
               eyes=("hit", "dim", "dead", "ember")[k - 6])
        if k == 6:                                  # the slam: dust and a jolt
            _dust(c, 8, 94)
            _dust(c, 66, 94)
            _sparks(c, 30, 84, ((-12, -2), (12, -2), (0, -8)))
        return c

    (hx, hy, torso, collar, pelvis, sh, mz, arm, near, far, glow) = UP_RIG[k]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    ant = ((34, 26), (28, 22), (22, 22)) if k < 3 else ((32, 20), (26, 24), (20, 28))
    _antenna(c, [(x, y + hy - 38) for x, y in ant],
             (17.0, (21.0 if k < 3 else 30.0) + hy - 38, 4.0), cc)

    _leg(c, far[0], far[1], far[2], far[3], prio=4, far=True)
    c.add(RR(hx - 5, hy + 8, hx + 4, hy + 18, r=3.0, round_r=4.0), "shell", prio=2)
    _torso(c, torso, collar, pelvis=pelvis)
    _leg(c, near[0], near[1], near[2], near[3], prio=6)
    _arm(c, arm[0], arm[1], arm[2], hand_r=5.4, r0=6.2, r1=5.2, r2=4.6, prio=9,
         cap=(arm[0][0] - 0.3, arm[0][1] - 1.5, 7.8, 7.2), gauntlet=True)
    face = _cannon(c, sh, mz, r=8.2, prio=16)
    _capacitor(c, torso[0][0] + 8.5, torso[0][1] + 8.0, cc, cell_w=3, gap=3,
               bh=5.8, prio=24)
    _helmet(c, hx, hy, rx=18.5, ry=13.0, jaw=(10.0, 3.0, 14.0), chin=hy + 7.0,
            pods=(6.2, 3.4), pod_y=5.0, vent=1)
    _face(c, FACE_LOCK if k >= 3 else FACE_TURN, hx - 10.5, hy - 6.5, cc,
          mood="lock" if k >= 3 else "angry")
    _finish(c)
    # the punch is thrown WITH the muzzle, so the energy is on the bore, not the
    # chest - that is what separates it from the beam at a glance
    _muzzle_blast(c, face, glow, back=_unit(sh, mz), hot=k >= 3)
    if k >= 4:
        _rise_trail(c, sh, mz)
    return c


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return (dx / L, dy / L)


def _rise_trail(c, sh, mz):
    """Where the barrel has just been: a short arc of fading green behind the swing,
    so the rise reads as one motion instead of three unrelated drawings."""
    bx, by = _unit(sh, mz)
    for n, (off, col) in enumerate(((0.55, BEAM_HI), (0.78, BEAM_MID),
                                    (1.0, BEAM_DK))):
        for t in range(10):
            a = math.pi * (0.10 + t * 0.045)
            rx = (mz[0] - sh[0]) * off
            ry = (mz[1] - sh[1]) * off
            x = sh[0] + rx * math.cos(a) - ry * math.sin(a) * 0.55
            y = sh[1] + ry * math.cos(a) + rx * math.sin(a) * 0.55
            if (t + n) % 2:
                continue
            c.raw_px([PX(x, y)], col)


# ===========================================================================
# THE OVERLOAD - a DPS check.  The player has to rush in and punch him.
# ===========================================================================
# THE SILHOUETTE RULE IS THE WHOLE ATTACK.  Both arms down and BACK, body arched,
# CANNON POINTED AT THE FLOOR.  It has to be unmistakably not aiming at the player,
# because that is the only thing separating it from the braced beam - one says dodge,
# this one says come here and hit me.  Every pose below keeps the muzzle below the
# hips and behind the heel line, and checks.py measures that.
#
# The energy is on his CHEST, never on the bore.  The beam gathers at the muzzle; if
# the overload did too, the two attacks would tell the same story.
OVERLOAD_AIM_ROW = 74          # the muzzle must be at or below this row, always
OVERLOAD_MUZZLE = (64.0, 90.0)  # where the barrel ends in every overload pose


def _overload(c, cc, arch, glow, blaze=0.0, crack=False):
    """`arch` is how far he is bent back over his heels (0 = planting, 1 = fully
    arched), `glow` the ramp level of the core light, `blaze` an extra white bloom.

    The read, in order of how loud it has to be: the BARREL HANGS STRAIGHT DOWN at
    his side with the muzzle on the mat, both hands are swept down and back, and his
    head is tipped back off his hips.  Nothing points at the player.  The braced beam
    is its exact opposite - barrel level, weight forward, both hands on the weapon -
    so at a glance the two can never be confused, which is the entire attack."""
    a = arch
    hy = 32.0 - a * 3.0
    hx = 34.0 - a * 3.0                       # head goes BACK off the hips
    _antenna(c, [(31 - a * 2, hy - 9), (24 - a * 5, hy - 13),
                 (17 - a * 8, hy - 15)],
             (14.0 - a * 9, hy - 16.0, 4.0), cc)

    # planted wide, both heels dug in, hips driven forward under him
    _leg(c, (36 - a, 74), (26 - a * 3, 83), (22 - a * 4, 91),
         (12 - a * 4, 89, 30 - a * 4, 95), prio=4, far=True)
    _leg(c, (48 + a, 74), (55 + a * 2, 82), (53 + a * 2, 91),
         (43 + a * 2, 89, 61 + a * 2, 95), prio=6)

    c.add(RR(hx + 2, hy + 9, hx + 11, hy + 21, r=3.0, round_r=4.0), "shell",
          prio=2)
    # shoulders back, hips forward: that tilt IS the arch at this size
    _torso(c, [(28 - a * 2, 50 - a * 2), (50 - a * 2, 47 - a * 3),
               (56 + a * 2, 72), (34 + a * 2, 75)],
           (28.5 - a * 2, 47.5 - a * 2, 51 - a * 2, 53 - a * 2),
           pelvis=(33, 64, 57, 76))

    # BOTH arms swept down and back, hands open, nothing braced on anything
    _arm(c, (30 - a * 2, 56), (22 - a * 4, 70), (16 - a * 6, 82), hand_r=5.4,
         r0=6.2, r1=5.2, r2=4.6, prio=9, cap=(30 - a * 2, 54.5, 7.8, 7.2),
         gauntlet=True)
    # THE BARREL HANGS.  Near vertical, outside the leg, muzzle down on the mat.
    sh = (53 + a * 2, 56)
    mz = (OVERLOAD_MUZZLE[0] + a * 3, OVERLOAD_MUZZLE[1])
    face = _cannon(c, sh, mz, r=8.2, prio=16)

    _capacitor(c, 37 - a, 57 - a * 2, cc, cell_w=3, gap=3, bh=6.4, prio=24,
               blaze=blaze > 0)
    _helmet(c, hx, hy, rx=18.5, ry=13.0, jaw=(10.0, 3.0, 14.0), chin=hy + 7.0,
            pods=(6.2, 3.4), pod_y=5.0, vent=1)
    _face(c, FACE_LOCK, hx - 10.5, hy - 6.5, cc, mood="lock" if blaze else "angry")
    _finish(c)

    _core_bloom(c, 37 - a, 57 - a * 2, glow, blaze)
    if crack:
        for pts in (((30, 50), (33, 56), (31, 62)), ((48, 48), (45, 54), (47, 60)),
                    ((40, 68), (42, 73))):
            for i, (x, y) in enumerate(pts):
                c.raw_px([PX(x, y)], BEAM_CORE if i % 2 else BEAM_HI)
    return face


def _core_bloom(c, cx, cy, level, blaze=0.0):
    """Light coming OUT of the chest plate.  Rings, not a beam: the player has to
    read `he is winding himself up`, not `something is about to be fired`."""
    if level <= 0:
        return
    r = 8.0 + level * 3.2 + blaze * 3.0
    cols = (BEAM_DK, BEAM_MID, BEAM_HI, BEAM_CORE)
    for n in range(level):
        rr = r * (0.5 + 0.26 * n)
        col = cols[min(n + (2 if blaze else 1), 3)]
        for i in range(140):
            t = 2.0 * math.pi * i / 140
            c.raw_px([PX(cx + math.cos(t) * rr, cy + math.sin(t) * rr * 0.72)],
                     col)
    if blaze:
        for i in range(10):
            a = i * (math.pi / 5.0)
            for t in range(int(r * (1.1 + blaze * 0.5))):
                if t % 2:
                    continue
                c.raw_px([PX(cx + math.cos(a) * t, cy + math.sin(a) * t * 0.72)],
                         BEAM_CORE if t < r * 0.5 else BEAM_HI)


def build_overload_brace(k=0):
    """He plants: three frames of setting his feet and arching back over them."""
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    _overload(c, CHARGE["full"], arch=(0.0, 0.45, 0.8)[k], glow=(0, 1, 1)[k])
    return c


def build_overload_charge(k=0, row=0):
    """4 frames x 3 rows.

    ROW 0 IS BARELY CHARGED AND ROW 2 IS WHITE-HOT - the INVERSE of computah_idle and
    computah_run, whose row 0 is a FULL battery.  Two sheets on one character running
    opposite ways is a genuine trap, so it is written at both ends."""
    tremble = (0.0, 0.5, 1.0, 0.5)[k]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    _overload(c, CHARGE["full"], arch=0.8 + tremble * 0.2,
              glow=(1, 2, 3)[row], blaze=(0.0, 0.0, 1.0)[row],
              crack=row == 2)
    return c


def build_overload_release(k=0):
    """The discharge.  Everything he was holding leaves the chest at once."""
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    _overload(c, CHARGE["half" if k else "full"], arch=(1.0, 0.5, 0.2)[k],
              glow=(3, 2, 1)[k], blaze=(1.4, 0.6, 0.0)[k])
    if k == 0:
        for i in range(28):
            a = 2.0 * math.pi * i / 28
            for t in range(16, 42, 2):
                c.raw_px([PX(36 + math.cos(a) * t, 55 + math.sin(a) * t * 0.72)],
                         BEAM_HI if t < 28 else BEAM_MID)
    return c


def build_overload_break(k=0):
    """The fizzle.  He has dumped everything and nothing came of it; this hands
    straight into the collapse."""
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    # the core light is already OUT on frame 0.  That is the point of the fizzle -
    # he spent everything and nothing came of it - and it also keeps the frame inside
    # the cast's colour band, which the leftover bloom was pushing it past.
    _overload(c, CHARGE[("low", "low", "dead")[k]], arch=(0.1, -0.3, -0.6)[k],
              glow=0)
    # five arcs, not seven: this frame already carries the dead-battery greys and
    # the vent steam, and the extra pair pushed it past the cast's colour band
    _sparks(c, 37, 57, ((-14, -4), (-17, 2), (14, -4), (17, 2), (0, -11))[:3 + k])
    if k == 2:
        _steam(c, 58, 50)
    return c


# ===========================================================================
# THE ENDING - the arm comes off, he goes down, and the player keeps the cannon
# ===========================================================================
# Where the cannon arm joins the shoulder.  This is the throw origin for the detached
# arm and the point the stump is drawn around, so it lives next to the rig that puts
# the shoulder there rather than being eyeballed later.
C_ARM_SOCKET = (52.0, 58.0)
# His core - where the finishing shot is aimed once he has nothing left to aim back.
C_ARMLESS_AIM = (40.0, 60.0)


def _stump(c, sx, sy, spray=1.0):
    """What is left of the shoulder: a torn socket, a bitten-off rim, and an arc of
    sparks.  Never a neat cap - a clean cut would read as a part he took off."""
    socket = Union([E(sx, sy, 8.0, 7.2),
                    CAP((sx - 3.0, sy), (sx + 3.5, sy - 1.5), 6.6, 7.2)], k=1.4 * K)
    c.add(socket, "armour", prio=17, bias=2)
    c.contour(socket, width=1.6, delta=3, mats=("shell", "armour"), below_prio=17)
    c.add(E(sx + 2.6, sy + 0.4, 5.4, 5.0), "dark", prio=18, flat=4)
    c.add(E(sx + 3.4, sy + 0.8, 3.0, 2.6), "dark", prio=19, flat=2)
    # torn teeth around the rim, so it reads as ripped off and not unbolted
    for n, (dx, dy) in enumerate(((6.0, -6.0), (8.4, -2.0), (7.8, 3.0),
                                  (4.4, 6.6), (-0.6, 7.4), (-5.0, 5.0))):
        c.add(E(sx + dx, sy + dy, 1.7, 1.7), "armour", prio=20,
              bias=1 if n % 2 else 3)
    if spray:
        pts = [(4 + i * 2.2, -7 + i * 3.2) for i in range(5)]
        pts += [(9 + i * 1.4, -2 + i * 2.0) for i in range(4)]
        _sparks(c, sx, sy, [(x * spray, y * spray) for x, y in pts])


DISARM_RIG = (
    # (body shift, head shift, stump spray, still has the arm)
    (0.0, 0.0, 0.0, True),
    (-4.0, -7.0, 1.0, False),
    (-9.0, -14.0, 0.9, False),
)


def build_disarm(k=0):
    """The arm comes off.  0 is the hit landing with the socket already split, 1 is
    the arm gone and the stump spraying, 2 is the stagger; 3 and 4 put him on the mat
    in the same band as every other down pose."""
    cc = CHARGE["low" if k else "half"]
    if k >= 3:
        c = Canvas(FRAME, FRAME, PAL, OUTLINE)
        _floor(c, CHARGE["dead"], dy=(-6.0, 0.0)[k - 3], eyes="dim",
               armless=True, spark=(30, 74))
        return c
    bx, hx, spray, armed = DISARM_RIG[k]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    _antenna(c, [(38 + hx, 25), (30 + hx * 1.6, 19), (24 + hx * 2.2, 16)],
             (21.0 + hx * 2.4, 14.4, 4.0), cc)
    _leg(c, (39.5 + bx * 0.4, 75), (35 + bx * 0.6, 84), (33 + bx, 91),
         (23 + bx, 89, 43 + bx, 95), prio=4, far=True)
    c.add(RR(41 + bx, 46, 54 + bx, 57, r=3.0, round_r=4.0), "shell", prio=2)
    _torso(c, [(28.0 + bx, 55.0), (67.0 + bx, 55.0), (62.0, 79.0), (33.0, 79.0)],
           (29.0 + bx, 53.5, 68.0 + bx, 60.5), pelvis=(30.0, 69.5, 66.0, 80.0))
    _leg(c, (55.5 + bx * 0.4, 75), (59 + bx * 0.6, 84), (60 + bx, 91),
         (50 + bx, 89, 70 + bx, 95), prio=6)
    _arm(c, (25.5 + bx, 60.0), (17 + bx * 1.4, 68.0), (13 + bx * 2, 78.0),
         hand_r=5.3, r0=5.8, r1=4.9, r2=4.2, prio=9,
         cap=(25.6 + bx, 58.5, 7.8, 6.9))
    if armed:
        _cannon(c, (65.0, 59.0), (83.0, 77.5), r=8.0, prio=16)
    _capacitor(c, 47.5 + bx, 66.0, cc, cell_w=3, gap=3, bh=6.4)
    _stump(c, 62.0 + bx, C_ARM_SOCKET[1] + 1, spray=spray)
    _helmet(c, 47.0 + hx, 33.5, rx=21.0, ry=13.0, jaw=(11.5, 4.0, 16.5),
            chin=41.5, pods=(6.0, 6.0), pod_y=5.5, vent=1)
    _face(c, FACE_BLINK, 33.0 + hx, 27.0, cc, mood="hit" if k == 0 else "dim")
    _finish(c)
    if k == 0:
        _sparks(c, 60, 58, ((-4, -6), (4, -6), (0, 6), (-7, 2), (7, 2)))
    return c


def build_armless_down(k=0):
    """The loop he lies in while the player picks the cannon up: on the mat, stump
    still arcing, one cell guttering."""
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    _floor(c, CHARGE["dead"], dy=(0.0, -1.0, 0.0)[k],
           eyes=("dim", "ember", "dim")[k], armless=True,
           spark=(30, 74) if k != 1 else (32, 72))
    return c


def build_scrapped(k=0):
    """The end.  A tidy heap of parts with his head sitting on top of it - a scrap
    pile, played for the joke, with ONE beat that is not: the grin is still on his
    face and a single ember will not quite go out.  That leaves the writing free to
    land either way; see the report."""
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    cc = CHARGE["dead"]
    sink = (0.0, 3.0, 5.0, 5.0)[k]

    # the heap: torso plate, a knee, a boot and a loose ear-pod, stacked not strewn
    c.add(RR(24, 80 + sink * 0.3, 62, 94, r=6.0, round_r=7.0), "armour", prio=3,
          bias=3)
    c.add(RR(30, 76 + sink * 0.4, 54, 86, r=5.0, round_r=6.0), "shell", prio=4,
          bias=2)
    c.add(E(64, 90, 7.0, 4.4), "armour", prio=5, bias=2)          # a boot
    c.add(E(20, 91, 5.6, 3.6), "armour", prio=5, bias=3)          # the other one
    c.add(E(70, 91.5, 4.0, 3.6), "shell", prio=6, bias=1)         # popped ear-pod
    c.add(E(70, 91.5, 2.0, 1.7), "dark", prio=7, flat=3)
    _capacitor(c, 40, 80 + sink * 0.4, cc, cell_w=3, gap=3, bh=5.2, prio=8)

    # the head, sat on top, antenna folded over
    hy = 62.0 + sink
    _antenna(c, [(34, hy - 8), (27, hy - 12), (20, hy - 9)],
             (17.0, hy - 7.6, 4.0), cc)
    _helmet(c, 36.0, hy, rx=17.0, ry=12.0, jaw=(9.5, 3.0, 13.5), chin=hy + 6.0,
            pods=(6.0, 3.2), pod_y=4.6, vent=1)
    _face(c, FACE_LOCK, 25.5, hy - 6.5, cc, mood="ember" if k >= 2 else "dim")
    _finish(c)
    if k == 1:
        _sparks(c, 48, 78, ((-6, -3), (6, -3), (0, -8)))
    if k >= 2:
        _steam(c, 58, 74)
    if k == 3:
        # the ember: one pixel that keeps going after everything else has stopped
        c.raw_px([PX(44, hy - 3), PX(45, hy - 3)], "#FF6A4E")
    return c


# If this ever fails, the overload has started aiming somewhere and stopped being an
# invitation.  Cheaper to catch here than in a playtest.
assert OVERLOAD_MUZZLE[1] >= OVERLOAD_AIM_ROW, (
    "the overload's muzzle has come up off the floor: %s" % (OVERLOAD_MUZZLE,))


# ===========================================================================
# POWERED DOWN, AND THE BOOT THAT GETS HIM OUT OF IT
# ===========================================================================
# THE ENTRANCE BEAT.  He is inert in the middle of the ring; Greyson's first shout
# does nothing, three seconds of dead air pass with a dead robot in the ring, and the
# second shout wakes him.  The joke only lands if he reads as SWITCHED OFF rather
# than merely dim, so three things go at once: the eye bars go dark, the antenna
# hangs instead of standing up off the crown, and nothing in the chassis carries its
# own weight any more.
#
# HE IS NOT DRAWN SAT ON THE MAT, and that was a deliberate call made by drawing it.
# Four seated poses were built and looked at - legs folded, legs straight out, sunk
# back on the heels, and a wide splay.  Every one of them collapses at 96x96: sitting
# stacks the torso, both legs, the pelvis and a barrel that is sixteen texels across
# into rows 70-95, and with no room between them the whole lower half reads as one
# purple-and-white pile.  The pose that DOES survive down there is _floor below, and
# it survives only because it is spread wide - head hard left, cannon hard right - and
# that silhouette is already spoken for: it is what being knocked over looks like, so
# borrowing it for the entrance would open the fight on his defeat pose.
# This instead keeps him on his feet and takes every prop away: knees buckled, spine
# folded forward, head hung off the front of the shoulders with no neck showing, both
# arms dead on their own weight and the cannon muzzle resting on the mat because he
# is no longer holding it up.  Crown to floor is 60 texels against the standing 75,
# so the silhouette is a fifth shorter and unmistakable beside the idle.
# ("sits in the middle of the arena" reads either way in the brief it came from - a
# posture, or the ordinary idiom for a thing parked somewhere.  If a literal seated
# pose is wanted anyway, say so: it is drawable, it just has to be a WIDE sprawl to
# read, and it will then look like he has already been knocked down.)
#
# THE POSE IS ONE PARAMETER.  u = 0 is the dead slump and u = 1 is build_idle frame
# 0's own rig, numbers copied from it, so the boot frames are this same drawing lerped
# toward the pose it hands over to and the cut into `idle` cannot pop.
DORMANT_CELL = (1, "#A34C3C", "#6E2A22", "#431A16", "#33201C", "#5A2420")

# Each entry is (the slump, the standing idle).  The right-hand column IS build_idle's
# frame 0 - if that pose is ever retuned, these have to be retyped with it or the boot
# will stop landing on it, and the drawing will still render while the cut into `idle`
# pops.  checks.py dormant_handover() measures the last boot frame against idle row 2
# frame 0 and fails if the step between them leaves 0-6 rows.
DORMANT_RIG = {
    "ant":    ([(34.0, 44.0), (24.0, 39.0), (18.0, 48.0)],
               [(38.0, 25.0), (30.0, 18.0), (24.0, 13.5)]),
    "ball":   ((16.0, 51.5, 3.9), (21.0, 11.4, 4.0)),
    "neck":   ((40.0, 58.0, 51.0, 68.0), (41.0, 46.0, 54.0, 57.0)),
    "quad":   ([(29.0, 66.0), (63.0, 63.0), (59.0, 83.0), (32.0, 85.0)],
               [(28.0, 55.0), (67.0, 55.0), (62.0, 79.0), (33.0, 79.0)]),
    "collar": ((29.5, 63.5, 64.0, 69.5), (29.0, 53.5, 68.0, 60.5)),
    "pelvis": ((30.0, 75.0, 62.0, 85.0), (30.0, 69.5, 66.0, 80.0)),
    # THE KNEES FALL INWARD AND THE FEET STAY APART.  A knee that buckles outward
    # arches both legs into the pelvis and the whole lower half goes to mush at this
    # size; knock-kneed puts a wedge of background back between the shins, and it is
    # also what legs actually do when they stop being held.
    "far":    (((40.0, 81.0), (44.0, 87.0), (36.0, 92.0), (27.0, 89.0, 45.0, 95.0)),
               ((39.5, 75.0), (37.5, 83.0), (37.0, 89.0), (27.5, 86.5, 46.0, 95.0))),
    "near":   (((53.0, 81.0), (51.0, 87.0), (59.0, 92.0), (50.0, 89.0, 68.0, 95.0)),
               ((55.5, 75.0), (57.5, 83.0), (58.0, 89.0), (49.5, 86.5, 68.0, 95.0))),
    "arm":    (((27.0, 68.0), (21.0, 78.0), (20.0, 88.0), (27.1, 66.5, 7.8, 6.9)),
               ((25.5, 60.0), (19.0, 70.0), (16.8, 80.5), (25.6, 58.5, 7.8, 6.9))),
    # the barrel is not being held up any more: it hangs until the muzzle is on the mat
    "gun":    (((66.0, 71.0), (77.0, 89.0)), ((65.0, 59.0), (83.0, 77.5))),
    "cap":    ((46.0, 75.0, 6.2), (47.5, 66.0, 6.4)),
    # cx, cy, rx, ry, jaw half-width / top / bottom, chin, both pods, pod_y
    "head":   ((45.0, 52.0, 19.0, 12.5, 10.0, 3.5, 14.5, 59.5, 6.0, 4.8, 5.0),
               (47.0, 33.5, 21.0, 13.0, 11.5, 4.0, 16.5, 41.5, 6.0, 6.0, 5.5)),
    "face":   ((31.0, 45.5), (33.0, 27.0)),
}

# u per frame, and the antenna's own u.  THE ANTENNA LEADS THE BODY on the wake-up:
# it is a whip with a weight on the end, so the jolt throws it most of the way up
# while the chassis has barely moved, and it settles back as he rises.  Animating it
# in step with the body instead makes the boot read as one rigid object tilting.
DORMANT_FRAMES = (
    #  u     antenna u  cell           eyes      face         sparks
    (0.00,   0.00,      None,          "dead",   "blink",     False),
    (0.10,   0.46,      "low",         "hit",    "front",     True),
    (0.46,   0.58,      "low",         "hit",    "front",     False),
    (0.82,   0.86,      "low",         "calm",   "front",     False),
)


def _lerp(a, b, u):
    """Walks the nested point tuples above, so a pose is interpolated whole."""
    if isinstance(a, (int, float)):
        return a + (b - a) * u
    return type(a)(_lerp(p, q, u) for p, q in zip(a, b))


def build_dormant(k=0):
    """Frame 0 is the dead slump the entrance holds; 1 is the jolt as the charge
    lands, 2 the push back up and 3 the last frame before `idle` takes over."""
    u, au, cell, eyes, face, spark = DORMANT_FRAMES[k]
    cc = DORMANT_CELL if cell is None else CHARGE[cell]
    c = Canvas(FRAME, FRAME, PAL, OUTLINE)
    g = {n: _lerp(lo, hi, u) for n, (lo, hi) in DORMANT_RIG.items()}

    _antenna(c, _lerp(DORMANT_RIG["ant"][0], DORMANT_RIG["ant"][1], au),
             _lerp(DORMANT_RIG["ball"][0], DORMANT_RIG["ball"][1], au), cc)

    # the back leg stays a step darker while the two are folded over each other;
    # once he is up they share the idle's single tone again
    hip, knee, ankle, foot = g["far"]
    _leg(c, hip, knee, ankle, foot, prio=4, far=u < 0.4)

    c.add(RR(g["neck"][0], g["neck"][1], g["neck"][2], g["neck"][3], r=3.0,
             round_r=4.0), "shell", prio=2)
    _torso(c, g["quad"], g["collar"], pelvis=g["pelvis"])

    hip, knee, ankle, foot = g["near"]
    _leg(c, hip, knee, ankle, foot, prio=6 if u < 0.4 else 4)

    sh, elbow, wrist, cap = g["arm"]
    _arm(c, sh, elbow, wrist, hand_r=5.3, r0=5.8, r1=4.9, r2=4.2, prio=6, cap=cap)

    _cannon(c, g["gun"][0], g["gun"][1], r=8.0, prio=16)
    _capacitor(c, g["cap"][0], g["cap"][1], cc, cell_w=3, gap=3, bh=g["cap"][2])

    h = g["head"]
    _helmet(c, h[0], h[1], rx=h[2], ry=h[3], jaw=(h[4], h[5], h[6]), chin=h[7],
            pods=(h[8], h[9]), pod_y=h[10], vent=1)
    _face(c, FACE_BLINK if face == "blink" else FACE_FRONT,
          g["face"][0], g["face"][1], cc, mood=eyes)

    _finish(c)
    if spark:
        _sparks(c, g["cap"][0], g["cap"][1] - 2,
                ((-17, -6), (-20, 1), (-16, 7), (16, -6), (19, 1), (15, 7),
                 (-10, -12), (10, -12), (0, 13)))
    return c


# The approved key frames, kept addressable on their own so golden/ can pin them.
POSES = {
    "computah_mm_idle": lambda: build_idle(0, CORE["key"]),
    "computah_mm_beam_charge": lambda: build_charge(True),
    "computah_mm_beam_ready": lambda: build_ready(True),
    "computah_mm_beam_charge_nofx": lambda: build_charge(False),
    "computah_mm_beam_ready_nofx": lambda: build_ready(False),
}

# Horizontal strips, frame 0 leftmost, vframes = 1, facing right.
#
# THE BATTERY COSTS NO EXTRA ART.  computah_idle and computah_run are each the same
# four-frame cycle emitted THREE TIMES, one per battery state, so the animation code
# reads `frame = charge_state * 4 + cycle_frame` with ROW 0 = FULL, row 1 half, row 2
# low.  Twelve frames each.  The chase clock is the battery and running it out is the
# only thing that ends a chase other than a catch, so the rows are load-bearing.
#
# `rows=True` marks the two sheets that do this.  Do not confuse it with the overload
# attack's own charge sheet, which is also 4x3 but runs the other way round - see the
# CHARGE table for both conventions side by side.
SHEETS = {
    "computah_idle": (build_idle, 4, True),
    "computah_run": (build_run, 4, True),
    # The entrance.  ONE ROW, NOT THREE: he is off, so there is no battery state to
    # read off him and `charge_rows` must be left off this sheet's anim entries.
    "computah_dormant": (build_dormant, 4, False),
    "computah_hit": (build_hit, 3, False),
    "computah_drop": (build_drop, 5, False),
    "computah_defeat": (build_defeat, 5, False),
    "computah_beam_fire": (build_fire, 3, False),
    "computah_beam_recover": (build_recover, 4, False),
    "computah_uppercut": (build_uppercut, 10, False),
    "computah_overload_brace": (build_overload_brace, 3, False),
    "computah_overload_release": (build_overload_release, 3, False),
    "computah_overload_break": (build_overload_break, 3, False),
    "computah_disarm": (build_disarm, 5, False),
    "computah_armless_down": (build_armless_down, 3, False),
    "computah_scrapped": (build_scrapped, 4, False),
}

# The overload's own charge sheet: 4 frames x 3 rows, ROW 0 BARELY CHARGED and ROW 2
# WHITE-HOT.  That is the OPPOSITE of computah_idle / computah_run, whose row 0 is a
# FULL battery.  It is emitted separately so the two conventions can never be read
# off one table by accident.
ROW_SHEETS = {
    "computah_overload_charge": (build_overload_charge, 4, 3),
}


# Where each pose's barrel ends, in FRAME texels.  C_MUZZLE is measured off
# `beam_ready`: that is the frame the beam spawns on.  C_MUZZLE_FIRE is per frame of
# computah_beam_fire, because the barrel is driven back into the shoulder on the
# recoil frame - a beam pinned to one fixed point detaches from it there.  All of it
# is derived from the same rig tuples the drawing uses, so it cannot go stale.
MUZZLE_RIG = {
    "idle": ((65.0, 59.0), (83.0, 77.5)),
    "beam_charge": ((43.0, 58.0), (69.0, 59.5)),
    "beam_ready": ((45.5, 54.5), (70.0, 54.5)),
    "beam_recover": ((47.0, 66.0), (66.0, 88.0)),
}


def _muzzle(sh, mz):
    ax, ay = mz[0] - sh[0], mz[1] - sh[1]
    L = math.hypot(ax, ay) or 1.0
    return (round((mz[0] + ax / L * 0.6) * K, 1),
            round((mz[1] + ay / L * 0.6) * K, 1))


def muzzle_points():
    out = {n: _muzzle(sh, mz) for n, (sh, mz) in MUZZLE_RIG.items()}
    out["beam_fire"] = [_muzzle(sh, mz) for sh, mz, _b, _h, _f in FIRE_RIG]
    return out


def _strip(fn, n, rows=False):
    from PIL import Image
    states = CHARGE_ROWS if rows else (None,)
    sheet = Image.new("RGBA", (FRAME * n * len(states), FRAME), (0, 0, 0, 0))
    i = 0
    for st in states:
        for k in range(n):
            im = fn(k) if st is None else fn(k, st)
            sheet.paste(im.to_image(), (i * FRAME, 0))
            i += 1
    return sheet


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    _set_frame(sys.argv[2] if len(sys.argv) > 2 else 96)
    bad = (_check(FACE_FRONT, True) + _check(FACE_BLINK, True)
           + _check(FACE_SCOWL, True) + _check(FACE_TURN, False)
           + _check(FACE_LOCK, False))
    if bad:
        print("face plates bad:" + "".join("\n  " + b for b in bad))
        sys.exit(1)
    prev = os.path.join(out, "preview")
    if not os.path.isdir(prev):
        os.makedirs(prev)
    for name, fn in POSES.items():
        im = fn().to_image()
        im.save(os.path.join(out, "%s.png" % name))
        im.resize((FRAME * 3, FRAME * 3)).save(
            os.path.join(prev, "%s_3x.png" % name))
        print("%-24s %dx%d  bbox=%s" % (name, FRAME, FRAME, im.getbbox()))
    for name, (fn, n, nrows) in ROW_SHEETS.items():
        from PIL import Image as _I
        sheet = _I.new("RGBA", (FRAME * n * nrows, FRAME), (0, 0, 0, 0))
        for row in range(nrows):
            for k in range(n):
                sheet.paste(fn(k, row).to_image(),
                            ((row * n + k) * FRAME, 0))
        sheet.save(os.path.join(out, "%s.png" % name))
        sheet.resize((sheet.width * 3, sheet.height * 3)).save(
            os.path.join(prev, "%s_3x.png" % name))
        print("%-24s %2d frames  %dx%d  (%d x %d rows, ROW 0 = BARELY CHARGED)"
              % (name, n * nrows, sheet.width, sheet.height, n, nrows))
    for name, (fn, n, rows) in SHEETS.items():
        sheet = _strip(fn, n, rows)
        sheet.save(os.path.join(out, "%s.png" % name))
        sheet.resize((sheet.width * 3, sheet.height * 3)).save(
            os.path.join(prev, "%s_3x.png" % name))
        print("%-24s %2d frames  %dx%d%s"
              % (name, sheet.width // FRAME, sheet.width, sheet.height,
                 "  (4 x full/half/low, row 0 = FULL)" if rows else ""))
    for k, v in sorted(muzzle_points().items()):
        print("muzzle  %-14s %s" % (k, v))
    print("ok")
