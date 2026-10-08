"""Writes every sheet of the approval pass into the approval folder (and nowhere else: common.out_path refuses).
Run: python export.py"""
import json
from common import *
import poses_a
import poses_b
import energy as E
import aura as AU
import shout as SH
import disintegrate as DI

ORDER = ["idle", "step", "charge0", "charge1", "charge2", "thrust1", "thrust2", "hold0", "hold1", "fail0", "fail1",
         "fail2"]
TAKES = {"a": "take_a_blue", "b": "take_b_hype"}
STAGES = {"side": poses_a, "back": poses_b}
STAGE_DIR = {"side": "a", "back": "b"}   # which way the ash streams: A up-right, B up


def burak():
    out = {}
    for st, mod in STAGES.items():
        frames = [mod.FRAMES[k]() for k in ORDER]
        img = strip([f.img() for f in frames])
        save_png(img, "player", "player_final_beam_%s.png" % st)
        out[st] = frames
    return out


def grid(rows):
    w, h = rows[0][0].size
    g = Image.new("RGBA", (w * max(len(r) for r in rows), h * len(rows)), (0, 0, 0, 0))
    for j, r in enumerate(rows):
        for i, im in enumerate(r):
            g.alpha_composite(im, (i * w, j * h))
    return g


def energy(take, poses):
    d = TAKES[take]
    save_png(grid([[E.ball(take, s, t) for t in range(4)] for s in range(5)]), d, "final_beam_ball.png")
    save_png(grid([[E.ball_glow(take, s, t) for t in range(4)] for s in range(5)]), d, "final_beam_ball_glow.png")
    save_png(strip([E.ball_fizzle(take, i) for i in range(E.FIZZLE_FRAMES)]), d, "final_beam_ball_fizzle.png")
    save_png(strip([E.ball_fizzle_glow(take, i) for i in range(E.FIZZLE_FRAMES)]), d,
             "final_beam_ball_fizzle_glow.png")
    save_png(strip([E.beam_muzzle(take, i) for i in range(E.MUZZLE_FRAMES)]), d, "final_beam_muzzle.png")
    save_png(strip([E.beam_muzzle_glow(take, i) for i in range(E.MUZZLE_FRAMES)]), d, "final_beam_muzzle_glow.png")
    save_png(strip([E.beam_start(take, t) for t in range(4)]), d, "final_beam_start.png")
    save_png(strip([E.beam_start_glow(take, t) for t in range(4)]), d, "final_beam_start_glow.png")
    save_png(strip([E.beam_body(take, t) for t in range(4)]), d, "final_beam_body.png")
    save_png(strip([E.beam_body_glow(take, t) for t in range(4)]), d, "final_beam_body_glow.png")
    save_png(strip([E.beam_spiral(take, t) for t in range(4)]), d, "final_beam_spiral.png")
    save_png(strip([E.beam_head(take, t) for t in range(4)]), d, "final_beam_head.png")
    save_png(strip([E.beam_head_glow(take, t) for t in range(4)]), d, "final_beam_head_glow.png")
    save_png(strip([E.beam_impact(take, i) for i in range(E.IMPACT_FRAMES)]), d, "final_beam_impact.png")
    save_png(strip([E.beam_impact_glow(take, i) for i in range(E.IMPACT_FRAMES)]), d, "final_beam_impact_glow.png")
    # his aura: rows = strength (bars 1-2, 3-4, 5), columns = the charge loop's 3 frames, per staging
    for st, frames in poses.items():
        charge = [frames[ORDER.index(k)] for k in ("charge0", "charge1", "charge2")]
        save_png(grid([[AU.aura_for(c.img(), take, t, lv) for t, c in enumerate(charge)] for lv in range(3)]), d,
                 "final_beam_aura_%s.png" % st)
    save_png(SH.sheet(take), d, "beam_shout_words.png")
    # his end
    for st in STAGES:
        fr = DI.success(take, STAGE_DIR[st])
        if st == "side":
            save_png(strip([f[0] for f in fr]), d, "god_disintegrate.png")
            save_png(strip([f[1] for f in fr]), d, "god_disintegrate_glow.png")
        save_png(strip([f[2] for f in fr]), d, "god_disintegrate_ash_%s.png" % st)
        ff = DI.fail(take, STAGE_DIR[st])
        if st == "side":
            save_png(strip([f[0] for f in ff]), d, "god_reform.png")
            save_png(strip([f[1] for f in ff]), d, "god_reform_glow.png")
        save_png(strip([f[2] for f in ff]), d, "god_reform_ash_%s.png" % st)


if __name__ == "__main__":
    poses = burak()
    for take in "ab":
        energy(take, poses)
    print("exported")
