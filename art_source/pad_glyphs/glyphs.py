"""glyphs.py - every gamepad glyph in the FMWO pad set (Assets/UI/Pad).

House rules shared with the keycaps (Assets/UI/key_*.png):
  * DawnBringer-32 only, 1px pure-black outline, light from the top-left;
  * the keycap plastic ramp  #FFFFFF / #CBDBFC / #9BADB7 / #696A6A;
  * every glyph stands on the keycaps' grey front lip (#847E87 / #696A6A /
    #595652), so pad prompts and keycaps carry the same visual weight;
  * glyph ink is the keycaps' navy #222034;
  * brass (#FBF236 / #D9A066 / #8A6F30) marks the input that is live - the
    same accent the hype meter and QTE key use.

Sizes land on an exact 3x in the ControlsScene slots: 32x32 -> 96x96,
96x64 -> 288x192 (the move card), 64x64 for the two legend-size extras.
The inline set (bottom of this file) is 11x11, shown at 3x = 33px, which is
Pixelify Sans's own 3-screen-pixel grain at the dialogue's 33px size.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from padlib import *
from bigfont import draw_big, draw_mid_text, draw_qmark, draw_mini, width, BIG, MID

LIGHT = (-0.7071, -0.7071)          # every glyph is lit from the top-left
LIP = (PL_LOW, PL_DARK, PL_DEEP)    # keycap front-lip ramp


# ----------------------------------------------------------------- helpers --
def dome(c, cx, cy, r, ramp, hi=WHITE, spec=0.86):
    """Round button read as a lit dome: bright crescent top-left, mid band,
    dark rim bottom-right."""
    face, mid, dark = ramp
    lx, ly = LIGHT
    for y in range(c.h):
        for x in range(c.w):
            fx, fy = (x + 0.5) - cx, (y + 0.5) - cy
            d = (fx * fx + fy * fy) ** 0.5
            if d > r:
                continue
            t = d / r
            l = 0.0 if d < 0.001 else (fx * lx + fy * ly) / d
            if t > 0.88:
                col = dark if l < 0.15 else (mid if l < 0.72 else face)
            elif t > 0.74:
                col = mid if l < -0.10 else (hi if l > spec - 0.06 else face)
            elif t > 0.55 and l > spec:
                col = hi
            elif t > 0.70 and l < -0.45:
                col = mid
            else:
                col = face
            c.set(x, y, col)


def plate(c, mask, ramp, hi=WHITE):
    """Shade a flat shape: 1px lit top/left edge, a mid band and a 1px dark
    bottom/right edge - the keycaps' own bevel."""
    face, mid, dark = ramp
    for (x, y) in list(mask):
        dn = (x, y + 1) not in mask
        rt = (x + 1, y) not in mask
        up = (x, y - 1) not in mask
        lf = (x - 1, y) not in mask
        dn2 = (x, y + 2) not in mask
        rt2 = (x + 2, y) not in mask
        if dn or rt:
            c.px[(x, y)] = dark
        elif dn2 or rt2:
            c.px[(x, y)] = mid
        elif up or lf:
            c.px[(x, y)] = hi
        else:
            c.px[(x, y)] = face


def lip(c, body, depth, brass_over=None):
    """Extrude `body` downward by `depth` px as the keycap-style front lip.
    Pixels under `brass_over` get the brass lip instead."""
    brass_over = brass_over or set()
    lp = set()
    for (x, y) in body:
        for k in range(1, depth + 1):
            p = (x, y + k)
            if p not in body:
                lp.add(p)
    for (x, y) in lp:
        # which body pixel is this lip under, and how far down?
        k = 1
        while (x, y - k) not in body and k <= depth:
            k += 1
        src = (x, y - k)
        right_edge = (x + 1, y) not in lp and (x + 1, y) not in body
        if src in brass_over:
            col = BR_LOW if (k == 1 and not right_edge) else BR_DARK
        else:
            col = LIP[0] if k == 1 else LIP[1]
            if right_edge or k >= 3:
                col = LIP[2]
        c.px[(x, y)] = col
    return lp


def rrect_mask(x0, y0, x1, y1, rad):
    m = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cx = x0 + rad if x < x0 + rad else (x1 - rad if x > x1 - rad else x)
            cy = y0 + rad if y < y0 + rad else (y1 - rad if y > y1 - rad else y)
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= rad * rad + rad * 0.6:
                m.add((x, y))
    return m


def disc_mask(cx, cy, r):
    m = set()
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = (x + .5) - cx, (y + .5) - cy
            if dx * dx + dy * dy <= r * r:
                m.add((x, y))
    return m


# ------------------------------------------------------------ face buttons --
# Xbox letters, because the user's pad is an XInput (Xbox-layout) controller
# and the code's text labels already say A/B/X/Y. Godot's JoyButton names are
# positional (A = bottom on every pad), so letter = JoyButton name.
FACE_SPEC = [
    ('down',  'A', RAMP_GREEN),
    ('right', 'B', RAMP_RED),
    ('left',  'X', RAMP_BLUE),
    ('up',    'Y', RAMP_YELLOW),
]


def _socket_button(c, cx, scy, bcy, r_sock, r_btn, ramp):
    """A domed button seated in a grey socket; the socket shows as a lip
    under the button, exactly where a keycap shows its lip."""
    sock = disc_mask(cx, scy, r_sock)
    for (x, y) in sock:
        dy = (y + .5) - scy
        c.px[(x, y)] = (LIP[0] if dy < r_sock * 0.45 else
                        (LIP[1] if dy < r_sock * 0.80 else LIP[2]))
    btn = C(c.w, c.h)
    dome(btn, cx, bcy, r_btn, ramp)
    for p, col in btn.px.items():
        c.px[p] = col
    c.inner_outline(set(btn.px.keys()), BLACK)
    return bcy


# ------------------------------------------------------------ lit / press --
# qte_key_q.png's lit frame is the model: the key is pressed 2px (its top
# drops, its bottom stays, so the lip shortens), its face turns gold, and
# little gold sparkle ticks float above it. Same rules here.
PRESS = 2
TO_BRASS = {PL_FACE: BR_HI, PL_MID: BR_MID, PL_DARK: BR_LOW, WHITE: WHITE}


def sparkles(c):
    """A centre dash over the top plus a ray off each upper corner, placed in
    the space every glyph leaves free once it is pressed 2px."""
    for p in [(15, 0), (16, 0), (5, 3), (6, 4), (26, 3), (25, 4)]:
        c.px[p] = BR_HI


def face_button(numeral, ramp, lit=False):
    c = C(32, 32)
    press = PRESS if lit else 0
    _socket_button(c, 16.0, 17.0, 14.0 + press, 14.4, 12.6,
                   RAMP_BRASS if lit else ramp)
    c.outline()
    draw_big(c, numeral, 16 - len(BIG[numeral][0]) // 2, 8 + press, NAVY)
    if lit:
        sparkles(c)
    return c


def face_diamond():
    """All four in the standard diamond - the legend for the numbering."""
    c = C(64, 64)
    pos = {'up': (32.0, 13.0), 'left': (13.0, 32.0),
           'right': (51.0, 32.0), 'down': (32.0, 51.0)}
    for name in ('up', 'left', 'right', 'down'):          # back to front
        num, ramp = {n: (k, r) for n, k, r in FACE_SPEC}[name]
        cx, cy = pos[name]
        b = C(64, 64)
        bcy = _socket_button(b, cx, cy + 0.8, cy - 1.8, 11.4, 9.9, ramp)
        b.outline()
        draw_big(b, num, int(cx) - len(BIG[num][0]) // 2, int(round(bcy - 6.5)), NAVY)
        c.blit(b, 0, 0)
    return c


# ------------------------------------------------------------------- d-pad --
DX0, DX1 = 10, 21          # vertical bar columns (12 wide)
DY0, DY1 = 1, 28           # vertical bar rows
DH0, DH1 = 9, 20           # horizontal bar rows (12 tall), centre row 14.5


def _cross_mask(dy=0):
    m = set()
    for y in range(DY0, DY1 + 1):
        for x in range(DX0, DX1 + 1):
            m.add((x, y + dy))
    for y in range(DH0, DH1 + 1):
        for x in range(1, 31):
            m.add((x, y + dy))
    for (cx, cy, sx, sy) in [(DX0, DY0, 1, 1), (DX1, DY0, -1, 1),
                             (DX0, DY1, 1, -1), (DX1, DY1, -1, -1),
                             (1, DH0, 1, 1), (30, DH0, -1, 1),
                             (1, DH1, 1, -1), (30, DH1, -1, -1)]:
        m.discard((cx, cy + dy)); m.discard((cx + sx, cy + dy)); m.discard((cx, cy + sy + dy))
    return m


def dpad(active=None, lit=None, mark_only=False):
    """active: None for the whole pad, or 'U' / 'D' / 'L' / 'R'.
    Standalone direction glyphs (lit=None) show the live arm in brass.
    mark_only=True is the at-rest atlas cell: grey cross, only the active
    arrow inked, the other three faded. lit=True is its pressed, gold,
    sparkling partner. The pressed cross drops 2px and loses its lip."""
    c = C(32, 32)
    dy = PRESS if lit else 0
    body = _cross_mask(dy)
    arm = set()
    if active:
        for (x, y) in body:
            yy = y - dy
            if ((active == 'U' and yy < DH0) or (active == 'D' and yy > DH1) or
                    (active == 'L' and x < DX0) or (active == 'R' and x > DX1)):
                arm.add((x, y))
    gold = active is not None and not mark_only
    if not lit:
        lip(c, body, 2, brass_over=arm if gold else set())
    plate(c, body, RAMP_PLASTIC, WHITE)
    # bevel the cross once, then re-ink only the live arm in brass: no seam
    # where the arm meets the hub, so it reads as one moulding, one arm lit
    if gold:
        for p in arm:
            c.px[p] = TO_BRASS[c.px[p]]
    c.outline()
    # embossed arrows, symmetric about x=15.5 and the cross's centre row
    for d in 'UDLR':
        ink = NAVY if (active is None or d == active) else PL_MID
        for i in range(5):
            for k in range(i + 1):
                if d == 'U':
                    c.set(15 - k, DY0 + 2 + i + dy, ink); c.set(16 + k, DY0 + 2 + i + dy, ink)
                elif d == 'D':
                    c.set(15 - k, DY1 - 2 - i + dy, ink); c.set(16 + k, DY1 - 2 - i + dy, ink)
                elif d == 'L':
                    c.set(3 + i, 14 - k + dy, ink); c.set(3 + i, 15 + k + dy, ink)
                else:
                    c.set(28 - i, 14 - k + dy, ink); c.set(28 - i, 15 + k + dy, ink)
    if lit:
        sparkles(c)
    return c


# -------------------------------------------------------------- left stick --
def stick(size=32, push=False, lip_px=None):
    """Top-down analog stick: a raised collar (standing on the keycap lip)
    around a recessed well, with the domed cap in it. push=True leans the cap
    right and lights that arc of the collar brass."""
    c = C(size, size)
    lp = lip_px if lip_px is not None else (2 if size <= 32 else 3)
    r_out = (size - 2 - lp) / 2.0
    cx, cy = size / 2.0, 1 + r_out
    rw = 3.0 if size <= 32 else max(3.0, 5.0 * size / 64.0)
    r_in = r_out - rw
    cap_r = r_in * 0.72
    off = (r_in - cap_r) * 0.95 if push else 0.0

    housing = disc_mask(cx, cy, r_out)
    brass_arc = set()
    if push:
        for (x, y) in housing:
            dx, dy = (x + .5) - cx, (y + .5) - cy
            if dx > 0 and abs(dy) < dx * 1.4:
                brass_arc.add((x, y))
    lip(c, housing, lp, brass_over=brass_arc)

    # recessed well
    for p in disc_mask(cx, cy, r_in):
        x, y = p
        dx, dy = (x + .5) - cx, (y + .5) - cy
        d = (dx * dx + dy * dy) ** .5
        l = 0.0 if d < .01 else (dx * LIGHT[0] + dy * LIGHT[1]) / d
        c.px[p] = INDIGO if (d > r_in - 1.6 and l < -0.25) else NAVY

    # collar
    ring = housing - disc_mask(cx, cy, r_in)
    for (x, y) in ring:
        dx, dy = (x + .5) - cx, (y + .5) - cy
        d = (dx * dx + dy * dy) ** .5
        l = 0.0 if d < .01 else (dx * LIGHT[0] + dy * LIGHT[1]) / d
        brass = (x, y) in brass_arc
        f, m, dk, hi = ((BR_HI, BR_MID, BR_LOW, BR_HI) if brass
                        else (PL_FACE, PL_MID, PL_DARK, WHITE))
        if d > r_out - 1.5:                       # outer wall
            col = hi if l > 0.35 else (dk if l < -0.35 else f)
        elif d < r_in + 1.5:                      # inner wall faces the other way
            col = dk if l > 0.20 else (f if l < -0.45 else m)
        else:
            col = f if l > 0.0 else m
        c.px[(x, y)] = col

    # cap
    ccx = cx + off
    cap = disc_mask(ccx, cy, cap_r)
    dome(c, ccx, cy, cap_r, RAMP_PLASTIC, spec=0.94)
    for (x, y) in cap:                            # dish groove
        dx, dy = (x + .5) - ccx, (y + .5) - cy
        d = (dx * dx + dy * dy) ** .5
        if cap_r * 0.62 < d <= cap_r * 0.62 + max(1.0, size / 96.0):
            l = 0.0 if d < .01 else (dx * LIGHT[0] + dy * LIGHT[1]) / d
            c.px[(x, y)] = PL_MID if l > -0.2 else PL_LOW
    c.inner_outline(cap, BLACK)
    c.outline()
    return c


# -------------------------------------------------- shoulders and triggers --
def bumper(side, lit=False):
    """Wide, shallow pill on a wider controller shoulder."""
    c = C(32, 32)
    dy = PRESS if lit else 0
    shoulder = rrect_mask(1, 20, 30, 29, 6)
    plate(c, shoulder, LIP, PL_MID)
    btn = rrect_mask(4, 3 + dy, 27, 20 + dy, 6)
    for p in btn:
        c.px[p] = PL_FACE
    plate(c, btn, RAMP_PLASTIC, WHITE)
    if lit:
        for p in btn:
            c.px[p] = TO_BRASS[c.px[p]]
    c.inner_outline(btn, BLACK)
    c.outline()
    label = side + 'B'
    draw_mid_text(c, label, 16 - width(MID, label, 2) // 2, 6 + dy, NAVY)
    if lit:
        sparkles(c)
    return c


def _paddle_mask(y0, y1, x0=4, x1=27, R=10.0):
    body = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if y < y0 + R:
                ccx = x0 + R if x < x0 + R else (x1 - R if x > x1 - R else x)
                dx, dy = x - ccx, y - (y0 + R)
                if dx * dx + dy * dy > R * R + R * 0.5:
                    continue
            body.add((x, y))
    for p in [(x0, y1), (x1, y1), (x0 + 1, y1), (x1 - 1, y1), (x0, y1 - 1), (x1, y1 - 1)]:
        body.discard(p)
    return body


def trigger(side, lit=False):
    """Tall tombstone paddle on the keycap lip. The lower band is the face
    curving away, carrying a brass 'pull' arrow. Its height is what tells it
    apart from the short, wide bumper. Pressed, it drops flush (no lip)."""
    c = C(32, 32)
    dy = PRESS if lit else 0
    body = _paddle_mask(1 + dy, 27 + dy)
    if not lit:
        lip(c, body, 2)
    plate(c, body, RAMP_PLASTIC, WHITE)
    for (x, y) in body:                           # lower face curving away
        if y >= 19 + dy and c.px[(x, y)] == PL_FACE:
            c.px[(x, y)] = PL_MID
        if y == 19 + dy and c.px[(x, y)] in (PL_MID, WHITE):
            c.px[(x, y)] = PL_FACE
    if lit:
        for p in body:
            c.px[p] = TO_BRASS[c.px[p]]
    c.outline()
    label = side + 'T'
    draw_mid_text(c, label, 16 - width(MID, label, 2) // 2, 6 + dy, NAVY)
    arrow = set()
    for i in range(5):
        for k in range(4 - i + 1):
            arrow.add((15 - k, 21 + i + dy)); arrow.add((16 + k, 21 + i + dy))
    for (x, y) in arrow:
        # on a gold paddle the pull arrow goes white-hot so it still reads
        c.px[(x, y)] = (WHITE if lit else BR_HI) if y < 24 + dy else (BR_HI if lit else BR_MID)
    c.inner_outline(arrow, NAVY)
    if lit:
        sparkles(c)
    return c


QMARK = [
    "..#####..",
    ".#######.",
    "###...###",
    "###...###",
    "......###",
    ".....###.",
    "....###..",
    "...###...",
    "...###...",
    ".........",
    ".........",
    "...###...",
    "...###...",
]


def fallback_button(lit=False):
    """The atlas's generic cell for any button without its own glyph
    (Back, Guide, L3, R3, Start in the atlas): a plain plastic button with
    a question mark, in the same socket as the face buttons."""
    c = C(32, 32)
    press = PRESS if lit else 0
    _socket_button(c, 16.0, 17.0, 14.0 + press, 14.4, 12.6,
                   RAMP_BRASS if lit else RAMP_PLASTIC)
    c.outline()
    for gy, row in enumerate(QMARK):
        for gx, v in enumerate(row):
            if v == '#':
                c.set(12 + gx, 8 + press + gy, NAVY)
    if lit:
        sparkles(c)
    return c


# ------------------------------------------------------------ start / menu --
def start_button(lit=False):
    """Small menu pill on a darker plateau. Pressed, it sinks 2px into the
    plateau (the lip below disappears, the plateau's rim shows above)."""
    c = C(32, 32)
    dy = PRESS if lit else 0
    plateau = rrect_mask(2, 8, 29, 24, 6)
    plate(c, plateau, LIP, PL_MID)
    btn = rrect_mask(4, 9 + dy, 27, 21 + dy, 5)
    for p in btn:
        c.px[p] = PL_FACE
    plate(c, btn, RAMP_PLASTIC, WHITE)
    if lit:
        for p in btn:
            c.px[p] = TO_BRASS[c.px[p]]
    c.inner_outline(btn, BLACK)
    c.outline()
    for yy in (11, 14, 17):
        for x in range(9, 23):
            c.set(x, yy + dy, NAVY); c.set(x, yy + dy + 1, NAVY)
    if lit:
        sparkles(c)
    return c


# ------------------------------------------------- movement card composite --
def move_card():
    """96x64 drop-in for Assets/UI/key_arrows.png: the left stick leaning,
    with the d-pad beside it as the alternative."""
    c = C(96, 64)
    c.blit(stick(56, push=True), 1, 4)
    c.blit(dpad(None), 62, 16)
    return c


# ============================================================================
# INLINE SET - 11x11 cells shown at 3x (33px), for glyphs inside dialogue text.
# Pixelify Sans is drawn at 33px = 3x its 11px design, so at 3x these cells
# share the text's exact pixel grain. Hand-authored grids: at 11px every pixel
# is placed on purpose. Same order as the atlas, plus Start at the end.
# ============================================================================
MINI_PAL = {
    'K': BLACK, 'N': NAVY, 'W': WHITE,
    'P': PL_FACE, 'M': PL_MID, 'D': PL_DARK, 'L': PL_LOW, 'E': PL_DEEP,
    'y': BR_HI, 'o': BR_MID, 'z': BR_LOW,
}

# round button in its socket; f/m/d = the button's own ramp, letter overlaid
MINI_ROUND = [
    "...KKKKK...",
    "..KWWffmK..",
    ".KWfffffmK.",
    "KWfffffffmK",
    "KffffffffmK",
    "KffffffffmK",
    "KmffffffmdK",
    "KLKmmmmdKLK",
    "KLLKKKKKLLK",
    ".KEEEEEEEK.",
    "..KKKKKKK..",
]
MINI_ROUND_LETTER_AT = (4, 2)

# bumper: wide, short pill on the lip
MINI_BUMPER = [
    "...........",
    "...........",
    ".KKKKKKKKK.",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KMMMMMMMMDK",
    "KLLLLLLLLEK",
    ".KKKKKKKKK.",
]
MINI_BUMPER_LABEL_AT = (2, 3)

# trigger: taller, round-shouldered paddle; lower band with the gold pull arrow
MINI_TRIGGER = [
    "..KKKKKKK..",
    ".KWPPPPPMK.",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KWPPPPPPPMK",
    "KMMMyyyMMDK",
    "KMMMMyMMMDK",
    "KLLLLLLLLEK",
    ".KKKKKKKKK.",
]
MINI_TRIGGER_LABEL_AT = (2, 2)

MINI_DPAD = [
    "...KKKKK...",
    "...KWPPK...",
    "...KPPMK...",
    "KKKKPPMKKKK",
    "KWPPPPPPPPK",
    "KPPPPPPPPMK",
    "KMMMPPPMMMK",
    "KKKKPPMKKKK",
    "...KPPMK...",
    "...KMMMK...",
    "...KKKKK...",
]
# the pixels of each arm, lit brass when that direction is the prompt
MINI_DPAD_ARM = {
    'U': {(x, y) for x in (4, 5, 6) for y in (1, 2, 3)},
    'D': {(x, y) for x in (4, 5, 6) for y in (7, 8, 9)},
    'L': {(x, y) for x in (1, 2, 3) for y in (4, 5, 6)},
    'R': {(x, y) for x in (7, 8, 9) for y in (4, 5, 6)},
}
MINI_TO_BRASS = {PL_FACE: BR_HI, WHITE: BR_HI, PL_MID: BR_MID, PL_DARK: BR_LOW}

MINI_START = [
    "...........",
    ".KKKKKKKKK.",
    "KWPPPPPPPMK",
    "KWPNNNNNPMK",
    "KWPPPPPPPMK",
    "KWPNNNNNPMK",
    "KWPPPPPPPMK",
    "KWPNNNNNPMK",
    "KMMMMMMMMDK",
    "KLLLLLLLLEK",
    ".KKKKKKKKK.",
]


def _grid(rows, subst=None):
    subst = subst or {}
    assert len(rows) == 11 and all(len(r) == 11 for r in rows), 'mini grids are 11x11'
    c = C(11, 11)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '.':
                continue
            c.px[(x, y)] = subst.get(ch) or MINI_PAL[ch]
    return c


def _mini_text(c, text, x, y):
    for ch in text:
        draw_mini(c, ch, x, y, NAVY)
        x += 4


def mini_face(letter, ramp):
    c = _grid(MINI_ROUND, {'f': ramp[0], 'm': ramp[1], 'd': ramp[2]})
    _mini_text(c, letter, *MINI_ROUND_LETTER_AT)
    return c


def mini_bumper(side):
    c = _grid(MINI_BUMPER)
    _mini_text(c, side + 'B', *MINI_BUMPER_LABEL_AT)
    return c


def mini_trigger(side):
    c = _grid(MINI_TRIGGER)
    _mini_text(c, side + 'T', *MINI_TRIGGER_LABEL_AT)
    return c


def mini_dpad(active):
    c = _grid(MINI_DPAD)
    for p in MINI_DPAD_ARM[active]:
        c.px[p] = MINI_TO_BRASS[c.px[p]]
    return c


def mini_fallback():
    c = _grid(MINI_ROUND, {'f': PL_FACE, 'm': PL_MID, 'd': PL_DARK})
    _mini_text(c, '?', *MINI_ROUND_LETTER_AT)
    return c


def mini_start():
    return _grid(MINI_START)


INLINE_COLUMNS = [
    ('A',          lambda: mini_face('A', RAMP_GREEN)),
    ('B',          lambda: mini_face('B', RAMP_RED)),
    ('X',          lambda: mini_face('X', RAMP_BLUE)),
    ('Y',          lambda: mini_face('Y', RAMP_YELLOW)),
    ('LB',         lambda: mini_bumper('L')),
    ('RB',         lambda: mini_bumper('R')),
    ('LT',         lambda: mini_trigger('L')),
    ('RT',         lambda: mini_trigger('R')),
    ('D-pad up',   lambda: mini_dpad('U')),
    ('D-pad down', lambda: mini_dpad('D')),
    ('D-pad left', lambda: mini_dpad('L')),
    ('D-pad right', lambda: mini_dpad('R')),
    ('?',          mini_fallback),
    ('Start',      mini_start),
]
