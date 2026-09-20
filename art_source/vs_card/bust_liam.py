"""LIAM - VS-card bust. Built by the shared crop-scale-rim method.

See busts_sprite.py: the base is this character's own pixels, cropped around
their centreline and scaled by an integer factor, then re-rimmed at 1px and
hand-detailed. Not a redraw - two redraw attempts at Eric lost the character.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import busts_sprite


def build():
    return busts_sprite.make("liam")


if __name__ == "__main__":
    import bustkit as K
    from pxlib import save_zoom
    im = build()
    K.measure("liam", im, busts_sprite.source_for("liam"))
    sp = sys.argv[1] if len(sys.argv) > 1 else "."
    im.save(os.path.join(sp, "bust_liam.png"))
    save_zoom(im, os.path.join(sp, "bust_liam_5x.png"), 5, "#222034")
