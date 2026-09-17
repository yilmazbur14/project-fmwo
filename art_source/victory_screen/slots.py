"""Rank ladder slot frames (40x40 cells, horizontal strip).
frame 0 LOCKED      opaque window with padlock
frame 1 CLEARED     brass ring, open window, green check badge
frame 2 CURRENT_A   blurple ring, open window, red '!' notification badge
frame 3 CURRENT_B   pulse frame: brighter ring + outer glow
frame 4 GOAL        gold ring with sparkles, open window, small padlock badge (the invite, not yet earned)
The window is a circle of radius WIN around the cell centre (20,20); icons sit UNDER the frame.
python slots.py outdir"""
import sys, math
from cv import *

S = 40
C0 = 20.0
WIN = 13.6      # window radius (pixel centres with d <= WIN are window)
IN_K = 14.7     # inner black line
RING = 17.6     # ring band
OUT_K = 18.7    # outer black line
GLOW = 19.8


def dist(x, y):
    return math.hypot(x + 0.5 - C0, y + 0.5 - C0)


def region(x, y):
    d = dist(x, y)
    if d <= WIN:
        return 'win'
    if d <= IN_K:
        return 'ink'
    if d <= RING:
        return 'ring'
    if d <= OUT_K:
        return 'outk'
    if d <= GLOW:
        return 'glow'
    return None


def ring_tone(x, y, ramp):
    """Tube-style ring like the UI kit's brass rods. ramp = 5 tones light->dark.
    Angular zones for the overall light (upper-left lit); the pixel line touching the
    outer black line is one step lighter on the lit half, the line touching the inner
    black line one step darker everywhere. Adjacency-based so the arcs stay clean."""
    ang = math.atan2(y + 0.5 - C0, x + 0.5 - C0)
    lit = math.cos(ang - math.radians(-135))
    if lit > 0.55:
        idx = 1
    elif lit > -0.2:
        idx = 2
    elif lit > -0.8:
        idx = 3
    else:
        idx = 3
    nb = [region(x + dx, y + dy) for dx, dy in N4]
    if 'outk' in nb and lit > -0.2:
        idx -= 1
    if 'ink' in nb:
        idx += 1
    return ramp[max(0, min(4, idx))]


def base_frame(ramp, window=None):
    cv = Canvas(S, S)
    for y in range(S):
        for x in range(S):
            r = region(x, y)
            if r in ('ink', 'outk'):
                cv.set(x, y, K)
            elif r == 'ring':
                cv.set(x, y, ring_tone(x, y, ramp))
            elif r == 'win' and window:
                cv.set(x, y, window)
    return cv


BADGE = [  # 11x11 round badge, 'F' fill, 'L' highlight, 'D' shade, 'k' outline
    "...kkkkk...",
    ".kkFFFFFkk.",
    ".kFLLFFFFk.",
    "kFLFFFFFFDk",
    "kFFFFFFFFDk",
    "kFFFFFFFFDk",
    "kFFFFFFFFDk",
    "kFFFFFFFDDk",
    ".kFFFFFDDk.",
    ".kkDDDDDkk.",
    "...kkkkk...",
]
CHECK = [
    ".......",
    "......w",
    ".....ww",
    "w...ww.",
    "ww.ww..",
    ".www...",
    "..w....",
]
BANG = [
    "ww",
    "ww",
    "ww",
    "ww",
    "..",
    "ww",
]
LOCK = [   # 11 x 13 padlock
    "...kkkkk...",
    "..kGGGGGk..",
    ".kGkkkkkGk.",
    ".kGk...kGk.",
    ".kGk...kGk.",
    "kkkkkkkkkkk",
    "kWYYYYYYYBk",
    "kYYYYkkYYBk",
    "kYYYYkkYYBk",
    "kYYYYYkYYBk",
    "kYYYYYkYYBk",
    "kBBBBBBBBBk",
    "kkkkkkkkkkk",
]
LOCK_S = [  # 7 x 9 small padlock badge
    "..kkk..",
    ".kGkGk.",
    ".kGkGk.",
    "kkkkkkk",
    "kYYYYBk",
    "kYYkYBk",
    "kYYYYBk",
    "kBBBBBk",
    "kkkkkkk",
]


def stamp(cv, rows, pal, ox, oy):
    cv.grid(rows, pal, ox, oy)


def badge(cv, ox, oy, fill, light, shade):
    stamp(cv, BADGE, {'k': K, 'F': fill, 'L': light, 'D': shade}, ox, oy)


def build():
    frames = []
    BRASS_R = (YEL, SKIN, TAN, BRASS, MUD)
    DARK_R = (GREY, DGREY, ASH, DASH, SLATE)
    BLUE_R = (WHITE, PALE, SKY, BLURPLE, INDIGO)
    BLUE_R2 = (WHITE, WHITE, PALE, SKY, BLURPLE)
    GOLD_R = (WHITE, YEL, YEL, TAN, BRASS)

    # 0 LOCKED
    f = base_frame(DARK_R, window=NAVY)
    for y in range(S):
        for x in range(S):
            if region(x, y) == 'win':
                d = math.hypot(x + 0.5 - C0 + 1.5, y + 0.5 - C0 + 1.5)
                if d > WIN - 0.2:
                    f.set(x, y, K)          # inner shadow top-left (recessed)
                elif (x + y) % 2 == 0 and dist(x, y) > WIN - 3:
                    f.set(x, y, NAVY)
    # recessed well: darker upper-left arc, faint indigo lower-right
    for y in range(S):
        for x in range(S):
            if region(x, y) == 'win':
                ang = math.atan2(y + 0.5 - C0, x + 0.5 - C0)
                lit = math.cos(ang - math.radians(-135))
                if dist(x, y) > WIN - 1.2 and lit < -0.3:
                    f.set(x, y, INDIGO)
    stamp(f, LOCK, {'k': K, 'G': DGREY, 'Y': TAN, 'W': SKIN, 'B': BRASS}, 15, 13)
    frames.append(f)

    # 1 CLEARED
    f = base_frame(BRASS_R)
    badge(f, 28, 28, GREEN, LIME, TEAL)
    stamp(f, CHECK, {'w': WHITE}, 30, 29)
    frames.append(f)

    # 2 CURRENT_A
    f = base_frame(BLUE_R)
    badge(f, 28, 1, RED, PINK, BROWN)
    stamp(f, BANG, {'w': WHITE}, 32, 3)
    frames.append(f)

    # 3 CURRENT_B (pulse)
    f = base_frame(BLUE_R2)
    for y in range(S):
        for x in range(S):
            if region(x, y) == 'glow' and (x + y) % 2 == 0:
                f.set(x, y, SKY)
    badge(f, 28, 1, PINK, WHITE, RED)
    stamp(f, BANG, {'w': WHITE}, 32, 3)
    frames.append(f)

    # 4 GOAL (invite, not yet earned)
    f = base_frame(GOLD_R)
    for (sx, sy) in [(3, 5), (34, 33)]:
        stamp(f, ["..w..", ".wYw.", "wYWYw", ".wYw.", "..w.."], {'w': YEL, 'Y': WHITE, 'W': WHITE}, sx, sy)
    stamp(f, LOCK_S, {'k': K, 'G': DGREY, 'Y': TAN, 'B': BRASS}, 30, 29)
    frames.append(f)
    return frames


def strip(frames):
    out = Canvas(S * len(frames), S)
    for i, f in enumerate(frames):
        out.blit(f, i * S, 0)
    return out


# ---------------- connectors between slots ----------------
LW = 8


def links():
    """8x40 cells, bar centred on the ring centre line (rows 18..21 + outline).
    0 LOCKED (dark dashes), 1 CLEARED (brass rod), 2 NEXT (blurple rod with a white chevron)."""
    fr = []
    # LOCKED
    f = Canvas(LW, S)
    for x in range(0, 5):
        f.set(x, 17, K)
        f.set(x, 18, DASH)
        f.set(x, 19, ASH)
        f.set(x, 20, SLATE)
        f.set(x, 21, K)
    for y in range(17, 22):
        f.set(5, y, K)
    fr.append(f)
    # CLEARED
    f = Canvas(LW, S)
    for x in range(LW):
        for y, c in zip(range(17, 22), [K, YEL, TAN, '8a6f30', K]):
            f.set(x, y, c)
    fr.append(f)
    # NEXT
    f = Canvas(LW, S)
    for x in range(LW):
        for y, c in zip(range(17, 22), [K, SKY, BLURPLE, INDIGO, K]):
            f.set(x, y, c)
    f.grid(["W..", ".W.", "..W", ".W.", "W.."], {'W': WHITE}, 3, 17)
    fr.append(f)
    return fr


def link_strip():
    fr = links()
    out = Canvas(LW * len(fr), S)
    for i, f in enumerate(fr):
        out.blit(f, i * LW, 0)
    return out


if __name__ == '__main__':
    od = sys.argv[1].rstrip('/') + '/'
    fr = build()
    strip(fr).save(od + 'rank_slot.png')
    link_strip().save(od + 'rank_link.png')
    print('ok', len(fr))
