"""Build beast Bixby's pound + spin attack sheets and previews.

  python quake_build.py build      -> ../final_quake/*.png (+ layer strips), lint + margin checks
  python quake_build.py previews   -> GIFs per animation, the whole-attack GIF, a 1920x1080 arena
                                      mockup at the busiest moment, and a 6x close-up of the new FX
                                      (env BIXBY_QUAKE_PREVIEWS)
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib
from lib import *
from pal import PALC
from pngio import read_png, write_png, crop, scale, blank
import anim_rig as AR
import quake_poses as QP
import quake_spin as QS
import quake_fx as QF
import fx2 as FX
import faces2 as F2
import small_art as SA

OUT = os.path.join(HERE, '..', 'final_quake')
PREVIEWS = os.environ.get('BIXBY_QUAKE_PREVIEWS', os.path.join(HERE, '..', 'bixby_quake_previews'))
ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/'
FLOOR = (136, 180, 99, 255)          # ArenaScene Panel/ColorRect
WALL = (113, 152, 79, 255)
RAIL = (113, 152, 79, 255)
FW, FH = 192, 160
B = 3                                 # the game's sprite scale

ALLOWED = set(PALC.values()) | set(FX.FX_PAL.values()) | set(QF.SONIC.values()) | \
    set(F2.EXTRA.values()) | set(SA.BPAL.values()) | set(SA.LPAL.values())

# ------------------------------------------------------------------ timing (ms per frame)
POUND_MS = [90, 120, 70, 80, 80, 120]
SPIN_MS = [110, 90, 50, 50, 50, 50, 100, 150]
DIZZY_MS = [130, 130, 130, 130]
CRACK_MS = [70, 70, 120, 120]
BURST_MS = [45, 45, 50, 55, 65, 90]
WAVE_MS = [60, 60, 60, 60]
BEAM_MS = [45, 45, 45, 45]

LAYERS = ['fx_back', 'wings', 'body', 'arms', 'fx_front']


# ------------------------------------------------------------------ frames
def pound_frames():
    out = []
    for i in range(6):
        L = QP.pound_layers(i)
        back, front = QF.pound_fx(i, QP.pound_paws(i))
        out.append(dict(fx_back=back, wings=L['wings'], body=L['body'], arms=L['arms'], fx_front=front))
    return out


def spin_frames():
    out = []
    for i in range(QS.N_FRAMES):
        fr = QS.spin_frame(i)
        out.append(dict(fx_back=fr['fx_back'], wings=None, body=fr['body'], arms=None,
                        fx_front=fr['fx_front']))
    return out


def dizzy_frames():
    out = []
    for i in range(4):
        P = QP.dizzy_pose(i)
        wings, body = AR.render(P, dy=QP.DY)
        back, front = QF.dizzy_fx(i, P)
        out.append(dict(fx_back=back, wings=wings, body=body, arms=None, fx_front=front))
    return out


CHAR_SHEETS = [('pound', pound_frames), ('spin', spin_frames), ('dizzy', dizzy_frames)]


def flatten(fr, w=FW, h=FH):
    cv = Canvas(w, h)
    for L in LAYERS:
        if fr.get(L) is not None:
            cv.blit(fr[L], 0, 0)
    return cv


# ------------------------------------------------------------------ build
def lint(path):
    w, h, px = read_png(path)
    alphas, off = set(), {}
    for row in px:
        for p in row:
            p = tuple(p)
            alphas.add(p[3])
            if p[3] and p not in ALLOWED:
                off[p] = off.get(p, 0) + 1
    ok = alphas <= {0, 255} and not off
    print('  lint %-28s %4dx%-4d alphas=%-10s off-palette=%-3d %s'
          % (os.path.basename(path), w, h, sorted(alphas), len(off),
             'OK' if ok else 'FAIL ' + str(sorted(off, key=off.get, reverse=True)[:3])))
    return ok


def edge_pixels(cv, m=1):
    return sum(1 for y in range(cv.h) for x in range(cv.w)
               if cv.px[y][x] is not None and (x < m or x > cv.w - 1 - m or y < m or y > cv.h - 1 - m))


def build():
    os.makedirs(OUT, exist_ok=True)
    ok = True
    for name, fn in CHAR_SHEETS:
        frs = fn()
        n = len(frs)
        comp = Canvas(FW * n, FH)
        for i, fr in enumerate(frs):
            comp.blit(flatten(fr), FW * i, 0)
        path = os.path.join(OUT, 'bixby_%s.png' % name)
        comp.save(path)
        ok &= lint(path)
        for L in LAYERS:
            if not any(fr.get(L) is not None for fr in frs):
                continue
            ls = Canvas(FW * n, FH)
            for i, fr in enumerate(frs):
                if fr.get(L) is not None:
                    ls.blit(fr[L], FW * i, 0)
            ls.save(os.path.join(OUT, 'layer_%s_%s.png' % (name, L)))
        bad = sum(edge_pixels(flatten(fr)) for fr in frs)
        print('  built bixby_%-8s %d frames, frame-edge pixels: %d' % (name, n, bad))
    for name, (w, h, n, fnf) in QF.SHEETS.items():
        strip = Canvas(w * n, h)
        for i in range(n):
            strip.blit(fnf(i), w * i, 0)
        path = os.path.join(OUT, name + '.png')
        strip.save(path)
        ok &= lint(path)
    print('BUILD', 'OK' if ok else 'LINT FAILURES')
    return ok


# ------------------------------------------------------------------ preview plumbing
def sheet_frames(path, fw, fh):
    w, h, px = read_png(path)
    px = [[tuple(p) for p in row] for row in px]
    return [crop(px, fw * i, 0, fw, fh) for i in range(w // fw)]


def blit(dst, src, x0, y0, s=1, flip=False):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        if flip:
            row = list(reversed(row))
        for x, p in enumerate(row):
            if not p[3]:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if 0 <= yy < H:
                    r = dst[yy]
                    for dx in range(s):
                        xx = x0 + x * s + dx
                        if 0 <= xx < W:
                            r[xx] = p
    return dst


def rot_frame(src, deg, pivot):
    """rotate a small RGBA frame about pivot (used for the sweeping sonic beams)"""
    cv = Canvas(len(src[0]), len(src))
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p[3]:
                cv.px[y][x] = p
    import rotsprite as RS
    r = RS.rotate(cv, deg, pivot, reclose=False)
    return r.rgba()


FLATTEN = 0.36          # how much the arena's viewing angle squashes a floor-plane sweep on screen


def beam_angle(a, k=FLATTEN):
    """screen angle (deg, clockwise from +x) of a beam fired radially outward by a head at orbit
    azimuth a. The sweep happens in the arena floor plane, which the camera sees edge-on-ish."""
    ar = math.radians(a)
    return math.degrees(math.atan2(math.sin(ar) * k, math.cos(ar)))


def beam_length(a, k=FLATTEN):
    """how long the beam reads on screen: full broadside, foreshortened to a stub when it points
    straight at or away from the camera. This is scale.x / scale.y on the Sprite2D."""
    ar = math.radians(a)
    return 0.45 + 1.55 * math.hypot(math.cos(ar), 0.22 * math.sin(ar))


def beam_on(dst, beam, x, y, deg, s=B, stretch=2.0):
    """one sonic beam whose mouth pivot sits at (x, y) screen px, pointing deg degrees clockwise
    from +x. `stretch` scales it along its own axis only, exactly like scale.x on a Sprite2D."""
    pw, ph = len(beam[0]), len(beam)
    R = int(pw * stretch) + 12
    W2 = H2 = R * 2
    big = [[(0, 0, 0, 0)] * W2 for _ in range(H2)]
    px0 = R - int(QF.BEAM_PIVOT[0] * stretch)
    py0 = R - QF.BEAM_PIVOT[1]
    for yy in range(ph):
        row = big[py0 + yy]
        for xx in range(int(pw * stretch)):
            p = beam[yy][min(pw - 1, int(xx / stretch))]
            if p[3]:
                row[px0 + xx] = p
    r = rot_frame(big, deg, (R, R))
    blit(dst, r, int(x - R * s), int(y - R * s), s)


_ARENA = []


def arena_base():
    """the fight arena from ArenaScene.tscn: black surround, crowd band, green floor panel"""
    if _ARENA:
        return [row[:] for row in _ARENA[0]]
    px = [[(0, 0, 0, 255)] * 1920 for _ in range(1080)]
    crowd = [[tuple(p) for p in row] for row in read_png(ASSETS + 'Environment/crowd_v2.png')[2]]
    ch, cw = len(crowd), len(crowd[0])
    for y in range(0, 130):
        sy = min(ch - 1, int(y / 130.0 * ch))
        for x in range(1920):
            sx = min(cw - 1, int(x / 1920.0 * cw))
            p = crowd[sy][sx]
            px[y][x] = p if p[3] else (0, 0, 0, 255)
    for y in range(100, 980):
        row = px[y]
        for x in range(100, 1820):
            row[x] = FLOOR
    for (x0, y0, x1, y1) in ((84, 105, 99, 987), (1819, 99, 1834, 987), (83, 987, 1833, 1010)):
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[y][x] = (113, 152, 79, 255)
    _ARENA.append([row[:] for row in px])
    return px


def shade(dst, src, x0, y0, s=1, alpha=0.36):
    H, W = len(dst), len(dst[0])
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if not p[3]:
                continue
            for dy in range(s):
                yy = y0 + y * s + dy
                if 0 <= yy < H:
                    r = dst[yy]
                    for dx in range(s):
                        xx = x0 + x * s + dx
                        if 0 <= xx < W:
                            q = r[xx]
                            r[xx] = (int(q[0] * (1 - alpha)), int(q[1] * (1 - alpha)),
                                     int(q[2] * (1 - alpha)), 255)


def previews():
    from gifio2 import write_gif
    os.makedirs(PREVIEWS, exist_ok=True)
    P_ = sheet_frames(os.path.join(OUT, 'bixby_pound.png'), FW, FH)
    S_ = sheet_frames(os.path.join(OUT, 'bixby_spin.png'), FW, FH)
    D_ = sheet_frames(os.path.join(OUT, 'bixby_dizzy.png'), FW, FH)
    CR = sheet_frames(os.path.join(OUT, 'bixby_quake_crack.png'), QF.CRACK_W, QF.CRACK_H)
    BU = sheet_frames(os.path.join(OUT, 'bixby_quake_burst.png'), QF.BURST_W, QF.BURST_H)
    WV = sheet_frames(os.path.join(OUT, 'bixby_quake_wave.png'), QF.WAVE_W, QF.WAVE_H)
    BM = sheet_frames(os.path.join(OUT, 'bixby_sonic_beam.png'), QF.BEAM_W, QF.BEAM_H)
    shadow = sheet_frames(ASSETS + 'Characters/Bixby/bixby_beast_shadow_ground.png', 192, 48)
    pl_w, pl_h, pl_px = read_png(ASSETS + 'Characters/MainPlayer/player_4dir_sheet.png')
    player = crop([[tuple(p) for p in r] for r in pl_px], 0, 32, 32, 32)

    def char_gif(frames, ms, name, s=3, pad=6):
        outs = []
        for f in frames:
            cv = blank(FW + pad * 2, FH + pad, FLOOR)
            blit(cv, shadow[1], pad, 151 - 25 + pad // 2)
            blit(cv, f, pad, pad // 2)
            outs.append(cv)
        write_gif(os.path.join(PREVIEWS, name), outs, [max(2, round(m / 10)) for m in ms], scale=s)
        print('gif', name, sum(ms), 'ms')

    char_gif(P_, POUND_MS, 'bixby_pound_3x.gif')
    char_gif(S_, SPIN_MS, 'bixby_spin_3x.gif')
    char_gif(D_, DIZZY_MS, 'bixby_dizzy_3x.gif')
    # the two loops on their own, at the cadence the coder should use
    char_gif([P_[i] for i in (2, 3, 4, 5)] * 3, [POUND_MS[i] for i in (2, 3, 4, 5)] * 3,
             'bixby_pound_loop_x3_3x.gif')
    char_gif([S_[i] for i in (2, 3, 4, 5)] * 4, [SPIN_MS[i] for i in (2, 3, 4, 5)] * 4,
             'bixby_spin_loop_x4_3x.gif')

    def fx_gif(frames, ms, name, s, pad=4, gy=None):
        w, h = len(frames[0][0]), len(frames[0])
        outs = []
        for f in frames:
            cv = blank(w + pad * 2, h + pad * 2, FLOOR)
            blit(cv, f, pad, pad)
            outs.append(cv)
        write_gif(os.path.join(PREVIEWS, name), outs, [max(2, round(m / 10)) for m in ms], scale=s)
        print('gif', name)

    fx_gif(CR, CRACK_MS, 'bixby_quake_crack_6x.gif', 6)
    fx_gif(BU, BURST_MS, 'bixby_quake_burst_5x.gif', 5)
    fx_gif(BM, BEAM_MS, 'bixby_sonic_beam_4x.gif', 4)
    # the wave as a row of 7 tiles, which is how it is actually used
    outs = []
    for k in range(4):
        cv = blank(QF.WAVE_PERIOD * 7 + 8, QF.WAVE_H + 8, FLOOR)
        for i in range(7):
            blit(cv, WV[k], 4 + QF.WAVE_PERIOD * i, 4)
        outs.append(cv)
    write_gif(os.path.join(PREVIEWS, 'bixby_quake_wave_row_4x.gif'), outs,
              [max(2, round(m / 10)) for m in WAVE_MS], scale=4)
    print('gif bixby_quake_wave_row_4x.gif')

    closeup(CR, BU, WV, BM)
    full_attack_gif(P_, S_, D_, CR, BU, WV, BM, shadow, player)
    mockup(S_, CR, BU, WV, BM, shadow, player)


# ------------------------------------------------------------------ 6x close-up of the new FX
def closeup(CR, BU, WV, BM):
    W, H = 300, 176
    cv = blank(W, H, FLOOR)
    blit(cv, CR[3], 6, 10)
    blit(cv, BU[3], 60, 2)
    for i in range(3):
        blit(cv, WV[1], 130 + QF.WAVE_PERIOD * i, 34)
    blit(cv, BM[2], 6, 76)
    blit(cv, BM[0], 150, 120)
    write_png(os.path.join(PREVIEWS, 'bixby_quake_fx_closeup_6x.png'), W * 6, H * 6, scale(cv, 6))
    print('closeup bixby_quake_fx_closeup_6x.png')


# ------------------------------------------------------------------ the whole attack
GX_SCREEN, GY_SCREEN = 960, 760           # Bixby's feet on the arena floor
PLAYER_PATH = [(1430, 700), (1330, 780), (1180, 840), (1080, 880)]


def wave_line(px, x0, y0, x1, y1, k, frames, n):
    """a line of wave tiles marching out from the burst at (x0, y0) toward (x1, y1)"""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    step = QF.WAVE_PERIOD * B
    ux, uy = dx / L, dy / L
    for i in range(n):
        d = step * (i + 1)
        if d > L:
            break
        x, y = x0 + ux * d, y0 + uy * d
        blit(px, frames[(k + i) % 4], int(x - QF.WAVE_W * B // 2), int(y - QF.WAVE_GY * B), B)


def stage(sprite, shadow, player, player_at, fx=(), front=(), s=B):
    px = arena_base()
    shade(px, shadow, GX_SCREEN - 96 * s, GY_SCREEN - 25 * s, s)
    for fn in fx:
        fn(px)
    blit(px, sprite, GX_SCREEN - 96 * s, GY_SCREEN - 151 * s, s)
    for fn in front:
        fn(px)
    if player_at:
        blit(px, player, int(player_at[0] - 16 * 2), int(player_at[1] - 30 * 2), 2)
    return px


def beams_for(frame_index, beam, out_back, out_front):
    """queue one sonic beam per head; the far heads' beams pass behind him, the near ones in front"""
    for (a, mx, my, near) in QS.mouth_anchors(frame_index):
        sx = GX_SCREEN + (mx - 96) * B
        sy = GY_SCREEN + (my - 151) * B
        deg = beam_angle(a)
        st = beam_length(a)
        tgt = out_front if near else out_back
        tgt.append(lambda px, sx=sx, sy=sy, deg=deg, st=st: beam_on(px, beam, sx, sy, deg, stretch=st))


def full_attack_frames(P_, S_, D_, CR, BU, WV, BM, shadow, player):
    """the whole attack, staged on the arena: returns (list of thunks -> RGBA frame, list of ms)"""
    # window on the action, 2x downscale of a 1920x1080 stage is too big for a gif: crop instead
    WX, WY, WW, WH = 380, 200, 1200, 800
    seq = []            # (sprite frame, ms, fx list, player pos)

    def crack_fx(pos, k):
        def fn(px):
            blit(px, CR[min(3, k)], int(pos[0] - QF.CRACK_C[0] * B), int(pos[1] - QF.CRACK_C[1] * B), B)
        return fn

    def burst_fx(pos, k):
        def fn(px):
            blit(px, BU[k], int(pos[0] - QF.BURST_C[0] * B), int(pos[1] - QF.BURST_C[1] * B), B)
        return fn

    def wave_fx(pos, k, n, tgt):
        def fn(px):
            wave_line(px, pos[0], pos[1], tgt[0], tgt[1], k, WV, n)
        return fn

    t = 0
    # --- rear up and three pounds
    order = [0, 1] + [2, 3, 4, 5] * 3
    crack_at = []
    pi = 0
    for j, fi in enumerate(order):
        fx = []
        if fi == 3:                                  # a slam lands: plant a crack at the player
            crack_at.append((PLAYER_PATH[min(pi, 3)], t))
            pi += 1
        for (pos, born) in crack_at:
            age = (t - born) // 80
            fx.append(crack_fx(pos, min(3, age)))
        seq.append((P_[fi], POUND_MS[fi], list(fx), PLAYER_PATH[min(pi, 3)]))
        t += POUND_MS[fi]
    # --- spin: beams sweep while the cracks erupt and the waves roll in
    spin_order = [0, 1] + [2, 3, 4, 5] * 4 + [6, 7]
    ang = 0.0
    for j, fi in enumerate(spin_order):
        fx = []
        for bi, (pos, born) in enumerate(crack_at):
            age = t - born
            if age < 1200:
                fx.append(crack_fx(pos, min(3, 2 + (age // 120) % 2)))
            elif age < 1200 + sum(BURST_MS):
                a = age - 1200
                k = 0
                acc = 0
                for kk, ms in enumerate(BURST_MS):
                    acc += ms
                    if a < acc:
                        k = kk
                        break
                fx.append(burst_fx(pos, k))
                if k >= 2:
                    fx.append(wave_fx(pos, j, min(6, (k - 1) * 2), PLAYER_PATH[3]))
            elif age < 2400:
                fx.append(wave_fx(pos, j, 6, PLAYER_PATH[3]))
        seq.append((S_[fi], SPIN_MS[fi], list(fx), PLAYER_PATH[3]))
        t += SPIN_MS[fi]
    # --- dizzy
    for rep in range(2):
        for i in range(4):
            seq.append((D_[i], DIZZY_MS[i], [], PLAYER_PATH[3]))
            t += DIZZY_MS[i]

    def make(i):
        sprite, ms, fx, ppos = seq[i]
        back_fx, front_fx = list(fx), []
        gi = i - len(order)
        if 0 <= gi < len(spin_order):
            fi = spin_order[gi]
            if fi >= 1:
                beams_for(fi, BM[gi % 4], back_fx, front_fx)
        px = stage(sprite, shadow, player, ppos, back_fx, front_fx)
        return [row[WX:WX + WW] for row in px[WY:WY + WH]]

    return [(lambda i=i: make(i)) for i in range(len(seq))], [s[1] for s in seq]


def full_attack_gif(P_, S_, D_, CR, BU, WV, BM, shadow, player):
    from gifio2 import write_gif
    thunks, ms = full_attack_frames(P_, S_, D_, CR, BU, WV, BM, shadow, player)
    write_gif(os.path.join(PREVIEWS, 'bixby_pound_spin_full.gif'), lambda i: thunks[i](),
              [max(2, round(m / 10)) for m in ms], scale=1)
    print('gif bixby_pound_spin_full.gif', sum(ms), 'ms,', len(ms), 'frames')


# ------------------------------------------------------------------ 1920x1080 mockup
def mockup(S_, CR, BU, WV, BM, shadow, player):
    fi = 3
    ppos = (1215, 962)
    back, front = [], []

    def add(fn):
        back.append(fn)
    # two earthquakes erupting and rolling at the player, plus a third crack still charging
    for (pos, k, n) in (((1500, 640), 3, 6), ((900, 866), 2, 4)):
        add(lambda px, p=pos, k=k, n=n: wave_line(px, p[0], p[1], ppos[0] + 80, ppos[1] - 70, k, WV, n))
        add(lambda px, p=pos, k=k: blit(px, BU[k], int(p[0] - QF.BURST_C[0] * B),
                                        int(p[1] - QF.BURST_C[1] * B), B))
    add(lambda px: blit(px, CR[3], int(1660 - QF.CRACK_C[0] * B), int(840 - QF.CRACK_C[1] * B), B))
    beams_for(fi, BM[2], back, front)
    px = stage(S_[fi], shadow, player, ppos, back, front)
    out = os.path.join(PREVIEWS, 'mockup_arena_pound_spin_1920x1080.png')
    write_png(out, 1920, 1080, px)
    print('mockup', out)


if __name__ == '__main__':
    what = sys.argv[1:] or ['build', 'previews']
    if 'build' in what:
        build()
    if 'previews' in what:
        previews()
