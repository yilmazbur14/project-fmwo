"""PORTAL MONTE: the small card-gate that opens round the player (three at a time), redrawn small in the
approved big gate's language (jh_portal): a wine vortex, a gold rim, a ring of his cream cards and wine
card backs, the gold spade at its heart. Upright and facing the camera, like the big ones; its own
texels (not a scaled copy of the big gate), in his palette only.

NEUTRAL: every small gate is drawn the same. There is no red or yellow in it that means anything: the
marks (the game's parry badge, Carter's pale X) are the only difference between the real one and a fake.

Two layers, same frame and pivot (corner convention, offset = frame/2 - pivot):
  back   the whole gate (normal blend): card ring, rim, vortex, sigil. Whatever comes out is drawn in
         front of it, so no front layer.
  glow   additive (blend ADD): the gold halo.

Every size is in CFG, so a resize is one edit: the rest (sequences, contract numbers) follows.
"""
import math
import random

import jh_lib as H
import jh_cards as C

CFG = {
    'FW': 56, 'FH': 56,          # the frame, texels (room for the burst's flare)
    'PIVOT': (28, 28),           # the opening's centre (corner coordinates)
    'R_VORTEX': 9.5,             # the vortex's radius
    'RIM_W': 3.0,                # the gold rim's width
    'N_CARDS': 8,                # the ring: faces and backs alternating, faces all spades (a seamless loop)
    'CARD_W': 5.0,
    'CARD_L': 9.0,
    'CARD_TUCK': 2.0,            # how far each card's foot hides under the rim
    'FLOOR_DROP': 22,            # the pivot's height above the gate's floor point (the code's y-sort point)
}

# Sequences, seconds a frame (HARD totals from the Monte plan: open 0.30, burst 0.18, close 0.20; loop
# 0.10 a frame).
SEQS = {
    'open': [0.06, 0.07, 0.08, 0.09],       # 0.30: the dealt card flips open into the gate
    'loop': [0.1] * 8,                      # seamless: the ring turns back two card slots, the vortex two arms
    'burst': [0.05, 0.06, 0.07],            # 0.18: the flare as the figure comes out, back into the loop
    'close': [0.05, 0.05, 0.05, 0.05],      # 0.20: ends empty
}
LOOPS = {'loop'}
ORDER = ['open', 'loop', 'burst', 'close']

# His hat badge, small: the gold spade with a black keyline, lit from the upper left.
SIGIL = [
    "...k...",
    "..kOk..",
    ".kOook.",
    "kOoooGk",
    "kooGoGk",
    ".kkGkk.",
    "..kGk..",
    ".kGGgk.",
    ".kkkkk.",
]
SIGIL_BRIGHT = [r.replace('o', 'O').replace('G', 'o') for r in SIGIL]


def centre():
    px, py = CFG['PIVOT']
    return px - 0.5, py - 0.5          # pixel-centre coordinates of the pivot


def vortex_key(r, a, phase, bright=0):
    """jh_portal's vortex, tuned for a small radius: three arms spiralling into a dark heart."""
    s = math.sin(3 * a + 7.0 * r - phase * 2 * math.pi)
    if r < 0.3:
        return 'w'
    if s > 0.62:
        k = 'R' if r > 0.52 else 'V'
        if bright >= 2 and r > 0.38:
            k = 'T'
        return k
    if s > 0.05:
        return 'y' if r > 0.45 else 'x'
    if s > -0.5:
        return 'x'
    return 'w' if r < 0.72 else 'v'


def gate(size=1.0, phase=0.0, turn=0.0, cards_up=1.0, bright=0, sigil=True, lift=0.0, sparks=0, seed=0):
    """One frame of the small gate: (back, glow) texel dicts in frame coordinates."""
    cx, cy = centre()
    back, glow = {}, {}
    rv = CFG['R_VORTEX'] * size
    if rv < 1.0:
        return back, glow
    rim_w = CFG['RIM_W'] * max(0.5, min(1.0, size))
    rim_out = rv + rim_w
    n = CFG['N_CARDS']
    items = []
    for i in range(n):
        a = math.radians(turn + 360.0 * i / n - 90.0)
        ux, uy = math.cos(a), math.sin(a)
        L = CFG['CARD_L'] * cards_up * min(1.0, size + 0.15)
        if L < 2.0:
            continue
        base = rim_out - CFG['CARD_TUCK'] + lift
        p0 = (cx + ux * base, cy + uy * base)
        p1 = (cx + ux * (base + L), cy + uy * (base + L))
        w = CFG['CARD_W'] * min(1.0, 0.5 + 0.5 * size)
        cs = C.seg(p0, p1, w, w)
        side = 'face' if i % 2 == 0 else 'back'
        tone = int(round(1.0 + 0.9 * (ux * 0.7 + uy * 0.7)))
        tone = max(0, min(3, tone - (1 if bright >= 2 else 0)))
        items.append((uy, cs, side, tone))
    for uy, cs, side, tone in sorted(items, key=lambda t: t[0]):
        back.update(C.quad(cs, tone, side, 'spade' if side == 'face' else None))
    # the rim: a gold torus lit from the upper left, keylined inside and out; the vortex inside it
    vort, rim = set(), {}
    R = int(rim_out) + 3
    for y in range(int(cy) - R, int(cy) + R + 2):
        for x in range(int(cx) - R, int(cx) + R + 2):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            if r < rv - 0.5:
                vort.add((x, y))
            elif r <= rim_out + 0.5:
                lit = -(dx + dy) / (r or 1.0)
                if lit > 0.55:
                    k = 'Y' if bright else 'O'
                elif lit > -0.2:
                    k = 'O' if bright >= 2 else 'o'
                elif lit > -0.7:
                    k = 'G'
                else:
                    k = 'g'
                if bright >= 2 and lit > 0:
                    k = 'Y'
                rim[(x, y)] = k
    for (x, y) in list(rim):
        n4 = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        if any(q in vort for q in n4) or any(q not in rim and q not in vort for q in n4):
            rim[(x, y)] = 'k'
    back.update(rim)
    for (x, y) in vort:
        dx, dy = x - cx, y - cy
        back[(x, y)] = vortex_key(math.hypot(dx, dy) / rv, math.atan2(dy, dx), phase, bright)
    if sigil and size >= 0.6:
        rows = SIGIL_BRIGHT if bright else SIGIL
        w, h = len(rows[0]), len(rows)
        back.update(H.JL.amap(rows, int(round(cx - (w - 1) / 2.0)), int(round(cy - (h - 1) / 2.0))))
    # glow: a gold halo round everything drawn
    body = set(back)
    ring = set(body)
    keys = ('U', 'u', 'q') if bright >= 2 else (('u', 'u', 'q') if bright else ('u', 'q'))
    for k in keys:
        nxt = set()
        for (x, y) in ring:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and q not in glow:
                    nxt.add(q)
        for q in nxt:
            glow[q] = k
        ring = ring | nxt
    # sparks: loose glints outside the ring
    rnd = random.Random(seed * 131 + int(phase * 60) + int(size * 50))
    fx = {}
    tip = rim_out - CFG['CARD_TUCK'] + lift + CFG['CARD_L'] * cards_up
    for _ in range(sparks):
        a = rnd.uniform(0, 2 * math.pi)
        rr = min(rnd.uniform(tip + 2.5, tip + 6.0), min(CFG['FW'], CFG['FH']) / 2.0 - 3.0)
        x, y = int(math.floor(cx + math.cos(a) * rr + 0.5)), int(math.floor(cy + math.sin(a) * rr + 0.5))
        fx[(x, y)] = 'W'
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            fx[(x + dx, y + dy)] = 'Y'
    for q, k in fx.items():
        if q not in back:
            back[q] = k
            glow.pop(q, None)
    W, Hh = CFG['FW'], CFG['FH']
    back = {q: k for q, k in back.items() if 0 <= q[0] < W and 0 <= q[1] < Hh}
    glow = {q: k for q, k in glow.items() if 0 <= q[0] < W and 0 <= q[1] < Hh and q not in back}
    return back, glow


def flip_card(open_k, tone=0):
    """The open's first beat: the dealt card at the centre, turning edge-on as it flips open, gold-edged,
    with a flash round it."""
    cx, cy = centre()
    w = 8.0 * max(0.25, open_k)
    cs = C.seg((cx, cy + 6.0), (cx, cy - 6.0), w, w)
    part = C.quad(cs, tone, 'face' if open_k > 0.45 else 'back', 'spade')
    glow = {}
    body = set(part)
    ring = set(body)
    for k in ('U', 'u', 'q'):
        nxt = set()
        for (x, y) in ring:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and q not in glow:
                    nxt.add(q)
        for q in nxt:
            glow[q] = k
        ring |= nxt
    # four glints thrown off it
    for (x, y) in ((int(cx) - 8, int(cy) - 7), (int(cx) + 9, int(cy) - 4), (int(cx) - 6, int(cy) + 8),
                   (int(cx) + 7, int(cy) + 8)):
        sp = {(x, y): 'W'}
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sp[(x + dx, y + dy)] = 'Y'
        for q, k in sp.items():
            if q not in part:
                part[q] = k
                glow.pop(q, None)
    return part, {q: k for q, k in glow.items() if q not in part}


LOOP_TURN = -2 * 360.0     # degrees the ring turns over the whole loop, per card count (two slots back)


def loop_state(i):
    n = len(SEQS['loop'])
    return 2.0 * i / float(n), LOOP_TURN / CFG['N_CARDS'] * i / n


def seq_frames(name):
    """[(back, glow)] for a sequence."""
    out = []
    if name == 'open':
        out.append(flip_card(0.6))
        # the vortex's phase runs on into the loop's first frame (phase 0), the ring settles at 0
        for (size, up, br, ph, tn, sp) in ((0.45, 0.35, 2, 0.55, -50, 3), (1.1, 1.0, 1, 0.72, -12, 3),
                                           (1.0, 1.0, 0, 0.86, -3, 1)):
            out.append(gate(size, ph, tn, up, br, sparks=sp, seed=int(size * 10)))
        return out
    if name == 'loop':
        for i in range(len(SEQS['loop'])):
            ph, tn = loop_state(i)
            out.append(gate(1.0, ph, tn, 1.0, 0, sparks=1 if i % 4 == 0 else 0, seed=i))
        return out
    if name == 'burst':
        # the flare: the vortex white-hot and the ring blown out as the figure comes through, then easing
        # back so the loop's first frame follows
        for (br, lift, ph, sp) in ((2, 3.0, -0.45, 5), (1, 1.5, -0.3, 3), (0, 0.5, -0.15, 1)):
            out.append(gate(1.0, ph, 6.0 * lift, 1.0, br, lift=lift, sparks=sp, seed=br + 11))
        return out
    if name == 'close':
        for (size, up, br, sp) in ((0.7, 0.7, 1, 2), (0.42, 0.4, 1, 3), (0.2, 0.15, 2, 4)):
            out.append(gate(size, 1.2 + size, 24.0 * (1 - size), up, br, sparks=sp, seed=int(size * 10) + 3))
        out.append(({}, {}))
        return out
    raise KeyError(name)
