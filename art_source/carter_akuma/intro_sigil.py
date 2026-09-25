"""Carter's back emblem.

WHAT SHIPS NOW (2026-09-23): the kanji 天, "heaven" - Akuma's own mark, at the
user's request, replacing the original trident below.  It is sigil_ten() at the
bottom of this file, and it is drawn at this size rather than traced from
anything: four brush strokes, each one closed outline, with a slanted brush
entry and a lifted end on both horizontals, the left sweep thick at the top and
tapering to a point low-left, and the right sweep widening into a blunt tail.
It is painted flat - one vermilion and one darker red on the side away from the
light - by paint_rest(), and the flare, the bloom and the overlay are unchanged:
they take whatever shape this file returns.

The rest of this docstring is the history of the ORIGINAL emblem, kept with the
candidates it describes.

The first pass was a loose hooked squiggle - an unclosed enso cut by a slash.
It carried the right idea but at 3x it read as a scribble.

These are deliberate emblems, built to three rules learned from the first
attempt, where every candidate collapsed into an insect:
  * two or three elements, never more - detail turns to mush at 29px wide
  * strokes of 5px, so they hold up at 3x and survive the flare blowing out
  * one big piece of negative space, so the shape is still there when the
    middle goes white
Symmetry is forced on the finished mask because the scanline rasteriser is not
exactly mirror-safe.  All three keep the original meaning: a circle he has
broken out of, and the thing that broke it.
"""
from lib import (W, H, poly, ell, union, inter, sub, mirror, empty, grow,
                 erode, band, PALC)

AX = 47.5


def sym(m):
    """mirror about the spine: lib.mirror maps x -> 95 - x, axis 47.5"""
    return union(m, mirror(m))


# ------------------------------------------------------------------ A: halo
# A heavy ring broken at ten and two, so the break itself makes the horns, with
# a single fang hanging free inside it.  The ring is what you read across the
# arena; the fang is what you read up close.

def sigil_halo():
    ring = sub(ell(AX, 56.4, 14.2, 12.6), ell(AX, 56.4, 9.3, 8.0))
    # ONE wide gap across the top, not two notches: the ends it leaves behind
    # are what become the horns, so the break reads as a break
    ring = sub(ring, poly([(37.6, 38.0), (57.4, 38.0), (57.4, 50.6), (37.6, 50.6)]))
    horn = poly([(33.4, 51.4), (31.0, 43.6), (35.4, 42.2), (38.4, 49.4),
                 (38.4, 52.2)])
    fang = poly([(43.8, 51.2), (51.2, 51.2), (47.5, 63.4)])
    return sym(union(union(ring, sym(horn)), fang))


# ------------------------------------------------------------------ B: trident
# A crossbar with three fangs hanging off it and horns turned up at the ends.
# The most brutal of the three and the one that survives smallest.

def sigil_trident():
    # laid out to fit INSIDE the back panel: the jacket only reaches x 30..65
    # around row 42 and tears into a ragged hem past row 72, so horns that go
    # any higher or prongs any lower get clipped off by the cloth
    # The whole emblem lives between rows 41 and 62: the rope belt is drawn
    # over the jacket at rows 63-68 and lopped the centre prong off, and the
    # back panel narrows to x 38-57 above row 41, which clipped the horns.
    bar = poly([(33.0, 44.8), (62.0, 44.8), (62.0, 50.0), (33.0, 50.0)])
    horn = poly([(33.2, 49.6), (31.4, 42.4), (35.6, 41.2), (38.4, 47.6),
                 (38.4, 50.0)])
    prong_c = poly([(44.3, 49.4), (50.7, 49.4), (50.7, 56.6), (47.5, 62.2),
                    (44.3, 56.6)])
    prong_s = poly([(35.6, 49.4), (41.0, 49.4), (41.0, 54.4), (38.3, 59.0),
                    (35.6, 54.4)])
    return sym(union(union(bar, sym(horn)), union(prong_c, sym(prong_s))))


# ------------------------------------------------------------------ C: cleft
# A diamond cut open top and bottom with a slit floating at its heart.

def sigil_cleft():
    out = poly([(AX, 41.0), (63.8, 56.0), (AX, 71.0), (31.2, 56.0)])
    inn = poly([(AX, 49.4), (54.8, 56.0), (AX, 62.6), (40.2, 56.0)])
    dia = sub(out, inn)
    # cut the top and bottom points open so it is a cleft, not a lozenge
    dia = sub(dia, poly([(43.6, 38.0), (51.4, 38.0), (51.4, 45.4), (43.6, 45.4)]))
    dia = sub(dia, poly([(43.6, 66.6), (51.4, 66.6), (51.4, 74.0), (43.6, 74.0)]))
    # a small slit floating clear of the walls - a fat one just fills the void
    slit = poly([(42.8, 53.6), (52.2, 53.6), (52.2, 58.4), (42.8, 58.4)])
    return sym(union(dia, slit))


CANDIDATES = [('A halo', sigil_halo),
              ('B trident', sigil_trident),
              ('C cleft', sigil_cleft)]

# The one that shipped until 2026-09-23.  B reads fastest at 3x: the crossbar
# gives it a strong horizontal to catch the eye, the three gaps between the
# prongs are the negative space that survives the flare, and the turned-up horns
# make it unmistakably a crest rather than a letter or a mark of punctuation.
# Superseded by sigil_ten below, which is what `sigil` is bound to.  The shipped
# trident sheets can still be rebuilt exactly: restamp_mark.OLD binds the
# trident, its bevelled paint and intro_lib.DARK_EDGE back together.


# ------------------------------------------------------------------ 天
# The mark that ships: Akuma's 天, "heaven", in red brush across the upper back.
#
# The room it has decides everything about it.  On the approved back view the
# visible gi between the collar and the rope belt is 15 rows deep at the spine -
# the neck covers the middle of row 53 and the belt starts on row 68 - and 29
# columns wide between the armholes.  So this 天 is 32x15 px at the shipping
# scale: squat, because the space is, with every stroke placed on purpose:
#   * both horizontals rise into the right: a slanted brush entry low-left and
#     a lifted end, rather than a staircase through the middle of the stroke
#   * the long stroke is 4 rows thick and the short one 3: sigil_paint lights a
#     stroke from the inside out (white only two pixels in), so a thinner one
#     never reaches the white at the peak
#   * one pixel of gi is left between the long stroke and each armhole, so it
#     sits on the cloth rather than running under his arms
#   * the long stroke's end is split by one pixel - the dry brush running out
#   * the left sweep bellies out to 8 px under the long stroke and tapers to its
#     point, like a scythe blade, instead of running as an even diagonal.  It
#     also needs that width to burn: a 5 px diagonal stepping 3 px a row has no
#     inside for sigil_paint's hot core
#   * the right sweep widens 2 -> 7 px into a blunt tail on the belt line
#
# The outlines are written in the PIXELS of the shipping sprite (scale 0.84,
# integer = pixel corner, so a pixel is (x, y) to (x + 1, y + 1)), because that
# is where a 32 px kanji has to be placed - and they are converted back to
# design space at that FIXED factor, not at lib.SCALE, so the emblem still
# scales with him if his size ever changes.  Each outline was fitted so that
# lib.poly's centre sampling lands on exactly the drawn pixels at 0.84 (every
# crossing sits half a pixel from the nearest pixel centre), with as few
# vertices as that allows, which is also what keeps it clean when
# carter_demon_fx/finish.py re-rasterises the same outlines at 3x.
#
# The 天 is not symmetric, so unlike the candidates above nothing here goes
# through sym().

AUTHORED_AT = 0.84             # carter_scale.SCALE when these were fitted
_ANCHOR = (47.5, 96.0)         # carter_scale.ANCHOR: the spine on the floor

TEN_STROKES = [
    # 1  the short top stroke: slanted entry, end lifted into row 53
    [(53, 53), (56, 53), (56, 53.5), (57, 54.5), (57, 55.5), (55, 56.5),
     (55, 57), (40, 57), (40, 56.5), (42, 54.5), (53, 53.5)],
    # 2  the long second stroke: pointed entry, lifted end split by dry brush
    [(58, 57), (60, 57), (60, 57.5), (61, 58.5), (60, 59.5), (61, 60.5),
     (58, 61.5), (58, 62), (35, 62), (35, 61.5), (34, 60.5), (36, 58.5),
     (58, 57.5)],
    # 3  the left sweep: from under the top stroke, straight down through the
    #    second, then out to the point low-left
    [(46, 54), (50, 54), (50, 54.5), (50, 62.5), (49, 63.5), (47, 64.5),
     (41, 66.5), (37, 67.5), (37, 68), (32, 68), (32, 67.5), (36, 65.5),
     (42, 63.5), (46, 61.5), (46, 54.5)],
    # 4  the right sweep: out of the left one under the second stroke, down to
    #    a blunt tail
    [(48, 60), (51, 60), (51, 60.5), (51, 61.5), (52, 62.5), (58, 64.5),
     (62, 66.5), (63, 67.5), (63, 68), (56, 68), (56, 67.5), (48, 60.5)],
]


def _design(pts):
    ax, ay = _ANCHOR
    return [(ax + (x - ax) / AUTHORED_AT, ay + (y - ay) / AUTHORED_AT)
            for x, y in pts]


def sigil_ten():
    """天, one closed outline per brush stroke.  `poly` is looked up at call
    time on purpose: carter_demon_fx/finish.py points it at a 3x wrapper."""
    m = poly(_design(TEN_STROKES[0]))
    for pts in TEN_STROKES[1:]:
        m = union(m, poly(_design(pts)))
    return m


sigil = sigil_ten


def paint_rest(cv, sg):
    """The mark at rest, as paint on the gi: flat vermilion, with ONE darker red
    on the edge pixels that face down or right - the side away from the rig's
    upper-left light - so the strokes stay separate where they cross without an
    outline eating a stroke that is only three or four pixels thick.

    This is the approved back view's own look.  The burning states repaint the
    same mask through intro_lib.sigil_paint, whose ramp is unchanged."""
    cv.paint(sg, PALC['y'])
    for y in range(H):
        for x in range(W):
            if sg[y][x] and ((y + 1 < H and not sg[y + 1][x]) or
                             (x + 1 < W and not sg[y][x + 1])):
                cv.px[y][x] = PALC['Y']


def check_symmetry(m):
    return sum(1 for y in range(H) for x in range(W) if m[y][x] != m[y][95 - x])


def bbox(m):
    xs = [x for y in range(H) for x in range(W) if m[y][x]]
    ys = [y for y in range(H) for x in range(W) if m[y][x]]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def stroke_stats(m):
    """distribution of horizontal run lengths, ignoring the 1-2px tapers at
    points - the bulk of the emblem wants to be 4px or more"""
    runs = []
    for y in range(H):
        run = 0
        for x in range(W + 1):
            if x < W and m[y][x]:
                run += 1
            else:
                if run:
                    runs.append(run)
                run = 0
    runs.sort()
    fat = sum(1 for r in runs if r >= 4)
    return len(runs), runs[len(runs) // 2], fat * 100 // max(1, len(runs))
