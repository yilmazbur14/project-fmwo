"""God Jordan coming apart in the beam: glowing cracks spreading out of his core, pieces heating and flaking off from
the wing tips, tail and crown inwards, streaming away down the beam, the core going last. And the FAIL take: he gets
half way, then pulls himself back together, his own lava red sealing the cracks.

Layers, every frame on his own 320x224 frame (anchor texel (160, 223) on GOD_POINT, 3x, like his hover):
  body  - his sprite as it crumbles (normal blend; plays in place of the hover)
  glow  - the cracks' and the core's light (additive, same frame)
  ash   - the flakes streaming off (normal blend), a 480x352 cell with his frame's texel (0,0) at (40,112), so his
          anchor texel (160,223) is the ash cell's (200,335). One sheet per staging: the flakes go with the beam."""
import math
import numpy as np
from PIL import Image
from common import *
from energy import RAMPS, GLOWS, rgba, rng
import scene

W, H = 320, 224
ASH_W, ASH_H, ASH_OFF = 480, 352, (40, 112)
CORE = (159.5, 117.5)
FRAMES = 24          # 0.1 s each: 2.4 s
FAIL_FRAMES = 16
DIRS = {"a": (0.7071, -0.7071), "b": (0.0, -1.0)}   # staging A: up-right; staging B: straight up
LAVA = ["fff3b0", "ec5a5b", "c9293f", "8c1b2d"]       # his own core and crack reds (measured off the hover)
ASH = ["847e87", "564b63", "3b3346"]


def _value_noise(shape, cell, seed):
    r = rng(seed)
    gh, gw = shape[0] // cell + 2, shape[1] // cell + 2
    g = r.random((gh, gw))
    ys, xs = np.mgrid[0:shape[0], 0:shape[1]]
    return g[ys // cell, xs // cell]


class Plan:
    """Everything decided once: when each texel goes, where the cracks run, the flakes."""

    def __init__(self, base):
        self.base = np.asarray(base).copy()
        self.mask = self.base[..., 3] > 0
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xs - CORE[0]) * 0.8, ys - CORE[1])
        d = d / d[self.mask].max()
        n = 0.6 * _value_noise((H, W), 6, 11) + 0.4 * _value_noise((H, W), 3, 12)
        # out-to-in: the extremities first, the core last; chunky so it goes in pieces
        self.T = np.clip(0.08 + 0.80 * np.clip(1 - d, 0, 1) ** 1.1 + 0.16 * (n - 0.5), 0.02, 0.97)
        core = np.hypot(xs - CORE[0], ys - CORE[1])
        self.T = np.where(core < 9, 0.9 + 0.006 * core, self.T)
        self.T = np.where(self.mask, self.T, 9.0)
        self.crack_t = np.full((H, W), 9.0, np.float32)
        r = rng(21)
        for k in range(16):
            ang = TAU * k / 16 + r.uniform(-0.15, 0.15)
            self._crack(CORE[0], CORE[1], ang, 0.04, r, depth=0)
        self.flakes = self._flakes()

    def _crack(self, x, y, ang, t0, r, depth):
        steps = int(r.integers(30, 70)) if depth == 0 else int(r.integers(8, 22))
        for s in range(steps):
            ang += r.uniform(-0.35, 0.35)
            x += math.cos(ang) * 1.6
            y += math.sin(ang) * 1.0
            xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < W and 0 <= yi < H):
                return
            t = t0 + s * 0.0075
            if self.mask[yi, xi]:
                self.crack_t[yi, xi] = min(self.crack_t[yi, xi], t)
            if depth < 2 and r.random() < 0.06:
                self._crack(x, y, ang + r.choice([-1, 1]) * r.uniform(0.5, 1.1), t, r, depth + 1)

    def _flakes(self):
        r = rng(33)
        out = []
        for y in range(0, H, 2):
            for x in range(0, W, 2):
                if not self.mask[y, x] or r.random() > 0.55:
                    continue
                big = r.random() < 0.18
                out.append(dict(x=x, y=y, t=float(self.T[y, x]), v=r.uniform(0.6, 1.4), spread=r.uniform(-0.5, 0.5),
                                big=big, col=tuple(self.base[y, x]), life=r.uniform(0.22, 0.42), kick=r.uniform(0, 1)))
        return out


def frame_layers(plan, tau, take, red=0.0, stage="b", ash_scale=1.0):
    """Body, glow and ash at dissolve time tau (0..1). red 0-1 turns the beam's light into his own lava (the fail)."""
    ramp = [c for _, c in RAMPS[take]]
    body = plan.base.copy()
    glow = np.zeros((H, W, 4), np.uint8)
    T = plan.T
    gone = T <= tau
    heat = (T - tau < 0.055) & ~gone
    hot2 = (T - tau < 0.025) & ~gone
    crack = (plan.crack_t <= tau) & ~gone
    crack_wide = np.zeros_like(crack)
    old = (plan.crack_t <= tau - 0.12)
    crack_wide[1:, :] |= old[:-1, :]
    crack_wide[:, 1:] |= old[:, :-1]
    crack_wide &= plan.mask & ~gone & ~crack

    def c(i):
        if red > 0.5:
            return rgba(LAVA[min(i, 3)])
        return rgba(ramp[i])

    body[heat] = c(5) if red <= 0.5 else rgba(LAVA[3])
    body[hot2] = c(2) if red <= 0.5 else rgba(LAVA[2])
    body[crack_wide] = c(4) if red <= 0.5 else rgba(LAVA[2])
    body[crack] = c(0) if red <= 0.5 else rgba(LAVA[1])
    body[gone] = 0
    gcol = rgba(GLOWS[take]) if red <= 0.5 else rgba("e0302a")
    lit = crack | crack_wide | heat
    # glow: a 2 px halo round everything lit
    halo = lit.copy()
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2):
            if abs(dx) + abs(dy) <= 3:
                halo |= np.roll(np.roll(lit, dy, 0), dx, 1)
    glow[halo] = (gcol[0], gcol[1], gcol[2], 90)
    glow[lit] = (gcol[0], gcol[1], gcol[2], 170)
    # the core: brightening, swelling, then going with a pop
    ys, xs = np.mgrid[0:H, 0:W]
    rr = np.hypot(xs - CORE[0], ys - CORE[1])
    if 0.55 <= tau < 0.93 and red == 0:
        k = (tau - 0.55) / 0.38
        R = 3 + 7 * k
        m = rr < R
        body[m] = rgba("f5d94e")
        body[m & (rr < R * 0.7)] = rgba(LAVA[0])
        body[m & (rr < R * 0.35)] = rgba("ffffff")
        for rad, al in ((2.6, 70), (1.8, 120), (1.2, 180)):
            gm = rr < R * rad
            glow[gm] = np.maximum(glow[gm], np.array([gcol[0], gcol[1], gcol[2], int(al * (0.6 + 0.4 * k))], np.uint8))
    if 0.93 <= tau < 1.0 and red == 0:
        k = (tau - 0.93) / 0.07
        R = 16 + 18 * k
        m = rr < R * (1 - 0.7 * k)
        body[m] = c(0)
        for rad, al in ((1.8, 90), (1.2, 160), (0.7, 230)):
            glow[rr < R * rad] = (gcol[0], gcol[1], gcol[2], int(al * (1 - k)))
    # ash: the flakes off on the beam's line
    ash = np.zeros((ASH_H, ASH_W, 4), np.uint8)
    dx, dy = DIRS[stage]
    for f in plan.flakes:
        age = tau - f["t"]
        if age < 0 or age > f["life"]:
            continue
        a = age / f["life"]
        ox, oy = f["x"] - CORE[0], f["y"] - CORE[1]
        on = math.hypot(ox, oy) + 1e-3
        dist = (60 * age + 420 * age * age) * f["v"] * ash_scale
        px = f["x"] + dx * dist + (ox / on) * 10 * age * f["kick"] + f["spread"] * dist * 0.35 * (-dy)
        py = f["y"] + dy * dist + (oy / on) * 10 * age * f["kick"] + f["spread"] * dist * 0.35 * dx
        if red > 0.5:
            px = f["x"] + (px - f["x"]) * 0.5
            py = f["y"] + (py - f["y"]) * 0.5
        if a < 0.25:
            col = c(1)
        elif a < 0.5:
            col = c(3)
        elif a < 0.75:
            col = rgba(ASH[0]) if red <= 0.5 else rgba(LAVA[2])
        else:
            col = rgba(ASH[1]) if red <= 0.5 else rgba(LAVA[3])
        if f["big"] and a < 0.4:
            col = np.array(f["col"], np.uint8) if a < 0.15 else c(2)
        size = 2 if (f["big"] and a < 0.6) else 1
        ix, iy = int(round(px)) + ASH_OFF[0], int(round(py)) + ASH_OFF[1]
        ash[max(iy, 0):max(iy + size, 0), max(ix, 0):max(ix + size, 0)] = col
    return Image.fromarray(body, "RGBA"), Image.fromarray(glow, "RGBA"), Image.fromarray(ash, "RGBA")


def success(take, stage):
    plan = Plan(scene.god_hit(0))
    out = []
    for k in range(FRAMES):
        tau = k / (FRAMES - 2)          # the last two frames: nothing but the last ash
        out.append(frame_layers(plan, min(tau, 1.2), take, stage=stage))
    return out


FAIL_TAUS = [0.0, 0.06, 0.12, 0.18, 0.24, 0.30, 0.36, 0.42, 0.45, 0.45, 0.40, 0.32, 0.22, 0.12, 0.04, 0.0]
FAIL_RED = [0] * 9 + [1] * 7


def fail(take, stage):
    """Half way, a beat, then back: the reverse in his own red, the flakes flying back in."""
    plan = Plan(scene.god_hit(0))
    out = []
    for tau, red in zip(FAIL_TAUS, FAIL_RED):
        b, g, a = frame_layers(plan, tau, take, red=red, stage=stage, ash_scale=0.6)
        if red and tau == 0.0:
            # whole again: a red flare round his outline
            m = np.asarray(b)[..., 3] > 0
            edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
            gl = np.asarray(g).copy()
            gl[edge] = (224, 48, 42, 200)
            g = Image.fromarray(gl, "RGBA")
        out.append((b, g, a))
    return out


TAU = math.tau

if __name__ == "__main__":
    fr = success("a", "b")
    pick = [0, 3, 6, 9, 12, 15, 18, 20, 21, 22]
    tiles = []
    for i in pick:
        b, g, a = fr[i]
        base = Image.new("RGBA", (ASH_W, ASH_H), (20, 14, 34, 255))
        base.alpha_composite(b, ASH_OFF)
        arr = np.asarray(base).astype(np.float32)
        gg = np.zeros_like(arr)
        gg[ASH_OFF[1]:ASH_OFF[1] + H, ASH_OFF[0]:ASH_OFF[0] + W] = np.asarray(g)
        arr[..., :3] = np.clip(arr[..., :3] + gg[..., :3] * gg[..., 3:4] / 255, 0, 255)
        base = Image.fromarray(arr.astype(np.uint8), "RGBA")
        base.alpha_composite(a)
        tiles.append(base)
    s = strip(tiles[:5]); s2 = strip(tiles[5:])
    sheet = Image.new("RGBA", (s.width, s.height * 2)); sheet.paste(s, (0, 0)); sheet.paste(s2, (0, s.height))
    sheet.save(WORK + "/dis_look.png")
