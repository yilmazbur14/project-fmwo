"""Shared locations for the uppercut-finisher art scripts. Work files and previews go OUTSIDE the project
(override with the UPPERCUT_WORK / UPPERCUT_PREVIEWS environment variables)."""
import os
import tempfile

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
GODOT = 'C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe'


def _norm(p):
    return p.replace(os.sep, '/')


WORK = _norm(os.environ.get('UPPERCUT_WORK') or os.path.join(tempfile.gettempdir(), 'fmwo_uppercut_work'))
OUT = _norm(os.environ.get('UPPERCUT_PREVIEWS') or os.path.join(WORK, 'previews'))
os.makedirs(WORK, exist_ok=True)
os.makedirs(OUT, exist_ok=True)


def work(name):
    return WORK.rstrip('/') + '/' + name
