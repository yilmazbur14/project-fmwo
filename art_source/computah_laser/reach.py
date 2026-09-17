import math, heapq
STEP = 6
X0, X1, Y0, Y1 = 117, 1803, 131, 947          # reachable player-centre bounds (walls)
BODY = (934 - 12, 994 + 12, 132 - 28, 242 + 26)  # Computah body grown by player collision half-size
EM = [((899, 175), math.pi, math.pi / 2), ((1029, 175), 0.0, math.pi / 2)]
HALF = 7.0
def point_hit(px, py, L):
    for (ex, ey), a0, a1 in EM:
        dx, dy = px - ex, py - ey
        lo, hi = min(a0, a1), max(a0, a1)
        r = math.hypot(dx, dy)
        ang = math.atan2(dy, dx)
        if ang < -math.pi / 2: ang += 2 * math.pi
        if lo <= ang <= hi and r <= L: return True
        for a in (a0, a1):
            ax, ay = math.cos(a), math.sin(a)
            along = dx * ax + dy * ay
            perp = abs(-dx * ay + dy * ax)
            if 0 <= along <= L and perp <= HALF: return True
    return False
def run(L):
    xs = list(range(X0, X1 + 1, STEP)); ys = list(range(Y0, Y1 + 1, STEP))
    offs = [(ox, oy) for ox in range(-12, 13, 3) for oy in range(-26, 29, 3)]
    grid = {}
    for y in ys:
        for x in xs:
            if BODY[0] < x < BODY[1] and BODY[2] < y < BODY[3]: continue
            # quick reject: far from both emitters
            if min(math.hypot(x - 899, y - 175), math.hypot(x - 1029, y - 175)) > L + 40:
                grid[(x, y)] = False; continue
            grid[(x, y)] = any(point_hit(x + ox, y + oy, L) for ox, oy in offs)
    dist = {}
    pq = []
    for k, hit in grid.items():
        if not hit:
            dist[k] = 0.0; heapq.heappush(pq, (0.0, k))
    while pq:
        d, (x, y) = heapq.heappop(pq)
        if d > dist[(x, y)]: continue
        for dx in (-STEP, 0, STEP):
            for dy in (-STEP, 0, STEP):
                n = (x + dx, y + dy)
                if n == (x, y) or n not in grid: continue
                nd = d + math.hypot(dx, dy)
                if nd < dist.get(n, 1e9):
                    dist[n] = nd; heapq.heappush(pq, (nd, n))
    hits = [k for k, v in grid.items() if v]
    worst = max(hits, key=lambda k: dist[k])
    print("beam %d px: %d reachable cells hit, worst start %s needs %.0f px -> %.2fs at 600px/s (telegraph 0.50s)" % (L, len(hits), worst, dist[worst], dist[worst] / 600))
run(360); run(468); run(480)
