"""demon_light.png - the light over a rushing clone's head.

RED = parry it.  YELLOW = fake, do not parry.  This is a reaction test read in
a fifth of a second, possibly by someone who cannot tell red from yellow, so
the two are separated four independent ways and colour is only one of them:

  1. SILHOUETTE   pointed vs round.  Red is a blade - a kite with a long spike
                  hanging off the bottom, taller than it is wide, aimed down at
                  the player.  Yellow is a flat ring, wider than it is tall.
                  The aspect ratios are opposite, so the two disagree even in
                  peripheral vision before either shape is resolved.
  2. SOLID/HOLLOW Red is a filled body.  Yellow is hollow - crescents of empty
                  space survive inside it and the dark arena shows through.
                  Nothing about the red light has a hole in it.
  3. GLYPH        a vertical "!" against a horizontal bar.  The strokes are
                  orthogonal, so if everything else is lost to motion the marks
                  still disagree.
  4. POLARITY     red is a light glyph on a dark body, yellow a dark glyph on a
                  light body.  Inverted, which also makes the greyscale gap
                  large: the red body sits near luma 120, the yellow near 200.

The red side is deliberately the diamond-and-exclamation of
Assets/Effects/parry_tell.png - the player has already been taught that mark
means "parry now" and the demon sequence should not teach it twice.  Drawing it
as a blade rather than a symmetric diamond is the only change, and it is what
says "this one is coming at your face".
The yellow side borrows the road sign everyone already knows: a bar across a
circle, meaning do not.

An earlier pass put thorns along the diamond's facets.  They filled in the
concave corners between the four tips and the whole thing read as a lumpy red
rectangle - the silhouette that was supposed to be the main tell was the first
thing lost.  Anything added to these shapes has to hang OFF the outline, never
sit on it.
"""
import math
from fxlib import (Mask, Cv, ell, rect, poly, ramp, sheet, hexc)

S = 24                     # texel size of one light
C = 12.0                   # centre, and the axis Mask.sym4() mirrors about
CY = 11.0                  # the blade's centre of scale

EM = ramp('ember')         # ffe2c0 ff9a6a ff4a3c c01830 780c28 440618
GO = ramp('gold')          # fffce0 ffe45c ffc21e d68a12 8a5208 4a2a04
WHITE = hexc('ffffff')
PINK = hexc('ffd2d8')
BLACK = (0, 0, 0, 255)

# "!"  - stem, gap, dot, sat in the wide upper half of the blade
BANG = """
##
##
##
##
##
##
##
..
##
##
"""


def _shade(cv, body, base, dark, drim, lite):
    """light from the upper left.  Three bands only: a small shape drowns in
    more than that, which is what went wrong on the first pass."""
    cv.paint(body, base)
    cv.paint(body - body.shift(-2, -2), dark)      # lower-right, 2px
    cv.paint(body - body.shift(-1, -1), drim)      # lower-right rim, 1px
    cv.paint(body - body.shift(1, 1), lite)        # upper-left rim, 1px


# ------------------------------------------------------------------- RED

def _blade(sc=1.0):
    """kite: short shoulders, long spike down"""
    pts = [(C, 2.0), (C + 7.5, 9.6), (C, 22.0), (C - 7.5, 9.6)]
    return poly(S, S, [(C + (x - C) * sc, CY + (y - CY) * sc) for x, y in pts])


def _wings():
    """two chevrons hanging clear of the blade - never touching it, so the
    kite silhouette stays intact"""
    m = Mask(S, S)
    w = poly(S, S, [(21.8, 4.6), (22.9, 5.6), (20.4, 11.6), (19.6, 10.4)])
    return (m | w).sym()


def red(stage):
    """stage 0 ignite / 1 peak / 2 hold / 3 fade"""
    cv = Cv(S, S)
    sc = {0: 0.55, 1: 1.0, 2: 1.0, 3: 0.9}[stage]
    body = _blade(sc)

    if stage == 0:            # ignite: hot and pale, no mark yet
        _shade(cv, body, EM[1], EM[2], EM[3], EM[0])
    elif stage == 1:          # peak: brighter than the hold but still RED -
        # lifting the base to EM[1] turned it salmon and lost the colour cue
        _shade(cv, body, EM[2], EM[3], EM[3], EM[0])
    elif stage == 2:          # hold: the frame the player actually reads
        _shade(cv, body, EM[2], EM[3], EM[4], EM[1])
    else:                     # fade
        _shade(cv, body, EM[3], EM[4], EM[5], EM[2])
    cv.outline(body, BLACK)

    if stage == 1:            # wings only at the peak, drawn as their own body
        wg = _wings()
        cv.paint(wg, EM[1])
        cv.paint(wg - wg.shift(-1, -1), EM[3])
        cv.outline(wg, BLACK)

    if stage != 0:
        g = Mask(S, S)
        for dy, row in enumerate(BANG.strip('\n').split('\n')):
            for dx, ch in enumerate(row):
                if ch != '.':
                    g.g[4 + dy][11 + dx] = True
        cv.paint(g & body, WHITE if stage != 3 else PINK)

    if stage in (0, 1):       # sparks flung off the points
        r = 12 if stage == 1 else 8
        for x, y in ((0, -r), (0, r), (-r - 1, -1), (r + 1, -1),
                     (-7, -7), (7, -7), (-6, 7), (6, 7)):
            cv.set(int(C + x), int(CY + y), EM[0] if stage else WHITE)
    return cv


# ----------------------------------------------------------------- YELLOW

def yellow(stage):
    cv = Cv(S, S)
    sc = {0: 0.58, 1: 1.0, 2: 1.0, 3: 0.95}[stage]
    # the hole has to survive TWO black outlines across its height (its own and
    # the bar's) and still leave open pixels, or the "hollow" tell is lost and
    # the light reads as a solid disc.  That sets the minimum hole height at
    # about 12 texels, which in turn sets everything else.
    rx, ry = 11.0 * sc, 9.0 * sc
    ix, iy = 7.4 * sc, 6.1 * sc

    outer = ell(S, S, C, C, rx, ry)
    hole = ell(S, S, C, C, ix, iy)
    ringm = outer - hole
    # the bar crosses the walls so it reads as the road sign, but stops one
    # pixel short of the outline so the ring still closes all the way round
    bar = rect(S, S, 0.0, C - 1.3, float(S), C + 1.3) & outer.erode(1)
    body = ringm | bar

    # the hold frame is kept as bright as the peak on purpose.  Two reasons:
    # a tell that flickers during the reaction window is a tell the player
    # re-reads instead of acting on, and the body's mean luma is the thing
    # carrying the difference from the red light for a colour-blind player -
    # dropping a step here closed that gap from 63 to 31.
    if stage in (0, 1, 2):
        _shade(cv, body, GO[1], GO[2], GO[3], GO[0])
    else:
        _shade(cv, body, GO[3], GO[4], GO[5], GO[2])

    if stage == 3:            # the ring breaks into dashes as it dies
        cv.erase((outer - outer.erode(2)).dither(5, off=2))

    cv.outline(body, BLACK)

    # the mark: a dark slot straight through the disc, drawn last so the
    # outline pass cannot eat it
    slot = bar.erode(1)
    cv.paint(slot, GO[5])
    cv.paint(slot - slot.shift(0, 1), GO[4])

    if stage in (0, 1):       # a soft halo, round like everything else here
        r = 13 if stage == 1 else 9
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            cv.set(int(C + math.cos(a) * r * 1.22),
                   int(C + math.sin(a) * r * 0.98), GO[0])
    return cv


def build(path):
    frames = [red(i) for i in range(4)] + [yellow(i) for i in range(4)]
    return sheet(frames, path)
