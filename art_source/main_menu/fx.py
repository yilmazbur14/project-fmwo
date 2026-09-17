"""Optional looping overlay for the main-menu background: 12 frames of 640x360 (horizontal strip).

Drawn over main_menu_bg.png at the same position/scale. 175 ms per frame (2.1 s loop):
  - the crowd runs crowd_v2's idle loop (frames 0,1,2 at 0.35 s, same timing as ArenaCrowdScript)
  - the INVITE sends out a notification 'ping' ring (frames 0-5), then rests
  - the corner-post lanterns flicker on staggered beats; the floating icon lanterns bob 1px
  - a few big stars twinkle; a glint slides across the padlock (frames 6-7)
Every overlay pixel is placed so that bg + overlay equals the intended frame exactly (erasures repaint
the layer underneath), so nothing ghosts.
"""
import math, os
from lib import *
import bg
import invite

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
N = 12
CROWD_SEQ = [0, 0, 1, 1, 2, 2, 0, 0, 1, 1, 2, 2]
BOB = [0, 0, -1, -1, -1, -1, 0, 0, 1, 1, 1, 1]


def build():
    comp, parts = bg.build()
    L = dict(parts)
    names = [n for n, _ in parts]
    top = [[None] * bg.W for _ in range(bg.H)]
    for n in names:
        lc = L[n]
        for y in range(bg.H):
            row = lc.p[y]
            for x in range(bg.W):
                if row[x] is not None:
                    top[y][x] = n
    sky_plain = bg.layer_sky(stars=False)
    frames = []
    for f in range(N):
        o = Canvas(bg.W, bg.H)

        # --- crowd idle loop
        cf = CROWD_SEQ[f]
        if cf != 0:
            crowd = bg.layer_crowd(cf)
            for (x0, x1), off in bg.CROWD_SLICES:
                for x in range(x0, x1 + 1):
                    for y in range(bg.CROWD_TOP, bg.BASE_Y + 1):
                        if top[y][x] not in ('sky', 'lanterns', 'crowd'):
                            continue
                        col = crowd.p[y][x] or L['lanterns'].p[y][x] or L['sky'].p[y][x]
                        if col != comp.p[y][x]:
                            o.set(x, y, col)

        # --- floating icon lanterns bob
        lan = bg.layer_lanterns(bob=[BOB[(f + i * 3) % N] for i in range(len(bg.SKY_LANTERNS))])
        for (lx, ly, s, k) in bg.SKY_LANTERNS:
            R = s + 6
            for y in range(ly - R, ly + R + 1):
                for x in range(lx - R, lx + R + 1):
                    if not (0 <= x < bg.W and 0 <= y < bg.H) or top[y][x] not in ('sky', 'lanterns'):
                        continue
                    col = lan.p[y][x] or L['sky'].p[y][x]
                    if col != comp.p[y][x]:
                        o.set(x, y, col)

        # --- invite 'ping' ring (frames 0-5)
        if f < 6:
            gx, gy = bg.GLOW
            rr = 46 + 8 * f
            dens = [0.5, 0.42, 0.34, 0.26, 0.18, 0.1][f]
            for y in range(max(0, int(gy - rr / 1.25) - 3), min(bg.H, int(gy + rr / 1.25) + 4)):
                for x in range(max(0, gx - rr - 3), min(bg.W, gx + rr + 4)):
                    if top[y][x] != 'sky':
                        continue
                    d = math.hypot(x - gx, (y - gy) * 1.25)
                    if abs(d - rr) <= 1.0 and dith(x, y, dens):
                        col = SB if f < 2 else RB if f < 4 else IN
                        if comp.p[y][x] in (SB, WH2) and col != WH2:
                            col = WH2
                        o.set(x, y, col)

        # --- corner-post lanterns flicker
        for k in range(1, bg.N_TIERS + 1):
            st, ft, fb, hw = bg.TIERS[k - 1]
            hi, base, lo = bg.ROLE[k]
            for side, px in enumerate((bg.CX - hw + 4, bg.CX + hw - 5)):
                phase = (k * 3 + side * 2) % 4
                if (f + phase) % 4 != 0:
                    continue
                ly = st - 14 - 4
                bright = ['..KKK..', '.KhhhK.', 'KhhWhhK', 'KhhhhbK', 'KhhhbbK', '.KbbbK.', '..KKK..']
                for j, row in enumerate(bright):
                    for i, ch in enumerate(row):
                        if ch == '.':
                            continue
                        o.set(px - 2 + i, ly - 3 + j, {'K': K, 'h': hi, 'b': base, 'W': WH}[ch])
                for y in range(ly - 13, ly + 14):
                    for x in range(px - 13, px + 15):
                        if not (0 <= x < bg.W and 0 <= y < bg.H) or top[y][x] not in ('sky',):
                            continue
                        d = math.hypot(x - (px + 0.5), y - ly)
                        if 6 < d < 13 and dith(x + 1, y + 2, (1 - d / 13.0) * 0.8) and comp.p[y][x] in (N0, P0):
                            o.set(x, y, IN)

        # --- big stars twinkle
        for i, (sx, sy) in enumerate(bg.BIG_STARS):
            ph = (f + i * 5) % 6
            if ph == 0:
                for d, col in ((1, WH2), (2, G5)):
                    for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                        x, y = sx + dx, sy + dy
                        if top[y][x] == 'sky':
                            o.set(x, y, col)
            elif ph == 3:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    x, y = sx + dx, sy + dy
                    if top[y][x] == 'sky':
                        o.set(x, y, sky_plain.p[y][x])
                if top[sy][sx] == 'sky':
                    o.set(sx, sy, G5)

        # --- glint across the padlock body (frames 6, 7)
        if f in (6, 7):
            card = invite.card()
            pad_x = bg.CARD_X + card.w // 2 - 7
            cy = 4 + 27 + 5
            pad_y = bg.CARD_Y + cy - 6
            gx0 = 3 if f == 6 else 8
            for j in range(3):
                x, y = pad_x + gx0 + j, pad_y + 8 + (2 - j)
                if top[y][x] == 'invite' and comp.p[y][x] in (TN, YL, GO):
                    o.set(x, y, WH if j == 1 else SK)
        frames.append(o)
    return comp, frames


if __name__ == '__main__':
    comp, frames = build()
    strip = Canvas(bg.W * N, bg.H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * bg.W, 0)
    p = strip.save(os.path.join(OUT, 'fx_strip.png'))
    # preview: each frame composited, tower region, 2x, stacked
    for i in (0, 3, 6, 9):
        c = comp.copy()
        c.blit(frames[i], 0, 0)
        c.save(os.path.join(OUT, 'fx_comp_%02d.png' % i))
    counts = [sum(1 for y in range(bg.H) for x in range(bg.W) if fr.p[y][x] is not None) for fr in frames]
    print('overlay pixels per frame', counts)
