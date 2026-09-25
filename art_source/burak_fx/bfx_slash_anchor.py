"""Anchor data for burak_slash_trail: reads the body artist's slash poses (art_source/burak_boss_anims, read-only,
no bytecode written there) and writes bfx_slash_anchor.json beside this file:
  blades  per burak_slash frame, [hand, tip] in 128x112 frame texels (the pose points + bob + frame offset)
  sword   per burak_slash frame, the exact texels of the cutlass, its knuckle-bow and the fist on its grip
          (the frame rendered as shipped, diffed against the same pose with the sword arm drawing only the arm)
bfx_slash.py builds the trails from it: the smears run through the real blade tips and never cover the sword.
Re-run this whenever burak_slash's poses change:  python bfx_slash_anchor.py
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ANIMS = os.path.normpath(os.path.join(HERE, '..', 'burak_boss_anims'))
sys.path.insert(0, ANIMS)
import akit as A  # noqa: E402
import aparts as AP  # noqa: E402
import sheets as S  # noqa: E402

OUT = os.path.join(HERE, 'bfx_slash_anchor.json')


def arm_only(elbow, hand):
    def draw(F):
        AP.arm(F, AP.SH_L, elbow, hand, lit=True)
    return draw


def main():
    blades, swords = [], []
    for (name, elbow, hand, tip, kw, hold) in S.SLASH:
        P = A.Pose(fw=128, fh=112, arm_l=S.sword_arm(elbow, hand, tip), arm_r=S.hand_on_hip, **kw)
        bx, by = P.bob
        blades.append([[hand[0] + bx + P.ox, hand[1] + by + P.oy], [tip[0] + bx + P.ox, tip[1] + by + P.oy]])
        full = A.render(P)
        bare = A.render(A.Pose(fw=128, fh=112, arm_l=arm_only(elbow, hand), arm_r=S.hand_on_hip, **kw))
        sword = sorted(p for p in full if full.get(p) != bare.get(p) and 0 <= p[0] < 128 and 0 <= p[1] < 112)
        swords.append([list(p) for p in sword])
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'source': 'art_source/burak_boss_anims/sheets.py SLASH', 'frame': [128, 112], 'feet': [64, 111],
                   'blades': blades, 'sword': swords}, f, separators=(',', ':'))
    print('wrote', OUT, [len(s) for s in swords])


if __name__ == '__main__':
    main()
