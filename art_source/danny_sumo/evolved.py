"""The evolved form's pixels, for the tools in this folder.

Danny's evolved (sumo) body was redesigned and approved on 2026-09-23; it is drawn by
art_source/danny_sumo_v2 (anim.py). sheets.py, transform.py and make_previews.py take the evolved
form from here, so the production sheets, the evolution flash and the previews all carry the NEW
body. The old rigs in this folder (danny_sumo.py, danny_honda.py) drew the previous body and are
kept for history only; nothing here uses them any more. The small form (danny_small.py) is
unchanged.

  pix(pose)            one frame as rows of RGBA tuples: 'idle', 'awake' (the flash's big
                       silhouette, evolve frame 1) or 'land' (evolve frame 2)
  sheet_frames(name)   every frame of one danny_sumo_* sheet
  sheet_meta(name)     its frame list (index, ms) and loop note
"""
import os
import sys

_V2 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'danny_sumo_v2')
if _V2 not in sys.path:
    sys.path.insert(0, _V2)
import anim  # noqa: E402

W, H = anim.FW, anim.FH
SHEETS = list(anim.SHEETS)
POSES = {'idle': ('danny_sumo_idle', 0), 'awake': ('danny_sumo_evolve', 1), 'land': ('danny_sumo_evolve', 2)}


def _pix(im):
    im = im.convert('RGBA')
    px = im.load()
    return [[px[x, y] for x in range(im.width)] for y in range(im.height)]


def pix(pose):
    name, i = POSES[pose]
    return _pix(anim.frame_image(anim.SHEETS[name][0][i][0]))


def sheet_frames(name):
    return [_pix(anim.frame_image(spec)) for spec, _ in anim.SHEETS[name][0]]


def sheet_meta(name):
    frames, loop = anim.SHEETS[name]
    return dict(frames=[(i, ms) for i, (_, ms) in enumerate(frames)], loop=loop)
