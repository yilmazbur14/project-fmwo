"""Josh's card-gate for his own fight: the same magic as the approved gate in Jordan's finale (a
vortex, a ring of his cards, a spade sigil), stood UP in the air and facing the camera, in his own
colours: a wine vortex, a gold rim, his cream cards and wine card backs, and his hat badge (the
gold-rimmed spade) as the sigil.

Drawn as the RIGHT portal (the left is the code's mirror). Two layers, same frame and pivot:
  back   the whole gate (normal blend): the card ring, the gold rim and the vortex with its sigil. A
         hand is always drawn in front of it: a hand coming out of a gate that faces the camera is in
         front of all of it, so no front layer is needed.
  glow   additive (blend ADD): the gold halo round the ring and the rim, hotter on the flares.

Sequences (SEQS): open 5 (0.42), loop 12 (0.10 each, seamless: the ring turns back two card slots, a
face and a back, while the vortex turns two arms), close 4 (0.30, the last frame empty), feed 2 (0.10,
optional: the flare as a card goes in).
"""
import math
import random

import jh_lib as H
import jh_cards as C

PW = PH = 112
PIVOT = (56, 56)             # the opening's centre, frame texels (corner coordinates): column 56 is the axis
PCX, PCY = 55.5, 55.5        # the same point in pixel-centre coordinates, which the drawing uses
R_VORTEX = 21.0              # the vortex's radius
RIM_W = 4.0                  # the gold rim's width
N_CARDS = 10
CARD_W, CARD_L = 9.0, 13.0   # the ring's cards, standing out from the rim
SUITS = ['spade', 'heart', 'club', 'diamond']

SEQS = {
    'open': [0.07, 0.08, 0.08, 0.09, 0.10],      # 0.42
    'loop': [0.1] * 12,                          # seamless (the ring turns two card slots, the vortex two arms)
    'close': [0.07, 0.07, 0.08, 0.08],           # 0.30, ends empty
    'feed': [0.05, 0.05],                        # 0.10, optional: a card going in
}
LOOPS = {'loop'}
ORDER = ['open', 'loop', 'close', 'feed']


def _h(s):
    h = 2166136261
    for ch in str(s):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


# The sigil: his hat badge, drawn big and gold (a black keyline, gold body, lit upper left).
SIGIL = [
    "......k......",
    ".....kOk.....",
    "....kOOok....",
    "...kOOoook...",
    "..kOOooooGk..",
    ".kOOoooooGGk.",
    "kOOoooooooGGk",
    "kOoooooooGGGk",
    "kooooGoGGGGgk",
    ".kGGGkoGkGgk.",
    "..kkkkoGkkk..",
    ".....kGgk....",
    "....kGGggk...",
    "...kkkkkkkk..",
]


def vortex_key(r, a, phase, bright=0):
    """The wine vortex: three arms spiralling in to a dark heart."""
    s = math.sin(3 * a + 9.0 * r - phase * 2 * math.pi)
    if r < 0.28:
        return 'w'
    if s > 0.72:
        k = 'R' if r > 0.55 else 'V'
        if bright >= 2 and r > 0.4:
            k = 'T'
        return k
    if s > 0.2:
        return 'y' if r > 0.45 else 'x'
    if s > -0.45:
        return 'x'
    return 'w' if r < 0.7 else 'v'


def gate(size=1.0, phase=0.0, turn=0.0, cards_up=1.0, bright=0, sigil=True, lift=0.0, sparks=0, seed=0,
         spin_open=0.0, only_cards=None):
    """One frame of the gate. size scales everything (0..1+); phase turns the vortex (1 = one full
    arm step); turn (degrees) turns the card ring; cards_up how far the cards stand out; bright 0/1/2;
    lift pushes the cards out from the rim (texels); sparks: a few loose glints."""
    back, glow = {}, {}
    rv = R_VORTEX * size
    if rv < 1.0:
        return back, glow
    rim_out = rv + RIM_W * max(0.5, min(1.0, size))
    # 1. the card ring, behind the rim
    n = N_CARDS
    items = []
    for i in range(n):
        if only_cards is not None and i not in only_cards:
            continue
        a = math.radians(turn + 360.0 * i / n - 90.0)
        ux, uy = math.cos(a), math.sin(a)
        L = CARD_L * cards_up * min(1.0, size + 0.15)
        if L < 2.0:
            continue
        base = rim_out - 3.0 + lift
        p0 = (PCX + ux * base, PCY + uy * base)
        p1 = (PCX + ux * (base + L), PCY + uy * (base + L))
        w = CARD_W * min(1.0, 0.5 + 0.5 * size)
        cs = C.seg(p0, p1, w, w)
        side = 'face' if i % 2 == 0 else 'back'      # faces all spades: the ring repeats every two slots
        # light from the upper left: the cards up there are lit
        tone = int(round(1.0 + 0.9 * (ux * 0.7 + uy * 0.7)))
        tone = max(0, min(3, tone - (1 if bright >= 2 else 0)))
        items.append((uy, cs, side, tone, 'spade'))
    for uy, cs, side, tone, suit in sorted(items, key=lambda t: t[0]):
        part = C.quad_uv(cs, tone, side, suit if side == 'face' else None, pip_uv=(0.5, 0.62))
        back.update(part)
    # 2. the rim: a gold torus lit from the upper left, keylined inside and out; 3. the vortex in it
    vort, rim = set(), {}
    for y in range(int(PCY - rim_out - 3), int(PCY + rim_out + 4)):
        for x in range(int(PCX - rim_out - 3), int(PCX + rim_out + 4)):
            dx, dy = x - PCX, y - PCY
            r = math.hypot(dx, dy)
            if r < rv - 0.5:
                vort.add((x, y))
            elif r <= rim_out + 0.5:
                lit = -(dx + dy) / (r or 1.0)                     # +1 upper left, -1 lower right
                t = (r - rv) / max(1.0, rim_out - rv)            # 0 inner .. 1 outer
                if lit > 0.55:
                    k = 'Y' if (t > 0.3 and bright) else 'O'
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
        dx, dy = x - PCX, y - PCY
        back[(x, y)] = vortex_key(math.hypot(dx, dy) / rv, math.atan2(dy, dx), phase, bright)
    # 4. the sigil at its heart
    if sigil and size >= 0.55:
        rows = SIGIL if bright == 0 else [r.replace('o', 'O').replace('G', 'o') for r in SIGIL]
        part = H.JL.amap(rows, int(round(PCX - 6)), int(round(PCY - 7)))
        back.update(part)
    # 5. glow: a gold halo round everything drawn, the vortex's crimson breath inside the rim
    body = set(back)
    ring = set(body)
    keys = ('U', 'u', 'q') if bright else ('u', 'q')
    for r_i, k in enumerate(keys):
        nxt = set()
        for (x, y) in ring:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in body and q not in glow:
                    nxt.add(q)
        for q in nxt:
            glow[q] = k
        ring = ring | nxt
    # 6. sparks
    rnd = random.Random(seed * 131 + int(phase * 60) + int(size * 50))
    fx = {}
    for s_i in range(sparks):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(rim_out + 6, rim_out + 16)
        x, y = int(PCX + math.cos(a) * rr), int(PCY + math.sin(a) * rr)
        big = rnd.random() < 0.4
        fx[(x, y)] = 'W'
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            fx[(x + dx, y + dy)] = 'Y'
        if big:
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                fx[(x + dx, y + dy)] = 'O'
    for q, k in fx.items():
        if q not in back:
            back[q] = k
            glow.pop(q, None)
    back = {q: k for q, k in back.items() if 0 <= q[0] < PW and 0 <= q[1] < PH}
    glow = {q: k for q, k in glow.items() if 0 <= q[0] < PW and 0 <= q[1] < PH and q not in back}
    return back, glow


def flick_card(phase, tone=0):
    """The open's first beat: one gold card spinning at the centre, flicked in by Josh."""
    back = {}
    a = phase * 180.0
    k = abs(math.cos(math.radians(a)))
    cs = C.seg((PCX, PCY - 6), (PCX, PCY + 6), 9 * max(0.2, k), 9 * max(0.2, k))
    cs = [H.rot_pt(p, 25, (PCX, PCY)) for p in cs]
    part = C.quad_uv(cs, tone, 'face' if math.cos(math.radians(a)) >= 0 else 'back', 'spade', pip_uv=(0.5, 0.5))
    back.update(part)
    return back


def seq_frames(name):
    """[(back, glow)] for a sequence."""
    out = []
    if name == 'open':
        b0 = flick_card(0.25)
        g0 = {}
        for q in list(b0):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (q[0] + dx, q[1] + dy)
                if p not in b0:
                    g0[p] = 'U'
        sp = {}
        for (x, y) in ((int(PCX) - 9, int(PCY) - 10), (int(PCX) + 11, int(PCY) + 5)):
            sp[(x, y)] = 'W'
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sp[(x + dx, y + dy)] = 'Y'
        b0.update({q: k for q, k in sp.items() if q not in b0})
        out.append((b0, {q: k for q, k in g0.items() if q not in b0}))
        # the vortex's phase runs on into the loop's first frame (phase 0), the ring settles at 0
        for (size, up, br, ph, tn, sp_) in ((0.36, 0.3, 2, 0.35, -60, 3), (0.72, 0.7, 2, 0.5, -24, 5),
                                            (1.06, 1.0, 1, 0.67, -6, 4), (1.0, 1.0, 0, 5.0 / 6.0, 0, 1)):
            out.append(gate(size, ph, tn, up, br, sparks=sp_, seed=int(size * 10)))
        return out
    if name == 'loop':
        # seamless: over the loop the vortex turns two arms (phase 0 -> 2) while the ring turns back two
        # card slots (a face and a back), which brings every card to where its twin was
        n = len(SEQS['loop'])
        for i in range(n):
            out.append(gate(1.0, 2.0 * i / float(n), -2 * 360.0 / N_CARDS * i / n, 1.0, 0,
                            sparks=1 if i % 4 == 0 else 0, seed=i))
        return out
    if name == 'feed':
        for (br, lift, sp_) in ((2, 2.0, 5), (1, 1.0, 3)):
            out.append(gate(1.0, 0.0, 0.0, 1.0, br, lift=lift, sparks=sp_, seed=br + 7))
        return out
    if name == 'close':
        for (size, up, br, sp_) in ((0.7, 0.7, 1, 3), (0.4, 0.35, 1, 4), (0.15, 0.1, 2, 5)):
            out.append(gate(size, 1.2 + size, 20.0 * (1 - size), up, br, sparks=sp_, seed=int(size * 10) + 3))
        out.append(({}, {}))                     # ends empty
        return out
    raise KeyError(name)
