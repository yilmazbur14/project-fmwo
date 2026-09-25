"""Write the approved GOTHIC boss bar + daze meter set to Assets/UI.

  python export_gothic.py <scratch_dir> [--only KEY[,KEY]] [--ase]      build, never ships
  python export_gothic.py --ship --only KEY[,KEY] [--replace] [--ase]   ship bosses to Assets/UI

SHIPPING IS GUARDED (2026-09-23).  This used to write the WHOLE set straight into
Assets/UI when run bare, and a re-run is not harmless: stamina() and daze_fx()
read the SHIPPED PNGs and remap them, and STAMINA_FILL_MAP is not idempotent -
its gold -> white glint rule would turn the already-gold stamina fill white on a
second pass.  So now:
  - a folder under Assets is refused unless --ship is given;
  - --ship needs --only, which writes just those bosses' own pieces (fill, hot
    fill, emblem, name plate) and nothing shared;
  - --ship refuses to overwrite an existing file unless --replace is given, and
    checks every target before writing any, so a refusal leaves nothing behind.
A full run into a scratch folder still works exactly as before.

Same names, same sizes, same frame counts as the brass set it replaces, so no
code edits are needed - a coder flips USE_FINAL_BOSS_BAR and it is live.

THREE FAMILIES, THREE TREATMENTS
1. Chrome (frame, crest, plate, daze rail) is redrawn in gothic.py from the
   measured reference palette.
2. FX (chip, low_pulse, flash, flash_punish, spark, sweep, ghost) and the daze
   meter's pulse / shatter / fill_hot are the EXISTING generators' output put
   through an explicit colour remap.  They are shape-correct already and their
   timing is tuned; only their tones belonged to the brass kit.  A remap keeps
   every pixel of shape and every frame boundary exactly.
3. Per-boss fills are rebuilt rather than remapped, because their shape carried
   brass in it: ramp_fill() laid faint sheen bands on the 19px notch pitch to
   echo the brass notches.  The gothic dividers are black and drawn over the
   fill, so those bands now fight them.  The gothic fill is the reference's own
   shape - one lit top line, a flat body, a two-row underside shifted toward
   plum so the fill seats into the charcoal channel - with the boss's OWN ramp
   supplying the hue, so per-boss identity is untouched.

PALETTE NOTE.  break_gauge.py asserts DB32 compliance on its own output.  The
approved gothic palette is not DB32 (it is sampled from the direction
reference), so the daze meter leaves DB32 along with the boss bar.  That is a
consequence of the approved direction, not an accident - flagging it because
the assert in break_gauge.py's __main__ will now fail if anyone runs it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image
from barlib import up3, canvas, rect, hline, rgba, WIN_W, WIN_H
import boss_bar as BB
import gothic as G
import gothicfont as GF
import plates as PL
from vs_card import bosses

OUT_DEFAULT = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI"
WRITTEN = []

# ---- the remap, keyed on the exact tones the brass generators emit ---------
# Left column is every colour found in the brass FX set plus the break gauge's
# own; right column is its gothic counterpart.  Gold becomes bone because the
# gothic kit has no gold at all, and the brass kit's cyan accent becomes a lit
# plum for the same reason.
MAP = {
    (0, 0, 0): (0, 0, 0),                 # keyline, unchanged
    (110, 31, 34): (73, 49, 56),          # HOT_DK   -> CRIMSON_DK
    (172, 50, 50): (173, 42, 60),         # HOT      -> CRIMSON
    (217, 87, 99): (200, 68, 83),         # HOT_LT   -> lit crimson
    (251, 242, 54): (237, 228, 214),      # BRASS_HI gold -> BONE
    (255, 255, 255): (255, 255, 255),     # flash white, unchanged
    (237, 228, 214): (237, 228, 214),     # BONE, unchanged
    (199, 187, 171): (169, 160, 180),     # BONE_DK  -> plum-tinted bone
    (154, 143, 128): (110, 104, 128),     # warm grey -> cool grey
    (95, 205, 228): (126, 111, 168),      # CYAN     -> lit plum
    (203, 219, 252): (196, 184, 216),     # CYAN_LT  -> pale plum
    (138, 111, 48): (64, 48, 88),         # BRASS    -> PLUM
    (217, 160, 102): (76, 63, 97),        # BRASS_LT -> PLUM_LT
    (82, 75, 36): (46, 35, 61),           # BRASS_DK -> PLUM_DK
    (34, 32, 52): (49, 60, 64),           # WELL     -> gothic WELL
    (63, 63, 116): (46, 35, 61),          # WELL_RIM -> PLUM_DK
    (238, 195, 154): (169, 160, 180),     # stray brass accent
    # Found by listing every colour in the shipped daze assets that the table
    # did NOT hit, rather than assuming the table was complete: the shatter and
    # fill_hot carry 300+ px of ember orange and a cold steel grey.
    (223, 113, 38): (173, 42, 60),        # ember orange -> CRIMSON
    (155, 173, 183): (110, 104, 128),     # cold steel   -> cool grey
    (69, 40, 60): (46, 35, 61),           # plum-brown   -> PLUM_DK
    (143, 86, 59): (73, 49, 56),          # brown        -> CRIMSON_DK
}


def remap(im, extra=None, base=True):
    """Recolour in place.  Alpha is preserved exactly, so soft FX keep their
    falloff, and any colour not in the table passes through untouched."""
    table = dict(MAP) if base else {}
    if extra:
        table.update(extra)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            t = table.get((r, g, b))
            if t:
                px[x, y] = (t[0], t[1], t[2], a)
    return im


def _rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _mix(a, b, t):
    a, b = _rgb(a), _rgb(b)
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---- per-boss fills, rebuilt in the reference's shape ---------------------
def gothic_fill(ramp, mark=None, accent=None, as_is=False, trim=None):
    # as_is: a bosses.py row with fill_as_is=True already carries a fill ramp, measured
    # off its sprite, and bar_ramp()'s boost would push it somewhere the boss is not
    # (Matt's lavender lands on Jordan's royal blue).  Every other row takes the boost.
    # trim: a bosses.py fill_trim colour replaces the lit top line on the fill AND the
    # hot fill - the edging of a costume (Captain Burak's gold-trimmed coat).  Trim is
    # metal, so it does not heat; the hot fill still gets its bone lip beneath it.
    r = list(ramp) if as_is else BB.bar_ramp(ramp, mark)   # the boss's own hue, unchanged
    im = canvas(WIN_W, WIN_H)
    body = r[2] if accent is None else _mix(r[2], accent, 0.45)
    lit = r[3] if accent is None else _mix(r[3], accent, 0.55)
    if trim is not None:
        lit = trim
    seat = _mix(r[0], G.PLUM_DK, 0.5)
    rect(im, 0, 0, WIN_W - 1, WIN_H - 1, body)
    hline(im, 0, WIN_W - 1, 0, lit)
    hline(im, 0, WIN_W - 1, WIN_H - 2, seat)
    hline(im, 0, WIN_W - 1, WIN_H - 1, seat)
    if accent is not None:
        hline(im, 0, WIN_W - 1, 1, G.BONE)      # the hot fill's bright lip
    return im


def strip(frames):
    w = sum(f.width for f in frames)
    h = max(f.height for f in frames)
    im = canvas(w, h)
    x = 0
    for f in frames:
        im.alpha_composite(f, (x, 0))
        x += f.width
    return im


def put(out, name, im):
    im.save(os.path.join(out, name + ".png"), optimize=False)
    up3(im).save(os.path.join(out, name + "_3x.png"), optimize=False)
    WRITTEN.append((name, im.size))


# ---- the stamina fill: a BRASS fix, not a gothic one ----------------------
# The player's gauge stays in the player's language.  Cold and ornate for the
# threat, warm and mechanical for the player, with the arena's purple-and-gold
# ringside sitting between them - moving this to the threat's language would
# collapse that split.  Only the FILL COLOUR was arbitrary: the frame, the tray
# and the hype meter already speak brass (#8A6F30 / #D9A066 / #FBF236 / #524B24,
# measured identical across all three).  The green ramp belonged to nothing.
# The green ramp -> brass.  The gold->white swap keeps the fill's own glint
# distinct now that its body is gold, so it applies to the FILL ONLY: `low` and
# `broken` are already red/orange/brass and carry no green at all, so they are
# copied through untouched rather than "converted" into something nobody asked
# for.  Every state and size is preserved either way.
STAMINA_FILL_MAP = {
    (251, 242, 54): (255, 255, 255),      # old gold glint -> white, so it still reads
    (153, 229, 80): (251, 242, 54),       # light green -> gold body
    (106, 190, 48): (217, 160, 102),      # mid green   -> tan
    (55, 148, 110): (138, 111, 48),       # dark green  -> brass underside
}


def stamina(out):
    for n in ("stamina_bar_fill", "stamina_bar_low", "stamina_bar_broken"):
        p = os.path.join(OUT_DEFAULT, n + ".png")
        if not os.path.exists(p):
            print("   missing %s" % n)
            continue
        im = Image.open(p).convert("RGBA")
        if n == "stamina_bar_fill":
            im = remap(im, STAMINA_FILL_MAP, base=False)
        put(out, n, im)


def boss_pieces(k):
    """One boss's own pieces, as (name, image) in write order: fill, hot fill,
    emblem, then the baked name plate (one line, or a pair's two lines plus the
    stacked pair).  Nothing here is shared with another boss, which is what lets
    --only ship a single boss without touching anyone else's files."""
    b = bosses.by_key(k)
    as_is, trim = b.get("fill_as_is", False), b.get("fill_trim")
    out = [("boss_hp_fill_%s" % k, gothic_fill(b["ramp"], b["mark"][1], as_is=as_is, trim=trim)),
           ("boss_hp_fill_hot_%s" % k,
            gothic_fill(b["ramp"], b["mark"][1], accent=b["accent"][1], as_is=as_is, trim=trim)),
           ("boss_hp_emblem_%s" % k, PL.emblem(k))]
    lines = PL.plate_lines(k)
    if len(lines) == 1:
        out.append(("boss_plate_name_%s" % k,
                    GF.render(lines[0], fill=rgba(G.BONE_HI), ink=rgba(G.INK))))
    else:
        baked = [GF.render(ln, fill=rgba(G.BONE_HI), ink=rgba(G.INK)) for ln in lines]
        for i, im in enumerate(baked):
            out.append(("boss_plate_name_%s_%s" % (k, "ab"[i]), im))
        # BossBarArtLayout.gd loads "boss_plate_name_<key>_pair_3x.png" for
        # the two pair fights, and NOTHING has ever written that name - the
        # old exporter wrote _a / _b only, so flipping USE_FINAL_BOSS_BAR
        # would have failed two texture loads.  Emit the stacked pair here,
        # which the condensed face makes trivial: both lines are one size.
        lead = 1
        pw = max(im.width for im in baked)
        ph = sum(im.height for im in baked) + lead * (len(baked) - 1)
        pair = canvas(pw, ph)
        y = 0
        for im in baked:
            pair.alpha_composite(im, ((pw - im.width) // 2, y))
            y += im.height + lead
        out.append(("boss_plate_name_%s_pair" % k, pair))
    return out


def run(out, do_stamina=True):
    os.makedirs(out, exist_ok=True)
    keys = [b["key"] for b in bosses.BOSSES]

    # ---- chrome -----------------------------------------------------------
    put(out, "boss_hp_frame_back", G.frame_back())
    put(out, "boss_hp_frame_over", G.frame_over())
    put(out, "boss_hp_frame_over_low", G.frame_over_low())
    put(out, "boss_hp_crest", G.crest())          # NEW asset - see gothic.py
    put(out, "boss_hp_crest_low", G.crest(True))
    put(out, "boss_plate", G.plate(False))
    put(out, "boss_plate_tall", G.plate(True))

    # ---- per-boss fills, emblems, names -----------------------------------
    for k in keys:
        for name, im in boss_pieces(k):
            put(out, name, im)

    # ---- FX: existing shapes, gothic tones --------------------------------
    put(out, "boss_hp_chip", remap(BB.chip()))
    put(out, "boss_hp_low", remap(strip(BB.low_pulse())))
    put(out, "boss_hp_flash", remap(BB.flash()))
    put(out, "boss_hp_flash_punish", remap(BB.flash_punish()))
    put(out, "boss_hp_spark", remap(strip(BB.spark())))
    put(out, "boss_hp_sweep", remap(strip(BB.sweep())))
    put(out, "boss_hp_ghost", remap(BB.ghost()))

    # ---- daze meter -------------------------------------------------------
    put(out, "break_gauge_frame", G.gauge_frame())
    put(out, "break_gauge_fill", G.gauge_fill())
    daze_fx(out)

    if do_stamina:
        stamina(out)


def daze_fx(out):
    """pulse / fill_hot / shatter keep their exact shapes, frame counts and
    timing - only their tones move.

    These are remapped from the SHIPPED PNGs rather than re-run through
    break_gauge.py.  Its frames are ev2_common Canvas objects on a character
    palette, and re-deriving them would risk a different frame count or a
    shifted sub-frame boundary for no gain: BreakGaugeUI reads these by fixed
    offsets.  Remapping the shipped bytes cannot move a single pixel."""
    for name in ("break_gauge_pulse", "break_gauge_fill_hot", "break_gauge_shatter"):
        p = os.path.join(OUT_DEFAULT, name + ".png")
        if not os.path.exists(p):
            print("   missing %s" % name)
            continue
        put(out, name, remap(Image.open(p).convert("RGBA")))


SCRATCH = ("C:/Users/theyi/AppData/Local/Temp/claude/"
           "C--Users-theyi-OneDrive-Documents-new-game-project/"
           "a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/hud_bars/_rt")
ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"


def roundtrip(out):
    import subprocess
    from imgdiff import pixel_diff
    os.makedirs(SCRATCH, exist_ok=True)
    back = os.path.join(SCRATCH, "back.png")
    bad = 0
    names = []
    for name, _ in WRITTEN:
        names += [name, name + "_3x"]
    for n in names:
        png = os.path.join(out, n + ".png")
        ase = os.path.join(out, n + ".aseprite")
        r1 = subprocess.run([ASE, "-b", png, "--save-as", ase], capture_output=True, text=True)
        if os.path.exists(back):
            os.remove(back)
        r2 = subprocess.run([ASE, "-b", ase, "--save-as", back], capture_output=True, text=True)
        if r1.returncode or r2.returncode or not os.path.exists(back):
            bad += 1
            print("   %-34s aseprite rc=%s/%s" % (n, r1.returncode, r2.returncode))
            continue
        a = Image.open(png).convert("RGBA")
        b = Image.open(back).convert("RGBA")
        why = pixel_diff(a, b)
        if why:
            bad += 1
            print("   %-34s %s" % (n, why))
    print("round-trip: %d files, %d mismatches" % (len(names), bad))
    return bad


ASSETS = os.path.dirname(OUT_DEFAULT)       # the project's Assets/, which only --ship may write


def _under(path, root):
    # realpath, not abspath: 8.3 short names are on for this drive, and an abspath test let
    # "...\DOCUME~1\NEW-GA~1\Assets\UI" through as a scratch folder (proven 2026-09-24 under
    # an audit-hook write net, which stopped it at its first mkdir).
    p = os.path.normcase(os.path.realpath(path))
    r = os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Gothic boss bar set (see the module docstring).")
    ap.add_argument("out", nargs="?", help="scratch folder to build into (never under Assets)")
    ap.add_argument("--only", help="comma-separated boss keys: only their fill, hot fill, emblem, name")
    ap.add_argument("--ship", action="store_true", help="write into Assets/UI; needs --only")
    ap.add_argument("--replace", action="store_true", help="with --ship, allow overwriting files")
    ap.add_argument("--ase", action="store_true", help="write + round-trip a .aseprite beside each PNG")
    ap.add_argument("--no-stamina", action="store_true")
    a = ap.parse_args()
    only = [k.strip() for k in a.only.split(",") if k.strip()] if a.only else None
    if only:
        known = [b["key"] for b in bosses.BOSSES]
        unknown = [k for k in only if k not in known]
        if unknown:
            raise SystemExit("unknown boss key(s) %s - bosses.py has %s" % (unknown, known))
    if a.ship:
        if a.out:
            raise SystemExit("--ship always writes %s; drop the folder argument" % OUT_DEFAULT)
        if not only:
            raise SystemExit("--ship needs --only KEY: a full re-run over Assets/UI is not idempotent "
                             "(stamina() re-remaps the shipped fill and would turn its gold white)")
        out = OUT_DEFAULT
    else:
        if not a.out:
            raise SystemExit("give a scratch folder to build into, or --ship --only KEY to ship")
        if _under(a.out, ASSETS):
            raise SystemExit("refusing to write under %s without --ship" % ASSETS)
        out = a.out
    if only:
        jobs = [(n, im) for k in only for n, im in boss_pieces(k)]
        if a.ship:
            # Every target is checked before any is written, so a refusal leaves nothing behind.
            stems = [s for n, _ in jobs for s in (n, n + "_3x")]
            targets = [s + ".png" for s in stems] + ([s + ".aseprite" for s in stems] if a.ase else [])
            clash = [t for t in targets if os.path.exists(os.path.join(out, t))]
            if clash and not a.replace:
                raise SystemExit("refusing to overwrite %d existing file(s) without --replace: %s"
                                 % (len(clash), ", ".join(clash)))
        os.makedirs(out, exist_ok=True)
        for n, im in jobs:
            put(out, n, im)
    else:
        run(out, do_stamina=not a.no_stamina)
    bad = roundtrip(out) if a.ase else 0
    print("%d assets (x2 with _3x = %d PNGs) -> %s" % (len(WRITTEN), len(WRITTEN) * 2, out))
    for name, size in WRITTEN:
        print("   %-30s %dx%d" % (name, size[0], size[1]))
    sys.exit(1 if bad else 0)
