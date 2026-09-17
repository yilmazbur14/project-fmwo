"""scaled cape variant: swinging hem"""
import scaled as SC
import lib
import parts
import body_s

_BASE = [(48, 40), (30, 39), (17, 45), (11.5, 56), (8.5, 68), (6.5, 80), (5, 90),
         (7, 94.5), (10, 90.5), (13.5, 95.5), (18, 90), (22, 94), (26, 91), (30, 95.5), (34, 92),
         (48, 92),
         (62, 92.5), (66, 95.5), (70, 91), (74.5, 94.5), (79, 89.5), (83, 95), (86.5, 90.5), (90, 93.5), (91.5, 88),
         (89.5, 78), (87.5, 67), (84.5, 56), (79, 45), (66, 39)]


def cape_swing(sway):
    def fn(cv):
        pts = []
        for x, y in _BASE:
            t = max(0.0, (y - 50) / 45.0)
            pts.append((x + sway * t, y - abs(sway) * 0.4 * t))
        m = parts.poly(pts)
        cv.part(m, 'cape', ('sphere', 44, 56, 46, 46, 0.7), th=[9.0, 0.95, 0.80, 0.55, 0.2], bias=0)
        for p0, p1 in [((13, 62), (10, 86)), ((19, 70), (18, 89)), ((81, 64), (84, 86)), ((75, 72), (76, 88))]:
            q0 = (p0[0] + sway * max(0, (p0[1] - 50) / 45), p0[1])
            q1 = (p1[0] + sway * max(0, (p1[1] - 50) / 45), p1[1])
            ln = lib.inter(parts.seg_line(q0, q1), m)
            for y in range(96):
                for x in range(96):
                    if ln[y][x] and cv.px[y][x] != lib.BLACK:
                        cv.px[y][x] = lib.PALC['S']
    return body_s._layer(fn)
