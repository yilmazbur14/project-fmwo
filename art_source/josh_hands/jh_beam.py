"""The finger-gun laser, its muzzle flash and its charge, cut to the addendum's art contract. Effects:
opaque, no keyline except on the little cards, his palette only - a white-hot core, his cream, and his
crimson and wine at the edges (the lanes' gold #FFD926 and the rune blue are never used). Drawn for the
RIGHT side's hand, so the beam runs LEFT; the left side's is the mirror.

  josh_gun_beam_start  16x20, 3 frames (0.05): the beam leaving the muzzle, white-hot at its right end.
                       Its right edge is the muzzle's column and its centre line the muzzle row.
  josh_gun_beam_tile   16x20, 3 frames (0.05), seamless left to right: the body, repeated to the rope.
  josh_gun_beam_end    16x20, 3 frames (0.05): the splash on the far rope; its LEFT edge is the rope.
  josh_gun_beam_glow   16x32, 3 frames (0.05), optional, additive: the halo, 6 texels above and below.
  All 20 texels tall = the hit band exactly (60 px); the band is solid edge to edge on every frame.

  josh_gun_flash       48x48, pivot (24, 24) on the muzzle, 4 frames (0.04, 0.05, 0.06, 0.08).
  josh_gun_charge_fx   32x32, pivot (16, 16) on the muzzle, 6 frames looping at 0.08 (optional): his cards
                       spiralling in to the fingertips, a hot bead pulsing there.
"""
import math

import jh_lib as H
import jh_cards as C
import jh_hand as HD

BW, BH = 16, 20
CYB = 10                       # the centre line (corner row)
BEAM_TIMES = [0.05, 0.05, 0.05]
FLASH_TIMES = [0.04, 0.05, 0.06, 0.08]
CHARGE_TIMES = [0.08] * 6

# the band, by distance from the centre line to the pixel's centre
BAND = [(3.5, 'W'), (4.5, '0'), (6.5, 'T'), (7.5, 'R'), (8.5, 'V'), (9.5, 'x')]


def band_key(d):
    for lim, k in BAND:
        if d <= lim + 1e-6:
            return k
    return None


def _ripple(x, f):
    """The core's edge shimmer: a column pattern with period 16 (seamless), shifted a third a frame."""
    return 1 if ((x - 5 * f) % 16) in (0, 1, 5, 9, 10, 13) else 0


def body(px, x0, x1, f, flow=True):
    for x in range(x0, x1):
        r = _ripple(x, f)
        for y in range(BH):
            d = abs(y + 0.5 - CYB)
            k = band_key(d)
            if r and 3.5 < d <= 4.5:
                k = 'W'                                    # the core bulging a row into the cream
            if r and 4.5 < d <= 5.5 and (x + f) % 2 == 0:
                k = '0'
            px[(x, y)] = k


def glints(px, x0, x1, f):
    """Suit pips riding the band: white on the crimson, one above and one below the core per tile,
    drifting left with the light."""
    for (base, cy, suit) in ((10, 3, 'diamond'), (2, 16, 'spade')):
        xx = (base - 5 * f) % 16
        rows = C.PIPS3[suit]
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == '.':
                    continue
                x = (xx + c) % 16
                q = (x0 + x, cy - 1 + r)
                if x0 <= q[0] < x1:
                    px[q] = 'W'


def tile_frames():
    out = []
    for f in range(3):
        px = {}
        body(px, 0, BW, f)
        glints(px, 0, BW, f)
        out.append(px)
    return out


def start_frames():
    out = []
    for f in range(3):
        px = {}
        body(px, 0, BW, f)
        glints(px, 0, 9, f)
        # white-hot where it leaves the fingertips: the right five columns burn through the cream and
        # the salmon, the edge rows stay dark so the band's edge never moves
        for x in range(11, BW):
            heat = (x - 10) / 5.0
            for y in range(BH):
                d = abs(y + 0.5 - CYB)
                if d <= 3.5 + 3.0 * heat:
                    px[(x, y)] = 'W' if d <= 2.5 + 3.5 * heat else '0'
        if f == 1:
            for y in (3, 16):
                px[(13, y)] = 'W'
        out.append(px)
    return out


def end_frames():
    out = []
    for f in range(3):
        px = {}
        body(px, 0, BW, f)
        # the splash on the rope: a white blot on the left columns, the full height of the band
        for x in range(0, 6):
            for y in range(BH):
                d = abs(y + 0.5 - CYB)
                lim = 9.5 - x * 1.2 + (f % 2) * 0.6
                if d <= lim:
                    px[(x, y)] = 'W' if d <= lim - 3.0 else ('0' if d <= lim - 1.5 else 'T')
        # rays thrown back along the band
        for (y, L) in ((2, 5 + f), (17, 6 - f), (5, 3 + f), (14, 4)):
            for x in range(4, 4 + L):
                if px.get((x, y)) not in ('W',):
                    px[(x, y)] = 'W' if x < 4 + L - 1 else '0'
        # a chip of card knocked off the rope: a little face, its pip a red dot
        cx, cy = (7, 4) if f == 0 else ((9, 3) if f == 1 else (8, 13))
        chip = {(cx + i, cy + j): '0' for i in range(3) for j in range(4)}
        chip[(cx + 1, cy + 1)] = 'R'
        chip[(cx + 1, cy + 2)] = 'R'
        for q, k in H.keyline(chip).items():
            if 0 <= q[0] < BW and 0 <= q[1] < BH:
                px[q] = k
        out.append(px)
    return out


def glow_frames():
    """The halo, additive: 6 texels above and below the 20-texel band, in crimson light."""
    out = []
    for f in range(3):
        g = {}
        for x in range(BW):
            wob = 1 if ((x - 5 * f) % 16) in (3, 4, 11) else 0
            for y in range(32):
                if 6 <= y <= 25:
                    continue
                d = (6 - y) if y < 6 else (y - 25)       # 1..6 texels out from the band
                if d <= 1 + wob:
                    g[(x, y)] = 'e'
                elif d <= 3 + wob:
                    g[(x, y)] = 'q'
        out.append(g)
    return out


# ------------------------------------------------------------------ the muzzle flash

def flash_frames():
    """48x48, the muzzle at the corner point (24, 24) = pixel centre (23.5, 23.5). The beam goes left, so
    the longest rays go left."""
    cx, cy = 23.5, 23.5
    out = []
    specs = [
        # core r, ray lengths (left, diag-left, up/down, diag-right, right), ring r, pips out
        (5.5, (22, 15, 12, 8, 7), 0, 0),
        (4.0, (16, 12, 10, 6, 5), 9, 6),
        (2.5, (9, 7, 6, 0, 0), 14, 12),
        (0.0, (0, 0, 0, 0, 0), 0, 17),
    ]
    for f, (core, rays, ring, pip_r) in enumerate(specs):
        px = {}
        if core:
            for y in range(48):
                for x in range(48):
                    d = math.hypot(x - cx, y - cy)
                    if d <= core:
                        px[(x, y)] = 'W'
                    elif d <= core + 1.5:
                        px[(x, y)] = '0'
        L, DL, UD, DR, R = rays
        for (ux, uy, n, w) in ((-1, 0, L, 1), (-1, -1, DL, 0), (-1, 1, DL, 0), (0, -1, UD, 0), (0, 1, UD, 0),
                               (1, -1, DR, 0), (1, 1, DR, 0), (1, 0, R, 0)):
            for t in range(int(core) + 1, n + 1):
                x, y = int(math.floor(cx + ux * t + 0.5)), int(math.floor(cy + uy * t + 0.5))
                k = 'W' if t <= n * 0.45 else ('0' if t <= n * 0.75 else 'T')
                px[(x, y)] = k
                if w and t <= n * 0.6:
                    px[(x, y - 1)] = '0'
                    px[(x, y + 1)] = '0'
        if ring:
            for a_i in range(180):
                a = 2 * math.pi * a_i / 180.0
                if (a_i // 12) % 3 == 2 and f >= 2:
                    continue
                x = int(math.floor(cx + math.cos(a) * ring + 0.5))
                y = int(math.floor(cy + math.sin(a) * ring * 0.85 + 0.5))
                px.setdefault((x, y), 'T' if f == 1 else 'R')
        if pip_r:
            for j, (deg, suit) in enumerate(((200, 'heart'), (160, 'spade'), (250, 'diamond'), (110, 'club'),
                                             (300, 'heart'), (60, 'spade'))):
                a = math.radians(deg)
                x = int(math.floor(cx + math.cos(a) * pip_r + 0.5))
                y = int(math.floor(cy + math.sin(a) * pip_r * 0.85 + 0.5))
                rows = C.PIPS3[suit]
                red = suit in ('heart', 'diamond')
                for r, row in enumerate(rows):
                    for c, ch in enumerate(row):
                        if ch != '.':
                            px[(x - 1 + c, y - 1 + r)] = ('R' if red else 'k') if f < 3 else ('T' if red else 'V')
                # a white rim so the black pips read on the green
                for r in range(-2, 3):
                    for c in range(-2, 3):
                        q = (x + c, y + r)
                        if q not in px and abs(r) + abs(c) <= 3 and f < 3:
                            px[q] = '0' if f < 2 else 'T'
        if f >= 2:
            for (sx, sy, big) in ((cx - 16, cy - 10, True), (cx - 12, cy + 12, False), (cx + 6, cy - 14, False)):
                q0 = (int(sx), int(sy))
                px[q0] = 'W'
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    px[(q0[0] + dx, q0[1] + dy)] = 'Y' if big else '0'
        out.append({q: k for q, k in px.items() if 0 <= q[0] < 48 and 0 <= q[1] < 48})
    return out


# ------------------------------------------------------------------ the charge

def charge_frames():
    """32x32, the muzzle at (16, 16): six of his cards on one inward spiral, spaced by their age so the
    loop closes (a card that reaches the tips is replaced by a new one at the rim); a hot bead pulsing."""
    cx, cy = 15.5, 15.5
    out = []
    n = 6
    for f in range(6):
        px = {}
        cards = []
        for k in range(n):
            age = ((k + f / 6.0) / n) % 1.0
            r = 14.0 - 10.0 * age
            th = math.radians(-60 + 450 * age)
            x = cx + math.cos(th) * r
            y = cy + math.sin(th) * r * 0.9
            size = 1.0 - 0.55 * age
            tang = math.degrees(th) + 90
            side = 'face' if k % 2 == 0 else 'back'
            cards.append((age, x, y, size, tang, side, HD.SUITS[k % 4]))
        # the bead first, then the cards over it, the oldest (nearest the tips) on top
        pulse = (2.6, 3.2, 3.8, 3.2, 2.6, 3.0)[f]
        for yy in range(32):
            for xx in range(32):
                d = math.hypot(xx - cx, yy - cy)
                if d <= pulse:
                    px[(xx, yy)] = 'W' if d <= pulse * 0.5 else ('0' if d <= pulse * 0.8 else 'T')
                elif d <= pulse + 1.2:
                    px[(xx, yy)] = 'R'
        for (age, x, y, size, tang, side, suit) in sorted(cards):
            w, h = 5.0 * size + 1.0, 7.0 * size + 1.5
            u = (math.cos(math.radians(tang)), math.sin(math.radians(tang)))
            p0 = (x - u[0] * h / 2, y - u[1] * h / 2)
            p1 = (x + u[0] * h / 2, y + u[1] * h / 2)
            cs = C.seg(p0, p1, w, w)
            part = C.quad(cs, 0 if side == 'face' else 1, side, suit if size > 0.8 and side == 'face' else None,
                          pip_big=False)
            for q, kk in part.items():
                if 0 <= q[0] < 32 and 0 <= q[1] < 32:
                    px[q] = kk
        # a streak of light behind each card on its way in
        for (age, x, y, size, tang, side, suit) in cards:
            dx, dy = cx - x, cy - y
            L = math.hypot(dx, dy) or 1.0
            for t in (2.0, 3.0):
                q = (int(math.floor(x - dx / L * t + 0.5)), int(math.floor(y - dy / L * t + 0.5)))
                if 0 <= q[0] < 32 and 0 <= q[1] < 32 and q not in px:
                    px[q] = 'T' if t == 2.0 else 'R'
        out.append(px)
    return out
