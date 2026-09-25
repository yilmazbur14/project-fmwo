"""Greyson's fight arm poses, traced as muscle polygons in the approved rig's convention
(gr_arms): coordinates for the LEFT arm (screen left), mirrored point by point for the right arm
and re-lit by the same upper-left light. Regions: 'delt', 'upper' (the triceps), 'biceps',
'forearm', 'brach' (the forearm's bulge). An arm that wears the cannon keeps only the upper-arm
regions; gf_cannon draws the rest.

  RAISED   the arm thrust straight up (the spirit-bomb raise): the delt bunched on the shoulder,
           the upper arm upright with the biceps on the side toward the head and the triceps on
           the outside, the elbow above the ear.
  CARRY    the barbell carry (the fight idle): the upper arm hangs down and a little forward, the
           forearm folds up across the front of the lat so the fist sits in front of the chest,
           holding the bar that rests on the shoulder.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
from gr_muscle import Form  # noqa: E402

gr_arms = B.gr_arms
LINE = gr_arms.LINE

RAISED = {
    'delt': [(36.4, 52.0), (34.4, 48.2), (30.6, 46.4), (26.6, 47.2), (24.0, 50.0), (23.4, 54.0),
             (24.8, 57.8), (28.2, 60.0), (32.2, 59.6), (35.4, 57.0)],
    'upper': [(25.6, 50.6), (23.6, 45.6), (22.8, 40.0), (23.0, 35.0), (24.4, 31.6), (27.0, 30.0),
              (29.8, 30.2), (29.8, 40.0), (29.4, 50.0)],
    'biceps': [(29.4, 50.0), (29.8, 40.0), (29.8, 30.2), (32.4, 31.4), (34.6, 34.6), (35.8, 39.6),
               (35.6, 45.0), (34.2, 49.6), (32.6, 51.6)],
}
RAISED_FORMS = {
    'delt': Form(ellipsoid=(29.6, 53.6, 8.0, 7.6)),
    'upper': Form(axis=[(29.4, 52.0), (29.2, 30.0)], r=6.6),
    'biceps': Form(axis=[(29.4, 52.0), (29.2, 30.0)], r=6.6),
}
RAISED_SPEC = {
    'upper': (1.4, 2.6, 2, 1),
    'biceps': (1.8, 3.0, LINE, 2),
    'delt': (2.0, 3.2, LINE, 4),
}
RAISED_ELBOW = (29.4, 31.0)      # where the cannon's socket sits

CARRY = {
    'delt': [(34.6, 50.6), (31.5, 48.9), (27.5, 48.9), (24.0, 50.6), (21.6, 53.4), (20.2, 57.0),
             (20.0, 60.6), (21.2, 63.8), (23.4, 65.4), (25.6, 62.8), (28.4, 60.6), (31.6, 58.6),
             (34.4, 56.6), (36.0, 54.4), (35.8, 52.2)],
    'upper': [(21.0, 59.0), (19.2, 62.6), (18.6, 66.4), (19.2, 70.0), (21.2, 73.2), (24.2, 74.8),
              (27.6, 74.4), (30.2, 72.0), (31.8, 68.4), (33.2, 64.2), (34.6, 60.8), (35.6, 58.0),
              (32.6, 58.0), (28.0, 59.6), (24.0, 60.4)],
    'biceps': [(26.0, 62.0), (24.4, 65.2), (24.0, 68.6), (25.2, 71.6), (27.6, 72.6), (30.0, 70.0),
               (31.6, 66.6), (33.0, 63.2), (33.4, 60.6), (29.8, 60.2)],
    'forearm': [(22.4, 71.6), (24.4, 68.4), (27.6, 65.4), (31.0, 62.4), (34.4, 59.6), (37.6, 57.8),
                (40.4, 58.6), (41.2, 61.0), (39.6, 63.6), (36.4, 66.2), (32.6, 69.6), (29.2, 73.0),
                (25.8, 75.4), (22.8, 74.8)],
    'brach': [(23.4, 70.0), (25.6, 67.2), (29.0, 64.4), (32.6, 61.6), (35.6, 59.6), (37.0, 61.4),
              (33.6, 64.0), (29.8, 67.2), (26.6, 70.4), (24.2, 72.4)],
}
CARRY_FORMS = {
    'delt': Form(ellipsoid=(28.0, 55.0, 9.0, 8.5)),
    'upper': Form(axis=[(29.0, 57.0), (24.0, 73.0)], r=7.5),
    'biceps': Form(axis=[(29.0, 57.0), (24.0, 73.0)], r=7.5),
    'forearm': Form(axis=[(24.0, 73.0), (39.0, 60.0)], r=6.0),
    'brach': Form(axis=[(24.0, 73.0), (39.0, 60.0)], r=6.0),
}
CARRY_SPEC = dict(gr_arms.SPEC, forearm=(1.5, 2.6, LINE, 5), brach=(1.6, 2.4, 0, 5))
CARRY_FIST = (41.0, 58.0)       # the fist in front of the chest, round the bar

# The rear V, seen from BEHIND: both arms up and out, the upper arms about 35 degrees off
# vertical, the forearms carrying on up. Regions: 'delt' (the rear delt), 'upper' (the triceps'
# long head, the back of the arm), 'biceps' here names the triceps' lateral head (the outer
# strip; from behind the biceps itself is out of sight), 'forearm' (the extensors).
REAR_V = {
    'delt': [(38.0, 49.0), (36.0, 45.4), (32.0, 44.0), (28.0, 45.0), (25.4, 48.4), (25.2, 52.4),
             (27.2, 56.2), (31.0, 58.0), (35.0, 57.2), (37.8, 53.8)],
    'upper': [(27.0, 53.9), (22.9, 50.0), (19.2, 45.8), (16.8, 40.7), (14.4, 35.6), (14.6, 32.4),
              (16.8, 30.2), (19.8, 29.2), (22.1, 30.1), (26.5, 33.7), (30.6, 37.6), (33.4, 42.4),
              (35.9, 47.5), (33.0, 52.0), (30.0, 54.0)],
    'biceps': [(27.0, 53.9), (22.9, 50.0), (19.2, 45.8), (16.8, 40.7), (14.4, 35.6), (14.6, 32.4),
               (17.2, 33.6), (19.6, 38.4), (22.4, 43.4), (25.6, 47.6), (28.6, 51.2)],
    'forearm': [(13.2, 34.2), (12.0, 29.4), (11.5, 22.7), (10.9, 17.8), (12.6, 16.0), (15.4, 15.6),
                (17.3, 16.2), (19.1, 20.8), (21.8, 27.0), (22.9, 31.8), (20.4, 34.8), (16.4, 35.6)],
}
REAR_V_FORMS = {
    'delt': Form(ellipsoid=(31.4, 51.2, 8.0, 7.6)),
    'upper': Form(axis=[(31.0, 51.0), (18.0, 33.0)], r=7.2),
    'biceps': Form(axis=[(31.0, 51.0), (18.0, 33.0)], r=7.2),
    'forearm': Form(axis=[(18.0, 33.0), (14.0, 17.0)], r=5.6),
}
REAR_V_SPEC = {
    'upper': (1.4, 2.6, 2, 1),
    'biceps': (1.6, 2.4, LINE, 2),
    'delt': (2.0, 3.2, LINE, 4),
    'forearm': (1.5, 2.6, LINE, 3),
}
REAR_V_ELBOW = (18.0, 33.0)      # the cannon's socket (his left arm, screen left from behind)
REAR_V_WRIST = (14.2, 18.0)      # the open hand's wrist (his right arm, mirrored)

# The three-quarter back twist (ref 25.png), seen from BEHIND.
# TWIST_EXT: his LEFT arm (screen left), extended out and a little down for the cannon to aim along
# (the frame's edge keeps it angled; the cannon is foreshortened toward us so its bore shows).
TWIST_EXT = {
    'delt': [(38.0, 49.0), (36.0, 45.4), (32.0, 44.0), (28.0, 45.0), (25.4, 48.4), (25.2, 52.4),
             (27.2, 56.2), (31.0, 58.0), (35.0, 57.2), (37.8, 53.8)],
    'upper': [(31.1, 46.3), (25.9, 47.5), (21.2, 49.6), (16.4, 52.3), (15.2, 55.4), (16.2, 59.2),
              (19.5, 61.6), (25.2, 61.5), (30.2, 60.3), (34.9, 57.7), (36.4, 53.4), (34.8, 48.4)],
    'biceps': [(31.1, 46.3), (25.9, 47.5), (21.2, 49.6), (16.4, 52.3), (17.8, 54.6), (22.6, 52.8),
               (27.4, 51.0), (31.6, 50.0)],
}
TWIST_EXT_FORMS = {
    'delt': Form(ellipsoid=(31.4, 51.2, 8.0, 7.6)),
    'upper': Form(axis=[(33.0, 52.0), (17.0, 57.0)], r=7.0),
    'biceps': Form(axis=[(33.0, 52.0), (17.0, 57.0)], r=7.0),
}
TWIST_EXT_ELBOW = (17.4, 57.2)

# TWIST_UP: his RIGHT arm (drawn here on the left, mirrored to screen right): the elbow high above
# the shoulder, the forearm folded back so the fist sits at the back of his head, the biceps
# peaking (from behind we see the triceps and the forearm's back).
TWIST_UP = {
    'delt': [(38.0, 49.0), (36.0, 45.4), (32.0, 44.0), (28.0, 45.0), (25.4, 48.4), (25.2, 52.4),
             (27.2, 56.2), (31.0, 58.0), (35.0, 57.2), (37.8, 53.8)],
    'upper': [(26.0, 54.3), (22.1, 48.1), (19.6, 41.3), (17.9, 33.8), (18.4, 30.4), (20.6, 28.4),
              (23.6, 28.0), (26.6, 29.9), (31.0, 36.1), (34.4, 42.5), (36.5, 49.5), (33.5, 53.5),
              (29.5, 55.0)],
    'biceps': [(26.0, 54.3), (22.1, 48.1), (19.6, 41.3), (17.9, 33.8), (18.4, 30.4), (20.8, 34.0),
               (22.8, 40.4), (25.2, 46.6), (28.2, 52.0)],
    'forearm': [(21.1, 36.9), (19.6, 33.0), (20.6, 29.0), (22.9, 27.1), (29.3, 28.1), (36.4, 30.2),
                (39.4, 31.6), (39.6, 35.0), (37.4, 36.8), (27.5, 36.4)],
}
TWIST_UP_FORMS = {
    'delt': Form(ellipsoid=(31.4, 51.2, 8.0, 7.6)),
    'upper': Form(axis=[(31.0, 52.0), (22.0, 32.0)], r=7.2),
    'biceps': Form(axis=[(31.0, 52.0), (22.0, 32.0)], r=7.2),
    'forearm': Form(axis=[(22.0, 32.0), (39.0, 33.0)], r=5.0),
}
TWIST_SPEC = {
    'upper': (1.4, 2.6, 2, 2),
    'biceps': (1.6, 2.4, LINE, 3),
    'delt': (2.0, 3.2, LINE, 4),
    'forearm': (1.5, 2.6, LINE, 1),      # behind the upper arm: it folds away from us
}
TWIST_FIST = (41.0, 33.0)          # at the back of his head (left-side coordinates)
