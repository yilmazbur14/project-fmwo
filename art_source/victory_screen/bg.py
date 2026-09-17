"""victory_bg: 640x360 arena seen from behind the champion.
python bg.py out.png [noplayer] [guides]"""
import sys, random
from cv import *

W, H = 640, 360
CX = 320            # mirror x' = 639 - x
HORIZON = 132

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
MINI = [".U.U.", "UUUUU", "UWUWU", "UUUUU", "UU.UU"]
MASCOT_S = [
    "..UU.....UU..",
    ".UUUUUUUUUUU.",
    "UUUUUUUUUUUUU",
    "UUUWWUUUWWUUU",
    "UUUWWUUUWWUUU",
    "UUUUUUUUUUUUU",
    ".UUUUUUUUUUU.",
    "..UUU...UUU..",
]

LIGHT = {
    K: NAVY, NAVY: INDIGO, PLUM: PURPLE, INDIGO: BLURPLE, BROWN: RUST, RUST: TAN,
    TAN: SKIN, SKIN: WHITE, PURPLE: ROSE, BLURPLE: SKY, SKY: PALE, PALE: WHITE,
    OLIVE: KHAKI, KHAKI: LIME, SLATE: ASH, ASH: DGREY, DGREY: GREY, GREY: PALE,
    RED: PINK, BRASS: TAN, MUD: BRASS, STEEL: SKY, TEAL: GREEN, DASH: DGREY,
    WHITE: WHITE, YEL: YEL, LIME: LIME, PINK: ROSE, ROSE: ROSE, CYAN: CYAN,
    GREEN: LIME, ORANGE: YEL,
}

FAR_Y = 206          # far canvas edge
FX0, FX1 = 92, 547   # far posts (mirror pair: 639-92 = 547)
ROPES = [164, 178, 192]
BOARD_Y = 150        # barrier top
PLAYER_XY = (284, 108)

CROWD = load("C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Environment/crowd_v2.png")
# (frame, x offset, top y, darken steps): far tier -> front tier; all cheer frames
CROWD_TIERS = [(4, 212, 47, 2), (4, 431, 79, 1), (3, 0, 110, 0)]
SHADOW = {  # one DB32 step darker, for the tiers further back
    'eec39a': 'd9a066', 'd9a066': '8f563b', '8f563b': '663931', '663931': '45283c', '45283c': '222034',
    '222034': '222034', '000000': '000000', '3f3f74': '222034', '5b6ee1': '3f3f74', '639bff': '5b6ee1',
    'cbdbfc': '9badb7', '9badb7': '696a6a', 'ffffff': 'cbdbfc', 'ac3232': '663931', 'd95763': 'ac3232',
    '76428a': '45283c', '306082': '3f3f74', '37946e': '323c39', '4b692f': '323c39', '524b24': '45283c',
    '8a6f30': '524b24', '595652': '323c39', '696a6a': '595652', '323c39': '222034', 'df7126': '8f563b',
    '5fcde4': '306082', 'd77bba': '76428a',
}


def lit_beam(cv, poly, strength_mask):
    m = poly_mask(poly)
    for (x, y) in m:
        if not cv.inb(x, y):
            continue
        strength_mask[(x, y)] = strength_mask.get((x, y), 0) + 1


def build(with_player=True, guides=False):
    random.seed(11)
    cv = Canvas(W, H, NAVY)

    # ---------------- stands: the approved Punch-Out-style crowd (crowd_v2, cheer frames) ----------------
    for y in range(0, BOARD_Y):
        for x in range(W):
            cv.set(x, y, NAVY)
    LAMPS = [(118, 14), (521, 14)]
    BEAMS = []
    for (lx, ly) in LAMPS:
        tx0, tx1 = (262, 372) if lx < CX else (267, 377)
        BEAMS.append([(lx - 5, ly + 4), (lx + 5, ly + 4), (tx1, 222), (tx0, 222)])
    beam_px = {}
    for bp in BEAMS:
        for p in poly_mask(bp):
            beam_px[p] = beam_px.get(p, 0) + 1
    crowd_px = set()
    for (frame, offset, ty, darken) in CROWD_TIERS:
        for y in range(40):
            for x in range(W):
                c = CROWD.get(frame * 640 + (x + offset) % 640, y)
                if c is None:
                    continue
                for _ in range(darken):
                    c = SHADOW.get(c, c)
                cv.set(x, ty + y, c)
                crowd_px.add((x, ty + y))

    # ---------------- barrier + ribbon board ----------------
    for y in range(BOARD_Y, FAR_Y):
        for x in range(W):
            cv.set(x, y, NAVY)
    for x in range(W):
        cv.set(x, BOARD_Y, K)
        cv.set(x, BOARD_Y + 1, TAN)
        cv.set(x, BOARD_Y + 2, BRASS)
        cv.set(x, BOARD_Y + 3, K)
    by0, by1 = BOARD_Y + 4, BOARD_Y + 12
    for y in range(by0, by1 + 1):
        for x in range(W):
            cv.set(x, y, K)
    for x in range(W):
        cv.set(x, by1 + 1, INDIGO)
        cv.set(x, by1 + 2, K)
    # lower wall panels
    for y in range(by1 + 3, FAR_Y):
        for x in range(W):
            c = NAVY
            if x % 40 == 0:
                c = K
            elif x % 40 == 1:
                c = INDIGO
            cv.set(x, y, c)
    feed = [("GG", LIME), ("@NEWCOMER", YEL), ("W", LIME), ("LETS GO", SKY), ("+1", PALE)]
    bx, i = 3, 0
    while bx < W:
        s, col = feed[i % len(feed)]
        text(cv, s, bx, by0 + 2, col)
        bx += text_w(s) + 7
        cv.grid(MINI, {'U': BLURPLE, 'W': WHITE}, bx, by0 + 2)
        bx += 5 + 7
        i += 1

    # ---------------- ring canvas ----------------
    NEARY = 470
    k = (NEARY - HORIZON) / (FAR_Y - HORIZON)
    NX0 = CX - (CX - FX0) * k
    NX1 = CX + (FX1 + 1 - CX) * k
    poly = [(FX0, FAR_Y), (FX1 + 1, FAR_Y), (NX1, NEARY), (NX0, NEARY)]
    cm = {(x, y) for (x, y) in poly_mask(poly) if 0 <= x < W and 0 <= y < H}
    # arena floor outside the ring
    for y in range(FAR_Y, H):
        for x in range(W):
            cv.set(x, y, K if (y > 250 or (x + y) % 2) else NAVY)
    # canvas falloff from the spotlight pool (elliptical bands + checker seams)
    PCX, PCY = 320, 218
    for (x, y) in cm:
        dx = (x + 0.5 - PCX) / 150.0
        dy = (y + 0.5 - PCY) / 30.0
        r = (dx * dx + dy * dy) ** 0.5
        ck = (x + y) % 2 == 0
        if r < 0.55:
            c = LIME if r < 0.42 or ck else KHAKI
        elif r < 0.85:
            c = KHAKI if (r < 0.75 or ck) else OLIVE
        elif r < 2.6:
            c = OLIVE if (r < 2.3 or ck) else SLATE
        elif r < 4.2:
            c = SLATE if (r < 3.9 or ck) else NAVY
        else:
            c = NAVY
        cv.set(x, y, c)
    # canvas edges
    for x in range(FX0, FX1 + 1):
        cv.set(x, FAR_Y, K)
    for (x, y) in outer_ring(cm, N4):
        if y > FAR_Y and cv.inb(x, y):
            cv.set(x, y, K)
    # apron edge highlight along the canvas border
    for (x, y) in inner_edge(cm, N4):
        if y > FAR_Y + 1:
            cv.set(x, y, OLIVE if cv.get(x, y) in (SLATE, NAVY) else KHAKI)

    # ---------------- far ropes ----------------
    def rope_px(x, y, thick):
        cv.set(x, y - 1, K)
        for t in range(thick):
            cv.set(x, y + t, WHITE if t < max(1, thick - 1) else GREY)
        cv.set(x, y + thick, K)

    for ry in ROPES:
        for x in range(FX0, FX1 + 1):
            rope_px(x, ry, 2)
    # side ropes toward the camera
    for ry in ROPES:
        for side in (FX0, FX1):
            ny = HORIZON + (ry - HORIZON) * k
            nx = NX0 if side == FX0 else NX1
            steps = 900
            last = None
            for s in range(steps + 1):
                t = s / steps
                x = side + (nx - side) * t
                y = ry + (ny - ry) * t
                xi, yi = int(round(x)), int(round(y))
                if (xi, yi) == last or not (0 <= xi < W):
                    continue
                last = (xi, yi)
                depth = abs(xi - side) / abs(nx - side)
                thick = 2 + int(depth * 9)
                rope_px(xi, yi, thick)

    # ---------------- posts ----------------
    def post(px):
        top, bot = 156, FAR_Y + 1
        for y in range(top, bot + 1):
            for x in range(px - 3, px + 4):
                c = TAN
                if x <= px - 2:
                    c = BRASS
                if x == px + 2:
                    c = SKIN
                cv.set(x, y, c)
            cv.set(px - 4, y, K)
            cv.set(px + 4, y, K)
        for x in range(px - 4, px + 5):
            cv.set(x, bot + 1, K)
        # rounded cap
        cv.grid([".kkkkk.", "kSSTTTk", "kBTTTSk"], {'k': K, 'S': SKIN, 'T': TAN, 'B': BRASS}, px - 3, top - 3)
        # turnbuckle pads
        for ry in ROPES:
            cv.grid(["kkkkkkkkk", "kPPPPPRRk", "kPWPPPRRk", "kPPPPPRRk", "kkkkkkkkk"],
                    {'k': K, 'P': BLURPLE, 'W': SKY, 'R': INDIGO}, px - 4, ry - 2)

    post(FX0)
    post(FX1)

    # ---------------- rig: truss, lamps, beams ----------------
    HAZE = {NAVY: INDIGO, PLUM: PURPLE, INDIGO: BLURPLE, K: NAVY, SLATE: ASH, OLIVE: KHAKI, KHAKI: LIME}
    CROWD_HAZE = {K: NAVY, NAVY: INDIGO, PLUM: PURPLE}
    for (x, y), n in beam_px.items():
        if y < 8 or not cv.inb(x, y):
            continue
        if (x, y) in crowd_px:
            # sparse shaft of light over the spectators' darkest pixels only
            c = cv.get(x, y)
            if c in CROWD_HAZE and ((x + 2 * y) % 4 == 0 or (n >= 2 and (x + y) % 2 == 0)):
                cv.set(x, y, CROWD_HAZE[c])
            continue
        c = cv.get(x, y)
        if c in HAZE and (n >= 2 or (x + y) % 2 == 0):
            cv.set(x, y, HAZE[c])

    # truss
    for x in range(W):
        for y in range(0, 10):
            cv.set(x, y, K)
        cv.set(x, 1, DASH)
        cv.set(x, 8, DASH)
    for x in range(-8, W, 8):
        for t in range(6):
            cv.set(x + 1 + t, 2 + t, ASH)
            cv.set(x + 6 - t, 2 + t, DASH)
    # lamp cans (aimed at the ring centre)
    LAMP = [
        "..kkkk..",
        ".kAAAAk.",
        "kAGGGAAk",
        "kAGAAAAk",
        "kAAAAADk",
        "kDAAADDk",
        ".kkkkkk.",
        ".kPPPPk.",
        "..kkkk..",
    ]
    for (lx, ly) in LAMPS:
        cv.grid(LAMP, {'k': K, 'A': ASH, 'G': GREY, 'D': DASH, 'P': WHITE}, lx - 4, ly - 5,
                flipx=lx > CX)

    # ---------------- hanging pennants ----------------
    def pennant(px, kind):
        """Same banners as the defeat screen's arena (swallowtail, rod on two strings, mascot + ARENA /
        '#' + ARENA-1), in victory colours: crimson cloth with a gold inner border."""
        w, top, bot = 36, 12, 66
        m = poly_mask([(px, top), (px + w, top), (px + w, bot), (px + w / 2.0, bot - 8), (px, bot)])
        ring1 = inner_edge(m, N4)
        inner = m - ring1
        ring2 = inner_edge(inner, N4)
        for (x, y) in m:
            cv.set(x, y, RED)
        for (x, y) in m:
            if x <= px + 1:
                cv.set(x, y, PINK)
            elif x >= px + w - 2:
                cv.set(x, y, BROWN)
        for (x, y) in (inner - inner_edge(inner, N4)) & set():
            pass
        # gold inner border one pixel in from the edge
        body = inner - ring2
        border = inner_edge(body, N4)
        for (x, y) in border:
            if y > top + 1:
                cv.set(x, y, YEL if (x < px + w / 2.0) else TAN)
        for (x, y) in outer_ring(m, N4):
            if y > top:
                cv.set(x, y, K)
        # strings + rod
        for sx in (px + 4, px + w - 4):
            for y in range(9, top - 1):
                cv.set(sx, y, DASH)
        for x in range(px - 3, px + w + 4):
            cv.set(x, top - 2, K)
            cv.set(x, top - 1, SKIN)
            cv.set(x, top, BRASS)
            cv.set(x, top + 1, K)
        cv.set(px - 4, top - 1, K); cv.set(px - 4, top, K)
        cv.set(px + w + 4, top - 1, K); cv.set(px + w + 4, top, K)
        cxp = px + w / 2.0
        if kind == 'mascot':
            disc = ellipse_mask(cxp, top + 18.5, 9.5, 9.5)
            for (x, y) in disc:
                shade = (x + 0.5 - cxp) + (y + 0.5 - (top + 18.5)) > 8
                cv.set(x, y, PALE if shade else WHITE)
            for (x, y) in outer_ring(disc, N4):
                cv.set(x, y, K)
            cv.grid(MASCOT_S, {'U': BLURPLE, 'W': WHITE}, px + (w - 13) // 2, top + 14)
            cv.grid(["..kkkk..", ".kGGGGk.", "kGLLGGTk", "kGLGGGTk", "kGGGGTTk", "kTGGTTTk",
                     ".kTTTTk.", "..kkkk.."], {'k': K, 'G': GREEN, 'L': LIME, 'T': TEAL}, px + 22, top + 23)
            text(cv, "ARENA", px + (w - text_w("ARENA")) // 2, bot - 22, PALE)
        else:
            HASH = [
                ".....WW...WW..",
                ".....WW...WW..",
                "WWWWWWWWWWWWWW",
                "WWWWWWWWWWWWWW",
                "....WW...WW...",
                "....WW...WW...",
                "....WW...WW...",
                "WWWWWWWWWWWWWW",
                "WWWWWWWWWWWWWW",
                "...WW...WW....",
                "...WW...WW....",
            ]
            hm = set()
            for j, row in enumerate(HASH):
                for i, ch in enumerate(row):
                    if ch == 'W':
                        hm.add((px + 11 + i, top + 8 + j))
            for (x, y) in outer_ring(hm, N4):
                cv.set(x, y, K)
            for (x, y) in hm:
                shade = (x + 1, y) not in hm or (x, y + 1) not in hm
                cv.set(x, y, GREY if shade else WHITE)
            text(cv, "ARENA-1", px + (w - text_w("ARENA-1")) // 2, bot - 22, PALE)

    pennant(14, 'mascot')
    pennant(639 - 14 - 36, 'hash')

    # ---------------- streamer swags ----------------
    SWAG_COLS = [RED, YEL, LIME, SKY, ROSE]

    def swag(x0, x1, sag, col, yoff=10):
        for x in range(x0, x1 + 1):
            t = (x - x0) / max(1, (x1 - x0))
            y = yoff + int(round(4 * sag * t * (1 - t)))
            cv.set(x, y, col)
            cv.set(x, y + 1, K)
            if (x // 3) % 2 == 0:
                cv.set(x, y + 1, col)

    swag(56, 120, 16, RED, 11)
    swag(120, 190, 12, YEL, 11)
    swag(639 - 120, 639 - 56, 16, LIME, 11)
    swag(639 - 190, 639 - 120, 12, ROSE, 11)

    # ---------------- confetti ----------------
    random.seed(3)
    CONF = [RED, YEL, LIME, SKY, ROSE, CYAN, WHITE, ORANGE]
    SHAPES = [[(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 1)], [(0, 0), (1, 0), (0, 1), (1, 1)], [(1, 0), (0, 1)]]
    for _ in range(170):
        x = random.randint(0, W - 2)
        y = random.randint(12, 146)
        # keep the title box and the pennants clear, the banner zone calmer
        if 176 <= x <= 464 and y <= 52:
            continue
        if (8 <= x <= 56 or 583 <= x <= 631) and y <= 70:
            continue
        if 150 < x < 490 and y < 112 and random.random() < 0.75:
            continue
        col = random.choice(CONF)
        for (dx, dy) in random.choice(SHAPES):
            cv.set(x + dx, y + dy, col)
    # confetti lying on the canvas
    for _ in range(90):
        x = random.randint(0, W - 2)
        y = random.randint(FAR_Y + 3, H - 1)
        if (x, y) in cm and (x + 1, y) in cm:
            col = random.choice([RED, YEL, SKY, ROSE, WHITE])
            cv.set(x, y, col)
            if random.random() < 0.5:
                cv.set(x + 1, y, col)

    if with_player:
        import player as _pl
        PX, PY = PLAYER_XY
        sh = ellipse_mask(320, PY + 118.5, 26, 3.6)
        DARK = {LIME: KHAKI, KHAKI: OLIVE, OLIVE: SLATE, SLATE: NAVY, NAVY: K}
        for (x, y) in sh:
            c = cv.get(x, y)
            if c in DARK:
                cv.set(x, y, DARK[c])
        cv.blit(_pl.render(_pl.final_rows()), PX, PY)

    if guides:
        # UI layout guides in base px
        for (x0, y0, x1, y1) in [(187, 12, 452, 52), (160, 58, 479, 105), (156, 222, 483, 261), (250, 279, 389, 313)]:
            for x in range(x0, x1 + 1):
                cv.set(x, y0, RED); cv.set(x, y1, RED)
            for y in range(y0, y1 + 1):
                cv.set(x0, y, RED); cv.set(x1, y, RED)
    return cv


if __name__ == '__main__':
    out = sys.argv[1]
    cv = build('noplayer' not in sys.argv, 'guides' in sys.argv)
    cv.save(out)
    print('saved', out)
