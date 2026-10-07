"""Jordan's own head, lifted from the approved v2 sheet (Assets/Characters/Jordan/
jordan_redesign_v2.png, read only). jg_lord turns it frontal by mirroring his near side about the
nose, so the god's face (A1) and the mask's proportions (A2) are his own pixels.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402


def head_1x(shout):
    """The v2 head (hair, face, beard, ear) at 1x: everything 4-connected to the face above the
    neck (rows <= 39), so the fist-pump arm, its pink puff and the collector box stay behind.
    shout=True takes frame 1 (brows down, teeth bared); False the idle frame 0."""
    v = B.v2_keys(1 if shout else 0)
    seed = (50, 28)
    assert seed in v
    seen = {seed}
    todo = [seed]
    while todo:
        p = todo.pop()
        for q in B.neighbours4(p):
            if q in v and q not in seen and q[1] <= 39:
                seen.add(q)
                todo.append(q)
    return {p: v[p] for p in seen}
