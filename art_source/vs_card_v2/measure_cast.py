"""Measure every VS-card character's source sheet: keyline colour, keyline ratio, colour count.

    python measure_cast.py

Read-only: opens sheets under Assets/Characters and prints. Writes nothing.

The keyline is asked of each sheet rather than assumed (Computah's is #0C111A, not black), and the
ratio is keyline pixels over opaque pixels - the same number pxlib.black_ratio() and
bustkit.key_ratio() print, so these are the targets the poses are held to.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vs_card"))
import bustkit as K                                                           # noqa: E402

CAST = [
    ("burak",    "MainPlayer/player_4dir_sheet.png"),
    ("eric",     "Eric/eric_sheet_v2.png"),
    ("computah", "Computah/computah_idle.png"),
    ("matt",     "Matt/matt.png"),
    ("mason",    "Mason/mason.png"),
    ("mason*",   "Mason/mason_sheet.png"),
    ("josh",     "Josh/josh_cards.png"),
    ("danny",    "Danny/Sumo/danny_sumo_redesign.png"),
    ("carter",   "Carter/carter_polish.png"),
    ("carter*",  "Carter/carter_look_back.png"),
    ("liam",     "Liam/liam.png"),
    ("bixby",    "Bixby/bixby_beast.png"),
    ("jordan",   "Jordan/jordan_redesign_v2.png"),        # v2, approved 2026-09-24: the card's source
]


def measure(path):
    im = K.raw(path)
    key = K.keyline_of(im)
    _, op, pct = K.key_ratio(im, key)
    _, _, blk = K.key_ratio(im, "#000000")
    return key, pct, blk, len(K.palette_of(im)), op


if __name__ == "__main__":
    print("%-9s %-38s %-8s %7s %7s %6s" % ("who", "sheet", "keyline", "key%", "black%", "cols"))
    for who, path in CAST:
        key, pct, blk, cols, op = measure(path)
        print("%-9s %-38s %-8s %6.1f%% %6.1f%% %6d" % (who, path, key, pct, blk, cols))
