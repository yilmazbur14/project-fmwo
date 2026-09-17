"""Loads every defense/hype asset as Canvas strips/sheets: from the project files (default, verifies the export)
or from a fresh in-memory build (--draft) while iterating."""
import sys
sys.dont_write_bytecode = True
from dh_common import *

NAMES_UI = ['stamina_bar_frame', 'stamina_bar_fill', 'stamina_bar_low', 'stamina_bar_broken', 'hype_meter_frame',
            'hype_meter_fill', 'hype_meter_full', 'hype_label', 'popup_parry', 'popup_perfect', 'popup_guard_break',
            'popup_hype']
NAMES_FX = ['block_spark', 'parry_flash', 'guard_break_stars', 'perfect_dodge_trail', 'uppercut_impact_super']
NAMES_PL = ['player_uppercut_super', 'player_guard_break']


def from_project():
    A = {}
    for n in NAMES_UI:
        A[n] = from_png(PROJ + 'Assets/UI/%s.png' % n)
        A[n + '_3x'] = from_png(PROJ + 'Assets/UI/%s_3x.png' % n)
    for n in NAMES_FX:
        A[n] = from_png(PROJ + 'Assets/Effects/%s.png' % n)
    for n in NAMES_PL:
        A[n] = from_png(PROJ + 'Assets/Characters/MainPlayer/%s.png' % n)
    return A


def from_build():
    import stamina_ui as ST, hype_ui as HY, popups as PO, fx_defense as FD, fx_dodge as DG, fx_super as FS
    import player_guard_break as GB
    A = {}
    d = {}
    d.update(ST.build())
    d.update(HY.build())
    d.update(PO.build())
    for n, frames in d.items():
        A[n] = strip(frames)
        A[n + '_3x'] = scale3(A[n])
    fd = FD.build()
    for n in ('block_spark', 'parry_flash', 'guard_break_stars'):
        A[n] = strip(fd[n])
    A['perfect_dodge_trail'] = grid_sheet(DG.build())
    A['uppercut_impact_super'] = strip(FS.impact_super())
    A['player_uppercut_super'] = strip(FS.uppercut_super()[0])
    A['player_guard_break'] = grid_sheet(GB.build())
    return A


def load():
    return from_build() if '--draft' in sys.argv else from_project()
