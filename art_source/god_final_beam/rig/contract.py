"""Writes approval/contract.json from the same numbers the sheets and mocks were made with."""
import sys
sys.argv = ["mock.py"]
import json
import math
from PIL import Image
from common import *
import mock
import energy as E
import shout as SH
import disintegrate as DI
import export


def word_widths():
    return {w: SH.render(w, "a").getbbox()[2] for w in SH.WORDS + ["KEN..."]}


def stage_numbers(name):
    st = mock.STAGES[name]
    hand = mock.cell_to_world(st["origin"], st["muzzle"])
    ball = mock.cell_to_world(st["origin"], st["ball"])
    dx, dy = mock.CORE[0] - hand[0], mock.CORE[1] - hand[1]
    return {
        "player_origin_world": list(st["origin"]),
        "player_soles_world_y": st["origin"][1] + 39,  # the drawn soles' bottom edge (his collision box bottom is +42)
        "ball_point_cell": list(st["ball"]),
        "ball_point_world": [round(ball[0], 1), round(ball[1], 1)],
        "muzzle_point_cell": list(st["muzzle"]),
        "muzzle_point_cell_hold1": [st["muzzle"][0], st["muzzle"][1] + 1],
        "muzzle_point_world": [round(hand[0], 1), round(hand[1], 1)],
        "beam_rotation_deg": round(math.degrees(st["angle"]), 2),
        "beam_rotation_rad": round(st["angle"], 5),
        "beam_length_world_to_core": round(math.hypot(dx, dy), 1),
        "beam_true_angle_to_core_deg": round(math.degrees(math.atan2(dy, dx)), 2),
        "ash_sheet": "god_disintegrate_ash_%s.png" % name,
        "reform_ash_sheet": "god_reform_ash_%s.png" % name,
        "shout_anchor_offset_world": list(st["shout"]),
        "ken_anchor_offset_world": list(st["ken"]),
        "camera_release": {"zoom": st["release_view"][0], "focus": list(st["release_view"][1])},
        "camera_dissolve_end": {"zoom": st["dissolve_view"][0], "focus": list(st["dissolve_view"][1])},
    }


C = {
    "what": "Approval pass (2026-10-06): god Jordan's ending - a 5-bar mash charging the final beam (shout "
            "SHIN / KU / HA / DO / KEN!!!!, one syllable a bar), the giant blue fireball-beam, and his 2.4 s "
            "disintegration; plus the FAIL (he half-dissolves and pulls himself back together, +5 HP). Nothing ships "
            "from here: every path below is relative to the approval folder.",
    "picks": {
        "staging": "B (from behind, bottom centre, beam straight up) - recommended: symmetric and centred on him, the "
                   "beam needs no rotation so its pixels stay square, he already faces UP on the void's mark, and "
                   "the ash streams straight up the beam. A (side-on) reads the charge pose and his face better in "
                   "the close-ups but needs a 45-degree rotated beam and a walk to a lower-left mark.",
        "take": "A classic blue-white (the user's lean; it is a royal/periwinkle blue, kept off the runes' teal "
                "#66C6EC). B is the HYPE ramp (the meter's white/yellow/pink/purple, as on the super uppercut).",
    },
    "units": "Texel coordinates are on each sheet's own cell, top-left (0,0), x right, y down, edges not centres "
             "(14.5 = the middle of column 14). World px = 3 a texel (the player's and the god's scale). Screen px "
             "are 1920x1080. Angles are Godot rotations (y down: -90 = straight up the screen).",
    "world": {
        "GOD_POINT": [960, 600], "god_anchor_texel": [160, 223], "god_scale": 3,
        "god_core_texel": list(DI.CORE), "god_core_world": list(mock.CORE),
        "view_default": {"zoom": mock.VIEW_ZOOM, "focus": list(mock.VIEW_FOCUS)},
        "floor": [-375, 99, 2670, 1410],
    },
    "player": {
        "sheets": {"side": "player/player_final_beam_side.png", "back": "player/player_final_beam_back.png"},
        "cell": [48, 48], "hframes": 12, "vframes": 1, "scale": 3, "centered": True,
        "placement": "Drawn centred on MainPlayer's origin exactly like player_4dir_sheet's 32x32 cells: his soles "
                     "land on the same pixels (cell rows 35-36 = the 32 sheet's rows 27-28, +8,+8). Swap texture + "
                     "hframes/vframes, keep the Sprite2D where it is.",
        "colours": "his own 7 (#000000 #d79864 #ac714f #2464bd #162fbb #3883c9 #ac3232), no keyline - black is hair "
                   "and shoes only, as on his sheets; black ratio side 11.3%, back 16.5% (his sheet 13.9%, his side "
                   "rows ~11%).",
        "frames": {k: i for i, k in enumerate(export.ORDER)},
        "anims": {
            "stance_in": {"frames": [1], "time": 0.12, "loop": False,
                          "note": "frame 0 is his own idle in this cell (a seamless swap from his sheet); step out on "
                                  "1 for 0.12 s, then the charge loop"},
            "charge": {"frames": [2, 3, 4], "time": 0.09, "loop": True,
                       "note": "cupped at the hip; headband tails and shorts whipping in the aura's draught"},
            "release": {"frames": [5, 6], "times": [0.05, 0.08], "loop": False, "note": "thrust (shout frame)"},
            "hold": {"frames": [7, 8], "time": 0.06, "loop": True,
                     "note": "bracing while the beam fires; 8 is 1 texel lower and the back foot 1 texel further "
                             "back - slide the node back ~40 world px over the hold for the feet-sliding"},
            "fail": {"frames": [9, 10, 11], "times": [0.15, 0.2, 1.25], "loop": False,
                     "note": "9 thrown back as the charge gives out, 10 stumbling, 11 bent double; then his idle"},
            "recover": "his own player_4dir_sheet idle (UP row for B, RIGHT row for A)",
        },
        "points": {
            "side": {"ball": [14.5, 29.0], "muzzle": [36.5, 12.5], "muzzle_hold1": [36.5, 13.5]},
            "back": {"ball": [33.0, 28.0], "muzzle": [23.5, 11.5], "muzzle_hold1": [23.5, 12.5]},
            "to_world": "origin + 3 * (point - (24, 24))",
            "note": "keep the beam's origin on frame 6's muzzle point through the hold (the 1-texel tremble is the "
                    "body's, not the beam's)",
        },
    },
    "stagings": {"side": stage_numbers("side"), "back": stage_numbers("back")},
    "takes": {
        "a": {"dir": "take_a_blue", "ramp": [c for _, c in E.RAMPS["a"]], "glow": E.GLOWS["a"]},
        "b": {"dir": "take_b_hype", "ramp": [c for _, c in E.RAMPS["b"]], "glow": E.GLOWS["b"]},
        "note": "Every take folder holds the same file names; pick one folder. Glow sheets are BLEND_MODE_ADD "
                "(colour x alpha added), the rest normal blend. Nearest filter everywhere.",
    },
    "aura": {
        "sheet": "final_beam_aura_{side|back}.png", "cell": [64, 64], "hframes": 3, "vframes": 3, "scale": 3,
        "pivot": [32, 32], "centered_on": "the player's origin (his 48 cell sits at (8,8) in it)",
        "blend": "add", "z": "BEHIND the player",
        "rows": {"0": "bars 1-2", "1": "bars 3-4", "2": "bar 5"},
        "columns": "the charge loop's frames 2,3,4 - step them with the player's charge frame (it hugs that frame's "
                   "silhouette)",
    },
    "ball": {
        "sheet": "final_beam_ball.png", "glow": "final_beam_ball_glow.png (add, under the ball)",
        "cell": [64, 64], "hframes": 4, "vframes": 5, "scale": 3, "pivot": [32, 32],
        "rows": "size = bars - 1 (row 0 at bar 1 ... row 4 at bar 5)", "columns": "pulse loop, 0.07 s a frame",
        "core_radius_texels": E.BALL_R,
        "placement": "its pivot on the staging's ball point; z above the player (it is held out at his hip)",
        "bar5": "row 4 wobbles and throws arcs and sparks - barely held",
        "fizzle": {"sheet": "final_beam_ball_fizzle.png", "glow": "final_beam_ball_fizzle_glow.png", "cell": [64, 64],
                   "hframes": E.FIZZLE_FRAMES, "time": 0.08,
                   "note": "the charge giving out into sparks and smoke. Used at the muzzle as the weak beam cuts "
                           "(the mocked fail); or at the ball point if the architect's fail fires no beam at all"},
    },
    "beam": {
        "authored_along": "+x; rotate the beam node by the staging's beam_rotation (B: -90 exactly, pixel-perfect; "
                          "A: -45, sampled nearest like the mocks)",
        "pieces": {
            "muzzle": {"sheet": "final_beam_muzzle.png", "glow": "final_beam_muzzle_glow.png", "cell": [80, 80],
                       "hframes": E.MUZZLE_FRAMES, "pivot": [40, 40], "at": "muzzle point, rotated with the beam",
                       "play": "0,1 once at 0.06 (the release flash), then 2-5 looped at 0.06"},
            "start": {"sheet": "final_beam_start.png", "glow": "final_beam_start_glow.png",
                      "cell": [64, E.BODY_H], "glow_cell": [64, E.BODY_GLOW_H], "hframes": 4,
                      "pivot": [0, E.BODY_H / 2], "glow_pivot": [0, E.BODY_GLOW_H / 2],
                      "at": "muzzle point", "note": "narrows to the ball's width at x 0; its x 32-63 are exactly the "
                      "body tile, so body tiles laid on from x 64 join it seamlessly. Crop it to the travelled "
                      "length while the beam is shorter than 64 texels"},
            "body": {"sheet": "final_beam_body.png", "glow": "final_beam_body_glow.png",
                     "cell": [32, E.BODY_H], "glow_cell": [32, E.BODY_GLOW_H], "hframes": 4, "time": 0.06,
                     "tile": "repeats every 32 texels along x, from 64; frame k = the flow moved 8 texels on; all "
                             "tiles on the same frame. A TextureRect/Sprite2D with region + texture repeat works",
                     "visible_half_width_texels": E.HALF, "with_flames_half_width_texels": E.HALF + 11,
                     "note": "~200-230 world px thick - wider than his torso (60 texels = 180 world px)"},
            "spiral": {"sheet": "final_beam_spiral.png", "cell": [32, E.BODY_H], "hframes": 4, "blend": "add",
                       "placement": "same tiles as the body, over it: a helix wrapping it and crackle off its rims"},
            "head": {"sheet": "final_beam_head.png", "glow": "final_beam_head_glow.png", "cell": [E.HEAD, E.HEAD],
                     "hframes": 4, "pivot": [78, E.HEAD / 2], "at": "the beam's tip",
                     "note": "the fireball front leading the beam out; body tiles stop 30 texels short of the tip, "
                             "under its sphere"},
            "impact": {"sheet": "final_beam_impact.png", "glow": "final_beam_impact_glow.png",
                       "cell": [E.IMPACT, E.IMPACT], "hframes": E.IMPACT_FRAMES, "pivot": [E.IMPACT / 2, E.IMPACT / 2],
                       "at": "god_core_world, not rotated", "play": "0-3 once at 0.07, then 4-7 looped at 0.07 while "
                       "the beam holds him"},
        },
        "z": "above the god (it hits his chest in front of him) and above the player except the muzzle at his hands",
        "travel": "muzzle to core in 0.35 s (~2700 world px/s), head leading",
        "after_he_is_gone": "the tip carries on past the core off screen at 2600 world px/s for 0.35 s, then the whole "
                            "beam thins (scale.y 1 -> 0) over 0.45 s",
    },
    "god": {
        "disintegrate": {
            "sheet": "god_disintegrate.png", "glow": "god_disintegrate_glow.png (add)",
            "ash": "god_disintegrate_ash_{side|back}.png - the flakes go WITH the beam: side = up-right, back = up",
            "cell": [320, 224], "hframes": DI.FRAMES, "time": 0.1, "anchor": [160, 223],
            "ash_cell": [DI.ASH_W, DI.ASH_H], "ash_anchor": [200, 335],
            "placement": "in place of his body, aura OFF: anchor texel on GOD_POINT at 3x, exactly like his hover",
            "base_pose": "jordan_god_hit frame 0 - hold him on it from the moment the beam lands",
            "beats": "0-5 cracks run out of his core; 3-17 wing tips, tail, crown, hands go first, inwards, each "
                     "piece glowing before it flakes; 13-20 the core swells white-gold; 21 it pops (flash); 22-23 "
                     "nothing but the last ash",
            "runes": "fade his rune circle out over 1.6 s from the hit",
        },
        "reform_fail": {
            "sheet": "god_reform.png", "glow": "god_reform_glow.png (add)", "ash": "god_reform_ash_{side|back}.png",
            "cell": [320, 224], "hframes": DI.FAIL_FRAMES, "time": 0.1, "anchor": [160, 223],
            "beats": "0-8 he comes half apart in the beam's colour; hold 8 while the weak beam sputters; 9-15 he "
                     "pulls back together in his own lava red, the flakes flying back in; 15 is whole with a red "
                     "rim (glow). Then his hover + aura again, +5 HP",
            "taus": DI.FAIL_TAUS,
            "by_bars": "for a shallower dissolve (fewer bars banked) play forward frames 0..k to the reached tau, then "
                       "enter the red reverse at the first of frames 9-15 whose tau is <= it (taus listed above), so "
                       "it never jumps",
        },
    },
    "shout": {
        "sheet": "beam_shout_words.png", "cell": [SH.CELL_W, SH.CELL_H], "hframes": 6,
        "frames": {"SHIN": 0, "KU": 1, "HA": 2, "DO": 3, "KEN!!!!": 4, "KEN... (fail)": 5},
        "ink_widths": word_widths(), "ink_height": 15,
        "layer": "screen space (a CanvasLayer), nearest; each word left-aligned at x 0 of its cell - centre on the "
                 "ink width",
        "scale_screen_px_a_texel": {"SHIN": 4.0, "KU": 4.5, "HA": 5.0, "DO": 5.5, "KEN!!!!": 7.0, "KEN...": 3.5},
        "anchor": "world point = player origin + the staging's shout_anchor_offset (bars 1-5) or "
                  "ken_anchor_offset (from the release on - KEN!!!! hops clear of the beam as the camera pulls out), converted to the screen each frame so it rides the zoom; the word "
                  "centred on it, clamped 16 screen px inside the edges",
        "pop": "scale 1.35x -> 1x over 0.15 s as each syllable lands; one word at a time; KEN!!!! stays 1.1 s",
    },
    "camera": {
        "bars_zoom": mock.BAR_ZOOM,
        "bars_focus_lerp": mock.BAR_FOCUS,
        "focus_target": "player origin + (0, -20) (his chest)",
        "per_bar": "tween zoom/focus over 0.22 s, ease-out-back (a little punch); shake 6 world px at bar 4, 9 at bar 5",
        "release": "snap out to the staging's camera_release over 0.25 s (ease-out cubic), shake 14 while the beam "
                   "travels",
        "dissolve": "drift to camera_dissolve_end over the 2.4 s (smoothstep), shake 9 -> 3.6",
    },
    "mock_timeline_s": {
        "bars_at": mock.BAR_TIMES, "step_in_at": mock.STEP_AT,
        "release": "bar 5 + 0.12", "hit": "release + 0.41", "dissolve": "hit .. hit + 2.4",
        "fail": "3 bars, timer out at 3.3 (meter flashes red), release anyway at +0.25 with KEN... (deflated), "
                "a thin flickering beam (scale.y ~0.5) for 0.75 s: he comes half apart; it cuts (fizzle at the "
                "hands), Burak fail 9-10-11, Jordan reform 9-15, a faint red flash, +5 on his bar",
    },
    "alignment_with_FinalBeamLayout_gd_as_seen_2026_10_06": {
        "player": "names and the 12-cell order already match (player_final_beam_side/back.png, 48x48, centred).",
        "core": "core() = GOD_POINT + RUNES_OFFSET = (960, 304) is the rune circle's centre; his DRAWN white core on hit "
                "frame 0 / hover frame 0 is (958.5, 283.5) - aim the beam and centre the impact there.",
        "marks": "stand-in marks side (-76, 1340) / back (960, 1330) vs the pass's (266, 975) / (960, 1290); the "
                 "mocks, the ash direction and the camera numbers here are built on the pass's.",
        "effect_sizes": "the stand-in FINAL_* sizes (body 32x64, head 64x96, impact 128x128 x6, muzzle 48x80 x4, "
                        "ball 6 rows, aura 4 frames) are guesses - take the cells, pivots and frame counts above.",
        "god": "the pass replaces his body with god_disintegrate / god_reform (+ glow + ash) instead of an additive "
               "jordan_god_beam_cracks overlay; no particle ash needed (it is drawn, streaming with the beam).",
        "shout": "the stand-in draws SHIN.../KU.../HA.../DO.../KEN!!!! as centred UI text; the pass offers drawn "
                 "lettering (beam_shout_words.png) anchored by him - either can sit at the anchors given.",
    },
    "mocks": "mocks/*.gif are 960x540 at 15 fps, drawn the way the game draws it (void_bg screen-space at 3x; "
             "world at the camera's zoom; additive glows) from these exact sheets; scene placement was checked "
             "against the real capture jordan_puppet_master/stills_B/03_pulled_back.png (body, wings and player "
             "pixel-identical).",
}

if __name__ == "__main__":
    p = out_path("contract.json")
    with open(p, "w") as f:
        json.dump(C, f, indent=2)
    print("wrote", p)
