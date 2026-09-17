"""victory_banner: chat-notification frame in the FMWO UI-kit style (brass tube + bolted plates,
navy panel), with a round bot-avatar socket (the server mascot) and a gold 'mention' bar.
9-slice with non-uniform margins: L=48 T=42 R=10 B=10 (1x). Centre region is flat navy.
python banner.py outdir"""
import sys, math
from cv import *
import slots

W, H = 72, 56
ML, MT, MR, MB = 48, 42, 10, 10

KIT = {'K': K, '1': YEL, '2': SKIN, '3': TAN, '4': '8a6f30', '5': MUD,
         'a': WHITE, 'b': YEL, 'c': RUST, 'd': PLUM, 'P': NAVY, 'p': K, 'q': INDIGO}

PLATE9 = [
    "KKKKKKKKK",
    "K1111112K",
    "K1333334K",
    "K13ab334K",
    "K13bcd34K",
    "K133dd34K",
    "K1333334K",
    "K2444445K",
    "KKKKKKKKK",
]
TUBE_TOP = list("K1234K")     # outer -> inner
TUBE_BOT = list("K2345K")     # inner -> outer when read bottom-up reversed below


def frame_rect(w, h):
    top = TUBE_TOP + ['p']
    left = TUBE_TOP + ['p']
    bot = ['q'] + TUBE_BOT            # inner -> outer
    right = ['q'] + TUBE_BOT
    g = [['P'] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            dt, db, dl, dr = y, h - 1 - y, x, w - 1 - x
            cand = []
            if dt < len(top):
                cand.append((dt, 0, top[dt]))
            if db < len(bot):
                cand.append((db, 0, bot[len(bot) - 1 - db]))
            if dl < len(left):
                cand.append((dl, 1, left[dl]))
            if dr < len(right):
                cand.append((dr, 1, right[len(right) - 1 - dr]))
            if cand:
                cand.sort()
                g[y][x] = cand[0][2]
    # plates in the four corners (chamfered outer corner)
    s = len(PLATE9)
    for ox, oy, cx, cy, sx, sy in [(0, 0, 0, 0, 1, 1), (w - s, 0, w - 1, 0, -1, 1),
                                   (0, h - s, 0, h - 1, 1, -1), (w - s, h - s, w - 1, h - 1, -1, -1)]:
        for y in range(s):
            for x in range(s):
                g[oy + y][ox + x] = PLATE9[y][x]
        g[cy][cx] = '.'
        g[cy][cx + sx] = '.'
        g[cy + sy][cx] = '.'
        g[cy + sy][cx + sx] = 'K'
    return g


def build():
    g = frame_rect(W, H)
    cv = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            ch = g[y][x]
            if ch != '.':
                cv.set(x, y, KIT[ch])

    # ---- gold mention bar (left margin, constant along y inside the stretch band)
    for y in range(7, H - 7):
        cv.set(44, y, YEL)
        cv.set(45, y, TAN)

    # ---- avatar socket: small brass ring with the server mascot (mask-built clean 1px lines)
    CX, CY = 25.5, 24.5
    R_WIN, R_DISC = 10.5, 14.2
    disc = {(x, y) for y in range(H) for x in range(W) if math.hypot(x + 0.5 - CX, y + 0.5 - CY) <= R_DISC}
    win = {(x, y) for (x, y) in disc if math.hypot(x + 0.5 - CX, y + 0.5 - CY) <= R_WIN}
    ink = outer_ring(win, N4) & disc
    ring = disc - win - ink
    outline = outer_ring(disc, N4)
    for (x, y) in outline | ink:
        cv.set(x, y, K)
    for (x, y) in ring:
        ang = math.atan2(y + 0.5 - CY, x + 0.5 - CX)
        lit = math.cos(ang - math.radians(-135))
        idx = 1 if lit > 0.55 else (2 if lit > -0.2 else 3)
        if any((x + dx, y + dy) in outline for dx, dy in N4) and lit > -0.2:
            idx -= 1
        if any((x + dx, y + dy) in ink for dx, dy in N4):
            idx += 1
        cv.set(x, y, [YEL, SKIN, TAN, '8a6f30', MUD][max(0, min(4, idx))])
    for (x, y) in win:
        shade = math.hypot(x + 0.5 - CX + 2.5, y + 0.5 - CY + 2.5) > R_WIN + 0.3
        cv.set(x, y, PALE if shade else WHITE)
    MASCOT = [
        "..UUU.....UUU..",
        ".UUUUUUUUUUUUU.",
        "UUUUUUUUUUUUUUU",
        "UUUUUUUUUUUUUUU",
        "UUUUWWUUUWWUUUU",
        "UUUUWWUUUWWUUUU",
        "UUUUWWUUUWWUUUU",
        "UUUUUUUUUUUUUUU",
        "UUUUUUUUUUUUUUU",
        ".UUUUUUUUUUUUU.",
        "..UUUU...UUUU..",
    ]
    cv.grid(MASCOT, {'U': BLURPLE, 'W': WHITE}, 18, 19)
    # online status dot (bottom-right of the avatar)
    DOT = [
        ".kkkkk.",
        "kkGGGkk",
        "kGLGGGk",
        "kGGGGGk",
        "kGGGGTk",
        "kkGTTkk",
        ".kkkkk.",
    ]
    cv.grid(DOT, {'k': K, 'G': GREEN, 'L': LIME, 'T': TEAL}, 33, 32)
    # notification count badge (top-right of the avatar)
    BADGE = [
        "..kkkkk..",
        ".kRRRRRk.",
        "kRPPRRRRk",
        "kRPRWRRRk",
        "kRRWWRRDk",
        "kRRRWRRDk",
        "kRRRWRRDk",
        ".kRWWWDk.",
        "..kkkkk..",
    ]
    cv.grid(BADGE, {'k': K, 'R': RED, 'P': PINK, 'W': WHITE, 'D': BROWN}, 33, 6)
    return cv


def check_nine(cv):
    probs = []
    # centre flat
    ref = cv.get(ML, MT)
    for y in range(MT, H - MB):
        for x in range(ML, W - MR):
            if cv.get(x, y) != ref:
                probs.append(('centre', x, y))
    # top/bottom bands constant along x in the stretched columns
    for y in list(range(0, MT)) + list(range(H - MB, H)):
        for x in range(ML, W - MR):
            if cv.get(x, y) != cv.get(ML, y):
                probs.append(('hband', x, y))
                break
    # left/right bands constant along y in the stretched rows
    for x in list(range(0, ML)) + list(range(W - MR, W)):
        for y in range(MT, H - MB):
            if cv.get(x, y) != cv.get(x, MT):
                probs.append(('vband', x, y))
                break
    return probs


def nine(cv, WW, HH):
    """render the 9-slice at WW x HH (1x units)."""
    out = Canvas(WW, HH)
    cw, ch = W - ML - MR, H - MT - MB
    CW, CH = WW - ML - MR, HH - MT - MB

    def mp(D, m0, m1, src_c, dst_c, total_dst):
        if D < m0:
            return D
        if D >= m0 + dst_c:
            return D - (m0 + dst_c) + (m0 + src_c)
        return m0 + min(src_c - 1, (D - m0) * src_c // dst_c)

    for Y in range(HH):
        for X in range(WW):
            sx = mp(X, ML, MR, cw, CW, WW)
            sy = mp(Y, MT, MB, ch, CH, HH)
            out.set(X, Y, cv.get(sx, sy))
    return out


if __name__ == '__main__':
    od = sys.argv[1].rstrip('/') + '/'
    cv = build()
    print('nine-slice problems:', check_nine(cv)[:10])
    cv.save(od + 'victory_banner.png')
    nine(cv, 320, 56).save(od + 'victory_banner_320x56.png')
    print('ok')
