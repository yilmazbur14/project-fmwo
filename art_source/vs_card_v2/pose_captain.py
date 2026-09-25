"""CAPTAIN BURAK - the tutorial boss's VS pose: the cutlass on his shoulder, the bell-mouthed
flintlock raised beside his head and levelled at the player, and his grin.

Built with his own rig (art_source/burak_boss, imported read-only; nothing there is changed or run
as a script, and no bytecode is written into it): every part is the rig's own function or grid.

  - Body, head, hat, bandana, the sword arm and the cutlass on his shoulder: frame 1 (the shot), as
    the sheet draws them - head cocked, hat knocked rakish, the wink and grin with the "ting".
  - The pistol hand and gun: frame 1's fist, hammer, flaring bell and bell mouth, translated as one
    unit (never redrawn) from hip height up to eye level, the bore dark: he has not fired yet.
  - Only the upper arm, the pushed-up cuff and the bare forearm are re-laid, with the rig's own
    sleeve / cuff_d / limb, to carry the shoulder up to the raised fist.

Why the gun moves: the sheet thrusts it out at hip height, which the card's waist-up crop cuts off
and the name plate would cover. Raised beside his head it frames the face with the blade.

Then the rig's palette merge and image(), Scale2x, and a lock to his 38 colours.
"""
import os
import sys

sys.dont_write_bytecode = True           # before the rig is imported: write nothing into its folder
HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.normpath(os.path.join(HERE, "..", "burak_boss"))
sys.path.insert(0, HERE)
for _clash in ("kit", "head"):
    if _clash in sys.modules and "burak_boss" not in (getattr(sys.modules[_clash], "__file__", "") or ""):
        raise ImportError("module %r is already loaded from %s; build Captain Burak in its own process"
                          % (_clash, sys.modules[_clash].__file__))
sys.path.append(RIG)
import pxkit as P                                                             # noqa: E402
import burak as CB                                                            # noqa: E402  (read-only)
import head as HD                                                             # noqa: E402  (read-only)
from kit import Canvas, amap, image                                          # noqa: E402  (read-only)

# frame 1's gun hand, as the rig lays it out (fist grid at dy=4, hammer, bell exit and mouth)
F1_FIST_DY, F1_HAMMER, F1_EXIT = 4, (79, 54), (81, 63.5)
F1_MOUTH = CB.MUZZLE
F1_WEDGE = (2.3, 5.4)
F1_RING = (6.2, 3.9)

# the raise: the whole gun hand moves by GUN (dx, dy); the arm is re-laid to reach it
GUN = (0, -27)
# an L like his sword arm's: the upper arm out and up from the shoulder, the forearm straight up
# from the elbow's gold-edged cuff to the fist beside his head. The fist sits just above the eye
# line: high enough that the bell's rim clears the name plate on the card, low enough that the
# hammer keeps a one-pixel gap under the bandana's tail instead of joining it.
SLEEVE = ((64.5, 52.0), (73.5, 47.5), 4.5, 4.2)
CUFF = ((75.0, 43.2), (0.15, -1.0), 1.5, 4.0)
FOREARM = ((75.4, 41.6), (76.8, 36.0), 2.3, 2.3)
# frame 1's own pistol arm, for the proof that this file rebuilds frame 1 exactly
F1_ARM = dict(gun=(0, 0), sleeve=((64, 53), (70, 57.5), 4.5, 4.0), cuff=((71.8, 59), (0.8, 0.6), 1.5, 4.0),
              forearm=((73.3, 60.5), (75, 61.8), 2.9, 2.8), cuff_over=False)


def build(face='shot', cock=True, gun=GUN, sleeve=SLEEVE, cuff=CUFF, forearm=FOREARM, cuff_over=True):
    cv = Canvas()

    def put(part, dx=0, dy=0, outline=True):
        cv.stamp({(x + dx, y + dy): k for (x, y), k in part.items()} if (dx or dy) else part, outline)

    hx, htilt = (-2, -0.06) if cock else (0, 0.0)          # frame 1's cocked head and rakish hat
    put(CB.coat_back())
    put(CB.legs())
    for b_, c_ in (CB.boot(0), CB.boot(1)):
        put(b_)
        put(c_)
    put(CB.tee())
    band, tails = CB.sash()
    put(band)
    put(amap(CB.BUCKLE, 45, 65), outline=False)
    put(CB.coat_panel(1, flare=True))
    put(CB.coat_panel(0))
    put(tails)
    put(CB.collar(), dx=hx // 2)
    put(HD.neck(), dx=hx)
    put(CB.tee_collar(), dx=hx // 2, outline=False)
    put(CB.chain(), dx=hx // 2, outline=False)
    # the pistol arm, raised: the rig's sleeve, forearm and cuff re-laid up to the fist. The cuff
    # goes on after the forearm here, so its gold-edged roll wraps the forearm's root instead of
    # being covered by it (the arm now rises out of the cuff rather than running along the view).
    p0, p1, r0, r1 = sleeve
    put(CB.sleeve(p0, p1, r0, r1, lit_side=False))
    a0, a1, q0, q1 = forearm
    c, axis, w, h = cuff
    if not cuff_over:                                       # the rig's own order (frame 1)
        put(CB.cuff_d(c, axis, w, h))
    put(CB.limb([(a0, a1, q0, q1)], '4', '3', '5', '6'))
    if cuff_over:
        put(CB.cuff_d(c, axis, w, h))
    # frame 1's gun hand, translated whole
    gx, gy = gun
    ex, ey = F1_EXIT[0] + gx, F1_EXIT[1] + gy
    mx, my = F1_MOUTH[0] + gx, F1_MOUTH[1] + gy
    put(CB.bell_wedge((ex, ey), (mx, my), *F1_WEDGE))
    put(CB.FIST_GUN, dx=gx, dy=F1_FIST_DY + gy, outline=False)
    put(CB.hammer(F1_HAMMER[0] + gx, F1_HAMMER[1] + gy))
    put(CB.bell_mouth((ex, ey), (mx, my), *F1_RING, fire=False))
    # the head
    if CB.BANDANA:
        for t in CB.bandana_tails(1.0):
            put(t, dx=hx)
    l, r = HD.ears()
    put(l, dx=hx)
    put(r, dx=hx)
    put(HD.face_base(), dx=hx)
    put(HD.features(face), dx=hx, outline=False)
    if face == 'shot':
        # frame 1's manga "ting!" off the grin
        put({(56, 36): 'W', (56, 37): 'W', (56, 38): 'Y', (56, 39): 'W', (56, 40): 'W', (54, 38): 'W',
             (55, 38): 'W', (57, 38): 'W', (58, 38): 'W'}, dx=hx, outline=False)
    put(HD.hair(), dx=hx)
    put(HD.flyaways(), dx=hx, outline=False)
    put(HD.hat(htilt), dx=hx, outline='soft')
    # the sword arm and the cutlass on his shoulder, as both frames draw them
    put(CB.sleeve((31.5, 53), (28.5, 63), 4.6, 3.9))
    put(CB.cuff((28.5, 64), 3.8, 1.5))
    put(CB.limb([((29, 66), (34, 58), 2.8, 2.6)], '3', '2', '4', '5'))
    put(CB.cutlass((31.5, 49.5), (9, 25), bow=2.4))
    put(amap(CB.FIST_SWORD, 29, 50), outline=False)
    px = {(x, y): CB.MERGE.get(k, k) for (x, y), k in cv.px.items()}
    return image(px)


def sheet():
    return P.load("BurakBoss/burak_boss.png")


def sheet_palette():
    return P.palette(sheet())


def pose(**kw):
    return P.lock(P.scale2x(build(**kw)), sheet_palette())


def rebuild_check():
    """This file's build() with frame 1's own arm must equal the rig's frame 1 (fx off), pixel for
    pixel: it proves the only things the pose changes are the ones the docstring lists."""
    rig = image(CB.frame_px(1, fx=False))
    mine = build(face='shot', **F1_ARM)
    return sum(1 for y in range(rig.height) for x in range(rig.width)
               if rig.getpixel((x, y)) != mine.getpixel((x, y)))


if __name__ == "__main__":
    from PIL import Image
    from gridview import grid
    out = sys.argv[1]
    if os.path.abspath(out).replace("\\", "/").lower().find("/assets/") >= 0:
        raise SystemExit("pose_captain.py writes previews only; refusing a path inside Assets/")
    for face in ("shot", "idle"):
        s = build(face=face)
        grid(s, (0, 0, 96, 72), 8, os.path.join(out, "captain_1x_%s_grid.png" % face))
        b = Image.new("RGBA", s.size, (120, 140, 170, 255))
        b.alpha_composite(s)
        b.resize((s.width * 5, s.height * 5), Image.NEAREST).save(os.path.join(out, "captain_1x_%s_5x.png" % face))
        print(face, "1x", P.numbers(s), "2x", P.numbers(pose(face=face)))
    print("frame-1 rebuild vs the rig's own build(1, fx=False):", rebuild_check() or "identical")
