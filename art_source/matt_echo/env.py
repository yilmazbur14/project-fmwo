"""Path setup for the Echo Roars rig. Import after guard.

Two homes, found automatically:
  - scratch (now): tools/ beside a COPY of the approved rigs in ../rig/art_source/, verified to
    rebuild the live sheets pixel for pixel (ea_verify_rig.py);
  - shipped: this folder copied to art_source/matt_echo/, where the approved rigs (matt, matt_intro,
    matt_fight, matt_glass, josh_redesign) are its siblings and the project root is two levels up.
Either way the approved rigs are imported read-only, and nothing is written unless an export is
given an explicit folder (or --ship).
"""
import os
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(TOOLS)
SHIPPED = os.path.basename(_parent) == 'art_source' and os.path.isfile(
    os.path.join(_parent, 'matt_intro', 'mi_base.py'))
if SHIPPED:
    RIG = _parent
    LIVE = os.path.dirname(RIG)
    WORK = os.environ.get('MATT_ECHO_SCRATCH', os.path.join(tempfile.gettempdir(), 'matt_echo_work'))
else:
    JOB = _parent
    RIG = os.path.join(JOB, 'rig', 'art_source')
    LIVE = r'C:\Users\theyi\OneDrive\Documents\new-game-project'
    WORK = os.environ.get('MATT_ECHO_SCRATCH', os.path.join(JOB, 'work'))
    APPROVAL = os.path.join(JOB, 'approval')
LIVE = os.path.realpath(LIVE)
LIVE_MATT = os.path.join(LIVE, 'Assets', 'Characters', 'Matt')
os.environ['MATT_INTRO_SCRATCH'] = os.path.join(WORK, 'matt_intro_scratch')
for d in ('matt_intro', 'matt_fight', 'matt_glass'):
    p = os.path.join(RIG, d)
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
sys.path.insert(0, TOOLS)
