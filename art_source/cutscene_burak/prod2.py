"""Burak intro cutscene v2: 25 frames; notice/read turn toward the poster (3/4-back).  python prod2.py"""
import os
from blib import *
import prod, heads, b34_build as B, back34_parts as BP

HEAD_UP = blk_rows(BP.HEAD_B34_UP)
SWEAT = prod.SWEAT


def notice():
    # (a) stop stance, head tilting up toward the poster, eyes going up-right
    a = prod.build(dict(prod.STAND, torso='slouch', near_arm='pocket', head=heads.side_head('up', heads.SIDE_MOUTHS['open']),
                        head_at=(23, 12), bob=0, **prod.SLOUCH_G))
    # (b) head and shoulders turned 3/4-back, looking up-right at the poster; legs still in the stop stance
    b = B.build_b34(dict(legs='side', head=HEAD_UP, head_at=(21, 12)))
    # (c) startle: body jolts up 2px, gloves lag and swing, sweat drop flicks off the hood
    c = B.build_b34(dict(legs='side', head=HEAD_UP, head_at=(21, 12), up=2, hip_up=1, gb=(29, 35),
                         fx=[('rows', 43, 10, SWEAT)]))
    return [a, b, c]


def read():
    r0 = B.build_b34(dict(legs='back', head=HEAD_UP, head_at=(21, 12)))
    r1 = B.build_b34(dict(legs='back', head=HEAD_UP, head_at=(21, 12), up=1, gb=(30, 34)))
    return [r0, r1]


def resolve():
    # R0: turning back to the right; head leads, shoulders still 3/4-back
    t = B.build_b34(dict(legs='side', head=heads.side_head('det', heads.SIDE_MOUTHS['set']), head_at=(23, 13)))
    old = prod.resolve()
    # R1: hand out of the pocket, now with the side-view determined head instead of the camera-facing one
    r1 = prod.build(dict(prod.STAND, torso='slouch', head=heads.side_head('det', heads.SIDE_MOUTHS['set']), head_at=(24, 13),
                         bob=0, near_arm=((29, 35), (24.5, 41), (30.5, 45), 'open'), hand_at=(33, 46),
                         gb=(16, 28), gf=(37, 35), lace_top=(28, 31)))
    return [t, r1, old[1], old[2]]


ANIMS = [('walk_gloomy', prod.walk_gloomy), ('stop', prod.stop), ('notice', notice), ('read', read), ('resolve', resolve),
         ('walk_purpose', prod.walk_purpose)]

TIMING = {
    'walk_gloomy': [150] * 8,
    'stop': [160, 420],
    'notice': [300, 380, 650],
    'read': [800, 800],
    'resolve': [240, 360, 220, 900],
    'walk_purpose': [120] * 6,
}


def all_frames():
    frames, ranges = [], []
    for name, fn in ANIMS:
        fr = fn()
        ranges.append((name, len(frames), len(frames) + len(fr) - 1))
        frames.extend(fr)
    return frames, ranges


if __name__ == '__main__':
    frames, ranges = all_frames()
    for r in ranges:
        print(r)
    prod.save_strip(frames, 'out/burak_cutscene_v2_1x.png')
    open('out/frames_v2.txt', 'w').write('\n\n'.join(to_text(c) for c in frames))
    print('frames', len(frames))
