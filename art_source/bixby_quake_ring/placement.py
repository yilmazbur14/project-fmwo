"""Where the quake ring's segments go: the rule the ring script should follow, and that the mocks use.

The ring is the ellipse P(theta) = (R cos theta, FLOOR_FLATTEN * R sin theta) around his feet, in screen px,
y down, so theta = 90 degrees is its front (nearest the camera) and 0 its right-hand side.

1. SPACE BY SCREEN ARC LENGTH, not by floor angle. Floor-angle spacing puts pivots 3x closer together up the
   sides than across the front (0.36 x the floor spacing), which is what piled the old tiles into clumps.
   N = 4 * max(1, round(perimeter / (4 * SPACING))) pivots, evenly spaced in arc length, starting at the
   front centre. N is a multiple of 4, so there is always a pivot on the front, back and both side points and
   the ring is symmetric. The arc-length table G is the same for every radius (it scales with R), so it is
   built once.
2. PICK THE VARIANT from the screen tangent there, phi = atan(0.36 |cos theta| / |sin theta|), 0 at the
   front and back, 90 at the sides, using BUCKETS.
3. FLIP: rows 1-5 are drawn rising to the right ("/"), which is the front-right and back-left quarters
   (sin theta * cos theta > 0). In the other two quarters set flip_h. Rows 0 and 6 are never flipped. Every
   pivot is on its frame's centre column, so flipping needs no change of offset.
4. SNAP each pivot to the 3 px texel grid in global coordinates (round(p / 3) * 3), so neighbouring segments'
   texels line up with each other and with the mat's.
"""
import math

K = 0.36                # BixbyCombinedArtLayout.FLOOR_FLATTEN
SPACING = 48.0          # px of screen arc between neighbouring pivots (16 texels)
TEXEL = 3

# (sheet row, lowest screen tangent in degrees, highest). Boundaries sit halfway between the rows' slopes:
# 0, 14.04 (1:4), 26.57 (1:2), 45 (1:1), 63.43 (2:1), 75.96 (4:1) and 90.
BUCKETS = [
    (0, 0.0, 7.0),
    (1, 7.0, 20.3),
    (2, 20.3, 35.8),
    (3, 35.8, 54.2),
    (4, 54.2, 69.7),
    (5, 69.7, 83.0),
    (6, 83.0, 90.0),
]


def screen_tangent(theta):
    """The ring's screen tangent at floor angle theta, in degrees from horizontal: 0 front/back, 90 sides."""
    return math.degrees(math.atan2(K * abs(math.cos(theta)), abs(math.sin(theta))))


def row_for(phi):
    for row, lo, hi in BUCKETS:
        if phi < hi:
            return row
    return BUCKETS[-1][0]


def flip_for(theta, row):
    return 1 <= row <= 5 and math.sin(theta) * math.cos(theta) < 0


class ArcTable:
    """Cumulative screen arc length of the unit ellipse (R = 1) from the front centre, theta = 90 degrees."""

    def __init__(self, samples=4096):
        self.n = samples
        self.thetas = [math.pi / 2 + 2 * math.pi * i / samples for i in range(samples + 1)]
        speed = [math.sqrt(math.sin(t) ** 2 + (K * math.cos(t)) ** 2) for t in self.thetas]
        self.cum = [0.0]
        step = 2 * math.pi / samples
        for i in range(samples):
            self.cum.append(self.cum[-1] + 0.5 * (speed[i] + speed[i + 1]) * step)
        self.total = self.cum[-1]    # the unit ellipse's perimeter, ~4.5125

    def theta_at(self, s):
        """The theta a unit arc length s (0 <= s < total) along from the front centre lands on."""
        lo, hi = 0, self.n
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        f = (s - self.cum[lo]) / max(1e-12, self.cum[hi] - self.cum[lo])
        return self.thetas[lo] + f * (self.thetas[hi] - self.thetas[lo])


TABLE = ArcTable()


def segments(radius, centre=(0.0, 0.0), snap=True):
    """[(index, theta, (x, y) global pivot, phi, row, flip)] for a ring of this radius around `centre`."""
    count = 4 * max(1, round(radius * TABLE.total / (4 * SPACING)))
    out = []
    for i in range(count):
        theta = TABLE.theta_at(TABLE.total * i / count)
        x = centre[0] + radius * math.cos(theta)
        y = centre[1] + K * radius * math.sin(theta)
        if snap:
            x, y = round(x / TEXEL) * TEXEL, round(y / TEXEL) * TEXEL
        phi = screen_tangent(theta)
        row = row_for(phi)
        out.append((i, theta, (x, y), phi, row, flip_for(theta, row)))
    return out


if __name__ == '__main__':
    print('unit perimeter %.4f' % TABLE.total)
    for r in (187, 400, 800):
        segs = segments(r)
        rows = [s[4] for s in segs]
        print('R %4d: %3d segments, rows used %s' % (r, len(segs), sorted(set(rows))))
    # the tangent range each bucket covers, as floor angle from the side (theta) and screen arc share
    for row, lo, hi in BUCKETS:
        th_hi = math.degrees(math.atan2(K, math.tan(math.radians(lo)))) if lo > 0 else 90.0
        th_lo = math.degrees(math.atan2(K, math.tan(math.radians(hi)))) if hi < 90 else 0.0
        print('row %d: phi %5.1f-%5.1f  <->  |theta| from side %5.2f-%5.2f deg' % (row, lo, hi, th_lo, th_hi))
