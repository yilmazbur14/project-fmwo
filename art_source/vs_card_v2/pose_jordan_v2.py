"""JORDAN v2 - the final boss's VS pose in his approved v2 look (thin, frail, greasy; approved
2026-09-24): the fist punched skyward with the pink pop and gold star, the chase-edition box held up
by his face on his other stick arm, mid-shout.

Built with the v2 rig (art_source/jordan_v2, imported read-only; nothing there is changed or run
as a script, and no bytecode is written into it). Every part is the rig's own:

  - legs, shoes, neck, the hanging tee and its Peach print, the dandruff, the head (the approved
    face, shouting) and the whole fist-pump arm with the pop, star and glints: frame 1, as drawn;
  - the far arm holding the box up beside his face, the box and the hand round it: frame 0, as drawn.

The only change from the sheet is which far arm frame 1 uses. The sheet's frame 1 hangs the box at
his hip, below the card's waist-up crop, so here he holds it up beside his face as frame 0 does. The
trophy stays in the card, which is the idea the v1 card had ("the chase box hoisted like a trophy,
laughing").

He faces screen-right, as his v2 sheet does, and is kept that way rather than mirrored, like Josh:
a mirror would move the light.

`rebuild_check()` proves this file's assembly draws the sheet's two frames pixel for pixel.

Note: the rig imports modules named kit, head and lib from its own folders. pose_captain imports
Captain Burak's kit and head under the same names, so the two poses cannot be built in one Python
process. ship.py ships them in separate runs.
"""
import os
import sys

sys.dont_write_bytecode = True           # before the rig is imported: write nothing into its folders
HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.normpath(os.path.join(HERE, "..", "jordan_v2"))
sys.path.insert(0, HERE)
for _clash in ("kit", "head", "lib", "torso", "jordan"):
    if _clash in sys.modules and "jordan" not in os.path.dirname(getattr(sys.modules[_clash], "__file__", "") or ""):
        raise ImportError("module %r is already loaded from %s; build Jordan in its own process"
                          % (_clash, sys.modules[_clash].__file__))
sys.path.append(RIG)
import pxkit as P                                                             # noqa: E402
import jv2_base as B                                                          # noqa: E402  (read-only)
import jv2_body as body                                                       # noqa: E402  (read-only)
import jv2_head as jhead                                                      # noqa: E402  (read-only)
import jv2_frames as F                                                        # noqa: E402  (read-only)

J = B.jordan
SHEET = "Jordan/jordan_redesign_v2.png"


def _stamp_all(cv, parts):
    for part, ol in parts:
        cv.stamp(part, outline=ol)


def build_px(variant="pump_box"):
    """variant: 'idle' (frame 0 as drawn), 'pump' (frame 1 as drawn), 'pump_box' (the card pose)."""
    frame = 0 if variant == "idle" else 1
    box_up = variant in ("idle", "pump_box")
    cv = B.Canvas(96, 96)
    cv.stamp(body.legs())
    for s in body.shoes():
        cv.stamp(s, outline=False)
    _stamp_all(cv, body.far_arm_box() if box_up else body.far_arm_box_low())
    dx, dy = F.HEAD_AT[frame]
    cv.stamp(body.neck(dx))
    cv.stamp(body.shirt(frame))
    body.dandruff(cv.px)
    cv.stamp(B.shift(jhead.head(shout=(frame == 1)), dx, dy), outline=False)
    if frame == 0:
        _stamp_all(cv, body.near_arm_hip())
    else:
        cv.stamp(J.pop_cloud())
        cv.stamp(B.amap(B.rows_of(J.STAR), 27, 0), outline=False)
        for q, k in J.GLINTS.items():
            cv.px[q] = k
        _stamp_all(cv, body.raised_arm())
    if box_up:
        cv.stamp(J.box_part(*F.BOX_AT[0]), outline=False)
        cv.stamp(B.amap(body.FAR_HAND_BOX, *F.FAR_HAND_AT), outline=False)
    else:
        cv.stamp(J.box_part(*F.BOX_AT[1]), outline=False)
        cv.stamp(B.amap(body.LOW_HAND, *F.LOW_HAND_AT), outline=False)
    return B.finish(cv.px)


def build(variant="pump_box"):
    return B.image(build_px(variant))


def fx_pixels(variant="pump_box"):
    return F.fx_pixels(0 if variant == "idle" else 1)


def sheet():
    return P.load(SHEET)


def sheet_palette():
    return P.palette(sheet())


def pose(variant="pump_box"):
    return P.lock(P.scale2x(build(variant)), sheet_palette())


def rebuild_check():
    """This file's assembly must draw the approved v2 sheet's two frames exactly (0 = idle, 1 = pump)."""
    s = sheet()
    out = []
    for i, v in ((0, "idle"), (1, "pump")):
        ref = s.crop((96 * i, 0, 96 * i + 96, 96))
        mine = build(v)
        out.append(sum(1 for y in range(96) for x in range(96) if ref.getpixel((x, y)) != mine.getpixel((x, y))))
    return out


if __name__ == "__main__":
    out = sys.argv[1]
    if os.path.abspath(out).replace("\\", "/").lower().find("/assets/") >= 0:
        raise SystemExit("pose_jordan_v2.py writes previews only; refusing a path inside Assets/")
    print("rebuild of the sheet's frames 0 and 1 (differing pixels):", rebuild_check())
    for v in ("idle", "pump", "pump_box"):
        s = build(v)
        a = B.audit(build_px(v), fx_pixels(v))
        print("%-9s 1x %s  2x %s  audit gaps %d lone %d holes %d keys %s" % (
            v, P.numbers(s), P.numbers(pose(v)), len(a["gaps"]), len(a["lone"]), len(a["holes"]), a["keys"] or "ok"))
        P.save_zoom(s, os.path.join(out, "jordan_v2_%s_5x.png" % v), 5, bg=(120, 140, 170, 255))
