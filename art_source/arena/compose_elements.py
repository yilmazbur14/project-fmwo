"""
Drops the game's real elements onto an arena mockup so the only question that
matters - can you still read the fight? - can actually be judged.

All scales are the ones the game uses, taken from the scenes/scripts:
  player   player_4dir_sheet.png  32x32 frames, 10x4, MainPlayer.tscn scale 2
  boss     carter_akuma.png       96x96 frames x3, boss scenes scale 3
  markers  drawn at scale 3 (CarterElbowDropScript, NuggetMeteorScript,
           BixbyCombinedArtLayout all say "at 3x")

    python compose_elements.py --out <dir> --assets <project root>
"""

import argparse
import os

from PIL import Image

PLAYER = "Assets/Characters/MainPlayer/player_4dir_sheet.png"
BOSS = "Assets/Characters/Carter/carter_akuma.png"
ELBOW = "Assets/Characters/Mason/elbow_target_v2.png"
NUGGET = "Assets/Characters/Mason/nugget_target.png"
CRACK = "Assets/Characters/Bixby/bixby_quake_crack.png"
CARD_SHADOW = "Assets/Characters/Josh/Cards/card_giant_shadow.png"
CARD = "Assets/Characters/Josh/Cards/card_giant.png"


def frame(root, path, fw, fh, col, row=0):
    im = Image.open(os.path.join(root, path)).convert("RGBA")
    return im.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))


def place(dst, spr, cx, cy, scale=3, alpha=1.0, tint=None):
    """Paste spr centred on (cx, cy) at an integer NEAREST scale."""
    s = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    if tint is not None:
        solid = Image.new("RGBA", s.size, tint + (255,))
        solid.putalpha(s.split()[3])
        s = solid
    if alpha < 1.0:
        a = s.split()[3].point(lambda v: int(v * alpha))
        s.putalpha(a)
    dst.alpha_composite(s, (int(cx - s.width // 2), int(cy - s.height // 2)))


# The engine's own player is baked into the render at this bbox. It is left in
# the plain environment mockups (it proves they sit on a real render) but has
# to go here, or the sheet shows two players.
ENGINE_PLAYER = (943, 870, 977, 931)


def compose(root, mockup_path, out_path):
    base = Image.open(mockup_path).convert("RGBA")

    x0, y0, x1, y1 = ENGINE_PLAYER
    patch = base.crop((x0 - 200, y0, x1 - 200, y1))     # clean mat, same row
    base.paste(patch, (x0, y0))

    # ---- floor markers, deliberately spread across bright centre AND the
    #      darker mat corners, because that is where a vignette can hurt
    place(base, frame(root, CARD_SHADOW, 191, 293, 0), 430, 520,
          scale=1, alpha=0.35, tint=(0, 0, 0))          # Josh giant card shadow
    place(base, frame(root, ELBOW, 76, 76, 1), 1290, 720)       # Carter elbow
    for (x, y, f) in ((430, 260, 2), (1560, 880, 1), (980, 180, 3)):
        place(base, frame(root, NUGGET, 48, 26, f), x, y)       # Mason nuggets
    for (x, y, f) in ((330, 870, 3), (1450, 380, 2), (700, 930, 1)):
        place(base, frame(root, CRACK, 48, 24, f), x, y)        # Bixby cracks

    # ---- the giant card itself, above its shadow
    place(base, frame(root, CARD, 191, 293, 0), 360, 450, scale=1)

    # ---- fighters
    place(base, frame(root, BOSS, 96, 96, 0), 760, 470, scale=3)
    place(base, frame(root, PLAYER, 32, 32, 0, 0), 1290, 700, scale=2)

    base.convert("RGB").save(out_path)
    print("wrote", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", required=True, help="project root")
    ap.add_argument("--keys", default="a,b,c")
    args = ap.parse_args()
    for k in args.keys.split(","):
        compose(args.assets, os.path.join(args.out, f"mockup_{k}.png"),
                os.path.join(args.out, f"elements_{k}.png"))


if __name__ == "__main__":
    main()
