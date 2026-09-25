"""The ringside spectators (arena_ringside.png's side columns and bottom row), made to react
-> arena_ringside_crowd.png.

An overlay the size of the screen, 640x360 per frame at 3x, drawn right above the Ringside sprite.
It is opaque over the crowd zone only (its own backdrop plus the figures) and clear everywhere
else, so it hides the static crowd baked into arena_ringside.png and nothing else. On the reaction
frames, hands may reach over the barrier rail. Same frame layout as the top band (crowd_v3.png),
so ArenaCrowdScript drives both from one call:

  frames 0-2 : idle   - pixel-identical to what arena_ringside.png already shows
  frames 3-4 : cheer  - arms up, one arm waving, hopping (vertical bounce)
  frames 5-6 : boo    - a fist (or two) at the ear, shaken side to side; the rest lean in and sulk

The figures are replayed from gen_arena.draw_crowd's own seeded RNG, so each one keeps its colours.
The run fails unless the idle frame matches the shipped ringside exactly.

Approved 2026-09-24. Writes only where it's told, and never into Assets - build_ship.py ships.
    python ringside_react.py --out <dir>     -> <dir>/arena_ringside_crowd.png
"""
import argparse
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "arena"))
import gen_arena as G  # noqa: E402
from PIL import Image  # noqa: E402

NAME = "arena_ringside_crowd.png"
W, H = G.ART
N_FRAMES = 7
CHEER = (3, 4)
BOO = (5, 6)
CFG = G.DIRECTIONS[G.APPROVED]
RINGSIDE = os.path.join(HERE, "..", "..", "Assets", "Environment", "arena_ringside.png")


def in_zone(x, y):
    return 0 <= x < W and G.CROWD_Y <= y < H and G.ring_dist(x, y) >= G.D_CROWD


def arm_ok(x, y):
    """Arms may reach over the barrier rail (hands above a barrier are natural); bodies may not."""
    return 0 <= x < W and G.CROWD_Y <= y < H and G.ring_dist(x, y) >= G.D_RAIL[0]


def backdrop():
    back = G.mix(CFG["barrier"], (34, 32, 52), 0.55)
    px = {}
    for y in range(G.CROWD_Y, H):
        for x in range(W):
            if in_zone(x, y):
                px[(x, y)] = back if G._hash2(x, y, 71) > 0.18 else G.mix(back, (0, 0, 0), 0.4)
    return px


def figures():
    """Replay gen_arena.draw_crowd: same RNG, same order, same colours."""
    rnd = random.Random(19)          # build_ringside's seed; nothing draws from it before the crowd
    SKINS = [(143, 86, 59), (217, 160, 102), (102, 57, 49), (89, 86, 82)]
    SHIRTS = [(63, 63, 116), (69, 40, 60), (48, 96, 130), (82, 75, 36), (50, 60, 57), (76, 66, 138)]
    out = []

    def ok(x, y):
        return 0 <= x < W and 0 <= y < H and G.ring_dist(x, y) >= G.D_CROWD

    def fig(cx, feet, where):
        k = rnd.uniform(0.56, 0.68)
        skin = G.mix(rnd.choice(SKINS), (0, 0, 0), k)
        shirt = G.mix(rnd.choice(SHIRTS), (0, 0, 0), k + 0.08)
        out.append(dict(cx=cx, feet=feet, skin=skin, shirt=shirt, where=where))

    for col, x in enumerate((25, 31)):
        for y in range(G.CROWD_Y + 9 + col * 5, H, 11):
            if ok(x - 24, y) and ok(x - 24, y - 7):
                fig(x - 24, y, "left")
            if ok(W - 1 - (x - 24), y) and ok(W - 1 - (x - 24), y - 7):
                fig(W - 1 - (x - 24), y, "right")
    for i, x in enumerate(range(6, W - 6, 5)):
        y = H - 1 - (i % 2)
        if ok(x, y) and ok(x, y - 7):
            fig(x, y, "bottom")
    return out


def assign(figs, seed=4242):
    rng = random.Random(seed)
    cheer_kinds = ["both"] * 5 + ["one"] * 4 + ["hop"] * 2
    boo_kinds = ["fist"] * 6 + ["fists"] * 2 + ["lean"] * 3
    for f in figs:
        f["ck"], f["bk"] = rng.choice(cheer_kinds), rng.choice(boo_kinds)
        f["cph"], f["bph"] = rng.randrange(2), rng.randrange(2)
        # arms reach toward the ring, over the barrier; along the bottom, either way
        f["side"] = {"left": 1, "right": -1}.get(f["where"]) or rng.choice((-1, 1))


def draw_frame(canvas, figs, fr):
    """Tiny flat figures (no outline): a 3x3 head over a 3x5 body. Arms rise one pixel clear of
    the head from a shoulder nub, or they would merge into it. Cheer bounces vertically with arms
    up; boo shakes side to side with fists at the ear - different in motion as well as pose."""
    for f in figs:
        cx, feet, skin, shirt, s = f["cx"], f["feet"], f["skin"], f["shirt"], f["side"]
        dx, dy, arms = 0, 0, []

        # arm segments: (x, first row, last row), rows counted from the head top, <0 = above it
        def up(sd):
            return [(cx + 2 * sd, 3, 3), (cx + 3 * sd, -2, 2)]

        def vee(sd):
            return [(cx + 2 * sd, 3, 3), (cx + 3 * sd, 0, 2), (cx + 4 * sd, -2, -1)]

        def fist(sd):
            return [(cx + 2 * sd, 3, 3), (cx + 3 * sd, 0, 2)]

        if fr in CHEER:
            k = (fr - CHEER[0] + f["cph"]) % 2
            if f["ck"] == "both":
                dy = -1 if k == 0 else 0
                arms = up(-1) + up(1) if k == 0 else vee(-1) + vee(1)
            elif f["ck"] == "one":
                dy = -1 if k == 1 else 0
                arms = up(s) if k == 0 else vee(s)
            else:
                dy = -1 if k == 0 else 0
        elif fr in BOO:
            k = (fr - BOO[0] + f["bph"]) % 2
            if f["bk"] == "lean":
                dy = 1
            else:
                dx = s if k == 1 else 0
                arms = fist(s) if f["bk"] == "fist" else fist(-1) + fist(1)
        top = feet - 7 + dy
        for y in range(top + 3, feet + dy + 1):
            for x in range(cx - 1 + dx, cx + 2 + dx):
                if in_zone(x, y):
                    canvas[(x, y)] = shirt
        for y in range(top, top + 3):
            for x in range(cx - 1 + dx, cx + 2 + dx):
                if in_zone(x, y):
                    canvas[(x, y)] = skin
        for ax, r0, r1 in arms:
            for r in range(r0, r1 + 1):
                x, y = ax + dx, top + r
                if arm_ok(x, y):
                    canvas[(x, y)] = skin


def render():
    figs = figures()
    assign(figs)
    base = backdrop()
    frames = []
    for fr in range(N_FRAMES):
        canvas = dict(base)
        draw_frame(canvas, figs, fr)
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        px = im.load()
        for (x, y), c in canvas.items():
            px[x, y] = c + (255,)
        frames.append(im)
    return figs, frames


def sheet(frames):
    s = Image.new("RGBA", (W * len(frames), H), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        s.paste(im, (i * W, 0))
    return s


def self_check(frames):
    """The idle frame must be exactly what arena_ringside.png already shows in the crowd zone,
    nothing may be drawn past the rail, and the three idle frames must be identical."""
    ship = Image.open(RINGSIDE).convert("RGBA")
    sp, ip = ship.load(), frames[0].load()
    zone = [(x, y) for y in range(G.CROWD_Y, H) for x in range(W) if in_zone(x, y)]
    bad = sum(1 for p in zone if sp[p] != ip[p])
    outside = sum(1 for y in range(H) for x in range(W) if not in_zone(x, y) and ip[x, y][3] != 0)
    beyond = sum(1 for im in frames for y in range(H) for x in range(W)
                 if im.getpixel((x, y))[3] and not arm_ok(x, y))
    same_idle = frames[1].tobytes() == frames[0].tobytes() == frames[2].tobytes()
    ok = bad == 0 and outside == 0 and beyond == 0 and same_idle
    return ok, (f"idle vs arena_ringside.png over {len(zone)} crowd px: "
                f"{'exact' if bad == 0 else f'{bad} differ'}; idle drawn outside the zone: {outside}; "
                f"any frame past the rail: {beyond}; idle frames identical: {same_idle}")


def refuse_assets(path):
    assets = os.path.realpath(os.path.join(HERE, "..", "..", "Assets"))
    p = os.path.realpath(path)
    if p == assets or p.startswith(assets + os.sep):
        raise SystemExit(f"refusing to write into Assets ({path}); build_ship.py --ship ships")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="folder to write arena_ringside_crowd.png into")
    args = ap.parse_args()
    refuse_assets(args.out)
    os.makedirs(args.out, exist_ok=True)
    figs, frames = render()
    ok, report = self_check(frames)
    print(f"figures {len(figs)} | {report}")
    if not ok:
        raise SystemExit("self-check failed - nothing written")
    sheet(frames).save(os.path.join(args.out, NAME))
    print("wrote", os.path.join(args.out, NAME))
