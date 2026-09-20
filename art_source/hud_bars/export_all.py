"""Write every HUD bar asset to Assets/UI/ as native + _3x.

  python export_all.py [out_dir]

Multi-frame assets ship as horizontal strips (hframes=N, vframes=1), the
project's convention. Output is deterministic - no randomness, no timestamps -
so two clean runs are byte-identical, and aseprite_roundtrip.py then writes the
.aseprite beside each PNG.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image
from barlib import up3, canvas
import boss_bar as BB
import player_hp as PH
import plates as PL
from vs_card import bosses

OUT_DEFAULT = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI"
WRITTEN = []


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
    WRITTEN.append((name, im.size, len(WRITTEN)))


def run(out):
    os.makedirs(out, exist_ok=True)
    keys = [b["key"] for b in bosses.BOSSES]

    # ---- boss bar frame ---------------------------------------------------
    put(out, "boss_hp_frame_back", BB.frame_back())
    put(out, "boss_hp_frame_over", BB.frame_over())
    put(out, "boss_hp_frame_over_low", BB.frame_over_low())

    # ---- per-boss fills + emblems + name plates --------------------------
    for k in keys:
        b = bosses.by_key(k)
        put(out, "boss_hp_fill_%s" % k, BB.fill(b["ramp"], b["mark"][1]))
        put(out, "boss_hp_fill_hot_%s" % k, BB.fill_hot(b["ramp"], b["accent"][1], b["mark"][1]))
        put(out, "boss_hp_emblem_%s" % k, PL.emblem(k))
        lines = PL.plate_lines(k)
        if len(lines) == 1:
            im, _ = PL.name_art(lines[0])
            put(out, "boss_plate_name_%s" % k, im)
        else:
            for i, line in enumerate(lines):
                im, _ = PL.name_art(line)
                put(out, "boss_plate_name_%s_%s" % (k, "ab"[i]), im)

    # ---- shared bar FX ----------------------------------------------------
    put(out, "boss_hp_chip", BB.chip())
    put(out, "boss_hp_low", strip(BB.low_pulse()))
    put(out, "boss_hp_flash", BB.flash())
    put(out, "boss_hp_flash_punish", BB.flash_punish())
    put(out, "boss_hp_spark", strip(BB.spark()))
    put(out, "boss_hp_sweep", strip(BB.sweep()))
    put(out, "boss_hp_ghost", BB.ghost())
    put(out, "boss_plate", PL.plate(False))
    put(out, "boss_plate_tall", PL.plate(True))

    # ---- player health ----------------------------------------------------
    put(out, "player_hp_tray", PH.tray(0))
    put(out, "player_hp_tray_warn", strip([PH.tray(1), PH.tray(2)]))
    put(out, "player_hp_heart_full", PH.heart_full())
    put(out, "player_hp_heart_half", PH.heart_half())
    put(out, "player_hp_heart_empty", PH.heart_empty())
    put(out, "player_hp_heart_break", strip(PH.heart_break()))
    put(out, "player_hp_heart_gain", strip(PH.heart_gain()))
    put(out, "player_hp_heart_low", strip(PH.heart_low()))


SCRATCH = ("C:/Users/theyi/AppData/Local/Temp/claude/"
           "C--Users-theyi-OneDrive-Documents-new-game-project/"
           "a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/hud_bars/_rt")
ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"


def roundtrip(out):
    """Save a .aseprite beside each PNG we wrote and verify it round-trips.

    Targeted at our own filenames only - Assets/UI holds ~100 other PNGs and
    sweeping the whole directory would rewrite .aseprite files we do not own.
    Uses a fixed scratch dir rather than tempfile: Aseprite would not write into
    the per-call temp directories and the failure surfaced as a missing file
    several assets later, with nothing saying which one."""
    import subprocess
    from imgdiff import pixel_diff
    os.makedirs(SCRATCH, exist_ok=True)
    back = os.path.join(SCRATCH, "back.png")
    names = []
    for name, _, _ in WRITTEN:
        names += [name, name + "_3x"]
    bad = 0
    for n in names:
        png = os.path.join(out, n + ".png")
        ase = os.path.join(out, n + ".aseprite")
        r1 = subprocess.run([ASE, "-b", png, "--save-as", ase], capture_output=True, text=True)
        if os.path.exists(back):
            os.remove(back)
        r2 = subprocess.run([ASE, "-b", ase, "--save-as", back], capture_output=True, text=True)
        if r1.returncode or r2.returncode or not os.path.exists(back):
            bad += 1
            print("   %-32s aseprite failed rc=%s/%s %s" % (n, r1.returncode, r2.returncode,
                                                            (r1.stderr or r2.stderr or "").strip()[:80]))
            continue
        a_im = Image.open(png).convert("RGBA")
        b_im = Image.open(back).convert("RGBA")
        why = pixel_diff(a_im, b_im)
        if why:
            bad += 1
            print("   %-32s %s" % (n, why))
    print("round-trip: %d files, %d mismatches" % (len(names), bad))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if args else OUT_DEFAULT
    run(out)
    if "--ase" in sys.argv:
        roundtrip(out)
    print("%d assets (x2 with _3x = %d PNGs) -> %s" % (len(WRITTEN), len(WRITTEN) * 2, out))
    for name, size, _ in WRITTEN:
        print("   %-28s %dx%d" % (name, size[0], size[1]))
