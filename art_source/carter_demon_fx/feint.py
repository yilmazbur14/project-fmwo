"""demon_feint.png - the light over a FAKE clone: do not press.

The user (2026-09-24 playtest): "the symbol for a feint is the same as a dodge which is confusing for the
player." The fake clone wore the yellow hollow ring with a bar (demon_light.png frames 4-7), and the
game's shared DODGE tell (Assets/Effects/dodge_tell.png) is that same ring. So the feint gets a mark of
its own, and the three tells now split three ways:

  RED KITE with "!"        parry it        solid body, light glyph, tall
  YELLOW RING with a bar   dodge it        hollow, dark slot, wide
  PALE STEEL X             don't press     a stroke mark: no body, no hole, no glyph but itself

The X is told from both by silhouette (four diagonal arms with the gaps between them open, against a
convex kite and a closed ellipse), by colour (Carter's pale steel, against red and gold) and by what it
is made of (a mark, against a body and a ring). In greyscale it is the lightest of the three (Rec.601
~235 against the red body's ~126), so the parry/feint pair a colour-blind player actually has to split
in this fight is split by value as well as by shape.

It is drawn the way lights.py draws the other two - the same three-band shading lit from the upper
left (lights._shade, imported), the same black keyline - and plays the same four steps at the same
size, so it drops into the clone light's contract as a separate 24x24 x4 strip:
  0 ignite   small and hot, no shading yet, a few sparks
  1 peak     full size, the brightest, a spark thrown off each arm's end
  2 hold     THE READ. Held steady for the whole reaction window: never pulsed, never looped.
  3 fade     a step darker and a little smaller, only ever shown by a clone that has gone past
THE PIVOT IS THE FRAME CENTRE (12, 12), as demon_light's is: it sits on CLONE_LIGHT_ANCHOR.

Two alternatives are drawn here for the review only (octagon() and slashed()); only the X ships.
"""
import math

from fxlib import Mask, Cv, ell, poly, ramp, sheet, hexc
import lights

S = 24
C = 12.0
ST = ramp('steel')            # e6ecf2 bed6ff 9badb7 6b7c8c 44505c 242c36 - Carter's own steel
WHITE = hexc('ffffff')
BLACK = (0, 0, 0, 255)


def _bar(ang, length, thick, sc, cx=C, cy=C):
    """a straight stroke through the centre at `ang` degrees, square-ended"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    hl, ht = length * sc / 2.0, thick * sc / 2.0
    return poly(S, S, [(cx + ux * hl + px * ht, cy + uy * hl + py * ht),
                       (cx + ux * hl - px * ht, cy + uy * hl - py * ht),
                       (cx - ux * hl - px * ht, cy - uy * hl - py * ht),
                       (cx - ux * hl + px * ht, cy - uy * hl + py * ht)])


def _cross(sc, length=23.5, thick=5.6):
    return _bar(45, length, thick, sc) | _bar(135, length, thick, sc)


# stage -> (scale, base, dark, drim, lite)
_X_STAGES = {
    0: (0.55, WHITE, ST[0], ST[1], WHITE),
    1: (1.0, WHITE, ST[0], ST[2], WHITE),
    2: (1.0, ST[0], ST[1], ST[2], WHITE),
    3: (0.9, ST[2], ST[3], ST[4], ST[1]),
}


def cross(stage):
    """THE FEINT MARK: a bold pale-steel X"""
    cv = Cv(S, S)
    sc, base, dark, drim, lite = _X_STAGES[stage]
    body = _cross(sc)
    lights._shade(cv, body, base, dark, drim, lite)
    cv.outline(body, BLACK)
    if stage == 0:
        # igniting: a few sparks round it, like the others' ignite
        for x, y in ((0, -9), (0, 9), (-9, 0), (9, 0)):
            cv.set(int(C + x), int(C + y), ST[0])
    if stage == 1:
        # the peak throws a spark off the end of each arm, out along its diagonal
        for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            for r in (11.4, 12.4):
                x, y = int(C + dx * r / math.sqrt(2) + (0 if dx > 0 else -1)), int(C + dy * r / math.sqrt(2) + (0 if dy > 0 else -1))
                if 0 <= x < S and 0 <= y < S and cv.px[y][x] is None:
                    cv.set(x, y, WHITE if r < 12 else ST[0])
    return cv


# ------------------------------------------------------ review alternatives

def _octagon(r, sc):
    pts = []
    for i in range(8):
        a = math.radians(22.5 + i * 45)
        pts.append((C + math.cos(a) * r * sc, C + math.sin(a) * r * sc))
    return poly(S, S, pts)


def octagon(stage):
    """ALTERNATIVE B: a charcoal stop-octagon with a white X on it. Solid, like the red kite, and with
    the same polarity (a light glyph on a darker body), so it leans on silhouette and glyph alone"""
    cv = Cv(S, S)
    sc = {0: 0.58, 1: 1.0, 2: 1.0, 3: 0.92}[stage]
    body = _octagon(10.6, sc)
    if stage == 3:
        lights._shade(cv, body, ST[4], ST[5], ST[5], ST[3])
    else:
        lights._shade(cv, body, ST[3], ST[4], ST[5], ST[2])
    cv.outline(body, BLACK)
    if stage != 0:
        glyph = (_bar(45, 13.0, 2.6, sc) | _bar(135, 13.0, 2.6, sc)) & body.erode(2, diag=True)
        cv.paint(glyph, WHITE if stage != 3 else ST[1])
    return cv


def slashed(stage):
    """ALTERNATIVE C: a pale-steel slashed circle (the no-entry sign). Hollow like the yellow ring and
    crossed by a bar like it: only the colour and the angle of the bar differ from the dodge tell"""
    cv = Cv(S, S)
    sc = {0: 0.58, 1: 1.0, 2: 1.0, 3: 0.95}[stage]
    r_out, r_in = 10.2 * sc, 6.8 * sc
    ring = ell(S, S, C, C, r_out, r_out) - ell(S, S, C, C, r_in, r_in)
    slash = _bar(135, 2 * r_out - 1.0, 3.0, 1.0) & ell(S, S, C, C, r_out - 1.0, r_out - 1.0)
    body = ring | slash
    base = (WHITE, ST[0], ST[0], ST[2])[stage]
    lights._shade(cv, body, base, ST[1] if stage < 3 else ST[3], ST[2] if stage < 3 else ST[4],
                  WHITE if stage < 3 else ST[1])
    cv.outline(body, BLACK)
    return cv


def frames():
    """the shipped strip: ignite, peak, hold, fade"""
    return [cross(i) for i in range(4)]


def build(path):
    return sheet(frames(), path)
