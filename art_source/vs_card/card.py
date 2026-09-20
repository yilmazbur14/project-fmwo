"""VS intro card mocks for Eric (boss 1).

Everything pixel is authored at 640x360 - the resolution the game's other
full-screen art uses (Assets/UI/Screens/main_menu_bg.png, Assets/Environment/
arena_ringside.png) - then scaled 3x with NEAREST to 1920x1080.

Text is drawn AFTER the 3x scale, at the sizes in Assets/UI/ui_theme.tres
(33 / 55 / 99 = 3x, 5x, 9x the 11px grid), because Godot draws Labels at the
native window resolution rather than through the pixel scale.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from pxlib import hx, poly, canvas, outline, lines_clip, px_clip
import emblems

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
FONT = PROJ + "/fonts/PixelifySans.ttf"
NW, NH, SCALE = 640, 360, 3
SW, SH = NW * SCALE, NH * SCALE

# Ramps: Burak's side stays dark (as Platinum keeps the player's half dark),
# Eric's side carries his own steel->white plate with the red cross and gold trim.
BURAK_RAMP = ["#15131F", "#222034", "#2E2C4A", "#3F3F74", "#3A5BA8"]
ERIC_RAMP = ["#525A74", "#7A86A0", "#A3B1C2", "#CDD7E2", "#EAF0F6"]
GOLD, GOLD_HI = "#C48A2C", "#F2C457"
CROSS = "#B0242A"
INK = "#000000"


# ---------------------------------------------------------------- backdrop
def backdrop(darken=0.34, tint="#222034"):
    """The real arena, pushed back so the card sits in front of it."""
    bg = Image.open(PROJ + "/Assets/Environment/arena_ringside.png").convert("RGBA")
    mat = Image.open(PROJ + "/Assets/Environment/arena_mat.png").convert("RGBA")
    bg.alpha_composite(mat, ((NW - mat.width) // 2, NH - mat.height - 10))
    t = hx(tint)
    out = Image.new("RGBA", (NW, NH))
    src, dst = bg.load(), out.load()
    for y in range(NH):
        for x in range(NW):
            r, g, b, a = src[x, y]
            dst[x, y] = (int(r * darken + t[0] * (1 - darken)),
                         int(g * darken + t[1] * (1 - darken)),
                         int(b * darken + t[2] * (1 - darken)), 255)
    return out


# ------------------------------------------------------------ banded ramps
def banded(w, h, ramp, ang_deg=-58.0, period=9, flip=False):
    """A ramp gradient broken into faint diagonal bands, so the block reads as
    energy rather than a flat fill (the 'gradient with faint banding' in the ref)."""
    im = Image.new("RGBA", (w, h))
    p = im.load()
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    ds = [x * ca + y * sa for x, y in ((0, 0), (w, 0), (0, h), (w, h))]
    lo, hi = min(ds), max(ds)
    cols = [hx(c) for c in ramp]
    n = len(cols) - 1
    for y in range(h):
        for x in range(w):
            d = x * ca + y * sa
            t = (d - lo) / (hi - lo)
            if flip:
                t = 1.0 - t
            stripe = 0.42 if int((d - lo) // period) % 2 else 0.0
            i = max(0, min(n, int(round(t * n + stripe - 0.21))))
            p[x, y] = cols[i]
    return im


def mask_from_poly(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([tuple(q) for q in pts], fill=255)
    return m


def drop_halo(layer, bust, xy, off=(3, 3), color="#0B0A12", spread=1):
    """A dark offset silhouette behind a bust, so a white knight still separates
    from a white block."""
    sil = Image.new("RGBA", bust.size, (0, 0, 0, 0))
    sil.paste(hx(color), (0, 0), bust.split()[3])
    for dx in range(-spread, spread + 1):
        for dy in range(-spread, spread + 1):
            layer.alpha_composite(sil, (xy[0] + off[0] + dx, xy[1] + off[1] + dy))


# ------------------------------------------------------------------- text
_fc = {}


def font(sz):
    if sz not in _fc:
        _fc[sz] = ImageFont.truetype(FONT, sz)
    return _fc[sz]


def _mask(text, f):
    box = f.getbbox(text)
    pad = 4
    m = Image.new("L", (box[2] - box[0] + pad * 2, box[3] - box[1] + pad * 2), 0)
    ImageDraw.Draw(m).text((pad - box[0], pad - box[1]), text, font=f, fill=255)
    return m.point(lambda v: 255 if v > 40 else 0), (box[0] - pad, box[1] - pad)


def text_block(text, sz, fill="#FFFFFF", ol=INK, ol_w=None, sh=None, sh_col="#0B0A12"):
    """Thick letters, heavy dark outline, hard drop shadow - the reference's VS
    and name treatment. Returns an RGBA image and the offset to subtract.

    ol_w and the shadow scale with the size: a fixed 6px dilation floods the
    counters of a 33px glyph, which turned BOSS into GOSS in the first pass."""
    if ol_w is None:
        # A 2px dilation closes the counters of a 33px glyph, and since the
        # outline is the same black the counter reads as filled - that is what
        # turned BOSS into GOSS. Keep the outline under ~1/30 of the size.
        ol_w = max(1, round(sz / 30))
    if sh is None:
        sh = (0, max(3, round(sz / 16)))
    f = font(sz)
    m, off = _mask(text, f)
    pad = ol_w + max(abs(sh[0]), abs(sh[1])) + 2
    W, H = m.width + pad * 2, m.height + pad * 2
    big = Image.new("L", (W, H), 0)
    big.paste(m, (pad, pad))
    grown = big.filter(ImageFilter.MaxFilter(ol_w * 2 + 1)) if ol_w else big
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if sh != (0, 0):
        out.paste(hx(sh_col), (sh[0], sh[1]), grown)
    out.paste(hx(ol), (0, 0), grown)
    out.paste(hx(fill), (0, 0), big)
    return out, (off[0] - pad, off[1] - pad)


def put_text(img, xy, text, sz, anchor="lt", **kw):
    blk, off = text_block(text, sz, **kw)
    x, y = xy
    bb = blk.split()[3].getbbox()
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    if anchor[0] == "c":
        x -= w // 2
    elif anchor[0] == "r":
        x -= w
    if anchor[1] == "c":
        y -= h // 2
    elif anchor[1] == "b":
        y -= h
    img.alpha_composite(blk, (x - bb[0], y - bb[1]))
    return w, h


# --------------------------------------------------------------- the band
def build_band(w, h, split_top, split_bot, burak, eric, bx, ex, by, ey,
               ramp_a=BURAK_RAMP, ramp_b=ERIC_RAMP, cross_wm=True):
    """One Elite-Four-style banner: two banded colour blocks meeting on a
    diagonal, busts facing each other across it."""
    band = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    left_pts = [(0, 0), (split_top, 0), (split_bot, h), (0, h)]
    right_pts = [(split_top, 0), (w, 0), (w, h), (split_bot, h)]

    band.paste(banded(w, h, ramp_a, -58, 9), (0, 0), mask_from_poly((w, h), left_pts))
    band.paste(banded(w, h, ramp_b, -58, 11, flip=True), (0, 0), mask_from_poly((w, h), right_pts))

    # Eric's ghosted red cross watermark, low contrast, inside his block only.
    # Thin arms relative to their length, or it reads as a pink rectangle.
    if cross_wm:
        wm = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        cx, cy, arm, thick = int(w * 0.80), h // 2, int(h * 0.40), int(h * 0.105)
        poly(wm, [(cx - thick, cy - arm), (cx + thick, cy - arm), (cx + thick, cy - thick),
                  (cx + arm, cy - thick), (cx + arm, cy + thick), (cx + thick, cy + thick),
                  (cx + thick, cy + arm), (cx - thick, cy + arm), (cx - thick, cy + thick),
                  (cx - arm, cy + thick), (cx - arm, cy - thick), (cx - thick, cy - thick)], CROSS)
        wm.putalpha(wm.split()[3].point(lambda v: 52 if v else 0))
        band.alpha_composite(Image.composite(wm, Image.new("RGBA", (w, h)), mask_from_poly((w, h), right_pts)))

    # the split itself: black seam, gold inner rule, and a parallel speed stripe
    d = ImageDraw.Draw(band)
    dx = split_bot - split_top
    d.line([(split_top, 0), (split_bot, h)], fill=hx(INK), width=5)
    d.line([(split_top + 4, 0), (split_bot + 4, h)], fill=hx(GOLD), width=2)
    d.line([(split_top + 6, 0), (split_bot + 6, h)], fill=hx(GOLD_HI), width=1)
    d.line([(split_top + 22, 0), (split_bot + 22, h)], fill=hx("#EAF0F6"), width=1)
    d.line([(split_top - 13, 0), (split_bot - 13, h)], fill=hx("#3A5BA8"), width=2)

    drop_halo(band, burak, (bx, by))
    drop_halo(band, eric, (ex, ey))
    band.alpha_composite(burak, (bx, by))
    band.alpha_composite(eric, (ex, ey))

    # top and bottom rules
    d = ImageDraw.Draw(band)
    d.rectangle([0, 0, w - 1, 2], fill=hx(INK))
    d.rectangle([0, h - 3, w - 1, h - 1], fill=hx(INK))
    d.line([(0, 3), (w - 1, 3)], fill=hx("#4A4A82"))
    d.line([(0, h - 4), (w - 1, h - 4)], fill=hx("#0B0A12"))
    return band


def up(img, f=SCALE):
    return img.resize((img.width * f, img.height * f), Image.NEAREST)


# ------------------------------------------------- the band, as two halves
def band_halves(w, h, split_top, split_bot, burak, eric, bx, by, ex, ey,
                ramp_b, accent, mark, ramp_a=BURAK_RAMP, stripe="#3A5BA8"):
    """The shipped form of the band: two independent images that slide apart.

    The seam furniture (black rule + accent hairlines) lives entirely in the
    RIGHT half and is drawn after masking, so it overhangs 2px to the left. That
    gives the right half a finished edge while it is still flying in, and the
    overhang is hidden under the left half once they meet."""
    left_pts = [(0, 0), (split_top, 0), (split_bot, h), (0, h)]
    right_pts = [(split_top, 0), (w, 0), (w, h), (split_bot, h)]
    lm, rm = mask_from_poly((w, h), left_pts), mask_from_poly((w, h), right_pts)

    def rules(mask):
        """Top and bottom rules, clipped to one half. Composited LAST so the
        busts crop against them instead of spilling over them."""
        r = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(r)
        d.rectangle([0, 0, w - 1, 2], fill=hx(INK))
        d.rectangle([0, h - 3, w - 1, h - 1], fill=hx(INK))
        d.line([(0, 3), (w - 1, 3)], fill=hx("#4A4A82"))
        d.line([(0, h - 4), (w - 1, h - 4)], fill=hx("#0B0A12"))
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        out.paste(r, (0, 0), mask)
        return out

    # ---- left: Burak's dark block, shared by every card --------------------
    lc = banded(w, h, ramp_a, -58, 9)
    ImageDraw.Draw(lc).line([(split_top - 13, 0), (split_bot - 13, h)], fill=hx(stripe), width=2)
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    L.paste(lc, (0, 0), lm)
    drop_halo(L, burak, (bx, by))
    L.alpha_composite(burak, (bx, by))
    L.alpha_composite(rules(lm))

    # ---- right: the boss's block -------------------------------------------
    rc = banded(w, h, ramp_b, -58, 11, flip=True)
    shape, mc, ma = mark
    wm = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for pts in emblems.emblem(shape, w, h):
        poly(wm, pts, mc)
    wm.putalpha(wm.split()[3].point(lambda v: ma if v else 0))
    rc.alpha_composite(wm)
    R = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    R.paste(rc, (0, 0), rm)
    d = ImageDraw.Draw(R)
    d.line([(split_top, 0), (split_bot, h)], fill=hx(INK), width=5)
    d.line([(split_top + 4, 0), (split_bot + 4, h)], fill=hx(accent[0]), width=2)
    d.line([(split_top + 6, 0), (split_bot + 6, h)], fill=hx(accent[1]), width=1)
    d.line([(split_top + 22, 0), (split_bot + 22, h)], fill=hx("#EAF0F6"), width=1)
    drop_halo(R, eric, (ex, ey))
    R.alpha_composite(eric, (ex, ey))
    # the seam overhangs 2px left of the polygon, so the rules mask has to cover
    # that overhang too or the band's edges break at the split
    rmask = mask_from_poly((w, h), [(split_top - 3, 0), (w, 0), (w, h), (split_bot - 3, h)])
    R.alpha_composite(rules(rmask))
    return L, R
