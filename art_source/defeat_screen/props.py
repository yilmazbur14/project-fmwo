"""Themed props: chat-mascot, server-icon emblem, hanging pennants, crowd signs,
boss shadow."""
import math
from lib import *
from font import draw_text, text_w

MASCOT = [
    "..uuu.....uuu..",
    ".uuuuuuuuuuuuu.",
    "uuuuuuuuuuuuuuu",
    "uuuuuuuuuuuuuuu",
    "uuuuwwuuuwwuuuu",
    "uuuuwwuuuwwuuuu",
    "uuuuwwuuuwwuuuu",
    "uuuuuuuuuuuuuuu",
    "uuuuuuuuuuuuuuu",
    ".uuuuuuuuuuuuu.",
    "..uuuu...uuuu..",
]


def mascot(img, x, y, body=BLURPLE, eyes=WHITE):
    img.stamp(MASCOT, x, y, {'u': body, 'w': eyes})


def circle_rows(halfw):
    """symmetric pixel circle from top-half half-widths (even diameter)"""
    top = []
    D = 2 * max(halfw)
    for hw in halfw:
        pad = D // 2 - hw
        top.append('.' * pad + '#' * (2 * hw) + '.' * pad)
    return top + top[::-1]


ICON24 = circle_rows([4, 6, 7, 8, 9, 10, 10, 11, 11, 11, 12, 12])
DOT10 = circle_rows([2, 4, 5, 5, 5])


def disc(img, rows, x0, y0, fill, outline=K, shade=None, shade_rows=None):
    m = {(x0 + x, y0 + y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == '#'}
    edge = inner_edge(m)
    for p in m:
        img.set(p[0], p[1], fill)
    if shade:
        # crescent on the lower-right: pixels whose up-left neighbour (2px) is outside
        for (x, y) in m:
            if (x + 3, y + 3) not in m:
                img.set(x, y, shade)
    for p in edge:
        img.set(p[0], p[1], outline)
    return m


def status_dot(img, x0, y0, ring):
    """do-not-disturb dot: 10px disc in the background colour, red 8px dot with a bar"""
    disc(img, DOT10, x0, y0, ring, outline=ring)
    dot = circle_rows([2, 3, 4, 4])
    m = disc(img, dot, x0 + 1, y0 + 1, RED, outline=K)
    img.set(x0 + 3, y0 + 3, RED_L); img.set(x0 + 4, y0 + 3, RED_L); img.set(x0 + 3, y0 + 4, RED_L)
    for x in range(x0 + 3, x0 + 7):
        img.set(x, y0 + 5, WHITE)
        img.set(x, y0 + 4, WHITE) if False else None


def server_icon(img, x0, y0, bg=ICE, shade=GREY_L, dot_ring=None):
    """24px round server icon holding the chat mascot, optional DND dot"""
    disc(img, ICON24, x0, y0, bg, outline=K, shade=shade)
    mascot(img, x0 + 5, y0 + 7)
    if dot_ring:
        status_dot(img, x0 + 16, y0 + 16, dot_ring)


def pennant(img, x0, y0, w, h, content):
    """hanging navy pennant on a brass rod with a V-notched tail"""
    notch = w // 4
    cloth = set()
    for y in range(y0 + 4, y0 + h):
        for x in range(x0, x0 + w):
            # V notch at the bottom
            depth = (y - (y0 + h - notch))
            if depth > 0:
                mid = x0 + w / 2.0 - 0.5
                if abs(x - mid) < depth * (w / 2.0) / notch:
                    continue
            cloth.add((x, y))
    for (x, y) in cloth:
        c = NAVY
        if x == x0 or x == x0 + 1:
            c = INDIGO
        img.set(x, y, c)
    # crimson inner trim
    trim = inner_edge(cloth)
    trim2 = set()
    for (x, y) in cloth:
        if (x, y) in trim:
            continue
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if (x + dx, y + dy) in trim:
                trim2.add((x, y))
                break
    inner = cloth - trim - trim2
    trim3 = set()
    for (x, y) in inner:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if (x + dx, y + dy) in trim2:
                trim3.add((x, y))
                break
    for (x, y) in trim3:
        if y > y0 + 5:
            img.set(x, y, RED)
    for (x, y) in outline_of(cloth):
        if y >= y0 + 4:
            img.set(x, y, K)
    # rod
    img.hline(x0 - 4, x0 + w + 3, y0 + 1, K)
    img.hline(x0 - 4, x0 + w + 3, y0 + 4, K)
    img.hline(x0 - 4, x0 + w + 3, y0 + 2, TAN)
    img.hline(x0 - 4, x0 + w + 3, y0 + 3, BRASS)
    img.vline(x0 - 5, y0 + 1, y0 + 4, K)
    img.vline(x0 + w + 4, y0 + 1, y0 + 4, K)
    # hanging cords up out of frame
    img.vline(x0 + 3, 0, y0, GREY_D)
    img.vline(x0 + w - 4, 0, y0, GREY_D)
    content(img, x0, y0, w, h)


def pennant_icon(img, x0, y0, w, h):
    server_icon(img, x0 + w // 2 - 12, y0 + 12, dot_ring=NAVY)
    tw = text_w('ARENA')
    draw_text(img, 'ARENA', int(x0 + (w - tw) / 2), y0 + 45, GREY_L)


def pennant_channel(img, x0, y0, w, h):
    # big bold '#' channel glyph
    g = [
        "...KKKK..KKKK...",
        "...KiiK..KiiK...",
        "KKKKiiKKKKiiKKKK",
        "KiiiiiiiiiiiiiiK",
        "KeeeeeeeeeeeeeeK",
        "KKKKiiKKKKiiKKKK",
        "..KiiK..KiiK....",
        "KKKiiKKKKiiKKKK.",
        "KiiiiiiiiiiiiiK.",
        "KeeeeeeeeeeeeeK.",
        "KKKiiKKKKiiKKKK.",
        ".KiiK..KiiK.....",
        ".KeeK..KeeK.....",
        ".KKKK..KKKK.....",
    ]
    img.stamp(g, int(x0 + w / 2 - 8), y0 + 12, {'K': K, 'i': ICE, 'e': GREY_L})
    tw = text_w('ARENA-1')
    draw_text(img, 'ARENA-1', int(x0 + (w - tw) / 2) + 1, y0 + 33, GREY_L)


def sign(img, cx, top, text, fg=RED, card=ICE, shade=GREY_L):
    tw = text_w(text)
    w = tw + 6
    h = 11
    x0 = int(cx - w / 2)
    # stick
    img.vline(x0 + w // 2, top + h, top + h + 8, BROWN_D)
    img.vline(x0 + w // 2 + 1, top + h, top + h + 8, K)
    img.vline(x0 + w // 2 - 1, top + h, top + h + 8, K)
    img.rect(x0, top, x0 + w - 1, top + h - 1, K)
    img.rect(x0 + 1, top + 1, x0 + w - 2, top + h - 2, card)
    img.hline(x0 + 1, x0 + w - 2, top + h - 2, shade)
    img.vline(x0 + w - 2, top + 1, top + h - 2, shade)
    draw_text(img, text, x0 + 3, top + 3, fg)


# ------------------------------------------------------------- boss shadow
# right half of a front double-biceps silhouette, design space 100 x 131 (x=50 centre)
SHADOW_HALF = [
    (50, 2), (57, 3), (62, 6), (65, 10), (66, 16), (65, 22), (62, 27),
    (67, 29), (74, 31),
    (79, 31), (83, 27), (87, 25), (90, 26),
    (90, 16), (89, 10),
    (88, 5), (91, 1), (97, 1), (100, 4), (100, 10), (98, 13),
    (99, 24), (100, 34),
    (97, 40), (89, 42), (80, 43),
    (76, 47), (79, 56),
    (74, 68), (71, 76),
    (73, 84), (73, 98),
    (71, 112), (72, 124), (75, 129), (75, 132), (59, 132), (60, 125),
    (59, 112), (57, 96), (53, 86), (50, 86),
]


def shadow_contour():
    right = SHADOW_HALF
    left = [(100 - x, y) for (x, y) in reversed(right)]
    return right + left[1:-1]


def boss_shadow_mask(x0, y0, sx, sy, skew):
    """x0: screen x of the silhouette centre at the feet line; y0: screen y of the top.
    skew: how far the top leans left per screen px of height."""
    poly = []
    for (x, y) in shadow_contour():
        Y = y0 + y * sy
        X = x0 + (x - 50) * sx - (132 * sy - y * sy) * skew
        poly.append((X, Y))
    return poly_mask(poly, 640, 360)


DARKEN = {
    OLIVE: NAVY, GREEN_D: NAVY, SLATE: NAVY, PLUM: NAVY, NAVY: K, K: K,
    SKIN_L: BROWN, TAN: BROWN_D, BROWN: PLUM, BROWN_D: PLUM,
    '3883c9': NAVY, '2464bd': NAVY, '162fbb': NAVY, BLUE_L: INDIGO, BLURPLE: NAVY, INDIGO: NAVY,
    RED_L: BROWN_D, RED: PLUM, GREY_D: NAVY, GREY: GREY_D, GREY_L: GREY, ICE: GREY_L,
}


def apply_shadow(img, mask):
    for (x, y) in mask:
        c = img.get(x, y)
        if c is None:
            continue
        img.set(x, y, DARKEN.get(c, NAVY))


# ---------------------------------------------------------------- house-style icon
# (matches the main menu / intro poster / intro papers: WHITE disc, BLURPLE mascot
#  with a sky-blue top highlight and indigo lower shade, green ONLINE dot)
def server_icon_house(img, x0, y0, dot_ring=None):
    m = {(x0 + x, y0 + y) for y, r in enumerate(ICON24) for x, ch in enumerate(r) if ch == '#'}
    edge = inner_edge(m)
    ring2 = inner_edge(m - edge)
    ring3 = inner_edge(m - edge - ring2)
    cx, cy = x0 + 11.5, y0 + 11.5
    for (x, y) in m:
        c = WHITE
        if (x, y) in ring2 or (x, y) in ring3:
            a = (x - cx) + (y - cy)
            c = WHITE if a < -4 else (GREY_L if a > 5 and (x, y) in ring2 else (ICE if a > -4 else WHITE))
        img.set(x, y, c)
    for (x, y) in edge:
        img.set(x, y, K)
    mx, my = x0 + 5, y0 + 7
    for j, row in enumerate(MASCOT):
        for i, ch in enumerate(row):
            if ch == 'u':
                c = BLURPLE
                if j == 0 or (j <= 2 and i <= 1):
                    c = BLUE_L
                if j >= 9 or (j >= 7 and i >= 13):
                    c = INDIGO
                img.set(mx + i, my + j, c)
            elif ch == 'w':
                img.set(mx + i, my + j, WHITE)
    if dot_ring:
        online_dot(img, x0 + 16, y0 + 16, dot_ring)


def online_dot(img, x0, y0, ring):
    """green online dot, same footprint as the old status dot (10px ring cut-out)"""
    disc(img, DOT10, x0, y0, ring, outline=ring)
    dot = circle_rows([2, 3, 4, 4])
    disc(img, dot, x0 + 1, y0 + 1, GREEN, outline=K)
    for (x, y) in [(x0 + 3, y0 + 3), (x0 + 4, y0 + 3), (x0 + 3, y0 + 4)]:
        img.set(x, y, LIME)
