"""Draw a VS card at its hold, 1920x1080, the way Scripts/VsCard.gd draws it.

    frame(arena, left, right, plates, half_at=...)   -> RGBA 1920x1080

`arena` is a still of the live fight with nothing of the card on it (shoot_arena.gd's t = 0 frame).
The card is drawn over it in VsCard.gd's order: the dim and the letterbox (Back), then the Card
node's children - the left half, the right half, the writing (fight number, epithet, name, WIN
plate, badge) and the VS on top. At the hold the seam flash and the burst are both gone, the knock
has settled and the writing is at full alpha, so none of those appear.

check_against_capture() rebuilds the SHIPPED Eric card this way and diffs it with the game's own
render of it, so a mock-up made here is known to be what the game would show.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as L                                                            # noqa: E402


def up(im, f=L.ART_SCALE):
    return im.resize((im.width * f, im.height * f), Image.NEAREST)


def dimmed(arena):
    """Back/Dim: #222034 at 0.78 over the arena, blended the way a 2D ColorRect is."""
    a = arena.convert("RGBA")
    over = Image.new("RGBA", a.size, L.DIM_COLOR + (round(255 * L.DIM_ALPHA),))
    out = a.copy()
    out.alpha_composite(over)
    return out


def letterbox(img):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for (x, y, w, h), col in ((L.LETTERBOX_TOP[0], L.LETTERBOX_COLOR),
                              (L.LETTERBOX_TOP[1], L.LETTERBOX_RULE_COLOR),
                              (L.LETTERBOX_BOTTOM[0], L.LETTERBOX_COLOR),
                              (L.LETTERBOX_BOTTOM[1], L.LETTERBOX_RULE_COLOR)):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=col + (255,))
    return img


def frame(arena, left, right, plates, half_at=L.BAND_AT):
    """plates: dict with any of fight, epithet, name, win, badge, vs (PIL images)."""
    img = letterbox(dimmed(arena))
    img.alpha_composite(up(left), half_at)
    img.alpha_composite(up(right), half_at)
    p = plates
    if p.get("fight") is not None:
        img.alpha_composite(p["fight"], L.FIGHT_AT)
    if p.get("epithet") is not None:
        img.alpha_composite(p["epithet"], L.EPITHET_AT)
    if p.get("name") is not None:
        img.alpha_composite(p["name"], (L.NAME_TOP_RIGHT[0] - p["name"].width, L.NAME_TOP_RIGHT[1]))
    if p.get("win") is not None:
        img.alpha_composite(p["win"], (L.WIN_TOP_RIGHT[0] - p["win"].width, L.WIN_TOP_RIGHT[1]))
    if p.get("badge") is not None:
        img.alpha_composite(up(p["badge"]), L.BADGE_AT)
    vs = p["vs"]
    img.alpha_composite(vs, (L.VS_CENTRE[0] - vs.width // 2, L.VS_CENTRE[1] - vs.height // 2))
    return img


def shipped(name):
    return Image.open(L.SHIPPED + name).convert("RGBA")


def shipped_eric_plates():
    return {"fight": shipped("fight_01.png"), "epithet": shipped("epithet_eric.png"),
            "name": shipped("name_eric.png"), "win": shipped("win_regular.png"),
            "badge": shipped("badge_eric.png"), "vs": shipped("vs.png")}


def old_eric_card(arena):
    return frame(arena, shipped("band_left.png"), shipped("band_right_eric.png"), shipped_eric_plates())


def check_against_capture(arena_path, capture_path):
    """Mean and worst channel error of our rebuild of the shipped card against the game's render."""
    from PIL import ImageChops, ImageStat
    ours = old_eric_card(Image.open(arena_path)).convert("RGB")
    game = Image.open(capture_path).convert("RGB")
    d = ImageChops.difference(ours, game)
    st = ImageStat.Stat(d)
    worst = max(hi for lo, hi in d.getextrema())
    bad = sum(1 for q in d.getdata() if max(q) > 8)
    return st.mean, worst, bad, ours


if __name__ == "__main__":
    cap = sys.argv[1]
    out = sys.argv[2]
    mean, worst, bad, ours = check_against_capture(os.path.join(cap, "eric_arena_t0.png"),
                                                   os.path.join(cap, "eric_hold.png"))
    print("mean channel error %s, worst %d, pixels off by more than 8: %d" % (
        ["%.3f" % m for m in mean], worst, bad))
    ours.save(out)
