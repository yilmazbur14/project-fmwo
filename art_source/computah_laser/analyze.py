import math, heapq, sys
STEP = 6
X0, X1, Y0, Y1 = 117, 1803, 131, 947
BODY = (922, 1006, 104, 269)   # player-centre positions blocked by Computah's body
HALF = 7.0
TELEGRAPH = 0.5
PTS = [(ox, oy) for ox in (-12, -6, 0, 6, 12) for oy in range(-26, 29, 6)]
EL, ER = (899.0, 175.0), (1029.0, 175.0)

def cells():
    for y in range(Y0, Y1 + 1, STEP):
        for x in range(X0, X1 + 1, STEP):
            if BODY[0] < x < BODY[1] and BODY[2] < y < BODY[3]:
                continue
            yield (x, y)

def earliest_u(x, y, L, alpha, delta):
    A = alpha + math.pi / 2 + delta
    best = None
    for side in (0, 1):
        ex, ey = EL if side == 0 else ER
        th0 = math.pi + alpha if side == 0 else -alpha
        for ox, oy in PTS:
            dx, dy = x + ox - ex, y + oy + 1 - ey
            r = math.hypot(dx, dy)
            if r > L:
                continue
            phi = math.atan2(dy, dx)
            if side == 0 and phi < -math.pi / 2:
                phi += 2 * math.pi
            w = math.pi / 2 if r <= HALF else math.asin(HALF / r)
            if side == 0:
                lo, hi = (th0 - (phi + w)) / A, (th0 - (phi - w)) / A
            else:
                lo, hi = (phi - w - th0) / A, (phi + w - th0) / A
            if hi < 0 or lo > 1:
                continue
            u = max(0.0, lo)
            if best is None or u < best:
                best = u
    return best

def analyze(L, T, rise, delta_deg, verbose=True):
    alpha = math.asin(rise / L)
    delta = math.radians(delta_deg)
    thit = {}
    for c in cells():
        u = earliest_u(c[0], c[1], L, alpha, delta)
        thit[c] = None if u is None else TELEGRAPH + math.acos(1 - 2 * u) / math.pi * T
    corridor_safe = [c for c, t in thit.items() if t is None and 899 <= c[0] <= 1029 and c[1] <= 175 + 0.85 * L]
    shoulder_safe = [c for c, t in thit.items() if t is None and c[1] < 175 and 780 <= c[0] <= 1150]
    # static: distance to nearest never-hit cell
    dist = {c: 0.0 for c, t in thit.items() if t is None}
    pq = [(0.0, c) for c in dist]
    heapq.heapify(pq)
    def nbrs(c):
        for dx in (-STEP, 0, STEP):
            for dy in (-STEP, 0, STEP):
                n = (c[0] + dx, c[1] + dy)
                if n != c and n in thit:
                    yield n, math.hypot(dx, dy)
    while pq:
        d, c = heapq.heappop(pq)
        if d > dist[c]: continue
        for n, s in nbrs(c):
            if d + s < dist.get(n, 1e18):
                dist[n] = d + s; heapq.heappush(pq, (d + s, n))
    worst_static = max((c for c in thit if thit[c] is not None), key=lambda c: dist[c])
    # time-aware: latest time you can stand in a cell and still escape
    INF = 1e9
    E = {c: (INF if t is None else -INF) for c, t in thit.items()}
    pq = [(-INF, c) for c, t in thit.items() if t is None]
    heapq.heapify(pq)
    while pq:
        ne, c = heapq.heappop(pq)
        e = -ne
        if e < E[c]: continue
        for n, s in nbrs(c):
            if thit[n] is None: continue
            cand = min(thit[n], e - s / 600.0)
            if cand > E[n]:
                E[n] = cand; heapq.heappush(pq, (-cand, n))
    worst_dyn = min(E, key=lambda c: E[c])
    if verbose:
        print("L=%d px T=%.2fs start_up=%.1f deg overshoot=%.1f deg total=%.1f deg tip_start_y=%.0f" % (L, T, math.degrees(alpha), delta_deg, math.degrees(alpha) + 90 + delta_deg, 175 - L * math.sin(alpha)))
        print("  corridor-under-him never-hit cells: %d %s" % (len(corridor_safe), corridor_safe[:6]))
        print("  never-hit cells near shoulders (y<175): %d  x-range %s y-range %s" % (len(shoulder_safe), (min(c[0] for c in shoulder_safe), max(c[0] for c in shoulder_safe)) if shoulder_safe else None, (min(c[1] for c in shoulder_safe), max(c[1] for c in shoulder_safe)) if shoulder_safe else None))
        print("  static worst: start %s needs %.0f px = %.2fs (telegraph 0.50s)" % (worst_static, dist[worst_static], dist[worst_static] / 600))
        print("  time-aware worst: start %s must leave by t=%.2fs after telegraph start (hit at %.2fs)" % (worst_dyn, E[worst_dyn], thit[worst_dyn]))
    return len(corridor_safe), E[worst_dyn]

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "delta":
        for d in range(14, 31, 2):
            n, _ = analyze(360, 1.6, 60, d, verbose=False)
            print("overshoot %d deg: corridor never-hit cells %d" % (d, n))
    else:
        L, T, rise, d = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
        analyze(L, T, rise, d)
