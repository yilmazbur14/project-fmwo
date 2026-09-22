"""The three review images: the pose line-up at game scale, how big he now is next to
the old Computah and next to Greyson, and the peripheral-vision check that `charge`
and `ready` really are different drawings and not just differently coloured ones."""
import os

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.join(HERE, "..", "..", "Assets", "Characters")
BG = (26, 26, 34, 255)
SCALE = 3                      # GreysonComputahArtLayout.SCALE


def _load(path, frame=None):
    im = Image.open(path).convert("RGBA")
    return im.crop((0, 0, frame, frame)) if frame else im


def lineup(names, out, gap=20):
    ims = [_load(os.path.join(HERE, n + ".png")) for n in names]
    w = sum(i.width * SCALE for i in ims) + gap * (len(ims) - 1)
    sheet = Image.new("RGBA", (w, max(i.height for i in ims) * SCALE), BG)
    x = 0
    for im in ims:
        sheet.alpha_composite(im.resize((im.width * SCALE, im.height * SCALE),
                                        Image.NEAREST), (x, 0))
        x += im.width * SCALE + gap
    sheet.save(os.path.join(HERE, "preview", out))
    return sheet


def scale_compare(out="scale_compare_3x.png"):
    """Feet aligned on one floor line, so the size change is the only difference."""
    parts = [(_load(os.path.join(CHARS, "Computah", "computah_idle.png"), 64), 64),
             (_load(os.path.join(HERE, "computah_mm_idle.png")), 96),
             (_load(os.path.join(CHARS, "Greyson", "greyson_idle.png"), 96), 96)]
    h = 96 * SCALE
    sheet = Image.new("RGBA", (sum(p[1] for p in parts) * SCALE + 60, h), BG)
    x = 0
    for im, fw in parts:
        big = im.resize((fw * SCALE, fw * SCALE), Image.NEAREST)
        sheet.alpha_composite(big, (x, h - fw * SCALE))
        x += fw * SCALE + 30
    sheet.save(os.path.join(HERE, "preview", out))


def peripheral(out="peripheral_test.png"):
    """Blurred and shrunk the way the edge of vision sees it.  If `charge` and
    `ready` are not obviously different here, the attack has no tell."""
    row = lineup(["computah_mm_beam_charge", "computah_mm_beam_ready"],
                 "_tmp.png").convert("RGB")
    small = row.filter(ImageFilter.GaussianBlur(7)).resize(
        (row.width // 3, row.height // 3), Image.LANCZOS)
    small.resize((small.width * 2, small.height * 2), Image.LANCZOS).save(
        os.path.join(HERE, "preview", out))
    os.remove(os.path.join(HERE, "preview", "_tmp.png"))


def silhouette_delta():
    a, b = (_load(os.path.join(HERE, n + ".png")).getchannel("A")
            for n in ("computah_mm_beam_charge", "computah_mm_beam_ready"))
    pa, pb = list(a.get_flattened_data()), list(b.get_flattened_data())
    on = lambda v: v > 128                                        # noqa: E731
    diff = sum(1 for x, y in zip(pa, pb) if on(x) != on(y))
    return diff, sum(1 for v in pa if on(v)), sum(1 for v in pb if on(v))


def sheet_board(out="sheets_2x.png", gap=10, names=None):
    """Sheets stacked, at 2x, so one image shows a whole group."""
    names = names or ["computah_idle", "computah_run", "computah_beam_fire",
                      "computah_beam_recover", "computah_hit", "computah_drop",
                      "computah_defeat"]
    ims = [_load(os.path.join(HERE, n + ".png")) for n in names]
    w = max(i.width for i in ims) * 2
    h = sum(i.height for i in ims) * 2 + gap * (len(ims) - 1)
    board = Image.new("RGBA", (w, h), BG)
    y = 0
    for im in ims:
        board.alpha_composite(
            im.resize((im.width * 2, im.height * 2), Image.NEAREST), (0, y))
        y += im.height * 2 + gap
    board.save(os.path.join(HERE, "preview", out))


def charge_rows(out="charge_rows_3x.png", gap=12):
    """One idle frame from each battery row: the count, the colour and the antenna
    ball all move together, which is the read the chase depends on."""
    im = _load(os.path.join(HERE, "computah_idle.png"))
    row = Image.new("RGBA", (96 * 3 * 3 + gap * 2, 96 * 3), BG)
    for i, f in enumerate((0, 4, 8)):
        row.alpha_composite(
            im.crop((f * 96, 0, (f + 1) * 96, 96)).resize((288, 288),
                                                          Image.NEAREST),
            (i * (288 + gap), 0))
    row.save(os.path.join(HERE, "preview", out))


if __name__ == "__main__":
    if not os.path.isdir(os.path.join(HERE, "preview")):
        os.makedirs(os.path.join(HERE, "preview"))
    lineup(["computah_mm_idle", "computah_mm_beam_charge",
            "computah_mm_beam_ready"], "lineup_3x.png")
    sheet_board()
    sheet_board("sheets_attacks_2x.png", names=[
        "computah_uppercut", "computah_overload_brace",
        "computah_overload_charge", "computah_overload_release",
        "computah_overload_break"])
    sheet_board("sheets_ending_2x.png", names=[
        "computah_disarm", "computah_armless_down", "computah_scrapped"])
    sheet_board("sheets_props_4x.png", gap=8, names=[
        "computah_mine", "computah_arm", "computah_held_cannon"])
    charge_rows()
    scale_compare()
    peripheral()
    d, pa, pb = silhouette_delta()
    print("line-up, scale compare and peripheral test written to preview/")
    print("charge %d px, ready %d px, silhouettes differ on %d px (%.0f%%)"
          % (pa, pb, d, 100.0 * d / max(pa, pb)))
