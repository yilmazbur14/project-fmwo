"""Eric's entrance walk - four poses, assembled from his own pixels.

=============================================================================
READ THIS BEFORE YOU DRAW ANYTHING FOR ERIC.  It cost four rejections.
=============================================================================
ERIC HAS NO VISIBLE UPPER ARMS.  Every one of the 40 frames in eric_sheet_v2
goes pauldron, then gauntlet.  The arm between them is never drawn - it is
hidden inside the pauldron silhouette, and the gauntlet touches the torso.

ERIC HAS NO LEGS.  Below the belt he is two tasset lobes, a maroon surcoat V
between them, and two sabatons.  In 36 of the 40 frames the bottom row of the
sprite is ONE unbroken run about 70px wide.  There is no frame anywhere on any
current sheet with separated legs.

Any arm or leg DRAWN for him is anatomy the character does not have, which is
exactly why every drawn limb read as detached.  A limb reads as detached when
its root is a visible boundary: a keyline between limb and torso tells the eye
these are two separate objects sitting side by side.  His art never shows a
root.  So: if a body part has to move, find it in his sheets and displace it.
Do not draw it.  This rule supersedes every looser version of it.

The pose used here is sheet frame 37 - a complete, front-facing, empty-handed,
full-body Eric at entrance scale, feet already on the frame's bottom row.  It
is one of the quake landing frames, so it carries loose dust motes; they are
stripped by keeping only the largest connected component.

Contact-right applies contact-left's displacements SWAPPED rather than
mirroring pixels.  His art is asymmetric - mirroring flips the beard highlight
and the gauntlet details, and that asymmetry is part of why he looks drawn.

Four poses, not eight: weight comes from bob, follow-through and timing, not
frame count, and every extra frame is more surface for the failure above.
=============================================================================
"""
import sys
import os
from collections import deque, Counter
from PIL import Image

SHEET = ("C:/Users/theyi/OneDrive/Documents/new-game-project/"
         "Assets/Characters/Eric/eric_sheet_v2.png")
SRC_F = 37
SRC_BOX = (75, 119, 183, 192)      # his f37, tight: 108 x 73, feet on the last row
FRAME_W, FRAME_H = 256, 192
FLOOR = 191                        # feet land here
BODY_CX = 51                       # torso centre in SRC_BOX-local coords
BAND = 65                          # first row BELOW the belt; the leg group starts here


def load_clean():
    """f37, debris stripped: keep only the largest 4-connected opaque component."""
    sh = Image.open(SHEET).convert("RGBA")
    f = sh.crop((SRC_F * FRAME_W, 0, (SRC_F + 1) * FRAME_W, FRAME_H)).crop(SRC_BOX)
    px = f.load()
    W, H = f.size
    seen = [[False] * H for _ in range(W)]
    comps = []
    for sx in range(W):
        for sy in range(H):
            if seen[sx][sy] or px[sx, sy][3] == 0:
                continue
            q = deque([(sx, sy)])
            seen[sx][sy] = True
            cur = []
            while q:
                x, y = q.popleft()
                cur.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[nx][ny] and px[nx, ny][3] > 0:
                        seen[nx][ny] = True
                        q.append((nx, ny))
            comps.append(cur)
    comps.sort(key=len, reverse=True)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    op = out.load()
    for x, y in comps[0]:
        op[x, y] = px[x, y]
    return out, [len(c) for c in comps[1:]]


def maroon_set(im):
    """The surcoat / cape reds.  They stay put - only the armour lobes walk."""
    cnt = Counter(p[:3] for p in im.getdata() if p[3] > 128)
    out = set()
    for (r, g, b) in cnt:
        if r > g + 24 and r > b + 12 and r < 190 and max(g, b) < 110:
            out.add((r, g, b))
    return out


def lobe_masks(im, reds):
    """Each tasset lobe, region-grown from a seed over everything that is not
    maroon.  The growth crosses the plates own black keylines, so a lobe comes
    away as one whole object - three stacked plates and its sabaton - and stops
    dead at the surcoat V and the cape.  A straight horizontal cut instead
    orphans the belt's lower edge and steps the cape."""
    px = im.load()
    W, H = im.size

    def grow(seed, lo, hi):
        # lo/hi bound the grow to one side of the centre line.  Without that it
        # leaks: his two sabatons touch on the bottom row (that unbroken run is
        # the same fact recorded at the top of this file), so a free grow from
        # either seed swallows both lobes.  The centre is where the surcoat V
        # sits, so cutting there is the natural seam; the OUTER edge of each
        # lobe still comes away along its own keyline.
        m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        mp = m.load()
        q = deque([seed])
        hit = {seed}
        while q:
            x, y = q.popleft()
            mp[x, y] = px[x, y]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (lo <= nx < hi and BAND <= ny < H) or (nx, ny) in hit:
                    continue
                c = px[nx, ny]
                if c[3] == 0 or c[:3] in reds:
                    continue
                hit.add((nx, ny))
                q.append((nx, ny))
        return m, hit

    lm, lh = grow((BODY_CX - 9, BAND + 3), 0, BODY_CX)
    rm, rh = grow((BODY_CX + 9, BAND + 3), BODY_CX, W)
    return lm, rm, lh | rh


# NOTE ON THE ARMS.  An earlier cut here displaced the gauntlets by a texel in
# opposition to the legs.  It was removed.  His gauntlet is a mitten at x15-22,
# y46-53 and a slitted hip box at x21-31, y56-64, and both share keylines with
# the torso and the pauldron lame above them - taking either as a rectangle
# slices a visible seam through his shoulder, and taking it as a region grow
# risks dropping the 1px keyline that is the only thing separating it from the
# torso.  A seam at the shoulder is precisely the "not even attached" failure
# this sheet exists to fix, so the arms ride the body bob instead.  His own
# front-facing standing frames do not swing the arms either.  Do not reinstate
# this without a pixel map of the region first.


def build(debug_dir=None):
    body, strays = load_clean()
    W, H = body.size
    reds = maroon_set(body)
    lobe_l, lobe_r, moving = lobe_masks(body, reds)

    rest = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bp = body.load()
    rp = rest.load()
    for x in range(W):
        for y in range(H):
            if bp[x, y][3] and (x, y) not in moving:
                rp[x, y] = bp[x, y]

    def compose(dl, dr, bob):
        im = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        ox = FRAME_W // 2 - BODY_CX
        oy = FLOOR + 1 - H
        im.alpha_composite(lobe_l, (ox + dl[0], oy + dl[1]))
        im.alpha_composite(lobe_r, (ox + dr[0], oy + dr[1]))
        im.alpha_composite(rest, (ox, oy + bob))
        return im

    # Contact is the BASELINE (bob 0) and pass is the lift.  The body must
    # never bob below baseline: his feet already sit on FLOOR, so a downward
    # bob pushes the sprite's last row past row 191 and it is silently clipped.
    # Weight still reads, because weight is the difference between the high
    # pass and the low contact, not an absolute drop.
    #
    # Exactly one lobe is planted at dy=0 in every frame, so he never floats.
    # The cycle is pass(left swinging) - contact left - pass(right swinging) -
    # contact right, which loops back cleanly.  The two passes differ by a
    # texel of bob so the cycle does not read as a two-frame flicker.
    poses = [
        compose((0, -2), (0, 0), -2),      # 0 pass  - left lobe swinging through
        compose((-2, 0), (2, -1), 0),      # 1 contact left  - left plants forward
        compose((0, 0), (0, -2), -1),      # 2 pass  - right lobe swinging through
        compose((-2, -1), (2, 0), 0),      # 3 contact right - right plants forward
    ]

    if debug_dir:
        dbg = Image.new("RGBA", (W * 4 + 30, H), (40, 40, 50, 255))
        for i, m in enumerate((lobe_l, lobe_r, rest, body)):
            dbg.alpha_composite(m, (i * (W + 10), 0))
        dbg.resize((dbg.width * 5, dbg.height * 5), Image.NEAREST).convert("RGB").save(
            os.path.join(debug_dir, "_masks.png"))
    return poses, strays, len(reds)


def main(outdir):
    poses, strays, nreds = build(outdir)
    strip = Image.new("RGBA", (FRAME_W * len(poses), FRAME_H), (0, 0, 0, 0))
    for i, p in enumerate(poses):
        strip.alpha_composite(p, (i * FRAME_W, 0))
    path = os.path.join(outdir, "eric_entrance.png")
    strip.save(path)
    print("eric_entrance  %dx%d  hframes=%d" % (strip.width, strip.height, len(poses)))
    print("  debris stripped: %s   maroon colours held static: %d" % (strays[:6], nreds))
    return path


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
