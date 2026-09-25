"""The mock-up cards: each fight's two halves, its lettering and the composite over its arena.

Lettering comes from the shipped plates where a fight has them (Eric) and is baked the shipped way
where it does not (textart.bake with the sizes and colours build_assets.py uses), so a mock-up's
writing is what the finished set would carry.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "vs_card"))
import layout as LY                                                           # noqa: E402
import compose as CO                                                          # noqa: E402
import textart                                                                # noqa: E402  (read-only)

PROJ = LY.PROJ


def badge(portrait, crop=(18, 6, 46, 34), idx=2):
    """build_assets.badge(): the rank ring with a crop of the dialogue portrait inside it."""
    ring = Image.open(PROJ + "/Assets/UI/Screens/rank_slot.png").convert("RGBA").crop(
        (idx * 40, 0, idx * 40 + 40, 40))
    por = Image.open(PROJ + "/Assets/Characters/" + portrait).convert("RGBA").crop(crop)
    out = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    out.alpha_composite(por, (6, 6))
    out.alpha_composite(ring, (0, 0))
    return out


def fight_plate(number):
    """The FIGHT NN plate at the shipped size and colour. Plates are per number, not per boss:
    fight_01..08 are this function's output byte for byte, whoever fights at that number."""
    return textart.bake("FIGHT %02d" % number, 33, fill="#9BADB7")


def baked_plates(name, epithet, number, rank, portrait, crop=(18, 6, 46, 34)):
    """What build_assets.build() would bake for a fight, at the shipped sizes and colours."""
    return {
        "name": textart.bake(name, 99),
        "epithet": textart.bake(epithet, 33, fill="#CDD7E2") if epithet else None,
        "fight": fight_plate(number),
        "win": textart.bake("WIN " + rank, 33, fill="#F2C457") if rank else None,
        "badge": badge(portrait, crop) if rank else None,
        "vs": CO.shipped("vs.png"),
    }


def arena(key, captures):
    return Image.open(os.path.join(captures, "%s_arena_t0.png" % key)).convert("RGBA")


def card(arena_img, left, right, plates):
    return CO.frame(arena_img, left, right, plates, half_at=LY.HALF_AT)
