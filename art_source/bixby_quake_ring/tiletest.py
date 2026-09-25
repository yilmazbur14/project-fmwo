"""Seam checks for the quake ring's rows. Reads nothing from Assets, writes nothing.

For every row, on the ground alone (the crest is what moves):
  1. the only ground that changes from frame to frame is magma in the segment's own stretch of the crack,
     further than the overlap from both seams: ground no neighbour draws, so neighbours playing different
     frames still meet cleanly;
  2. the ground is periodic: a texel and the texel one period along show the same key wherever both
     copies draw the ground, so neighbours of one row laid at the row's period join exactly.
And for the finished frames (crest included): nothing that moves sits over the band within KEEP texels of an end
a nearer neighbour is drawn over (both ends of the flat row, the lower end of the others). Crest rising past
the far end is drawn over the farther neighbour, which is right, so it is allowed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ground as G  # noqa: E402
import ring  # noqa: E402
import segment as S  # noqa: E402


def along(gr, x, y):
    """Screen texel (x, y) relative to the pivot -> distance along the band in screen texels."""
    ux, uy = gr.u[0], gr.u[1] * G.K
    n = (ux * ux + uy * uy) ** 0.5
    return (x * ux + y * uy) / n


def main():
    bad = 0
    for i, (name, period, seeds, stretch) in enumerate(ring.ROWS):
        frames, gr = ring.build_canvas(i)
        hit = gr.march(ring.CW, ring.CH, ring.CPX, ring.CPY)
        grounds = [S.shade(gr, hit, ring.CW, ring.CH, f)[0] for f in range(ring.FRAMES)]
        half = gr.ls / 2
        still_bad = periodic_bad = periodic_n = moving_bad = 0
        dx, dy = period
        for r in range(ring.CH):
            for c in range(ring.CW):
                keys = {g[r][c] for g in grounds}
                # 1. ground that changes between frames must be magma in the segment's own stretch, further
                #    than the overlap from both seams: the only ground no neighbour ever draws
                if len(keys) > 1:
                    t_hit = gr.T[hit['it'][r, c], hit['iv'][r, c]]
                    if hit['mat'][r, c] != G.MAGMA or abs(t_hit) > gr.lt / 2 - gr.m_t:
                        still_bad += 1
                # 2. periodic: this texel against the one a period along (both drawn, both inside the canvas)
                c2, r2 = c + dx, r + dy
                if 0 <= c2 < ring.CW and 0 <= r2 < ring.CH:
                    k1, k2 = grounds[0][r][c], grounds[0][r2][c2]
                    if k1 != '.' and k2 != '.':
                        periodic_n += 1
                        if k1 != k2:
                            periodic_bad += 1
                # 3. moving crest over the band at an end a nearer neighbour draws over: both ends of the flat
                #    row (the ring's curve puts the nearer neighbour on either side), the lower end of the rest
                a = along(gr, c + 0.5 - ring.CPX, r + 0.5 - ring.CPY)
                covered_end = a < -(half - ring.KEEP) or (i == 0 and a > half - ring.KEEP)
                on_band = any(g[r][c] != '.' for g in grounds)
                if covered_end and on_band and len({f[r][c] for f in frames}) > len(keys):
                    moving_bad += 1
        ok = still_bad == 0 and periodic_bad == 0 and moving_bad == 0
        bad += not ok
        print('%-4s row %d %-8s ground that moves outside its own magma: %d | periodic: %d/%d texels differ | '
              'crest at a covered end: %d' % ('OK' if ok else 'FAIL', i, name, still_bad, periodic_bad, periodic_n,
                                               moving_bad))
    print('tiletest: %d rows, %d failing' % (len(ring.ROWS), bad))
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
