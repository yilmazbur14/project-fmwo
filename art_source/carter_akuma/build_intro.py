"""Build Carter's entrance and its overlays into Assets/Characters/Carter.

    python build_intro.py

Writes
  carter_intro.png       17 frames of 96x96, feet on row 95
  carter_mark_glow.png    6 frames, additive overlay of the mark alone
  carter_aura.png         6 frames of 96x96, looping ambient aura for behind him
  carter_intro_flash.png  1 frame, ground scorch + shock ring for the peak
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import carter_scale
carter_scale.apply()          # draw him at his reduced size
from lib import (W, H, Canvas, union, inter, sub, grow, erode, ell, poly,
                 empty, PALC, bayer, mirror)
from pngio import write_png, read_png, blank, paste, crop
import aura as AU
import poses as PO
import intro_lib as IL
import intro_frames as IF

OUT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Assets', 'Characters', 'Carter'))
APPROVED = os.path.join(OUT, 'carter_akuma.png')

N_INTRO = 17


# ---------------------------------------------------------------- intro strip

def build_intro():
    _, _, appr = read_png(APPROVED)
    fs = []
    for k in range(5):
        fs.append(IF.frame_materialise(k).rgba())
    for i in range(4):
        fs.append(IF.frame_flare(i).rgba())
    for i in range(5):
        fs.append(IF.frame_turn(i).rgba())
    # settle: the two ends are the approved frames themselves, pixel for pixel,
    # so the fight can cut from the last entrance frame straight into idle.
    fs.append(crop(appr, W, 0, W, H))          # 14 = approved frame 1
    fs.append(IF.frame_settle(1).rgba())       # 15 = arms dropping
    fs.append(crop(appr, 0, 0, W, H))          # 16 = approved frame 0 (idle)
    assert len(fs) == N_INTRO, len(fs)
    return fs


# ---------------------------------------------------------------- mark glow

MARK_LV = [0.10, 0.34, 0.66, 1.00, 0.70, 0.36]


def mark_box():
    sg = IF.sigil_mask()
    xs = [x for y in range(H) for x in range(W) if sg[y][x]]
    ys = [y for y in range(H) for x in range(W) if sg[y][x]]
    # the peak's free-air bloom reaches 16 rings, so anything tighter than
    # this clips the halo square at the texture edge
    pad = 18
    x0 = max(0, min(xs) - pad)
    y0 = max(0, min(ys) - pad)
    x1 = min(W - 1, max(xs) + pad)
    y1 = min(H - 1, max(ys) + pad)
    return x0, y0, x1 - x0 + 1, y1 - y0 + 1


def build_mark_glow():
    """The mark on its own for an ADDITIVE layer: everything here is light, so
    it is drawn on transparent with no body underneath."""
    sg = IF.sigil_mask()
    frames = []
    for i, lv in enumerate(MARK_LV):
        cv = Canvas()
        IL.sigil_paint(cv, sg, lv)
        # free-air bloom: paints light onto empty pixels, so the halo survives
        # on a layer that has no body underneath it
        IL.glow_halo(cv, sg, lv)
        if lv >= 0.95:
            for j in range(12):
                a = j * math.pi / 6 + 0.26
                for r in range(13, 34):
                    x = int(round(47.5 + math.cos(a) * r * 0.95))
                    y = int(round(52.0 + math.sin(a) * r * 1.05))
                    if not (0 <= x < W and 0 <= y < H):
                        break
                    if (r + j) % 3 == 0 and cv.px[y][x] is None:
                        cv.px[y][x] = PALC['X'] if r < 22 else PALC['y']
        frames.append(cv.rgba())
    x0, y0, bw, bh = mark_box()
    return [crop(f, x0, y0, bw, bh) for f in frames], (x0, y0, bw, bh)


# ---------------------------------------------------------------- aura loop

def build_aura():
    """A wider, cooler halo than the wisps baked into the sprite - it layers
    UNDER him and adds atmosphere instead of doubling the existing crown."""
    body = IF.back_body().mask_of()
    inner = erode(body, 3)          # keep the roots so wisps do not float free
    frames = []
    for k in range(6):
        cv = Canvas()
        # jitter's phase is k*pi/2, so k must span exactly 2pi over the 6
        # frames or the loop jumps on the wrap: 6 frames => step 4/6
        ph = k * 4.0 / 6.0
        puls = math.sin(k * math.pi / 3.0)
        # the entrance strand set, not the sheet's crown: stacking the shipped
        # vertical wisps on top of the entrance aura rebuilt the spiky crown
        # this pass exists to get rid of
        specs = IL.entr_specs(ph, scale=1.10 + 0.12 * puls,
                              reach=1.22 + 0.12 * puls)
        AU.paint(cv, specs, IL.entr_sparks(ph), inner, hot=True)
        # thinned to haze: this layers behind a sprite that already carries its
        # own wisps, so it must widen the aura, not duplicate it
        m = cv.mask_of()
        keep = bayer(m, 13, k % 3)
        for y in range(H):
            for x in range(W):
                if m[y][x] and not keep[y][x]:
                    cv.px[y][x] = None
        frames.append(cv.rgba())
    return frames


# ---------------------------------------------------------------- flash

# This one draws straight into its own canvas instead of going through lib's
# rasterisers, so the scale transform does not reach it - the ring has to be
# sized by hand or it stays a shockwave for the big Carter under the small one.
_FS = carter_scale.SCALE
FLASH_W = int(round(144 * _FS)) // 2 * 2
FLASH_H = int(round(52 * _FS))
FLASH_CX, FLASH_CY = FLASH_W / 2.0, FLASH_H / 2.0
FLASH_RX, FLASH_RY = 60.0 * _FS, 21.0 * _FS


def build_flash():
    """Ground shock ring for the frame the mark peaks on.  It is an ADDITIVE
    layer, so the charred middle is left empty - the floor shows through and
    only the ring itself adds light."""
    px = blank(FLASH_W, FLASH_H)

    def put(x, y, ch):
        if 0 <= x < FLASH_W and 0 <= y < FLASH_H:
            px[y][x] = PALC[ch]

    def band(r0, r1, ch, dens=16, step=0):
        for y in range(FLASH_H):
            for x in range(FLASH_W):
                u = (x + 0.5 - FLASH_CX) / FLASH_RX
                v = (y + 0.5 - FLASH_CY) / FLASH_RY
                d = math.sqrt(u * u + v * v)
                if not (r0 <= d < r1):
                    continue
                # hash scatter, not an ordered pattern: a modulo dither lays
                # the embers out in visible diagonal stripes
                if dens < 16 and IL._hash(x, y, step) >= dens / 16.0:
                    continue
                put(x, y, ch)

    # sparse embers scattered over the scorched floor
    band(0.30, 0.78, 'Z', dens=2, step=1)
    band(0.55, 0.88, 'z', dens=2, step=7)
    # the shock ring: hot inner lip, bright core, cooling outer wash
    band(0.86, 0.92, 'X', dens=11, step=3)
    band(0.92, 0.99, 'y', dens=16)
    band(0.99, 1.02, 'x', dens=9, step=5)
    band(1.02, 1.10, 'Y', dens=10, step=2)
    band(1.10, 1.22, 'z', dens=5, step=6)
    # streaks kicking outward, only in the outer third
    for j in range(16):
        a = j * math.pi / 8 + 0.19
        for t in range(78, 124):
            d = t / 100.0
            x = int(round(FLASH_CX + math.cos(a) * FLASH_RX * d))
            y = int(round(FLASH_CY + math.sin(a) * FLASH_RY * d))
            if (t + j) % 3:
                continue
            put(x, y, 'x' if d < 1.0 else 'y')
    return px


# ---------------------------------------------------------------- write

def sheet(frames, fw, fh):
    s = blank(fw * len(frames), fh)
    for i, f in enumerate(frames):
        paste(s, f, i * fw, 0)
    return s


if __name__ == '__main__':
    intro = build_intro()
    write_png(os.path.join(OUT, 'carter_intro.png'), W * N_INTRO, H,
              sheet(intro, W, H))
    print('carter_intro.png       %dx%d  %d frames' % (W * N_INTRO, H, N_INTRO))

    glow, box = build_mark_glow()
    gw, gh = box[2], box[3]
    write_png(os.path.join(OUT, 'carter_mark_glow.png'), gw * len(glow), gh,
              sheet(glow, gw, gh))
    print('carter_mark_glow.png   %dx%d  %d frames of %dx%d  offset (%d,%d)'
          % (gw * len(glow), gh, len(glow), gw, gh, box[0], box[1]))

    aur = build_aura()
    write_png(os.path.join(OUT, 'carter_aura.png'), W * len(aur), H,
              sheet(aur, W, H))
    print('carter_aura.png        %dx%d  %d frames' % (W * len(aur), H, len(aur)))

    fl = build_flash()
    write_png(os.path.join(OUT, 'carter_intro_flash.png'), FLASH_W, FLASH_H, fl)
    print('carter_intro_flash.png %dx%d  1 frame' % (FLASH_W, FLASH_H))
