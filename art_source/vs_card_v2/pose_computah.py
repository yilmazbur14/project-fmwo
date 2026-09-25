"""COMPUTAH - the cannon levelled at Burak, the muzzle charging green, the battery full.

Built from his own pixels (all 96 x 96 frames, keyline #0C111A):
  * computah_beam_charge.png - the base: the Mega Man charge stance, the arm cannon out level, the
                               other fist bracing it from below, the red eyes lit
  * computah_beam_fire.png   - frame 1's orb, the green charge that sits on the muzzle

He aims to screen RIGHT in every sheet; Burak is on the left. So the figure is turned, and the turn
keeps the cast's one light (STYLE.md, upper left):
  * the whole frame is mirrored, which turns the head, the cannon and the bracing fist to Burak
  * everything that is lit across its width is then re-lit by TRANSLATION rather than mirroring:
    every horizontal run of one part keeps its own left-to-right tones (the dome's highlight stays on
    its upper left, the ear discs', the jaw's, the shoulder's, the antenna's) - only the run moves
  * what is flat or shaded along its length stays mirrored: the visor and its eyes, the battery, and
    the barrel with its muzzle (STYLE.md: "the barrel mirrored (shaded along its length)")
The parts are his own components, cut along his keyline (segment.py), so every join is his line.

The arm is raised: the barrel, its muzzle and the bracing fist are TRANSLATED up 4 px as one piece
(STYLE.md: "the arm translated"). The charge frame holds the cannon at the waist, which the card's
chest crop would cut through at the bottom rule; 4 px lifts the whole gesture inside the band, and
still clears his jaw. The body keeps every keyline it shares with the arm (segment.take), so the
torso's side stays closed where the arm left it.

Two edits, both in his own colours:
  * battery full: the fourth cell, dark in the charge frame (#46536A / #333E52), takes the third
    cell's green column - the idle sheet's full battery
  * the charge: beam_fire frame 1's orb is set on the muzzle, facing Burak, without its firing trail

Then Scale2x (pxkit), and the 2x pass (detail): one glint on each eye.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pxkit as P                                                             # noqa: E402
import segment as S                                                           # noqa: E402

KEY = (0x0C, 0x11, 0x1A)                  # his keyline, measured (measure_cast.py)
KEY_RGBA = KEY + (255,)
BASE = "Computah/computah_beam_charge.png"
FIRE = ("Computah/computah_beam_fire.png", 1)

# component ids in the charge frame (segment.components order, checked by tint_view)
VISOR, BARREL, MUZZLE, TORSO, FIST = 3, 14, 16, 15, 17
ARM = [BARREL, MUZZLE, FIST]
ARM_LIFT = -4
# inside the torso component, the battery is flat: mirrored, not re-lit
BATTERY = {"#2A7A3C", "#1F9A38", "#4FE066", "#A9FFB4", "#2B3444", "#222A38", "#1A202B", "#333E52",
           "#46536A"}
# the fourth cell (x 44-46) and the third (x 38-40), rows 56-64 of the charge frame
CELL4, CELL3, CELL_ROWS = 44, 38, range(56, 65)
# the orb on the muzzle in beam_fire frame 1 (sheet coordinates) and its footprint
ORB_BOX = (140, 49, 168, 68)
ORB_C, ORB_R = (154.0, 59.0), 9.6
ORB_GREEN = {"#4FE066", "#A9FFB4", "#E6FFE9"}
ORB_TRAIL = [(x, 59) for x in range(161, 170)]       # the firing trail, left behind
W = 96


def frame(path, i=0):
    return P.load(path, (i * W, 0, i * W + W, W))


def battery_full(f):
    px = f.load()
    for y in CELL_ROWS:
        for dx in range(3):
            px[CELL4 + dx, y] = px[CELL3 + dx, y]
    return f


def turn(f, comps):
    """Mirror the frame; re-light every lit part by translating its runs."""
    owner = {}
    for c in comps:
        for q in c["pixels"]:
            owner[q] = c["id"]
    src = f.load()
    out = P.mirror(f)
    o = out.load()

    def lit(x, y):
        cid = owner.get((x, y))
        if cid is None or cid in (VISOR, BARREL, MUZZLE):
            return False
        if cid == TORSO and P.hexc(src[x, y]) in BATTERY:
            return False
        return True

    for y in range(W):
        x = 0
        while x < W:
            if not lit(x, y):
                x += 1
                continue
            cid = owner[(x, y)]
            x1 = x
            while x1 + 1 < W and lit(x1 + 1, y) and owner[(x1 + 1, y)] == cid:
                x1 += 1
            # the run x..x1 lands on W-1-x1 .. W-1-x, in its own order
            for i in range(x1 - x + 1):
                o[W - 1 - x1 + i, y] = src[x + i, y]
            x = x1 + 1
    return out


def orb():
    """beam_fire frame 1's charge, cut out: its green, and the dark of its own halo."""
    sheet = P.load(FIRE[0])
    src = sheet.load()
    x0, y0, x1, y1 = ORB_BOX
    part = Image.new("RGBA", (x1 - x0, y1 - y0), P.CLEAR)
    p = part.load()
    cx, cy = ORB_C
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x, y) in ORB_TRAIL:
                continue
            q = src[x, y]
            inside = ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) ** 0.5 <= ORB_R
            if q[3] > 128 and P.hexc(q) in ORB_GREEN and inside:
                p[x - x0, y - y0] = q
            elif inside:
                p[x - x0, y - y0] = (1, 1, 1, 1)         # a halo gap: filled by what is under it
    return part


# where the orb's centre goes on the turned frame: the muzzle's centre, pushed out toward Burak
ORB_AT = (24.5, 59.0 + ARM_LIFT)


def lift_arm(turned, comps):
    """The arm (barrel, muzzle, fist), cut from the turned frame along its keyline and put back
    ARM_LIFT px higher. Found by its components' mirrored pixels: turn() moves no pixel of a part
    outside that part's own mirror image."""
    flipped = [{"id": c["id"], "pixels": {(W - 1 - x, y) for (x, y) in c["pixels"]}} for c in comps]
    arm = S.take(turned, flipped, ARM, key=KEY)
    body = S.take(turned, flipped, [c["id"] for c in comps if c["id"] not in ARM], key=KEY)
    lifted = Image.new("RGBA", turned.size, P.CLEAR)
    lifted.paste(arm, (0, ARM_LIFT), arm)
    body.alpha_composite(lifted)
    return body


def charge(f):
    part = orb()
    px = f.load()
    p = part.load()
    ox = int(round(ORB_AT[0] - (ORB_C[0] - ORB_BOX[0])))
    oy = int(round(ORB_AT[1] - (ORB_C[1] - ORB_BOX[1])))
    for y in range(part.height):
        for x in range(part.width):
            q = p[x, y]
            if q[3] == 0:
                continue
            X, Y = ox + x, oy + y
            if not (0 <= X < f.width and 0 <= Y < f.height):
                continue
            if q[3] == 255:
                px[X, Y] = q
            elif px[X, Y][3] < 128:
                px[X, Y] = KEY_RGBA                   # the halo's dark, where it meets the air
    return f


def assemble():
    f = battery_full(frame(BASE))
    comps = S.components(f, KEY)
    return charge(lift_arm(turn(f, comps), comps))


EYE_GLINT = "#FFFFFF"


def detail(im):
    """The 2x pass: a glint in the upper left of each red eye (the lit side)."""
    px = im.load()
    reds = {P.rgba("#FF4436"), P.rgba("#FF7055")}
    w, h = im.size
    done = set()
    for y in range(h):
        for x in range(w):
            if px[x, y] not in reds or (x, y) in done:
                continue
            # flood this eye
            stack, eye = [(x, y)], set()
            while stack:
                q = stack.pop()
                if q in eye or not (0 <= q[0] < w and 0 <= q[1] < h) or px[q] not in reds:
                    continue
                eye.add(q)
                stack += [(q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)]
            done |= eye
            ex0 = min(q[0] for q in eye)
            ey0 = min(q[1] for q in eye)
            for q in ((ex0 + 2, ey0 + 2), (ex0 + 3, ey0 + 2), (ex0 + 2, ey0 + 3)):
                if q in eye:
                    px[q] = P.rgba(EYE_GLINT)
    return im


def build():
    im = detail(P.scale2x(assemble()))
    return im.crop(im.getbbox())


def source_numbers():
    f = frame(BASE)
    return P.numbers(f, KEY)


if __name__ == "__main__":
    out = sys.argv[1]
    a = assemble()
    P.save_zoom(a, os.path.join(out, "computah_pose_1x_8x.png"), 8)
    b = build()
    P.save_zoom(b, os.path.join(out, "computah_pose_2x_4x.png"), 4)
    print("source", source_numbers())
    print("1x", P.numbers(a, KEY))
    print("2x", b.size, P.numbers(b, KEY))
