"""The cast's measured numbers, per frame, for every sheet in this topic.

The bar is the shipped art, not a rule of thumb: Computah's 64x64 sheets run 21-25%
keyline over 21-27 colours a frame, Greyson's 96x96 sheets 20-24% over 25-30.  Zero
pure black anywhere - the keyline is #0C111A.

  python checks.py [frame_size]
"""
import glob
import os
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
KEYLINE = (0x0C, 0x11, 0x1A)


def frame_stats(im, fw):
    px = im.convert("RGBA").load()
    for f in range(im.width // fw):
        c = Counter()
        for y in range(im.height):
            for x in range(f * fw, (f + 1) * fw):
                r, g, b, a = px[x, y]
                if a > 128:
                    c[(r, g, b)] += 1
        yield c


def main(fw=96):
    worst = []
    for path in sorted(glob.glob(os.path.join(HERE, "computah_*.png"))):
        im = Image.open(path)
        # only his 96x96 body sheets hold the character band; props are their own
        # size and are checked by their own rules (see mine_ring)
        if im.height != fw or im.width % fw:
            continue
        rows = list(frame_stats(im, fw))
        ks = [100.0 * c[KEYLINE] / sum(c.values()) for c in rows]
        ns = [len(c) for c in rows]
        black = sum(c.get((0, 0, 0), 0) for c in rows)
        print("%-30s %d frames  keyline %4.1f-%4.1f%%  colours %2d-%2d  pure black %d"
              % (os.path.basename(path), len(rows), min(ks), max(ks),
                 min(ns), max(ns), black))
        if black or max(ns) > 32 or not (18.0 <= min(ks) <= 26.0):
            worst.append(os.path.basename(path))
    if worst:
        print("OUT OF BAND: " + ", ".join(worst))
    return 1 if worst else 0


# ---------------------------------------------------------------------------
# the hurtboxes, measured off the drawings rather than guessed
# ---------------------------------------------------------------------------
# sheet, frame the box is measured on, and the constant it feeds
BOXES = (
    ("computah_idle.png", 0, "C_BODY_BOX"),
    ("computah_beam_recover.png", 2, "C_VENT_BODY_BOX"),
    ("computah_drop.png", 3, "C_DOWN_BODY_BOX"),
)


def boxes(fw=96):
    """Rows narrower than 20 px are skipped so the antenna - a thin whip - cannot
    inflate a hurtbox.  The cannon IS included: whether the weapon is punchable is a
    design call, so the number here is the whole silhouette and trimming it is a
    decision someone makes on purpose."""
    for name, f, const in BOXES:
        im = Image.open(os.path.join(HERE, name)).convert("RGBA")
        px = im.crop((f * fw, 0, (f + 1) * fw, im.height)).load()
        runs = {}
        for y in range(im.height):
            xs = [x for x in range(fw) if px[x, y][3] > 128]
            if len(xs) >= 20:
                runs[y] = xs
        ys = sorted(runs)
        lo = min(min(runs[y]) for y in ys)
        hi = max(max(runs[y]) for y in ys)
        print("%-26s %-18s Rect2(%d, %d, %d, %d)   top row %d = %d px above the "
              "floor point at SCALE 3"
              % (name, const, lo, ys[0], hi - lo + 1, im.height - ys[0],
                 ys[0], (im.height - ys[0]) * 3))


# ---------------------------------------------------------------------------
# THE MINE'S TRIGGER RING
# ---------------------------------------------------------------------------
def mine_ring():
    """The drawn ring IS the trigger area, so it has to be exactly 24 x 12 texels on
    every armed frame and no cyan may ever appear outside that box.  A player who
    steps just clear of the ring they can see must never be caught by it, and the
    only way to keep that true across redraws is to measure it.
    """
    import computah_props as P
    im = Image.open(os.path.join(HERE, "computah_mine.png")).convert("RGBA")
    cyan = {tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            for h in P.PAL["spark"]}
    x0, y0, x1, y1 = P.RING_BOX
    fw = P.MINE_FRAME
    px = im.load()
    bad = []
    for f in range(im.width // fw):
        pts = [(x - f * fw, y) for y in range(im.height)
               for x in range(f * fw, (f + 1) * fw)
               if px[x, y][3] > 128 and px[x, y][:3] in cyan]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        box = (min(xs), min(ys), max(xs), max(ys))
        w, h = box[2] - box[0] + 1, box[3] - box[1] + 1
        inside = box[0] >= x0 and box[1] >= y0 and box[2] <= x1 and box[3] <= y1
        exact = box == (x0, y0, x1, y1)
        ring = 1 <= f <= 6                      # the frames that show the warning
        ok = exact if ring else inside
        print("  mine f%d  cyan %dx%d at %s  %s" % (f, w, h, box,
              "EXACTLY the trigger box" if exact else
              ("inside it" if inside else "OUTSIDE THE TRIGGER BOX")))
        if not ok:
            bad.append(f)
    if bad:
        print("  RING WRONG on frames: %s (want exactly %dx%d at %s on 1-6)"
              % (bad, P.RING_W, P.RING_H, P.RING_BOX))
    return 1 if bad else 0


def fall_band(fw=96):
    """computah_uppercut frames 6-9 have the same down hurtbox swapped in as
    computah_drop's floor frames, so the two have to lie in the same vertical band.
    Drawn months apart they would drift; measured, they cannot."""
    tops = {}
    for name, frames in (("computah_drop.png", (2, 3, 4)),
                         ("computah_uppercut.png", (6, 7, 8, 9)),
                         ("computah_armless_down.png", (0, 1, 2)),
                         ("computah_disarm.png", (3, 4))):
        im = Image.open(os.path.join(HERE, name)).convert("RGBA")
        px = im.load()
        rows = []
        for f in frames:
            ys = [y for y in range(im.height)
                  if sum(1 for x in range(f * fw, (f + 1) * fw)
                         if px[x, y][3] > 128) >= 20]
            rows.append(min(ys))
        tops[name] = rows
        print("  %-26s down frames top rows %s" % (name, rows))
    flat = [r for rows in tops.values() for r in rows]
    spread = max(flat) - min(flat)
    print("  spread across every down pose: %d rows (%d px at SCALE 3)"
          % (spread, spread * 3))
    if spread > 8:
        print("  DOWN POSES HAVE DRIFTED APART - one hurtbox cannot cover them all")
    return 1 if spread > 8 else 0


def dormant_handover(fw=96):
    """The entrance's last boot frame has to land on the pose it hands over to.

    computah_dormant is build_idle frame 0's own rig lerped back into a slump, so the
    two CAN only drift if someone retunes the idle and leaves DORMANT_RIG's right-hand
    column behind.  That is a silent break - the drawing still renders, the cut into
    `idle` just pops - so it is measured here instead of being trusted.

    The last boot frame is deliberately still short of the idle: it is the frame
    BEFORE it, not a copy of it.  What must not happen is a big step either way.
    """
    pairs = (("computah_dormant.png", 3, "computah_idle.png", 8),)
    bad = 0
    for an, af, bn, bf in pairs:
        rows = []
        for name, f in ((an, af), (bn, bf)):
            im = Image.open(os.path.join(HERE, name)).convert("RGBA")
            px = im.load()
            ys = [y for y in range(im.height)
                  if sum(1 for x in range(f * fw, (f + 1) * fw)
                         if px[x, y][3] > 128) >= 20]
            rows.append(min(ys))
        step = rows[0] - rows[1]
        print("  %s f%d tops at row %d, %s f%d at row %d: a %d row step "
              "(%d px at SCALE 3)"
              % (an, af, rows[0], bn, bf, rows[1], step, step * 3))
        if not 0 <= step <= 6:
            print("  THE BOOT NO LONGER LANDS ON THE IDLE - retype DORMANT_RIG's "
                  "right-hand column from build_idle frame 0")
            bad = 1
    return bad


if __name__ == "__main__":
    fw = int(sys.argv[1]) if len(sys.argv) > 1 else 96
    code = main(fw)
    print()
    boxes(fw)
    print()
    code |= mine_ring()
    print()
    code |= fall_band(fw)
    print()
    code |= dormant_handover(fw)
    sys.exit(code)
