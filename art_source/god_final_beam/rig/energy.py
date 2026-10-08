"""The charge ball, the beam and its bursts, drawn as hard-banded heat fields quantized to a 7-colour ramp.
Two colour takes share every shape: A = classic blue-white, B = the HYPE ramp (the meter's and the super uppercut's
white / yellow / pink / purple). The beam is authored travelling along +x; the coder rotates it."""
import math
import numpy as np
from PIL import Image
from common import *

TAU = math.tau

# hottest first: (threshold, colour)
RAMPS = {
    "a": [(0.86, "ffffff"), (0.72, "cbdbfc"), (0.58, "8fb8ff"), (0.44, "639bff"), (0.30, "3f63e8"),
          (0.17, "2b2fb0"), (0.06, "1e1a6e")],
    "b": [(0.86, "ffffff"), (0.72, "fff7b8"), (0.58, "fbf236"), (0.44, "f5a05a"), (0.30, "d77bba"),
          (0.17, "9a4b9e"), (0.06, "5a2e6e")],
}
GLOWS = {"a": "2a4ce0", "b": "c8408a"}
GLOW_STEPS = [(0.75, 0.55), (0.5, 0.38), (0.28, 0.24), (0.1, 0.12)]
SMOKE = ["9badb7", "847e87", "595652"]


def rgba(h):
    return np.array(hexc(h), np.uint8)


def quant(h, take):
    out = np.zeros(h.shape + (4,), np.uint8)
    done = np.zeros(h.shape, bool)
    for thr, col in RAMPS[take]:
        m = (h >= thr) & ~done
        out[m] = rgba(col)
        done |= m
    return Image.fromarray(out, "RGBA")


def glow_quant(g, take, gain=1.0):
    out = np.zeros(g.shape + (4,), np.uint8)
    done = np.zeros(g.shape, bool)
    c = rgba(GLOWS[take])
    for thr, a in GLOW_STEPS:
        m = (g >= thr) & ~done
        out[m] = (c[0], c[1], c[2], int(255 * min(1.0, a * gain)))
        done |= m
    return Image.fromarray(out, "RGBA")


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def rng(seed):
    return np.random.default_rng(seed)


# ------------------------------------------------------------------------------------------------ the beam body
BODY_LEN, BODY_H, BODY_GLOW_H = 32, 104, 144
HALF = 34.0
FLOW = 8  # px a frame along +x; 4 frames = one 32 px period, so the strip loops


def _streaks():
    r = rng(7)
    out = []
    for i in range(9):
        out.append((float(r.integers(-23, 24)), int(r.integers(0, 32)), int(r.integers(5, 12))))
    return out


STREAKS = _streaks()


def body_heat(x, yc, t, env=1.0):
    u = (x - FLOW * t) % 32
    ay = np.clip(np.abs(yc) - HALF * 0.6 * env, 0, None)
    v_top = ((u + 0.9 * ay) / 16.0) % 1.0
    v_bot = ((u + 8 + 0.9 * ay) / 16.0) % 1.0
    lick_top = 11.0 * (1 - v_top) ** 1.7 * (0.75 + 0.25 * np.sin(TAU * u / 32))
    lick_bot = 9.0 * (1 - v_bot) ** 1.7 * (0.75 + 0.25 * np.cos(TAU * u / 32))
    wob = 1.6 * np.sin(TAU * u / 32 + 0.6)
    W = np.where(yc < 0, HALF + wob + lick_top, HALF - wob + lick_bot) * env
    h = np.clip(1 - np.abs(yc) / W, 0, 1) ** 0.85
    h = h + 0.05 * np.sin(TAU * u / 32 * 2 + yc * 0.35) * (h > 0.1)
    for ys, x0, ln in STREAKS:
        m = (np.abs(yc - ys * env) < 0.6) & (((u - x0) % 32) < ln) & (h > 0.3)
        h = np.where(m, h + 0.22, h)
    return np.clip(h, 0, 1)


def beam_body(take, t):
    ys, xs = np.mgrid[0:BODY_H, 0:BODY_LEN].astype(np.float32)
    return quant(body_heat(xs, ys - (BODY_H - 1) / 2, t), take)


def beam_body_glow(take, t):
    ys, xs = np.mgrid[0:BODY_GLOW_H, 0:BODY_LEN].astype(np.float32)
    yc = ys - (BODY_GLOW_H - 1) / 2
    u = (xs - FLOW * t) % 32
    g = np.clip(1 - np.abs(yc) / (70 + 2 * np.sin(TAU * u / 32)), 0, 1) ** 1.1
    return glow_quant(g, take)


START_LEN = 64


def start_env(xs):
    return 0.28 + 0.72 * smoothstep(0, 48, xs)


def beam_start(take, t):
    """From the hands' width (ball 5) out to the full beam; its last 32 px are exactly body tile phase 0's 32 px,
    so body tiles laid on from x = 64 join it seamlessly."""
    ys, xs = np.mgrid[0:BODY_H, 0:START_LEN].astype(np.float32)
    yc = ys - (BODY_H - 1) / 2
    env = start_env(xs)
    h = body_heat(xs, yc, t, env)
    h = np.where((xs < 6) & (h > 0.06), np.clip(h + (6 - xs) * 0.05, 0, 1), h)
    return quant(h, take)


def beam_start_glow(take, t):
    ys, xs = np.mgrid[0:BODY_GLOW_H, 0:START_LEN].astype(np.float32)
    yc = ys - (BODY_GLOW_H - 1) / 2
    env = start_env(xs)
    g = np.clip(1 - np.abs(yc) / (70 * env + 4), 0, 1) ** 1.1
    return glow_quant(g, take)


def beam_spiral(take, t):
    """Additive helix wrapping the beam, plus crackle along its rims. Tiles every 32 px, 4 frames."""
    ramp = RAMPS[take]
    img = np.zeros((BODY_H, BODY_LEN, 4), np.uint8)
    cy = (BODY_H - 1) / 2
    for strand in (0, 1):
        for x in range(BODY_LEN):
            u = (x - FLOW * t) % 32
            ph = TAU * u / 32 + strand * math.pi
            y = cy + 27 * math.sin(ph)
            front = math.cos(ph) > 0
            col = rgba(ramp[0][1] if front else ramp[2][1])
            a = 230 if front else 110
            for dy in ((0, 1) if front else (0,)):
                yy = int(round(y)) + dy
                if 0 <= yy < BODY_H:
                    img[yy, x] = (col[0], col[1], col[2], a)
    r = rng(100 + t)
    col = rgba(ramp[0][1])
    for k in range(2):
        side = -1 if (k + t) % 2 == 0 else 1
        x = int(r.integers(0, 20))
        y = cy + side * r.integers(18, 29)
        for step in range(int(r.integers(8, 13))):
            x += 1
            y += side * r.choice([0, 1, 1, 2])
            if 0 <= x < BODY_LEN and 0 <= int(y) < BODY_H:
                img[int(y), x] = (col[0], col[1], col[2], 235)
    return Image.fromarray(img, "RGBA")


# ------------------------------------------------------------------------------------------------ the beam head
HEAD = 144


def head_heat(t, cx=78.0, cy=71.5, R=46.0, impact=0.0):
    ys, xs = np.mgrid[0:HEAD, 0:HEAD].astype(np.float32)
    dx, dy = xs - cx, ys - cy
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    back = np.clip(-np.cos(th), 0, 1)
    side = np.abs(np.sin(th))
    # tongues: round at the front, sweeping back off the top and bottom, flickering
    ph = 6 * th + 0.08 * r - TAU * t / 4
    flick = np.clip(np.sin(ph), 0, 1) ** 1.5
    Rf = R * (1 + 0.05 * np.sin(4 * th - TAU * t / 4)) + back * side * (10 + 20 * flick) + back * 8 * flick
    h = np.clip(1 - np.clip(r / Rf, 0, 1) ** 1.8, 0, 1) * (r < Rf)
    # the swirl: three arms turning inwards
    h = h + 0.14 * np.sin(3 * th - r * 0.26 + TAU * t / 4) * (h > 0.12) * (r > R * 0.25)
    # a white-hot heart, set forward
    h = h + 0.3 * (np.hypot(dx - R * 0.2, dy) < R * 0.38)
    bh = body_heat(xs - cx, ys - cy, t)
    h = np.where(xs < cx, np.maximum(h, bh), h)
    return np.clip(h, 0, 1), xs, ys, r


def beam_head(take, t):
    h, *_ = head_heat(t)
    return quant(h, take)


def beam_head_glow(take, t):
    ys, xs = np.mgrid[0:HEAD, 0:HEAD].astype(np.float32)
    r = np.hypot(xs - 78, ys - 71.5)
    g = np.clip(1 - r / 71, 0, 1) ** 1.1
    return glow_quant(g, take, 0.9)


# ------------------------------------------------------------------------------------------------ the impact
IMPACT = 208
IMPACT_K = 1.3
IMPACT_FRAMES = 8  # 0-3 the burst, once; 4-7 the churn, looped while the beam holds him


def _rays(r, th, spin, length, seed, n):
    """n tapered rays at uneven angles and lengths, turning by spin."""
    g = rng(seed)
    out = np.zeros_like(r)
    for k in range(n):
        a = TAU * (k + g.uniform(-0.3, 0.3)) / n + spin
        ln = length * g.uniform(0.55, 1.0)
        w = g.uniform(1.6, 3.0)
        d = np.abs((th - a + math.pi) % TAU - math.pi) * r
        m = (d < w * np.clip(1 - r / ln, 0, 1)) & (r < ln)
        out = np.where(m, np.maximum(out, np.clip(1.05 - r / ln, 0, 1)), out)
    return out


def impact_heat(i):
    ys, xs = np.mgrid[0:IMPACT, 0:IMPACT].astype(np.float32)
    dx, dy = xs - (IMPACT - 1) / 2, ys - (IMPACT - 1) / 2
    r = np.hypot(dx, dy) / IMPACT_K
    th = np.arctan2(dy, dx)
    h = np.zeros_like(r)
    if i < 4:
        core = [34, 30, 26, 24][i]
        ring = [0, 44, 58, 70][i]
        ring_w = [0, 6, 5, 3][i]
        h = np.clip(1 - r / core, 0, 1) ** 0.5 * 1.2
        if ring:
            h = np.maximum(h, np.clip(1 - np.abs(r - ring) / ring_w, 0, 1) * [0, 0.95, 0.75, 0.5][i])
        h = np.maximum(h, _rays(r, th, i * 0.07, [60, 76, 78, 72][i], seed=1, n=13) * 0.95)
    else:
        k = i - 4
        spin = TAU * k / 16
        wob = 1 + 0.12 * np.sin(6 * th + TAU * k / 4)
        h = np.clip(1 - r / (28 * wob), 0, 1) ** 0.6 * 1.15
        h = np.maximum(h, _rays(r, th, spin, 58 + 6 * (k % 2), seed=2 + k % 2, n=11))
        ring = 34 + 7 * k
        h = np.maximum(h, np.clip(1 - np.abs(r - ring) / 2.2, 0, 1) * (0.62 - 0.1 * k))
        h = h + 0.12 * np.sin(3 * th - r * 0.3 + TAU * k / 4) * (h > 0.15)
    return np.clip(h, 0, 1), r


def beam_impact(take, i):
    h, _ = impact_heat(i)
    return quant(h, take)


def beam_impact_glow(take, i):
    _, r = impact_heat(i)
    rad = [78, 80, 80, 76, 66, 68, 66, 68][i]
    g = np.clip(1 - r / rad, 0, 1) ** 0.8
    return glow_quant(g, take, [1.4, 1.3, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0][i])


# ------------------------------------------------------------------------------------------------ the muzzle
MUZZLE = 80
MUZZLE_FRAMES = 6  # 0-1 the release flash, once; 2-5 the flare at his hands, looped


def muzzle_heat(i):
    ys, xs = np.mgrid[0:MUZZLE, 0:MUZZLE].astype(np.float32)
    dx, dy = xs - 39.5, ys - 39.5
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    fwd = np.clip(np.cos(th), 0, 1)
    if i < 2:
        R = [30, 36][i]
        h = np.clip(1 - r / (R * (0.75 + 0.25 * fwd)), 0, 1) ** 0.5 * 1.3
        h = np.maximum(h, _rays(r, th, 0.3 * i, 39, seed=5, n=9) * 1.1)
    else:
        k = i - 2
        R = 15 + 2 * (k % 2)
        spikes = np.clip(np.cos(10 * th + TAU * k / 8), 0, 1) ** 4
        h = np.clip(1 - r / (R * (0.45 + 0.95 * fwd) + 12 * spikes * (0.12 + fwd)), 0, 1) ** 0.6 * 1.15
    return np.clip(h, 0, 1), r


def beam_muzzle(take, i):
    h, _ = muzzle_heat(i)
    return quant(h, take)


def beam_muzzle_glow(take, i):
    _, r = muzzle_heat(i)
    g = np.clip(1 - r / (39 if i < 2 else 30), 0, 1) ** 0.9
    return glow_quant(g, take, 1.3 if i < 2 else 1.0)


# ------------------------------------------------------------------------------------------------ the ball
BALL = 64
BALL_R = [3.0, 4.5, 6.0, 8.0, 10.5]  # core radius a bar, texels


def ball_heat(size, t):
    """size 0-4 (bars 1-5), t 0-3 the pulse."""
    ys, xs = np.mgrid[0:BALL, 0:BALL].astype(np.float32)
    dx, dy = xs - 31.5, ys - 31.5
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    R = BALL_R[size] * (1 + 0.07 * math.sin(TAU * t / 4))
    unstable = [0.0, 0.04, 0.07, 0.11, 0.18][size]
    Rs = R * (1 + unstable * np.sin(6 * th + TAU * t / 4 * 2))
    q = np.clip(r / Rs, 0, 2)
    # the sphere: a white heart, shells out to a hot rim
    h = np.where(q < 1, 1 - q ** 2.6 * 0.82, 0)
    h = np.maximum(h, np.exp(-((r - Rs * 0.93) / 0.9) ** 2) * 0.74 * (q < 1.15))
    # the swirl turning in it
    h = h + 0.07 * np.sin(3 * th - r * (1.6 / max(R, 1)) * 3 + TAU * t / 4) * (q < 0.9) * (q > 0.3)
    # flame wisps curling up off it in the draught
    up = np.clip(-np.sin(th), 0, 1) ** 1.5
    ph = (3 + size) * th + TAU * t / 4 + size
    tongue = np.clip(np.sin(ph), 0, 1) ** 2 * up * (0.6 + 0.5 * R)
    wisp = (q >= 0.95) & (r < Rs + tongue)
    h = np.where(wisp, np.maximum(h, 0.24 + 0.2 * (1 - (r - Rs) / (tongue + 0.01))), h)
    return np.clip(h, 0, 1), r, R


def ball_crackle(img, size, t, take):
    """Size 5 only: arcs leaping off it and sparks spitting - barely held."""
    if size < 3:
        return img
    a = np.asarray(img).copy()
    r = rng(500 + size * 10 + t)
    ramp = RAMPS[take]
    n_arcs = 2 if size == 3 else 4
    for k in range(n_arcs):
        ang = r.uniform(0, TAU)
        R = BALL_R[size]
        x, y = 31.5 + math.cos(ang) * R, 31.5 + math.sin(ang) * R
        for step in range(int(R * (0.9 if size == 3 else 1.4))):
            ang2 = ang + r.uniform(-0.9, 0.9)
            x += math.cos(ang2) * 1.0
            y += math.sin(ang2) * 1.0
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < BALL and 0 <= yi < BALL:
                c = rgba(ramp[0][1] if step % 3 else ramp[1][1])
                a[yi, xi] = c
    for k in range(3 + size * 2):
        ang = r.uniform(0, TAU)
        d = BALL_R[size] * r.uniform(1.6, 2.6)
        xi, yi = int(31.5 + math.cos(ang) * d), int(31.5 + math.sin(ang) * d)
        if 0 <= xi < BALL and 0 <= yi < BALL:
            a[yi, xi] = rgba(ramp[r.integers(0, 3)][1])
    return Image.fromarray(a, "RGBA")


def ball(take, size, t):
    h, _, _ = ball_heat(size, t)
    return ball_crackle(quant(h, take), size, t, take)


def ball_glow(take, size, t):
    _, r, R = ball_heat(size, t)
    g = np.clip(1 - r / (R * 2.0 + 4), 0, 1) ** 1.2
    return glow_quant(g, take, 0.7 + 0.1 * size)


FIZZLE_FRAMES = 6


def ball_fizzle(take, i):
    """The under-charged ball giving out in his hands: it wobbles, spits, pops, and goes to smoke."""
    ys, xs = np.mgrid[0:BALL, 0:BALL].astype(np.float32)
    dx, dy = xs - 31.5, ys - 31.5
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    out = np.zeros((BALL, BALL, 4), np.uint8)
    if i < 3:
        R = [6.0, 4.2, 2.4][i]
        Rf = R * (1 + [0.3, 0.45, 0.6][i] * np.sin(5 * th + i * 2.0))
        h = np.clip(1 - r / Rf, 0, 1) ** 0.7 * [1.0, 0.85, 1.2][i]
        out = np.asarray(quant(np.clip(h, 0, 1), take)).copy()
    rr = rng(900 + i)
    ramp = RAMPS[take]
    # sparks spat outwards, further each frame
    if 1 <= i <= 4:
        for k in range(14):
            ang = rr.uniform(0, TAU)
            d = (4 + 5 * i) * rr.uniform(0.6, 1.1)
            xi, yi = int(31.5 + math.cos(ang) * d), int(31.5 + math.sin(ang) * d + i * 1.5)
            if 0 <= xi < BALL and 0 <= yi < BALL:
                out[yi, xi] = rgba(ramp[min(6, 1 + i + rr.integers(0, 2))][1])
    # smoke puffs drifting up
    if i >= 2:
        for k, (ox, oy, pr) in enumerate([(-3, -2, 3.5), (3, -4, 3.0), (0, -7, 2.6), (-5, -8, 2.0)]):
            grow = (i - 2) * 1.2
            cx, cy = 31.5 + ox * (1 + 0.3 * (i - 2)), 31.5 + oy - (i - 2) * 3
            rad = pr + grow * 0.5
            m = np.hypot(xs - cx, ys - cy) < rad
            shade = SMOKE[min(2, (i - 2) // 1 if k % 2 == 0 else (i - 1) // 2)]
            if i == 5 and k % 2:
                continue
            col = rgba(shade)
            fade = [255, 230, 190, 140][min(3, i - 2)]
            sel = m & (out[..., 3] == 0)
            out[sel] = (col[0], col[1], col[2], fade)
    return Image.fromarray(out, "RGBA")


def ball_fizzle_glow(take, i):
    ys, xs = np.mgrid[0:BALL, 0:BALL].astype(np.float32)
    r = np.hypot(xs - 31.5, ys - 31.5)
    rad = [20, 16, 22, 10, 0, 0][i]
    if rad == 0:
        return Image.new("RGBA", (BALL, BALL), (0, 0, 0, 0))
    g = np.clip(1 - r / rad, 0, 1) ** 0.9
    return glow_quant(g, take, [0.9, 0.7, 1.2, 0.5, 0, 0][i])


# ------------------------------------------------------------------------------------------------ Burak's aura
AURA_W, AURA_H = 64, 64


def aura(take, t, level):
    """Flame aura round him while he charges, feet at the cell's (32, 44) like his 48 cell's (24, 36) + (8, 8).
    level 0-2: bars 1-2, 3-4, 5. Additive."""
    ys, xs = np.mgrid[0:AURA_H, 0:AURA_W].astype(np.float32)
    cx, cy = 31.5, 30.0
    dx, dy = (xs - cx) / (13 + 3 * level), (ys - cy) / (17 + 3 * level)
    r = np.hypot(dx, dy)
    th = np.arctan2(ys - cy, xs - cx)
    up = np.clip(-np.sin(th), 0, 1)
    flick = np.clip(np.sin(9 * th - TAU * t / 4 * 2 + xs * 0.05), 0, 1) ** 2
    rr = 1.0 + up * flick * (0.45 + 0.2 * level) - np.clip(dy, 0, None) * 0.25
    shell = np.clip(1 - np.abs(r - rr * 0.82) / 0.22, 0, 1) * (ys < 46)
    rise = np.clip(1 - r / (rr * 0.9), 0, 1) * 0.45
    g = np.maximum(shell, rise)
    out = np.zeros((AURA_H, AURA_W, 4), np.uint8)
    ramp = RAMPS[take]
    for thr, col, a in [(0.85, ramp[1][1], 0.85), (0.6, ramp[3][1], 0.7), (0.35, ramp[4][1], 0.5),
                        (0.15, ramp[5][1], 0.35)]:
        m = (g >= thr) & (out[..., 3] == 0)
        c = rgba(col)
        out[m] = (c[0], c[1], c[2], int(255 * a))
    return Image.fromarray(out, "RGBA")


def preview(take):
    """A contact sheet of every piece for a look."""
    rows = []
    rows.append(strip([ball(take, s, 0) for s in range(5)] + [ball(take, 4, t) for t in range(1, 4)]))
    rows.append(strip([ball_fizzle(take, i) for i in range(6)]))
    rows.append(strip([beam_start(take, 0)] + [beam_body(take, t) for t in range(4)] + [beam_body(take, 0)] * 3))
    rows.append(strip([beam_spiral(take, t) for t in range(4)]))
    rows.append(strip([beam_head(take, t) for t in range(4)]))
    rows.append(strip([beam_muzzle(take, i) for i in range(6)]))
    rows.append(strip([beam_impact(take, i) for i in range(8)]))
    rows.append(strip([aura(take, t, 2) for t in range(4)]))
    W = max(r.width for r in rows)
    H = sum(r.height + 4 for r in rows)
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = 0
    for r in rows:
        sheet.alpha_composite(r, (0, y))
        y += r.height + 4
    return sheet


if __name__ == "__main__":
    for take in "ab":
        zoomed(preview(take), 2, (20, 14, 34, 255)).save(WORK + "/energy_%s.png" % take)
