"""Echo Roars approval pass: shared imports, on the scratch COPY of Matt's rig (never the live one)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard  # noqa: F401  (refuses any write into the live project)
import env    # noqa: F401
import mg_base as M            # noqa: E402
from mg_base import B, A, G, F, H, L, PZ, FF  # noqa: E402
import mg_matt as MM           # noqa: E402
import mf_hands as MH          # noqa: E402
import mi_view as V            # noqa: E402
from mi_base import sh, poly, ellipse, capsule, matt, details, moved  # noqa: E402
from shapes import sym         # noqa: E402

for _m in (B, A, G, F, H, L, PZ, FF, MM, MH):
    assert os.path.normcase(_m.__file__).startswith(os.path.normcase(env.RIG)), _m.__file__
