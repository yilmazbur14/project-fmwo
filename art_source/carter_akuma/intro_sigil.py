"""Carter's back emblem, redrawn bold and symmetrical.

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
                 erode, band)

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

# The one that ships.  B reads fastest at 3x: the crossbar gives it a strong
# horizontal to catch the eye, the three gaps between the prongs are the
# negative space that survives the flare, and the turned-up horns make it
# unmistakably a crest rather than a letter or a mark of punctuation.
sigil = sigil_trident


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
