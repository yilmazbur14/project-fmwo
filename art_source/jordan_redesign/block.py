"""Blocking pass: rough shapes only, to settle proportions and pose at game scale before detailing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import (Canvas, capsule, ellipse, fill, image, poly, rect, rim, row, save, stats, up)  # noqa: E402


def mannequin(pump=False):
    cv = Canvas(96, 96)
    # far leg (relaxed), near leg (weight)
    far_leg = fill(poly([(49, 63), (57, 63), (58, 76), (57, 89), (51, 89), (50, 76)]), 'N')
    near_leg = fill(poly([(39, 63), (48, 63), (47, 76), (46, 89), (40, 89), (40, 76)]), 'N')
    cv.stamp(far_leg)
    cv.stamp(near_leg)
    cv.stamp(fill(poly([(51, 89), (57, 89), (61, 92), (61, 95), (50, 95), (50, 91)]), '2'))
    cv.stamp(fill(poly([(39, 89), (46, 89), (49, 92), (49, 95), (38, 95), (38, 91)]), '2'))
    # far arm behind the torso
    if not pump:
        cv.stamp(fill(capsule((57, 45), (63, 51), 2.8, 2.4), 'd'))
        cv.stamp(fill(capsule((63, 51), (65, 42), 2.3, 2.0), 'd'))
    else:
        cv.stamp(fill(capsule((57, 45), (61, 54), 2.8, 2.4), 'd'))
        cv.stamp(fill(capsule((61, 54), (60, 61), 2.3, 2.3), 'd'))
    # neck, torso
    cv.stamp(fill(rect(44, 34, 52, 44), 'c'))
    cv.stamp(fill(poly([(39, 50), (42, 41), (45, 41), (48.5, 47), (52, 41), (55, 41), (58, 50),
                        (57, 58), (58, 66), (39, 66), (40, 58)]), 'R'))
    # near arm, hand on hip
    if not pump:
        cv.stamp(fill(capsule((39, 45), (32, 54), 3.0, 2.5), 'd'))
        cv.stamp(fill(capsule((32, 54), (39, 61), 2.4, 2.1), 'd'))
    else:
        cv.stamp(fill(capsule((39, 44), (33, 33), 3.0, 2.5), 'd'))
        cv.stamp(fill(capsule((33, 33), (33, 20), 2.4, 2.2), 'd'))
        cv.stamp(fill(ellipse(33, 16, 3.3, 3.6), 'd'))
    # head: skull, jaw/beard, ear, hair
    cv.stamp(fill(ellipse(48.5, 25, 9.5, 11), 'd'))
    cv.stamp(fill(poly([(40, 28), (57, 27), (58, 32), (56, 36), (52, 39), (45, 39), (41, 35)]), 'j'))
    cv.stamp(fill(ellipse(40, 28, 1.6, 2.6), 'c'))
    hair = poly([(39, 27), (39, 19), (43, 15), (48, 13), (51, 10), (57, 11), (59, 16), (57, 22), (45, 22), (42, 27)])
    cv.stamp(fill(hair, 'i'))
    # box beside the face, in the far hand
    if not pump:
        cv.stamp(fill(rect(61, 26, 72, 41), 'o'))
    return cv


if __name__ == '__main__':
    f0 = image(mannequin(False).px)
    f1 = image(mannequin(True).px)
    print(stats(f0), stats(f1))
    save(row([up(f0, 5), up(f1, 5)]), 'block_5x.png')
