"""Computah armless: the defeated pose without the cannon, its loop, the wrench, and
the loose arm Greyson wears.  The frames themselves live in armless.py.

  python armless_build.py                 render, prove, report.  WRITES NOTHING.
  python armless_build.py --preview DIR   also writes a 4x sheet and a game-scale
                                          mock on the real arena mat into DIR (and
                                          only DIR).
  python armless_build.py --ship          writes each sheet's PNG + .aseprite into
                                          this folder (the working copy rtcheck.py,
                                          checks.py and regress.py read) AND into
                                          Assets/Characters/Computah, re-exports every
                                          .aseprite and pixel-diffs it against its
                                          PNG, and pins golden/ on the first ship.

Without --ship this script has no path into Assets at all: art_source exporters that
default to the live folder have clobbered shipped art before.  --ship refuses to write
unless every proof below passes, and refuses to replace an existing golden that
differs unless --replace is also given.
"""
import math
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import armless as A                                              # noqa: E402
from imgdiff import pixel_diff                                   # noqa: E402
from PIL import Image, ImageDraw                                 # noqa: E402

M = A.M
ASSETS = os.path.realpath(os.path.join(HERE, "..", "..", "Assets", "Characters",
                                       "Computah"))
GOLDEN = os.path.join(HERE, "golden")
GREYSON_RIG = os.path.realpath(os.path.join(HERE, "..", "greyson_fight"))
ASEPRITE = os.environ.get(
    "ASEPRITE", r"C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe")
KEYLINE = (0x0C, 0x11, 0x1A)
GOLDEN_NAMES = {"computah_armless": "armless.png", "computah_wrench": "wrench.png",
                "computah_arm_prop": "arm_prop.png"}


# ---------------------------------------------------------------------------
# the proofs
# ---------------------------------------------------------------------------
def prove_body():
    """The armless body IS computah_defeat's last frame's body: rendered through
    that frame's own code path with the cannon stubbed out, and through ours, with
    no wound, they must match pixel for pixel."""
    keep = M._cannon
    try:
        M._cannon = lambda *a, **k: (0, 0)
        theirs = M.Canvas(96, 96, M.PAL, M.OUTLINE)
        M._floor(theirs, M.CHARGE["dead"], dy=0.0, eyes="dead", smoke=False)
    finally:
        M._cannon = keep
    ours = M.Canvas(96, 96, M.PAL, M.OUTLINE)
    A.body_on_mat(ours, M.CHARGE["dead"])
    M._finish(ours)
    return pixel_diff(theirs.to_image(), ours.to_image())


def prove_source():
    """...and that frame is the one actually shipped."""
    shipped = Image.open(os.path.join(ASSETS, "computah_defeat.png"))
    return pixel_diff(shipped.crop((384, 0, 480, 96)), M.build_defeat(4).to_image())


def prove_handoff():
    """The hauled arm and the prop's first frame are the same arm: same length, same
    angle, so on the tear one replaces the other without a pop."""
    (s0, m0), (s1, m1, _u) = A.WRENCH_GUN, A.prop_rig("torn")
    l0, l1 = math.hypot(m0[0] - s0[0], m0[1] - s0[1]), math.hypot(m1[0] - s1[0],
                                                                   m1[1] - s1[1])
    a0 = math.degrees(math.atan2(m0[1] - s0[1], m0[0] - s0[0]))
    a1 = math.degrees(math.atan2(m1[1] - s1[1], m1[0] - s1[0]))
    ok = abs(l0 - l1) <= 0.2 and abs(a0 - a1) <= 0.5
    return ok, "haul %.1f long at %.1f deg, prop 'torn' %.1f at %.1f" % (l0, a0, l1, a1)


def prove_worn():
    """The prop is still the cannon Greyson wears.  Re-samples his LIVE profile at
    the points PROFILE_WORN was frozen from; if his rig changes the cannon, this
    fails and the prop has to be re-matched before it can ship again."""
    if not os.path.isdir(GREYSON_RIG):
        return False, "art_source/greyson_fight is missing - cannot check the worn match"
    sys.path.insert(0, GREYSON_RIG)
    try:
        import inspect
        import gf_cannon as G
    except Exception as e:                                        # noqa: BLE001
        return False, "could not import gf_cannon read-only: %r" % (e,)
    d = {k: v.default for k, v in inspect.signature(G.cannon).parameters.items()
         if v.default is not inspect.Parameter.empty}
    r_col, r_bar, r_muz = d["r_col"], d["r_bar"], d["r_muz"]
    L = A.PROP_LEN
    c1, m1 = 0.30 * L, L - 0.20 * L
    worst = 0.0
    for t, k in A.PROFILE_WORN:
        live = G._profile(min(t * L, L), L, r_col, r_bar, r_muz, c1, m1) / r_col
        worst = max(worst, abs(live - k))
    ok = abs(r_col - A.PROP_R) < 1e-6 and worst <= 0.01
    return ok, ("his r_col %.1f / r_bar %.1f / r_muz %.1f, ours r %.1f; worst profile "
                "gap %.3f" % (r_col, r_bar, r_muz, A.PROP_R, worst))


def prove_grip():
    """Greyson's tear sheet is drawn to the prop's grip, so it cannot move."""
    bad = [n for n, p in A.prop_points().items() if p["grip"] != A.GRIP]
    return not bad, ("grip (%g, %g) on every frame" % A.GRIP if not bad
                     else "grip moved on %s" % bad)


def geometric_floor():
    """The keyline share the armless frame cannot go below: defeat's last frame with
    the cannon deleted and nothing added.  Taking the arm's big purple mass away
    raises the outline's share on its own, so this - not the source's 21-23% - is
    the honest target for a frame with no arm."""
    keep = M._cannon
    try:
        M._cannon = lambda *a, **k: (0, 0)
        c = M.Canvas(96, 96, M.PAL, M.OUTLINE)
        M._floor(c, M.CHARGE["dead"], dy=0.0, eyes="dead", smoke=True)
    finally:
        M._cannon = keep
    return keyline(c.to_image())


def keyline(im):
    px = [p for p in im.convert("RGBA").get_flattened_data() if p[3] > 128]
    return 100.0 * sum(1 for p in px if p[:3] == KEYLINE) / len(px)


def lint(images):
    """Per frame: no pure black, colours inside the cast's band, nothing touching the
    frame edge, and the keyline where the geometry puts it."""
    fatal = []
    floor = geometric_floor()
    for name, sheet in images.items():
        _fn, n, size = A.SHEETS[name]
        for f in range(n):
            im = sheet.crop((f * size, 0, (f + 1) * size, size)).convert("RGBA")
            px = [p for p in im.get_flattened_data() if p[3] > 128]
            black = sum(1 for p in px if p[:3] == (0, 0, 0))
            colours = len({p[:3] for p in px})
            k = keyline(im)
            b = im.getbbox()
            # A body frame STANDS on its last row (feet on row 95 is the contract), so
            # its bottom edge is the floor line, not a clip.  The loose arm floats, so
            # it must clear all four edges.
            floor_ok = size == M.FRAME
            edge = (b[0] == 0 or b[1] == 0 or b[2] == size
                    or (b[3] == size and not floor_ok))
            if black:
                fatal.append("%s f%d has %d pure black px" % (name, f, black))
            if colours > 32:
                fatal.append("%s f%d has %d colours (cast band tops out at 31)"
                             % (name, f, colours))
            if edge:
                fatal.append("%s f%d touches its frame edge %s" % (name, f, b))
            if name == "computah_armless" and not floor <= k <= floor + 1.5:
                fatal.append("%s f%d keyline %.1f%%, outside %.1f-%.1f (the geometric "
                             "floor plus the wound)" % (name, f, k, floor, floor + 1.5))
            print("  %-18s f%d  keyline %4.1f%%  colours %2d  pure black %d  bbox %s"
                  % (name, f, k, colours, black, b))
    print("  armless keyline floor (defeat's last frame, cannon deleted): %.1f%%" % floor)
    return fatal


# ---------------------------------------------------------------------------
# preview and ship
# ---------------------------------------------------------------------------
def preview(images, out):
    os.makedirs(out, exist_ok=True)
    bg, ink = (26, 26, 34, 255), (200, 206, 220, 255)
    rows = [(n, images[n], A.SHEETS[n][2]) for n in A.SHEETS]
    k, gap, pad, head = 4, 10, 20, 26
    w = max(s.width * k + gap * (s.width // size - 1) for _, s, size in rows) + 2 * pad
    h = sum(head + s.height * k + 14 for _, s, _ in rows) + 2 * pad
    board = Image.new("RGBA", (w, h), bg)
    d = ImageDraw.Draw(board)
    y = pad
    for name, sheet, size in rows:
        d.text((pad, y + 4), name, fill=ink)
        y += head
        for f in range(sheet.width // size):
            tile = sheet.crop((f * size, 0, (f + 1) * size, size))
            board.alpha_composite(tile.resize((size * k, size * k), Image.NEAREST),
                                  (pad + f * (size * k + gap), y))
        y += sheet.height * k + 14
    board.save(os.path.join(out, "computah_armless_set_4x.png"))
    # game scale: the mat and Computah are both drawn at scale 3 (ArenaScene.tscn)
    mat = Image.open(os.path.join(HERE, "..", "..", "Assets", "Environment",
                                  "arena_mat.png")).convert("RGBA")
    tile = mat.crop((150, 70, 330, 200)).copy()
    tile.alpha_composite(images["computah_armless"].crop((0, 0, 96, 96)), (42, 8))
    tile.resize((tile.width * 3, tile.height * 3), Image.NEAREST).save(
        os.path.join(out, "computah_armless_on_mat_3x.png"))
    print("\npreviews written to", out)


def aseprite_roundtrip(png, ase):
    """Save the PNG as an .aseprite with Aseprite itself, re-export that, and
    pixel-diff the re-export against the PNG (imgdiff, never a bare getbbox)."""
    subprocess.run([ASEPRITE, "-b", png, "--save-as", ase], check=True,
                   capture_output=True)
    tmp = os.path.join(tempfile.mkdtemp(), os.path.basename(png))
    subprocess.run([ASEPRITE, "-b", ase, "--save-as", tmp], check=True,
                   capture_output=True)
    return pixel_diff(Image.open(png), Image.open(tmp))


def pin_goldens(images, replace):
    """First ship writes golden/.  After that a golden is only replaced on purpose."""
    problems = []
    for name, file in GOLDEN_NAMES.items():
        path = os.path.join(GOLDEN, file)
        if os.path.exists(path):
            d = pixel_diff(Image.open(path), images[name])
            if d and not replace:
                problems.append("%s differs from golden/%s (%s); pass --replace to "
                                "re-pin it deliberately" % (name, file, d))
    return problems


def ship(images, replace):
    real = os.path.realpath(ASSETS).replace("\\", "/").lower()
    assert real.endswith("assets/characters/computah") and os.path.isdir(ASSETS), \
        "refusing: %s is not the live Computah folder" % ASSETS
    bad = 0
    for name, im in images.items():
        for folder in (HERE, ASSETS):
            png = os.path.join(folder, name + ".png")
            ase = os.path.join(folder, name + ".aseprite")
            im.save(png)
            d = aseprite_roundtrip(png, ase)
            where = "Assets/Characters/Computah" if folder == ASSETS else \
                "art_source/computah_redesign"
            print("shipped %-18s -> %-28s round trip: %s"
                  % (name, where, d or "identical (alpha and colour, every pixel)"))
            bad += d is not None
        d = pixel_diff(Image.open(os.path.join(HERE, name + ".png")),
                       Image.open(os.path.join(ASSETS, name + ".png")))
        print("        %-18s working copy vs live copy: %s" % (name, d or "identical"))
        bad += d is not None
    os.makedirs(GOLDEN, exist_ok=True)
    for name, file in GOLDEN_NAMES.items():
        images[name].save(os.path.join(GOLDEN, file))
    print("golden/ pinned: %s" % ", ".join(GOLDEN_NAMES.values()))
    return bad


def main(argv):
    do_ship = "--ship" in argv
    replace = "--replace" in argv
    out = argv[argv.index("--preview") + 1] if "--preview" in argv else None

    images = {name: A.render(name) for name in A.SHEETS}
    fatal = []
    print("proofs")
    for label, (ok, msg) in (
            ("body is defeat's last frame, minus the arm",
             (prove_body() is None, prove_body() or "pixel for pixel")),
            ("that frame is the shipped one",
             (prove_source() is None, prove_source() or "pixel for pixel")),
            ("haul -> prop hand-over", prove_handoff()),
            ("prop is the cannon Greyson wears", prove_worn()),
            ("grip held for Greyson's tear sheet", prove_grip())):
        print("  %-44s %s  %s" % (label, "ok  " if ok else "FAIL", msg))
        if not ok:
            fatal.append(label + ": " + msg)
    print("\nlint")
    fatal += lint(images)

    print("\nanchors (texels)")
    print("  computah_armless  3 x 96x96, feet row 95, anchor (48, 96)  wound centre %s"
          % (tuple(round(v, 1) for v in A.wound_centre()),))
    print("  computah_wrench   2 x 96x96, feet row 95, anchor (48, 96)  socket f0 %s, "
          "f1 %s; hauled arm f0 %s -> %s"
          % (A.wrench_socket(0), A.wrench_socket(1), A.WRENCH_GUN[0], A.WRENCH_GUN[1]))
    print("  computah_arm_prop 5 x 56x56 (%s)"
          % ", ".join(n for n, _a in A.PROP_POSES))
    for n, p in A.prop_points().items():
        print("      %-5s socket %-12s grip %-12s muzzle %s"
              % (n, p["socket"], p["grip"], p["muzzle"]))
    print("  hand-over: on the tear draw prop 'torn' at %s from Computah's frame origin"
          % (A.handoff_offset(),))

    if out:
        preview(images, out)
    if fatal:
        print("\nFAILED:\n  " + "\n  ".join(fatal))
    if not do_ship:
        print("\n(no --ship: nothing written)")
        return 1 if fatal else 0
    fatal += pin_goldens(images, replace)
    if fatal:
        print("\nREFUSING TO SHIP:\n  " + "\n  ".join(fatal))
        return 1
    print()
    return 1 if ship(images, replace) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
