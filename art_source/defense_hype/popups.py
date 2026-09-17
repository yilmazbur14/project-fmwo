"""Popup words (2 frames each: 0 rest, 1 pop - the MASH!/FULL! pulse):
  popup_parry        72x20  "PARRY!"        bright white-gold
  popup_perfect      96x20  "PERFECT!"      cyan (perfect dodge)
  popup_guard_break 136x20  "GUARD BREAK!"  red, flashing hot
  popup_hype         64x20  "HYPE!"         gold into magenta (hype meter full)
"""
import sys
sys.dont_write_bytecode = True
from dh_common import *
import lettering as LT

POPUPS = {
    'popup_parry': ('PARRY!', 'parry', 72),
    'popup_perfect': ('PERFECT!', 'perfect', 96),
    'popup_guard_break': ('GUARD BREAK!', 'guard', 136),
    'popup_hype': ('HYPE!', 'hype', 64),
}
TH = 20
DURATIONS_MS = {'popup_parry': [80, 80], 'popup_perfect': [80, 80], 'popup_guard_break': [100, 100],
                'popup_hype': [80, 80]}


def build():
    out = {}
    for name, (word, scheme, tw) in POPUPS.items():
        out[name] = [LT.word_canvas(word, scheme, False, tw, TH), LT.word_canvas(word, scheme, True, tw, TH)]
    return out


if __name__ == '__main__':
    for name, frames in build().items():
        s = strip(frames)
        save_zoom(s, work(name + '_8x.png'), 8, bg=(70, 70, 90), grid=(frames[0].w, TH))
        print(name, s.w, s.h, bbox(frames[0]), bbox(frames[1]), s.colours() - DB32)
