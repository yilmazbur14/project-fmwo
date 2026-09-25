"""matt_trueshot_charge.png and matt_trueshot_fire.png: the megaphone.

matt_trueshot_charge: 4 frames at 0.12 s, looping. Both hands cupped at his mouth like a megaphone,
the chest swelling with a gathering breath; the crest lifts on the swell.
    0  gather   1  swell   2  full   3  ease
matt_trueshot_fire: 3 frames, 0.06, 0.08, hold. The blast: leaning in, mouth wide in the cupped
hands, crest flared, then the recoil throws his hands apart and his head back.
    0  blast (the wave leaves the mouth texel)   1  recoil   2  hold
"""
import mf_base as M
from mf_base import B, A, G, F, H, L, PZ
import mf_faces as FF
import mf_hands as MH

# the charge's mouth: open round, drawing breath through the megaphone
M_AAH = [(44, 45, 'kkkkkkk'), (45, 44, 'kmmnnnmmk'), (46, 44, 'kmnqrqnmk'), (47, 45, 'kkkkkkk'),
         (48, 46, '11113')]


def mega_arms(dy=0, spread=0, lift=0):
    """Forearms up from low elbows in front of his chest, the hands cupped either side of the mouth.
    Forearm, cuff and hand are all stamped over the face, so the arms visibly lead up to it."""
    wl = (38 - spread, 58 + dy - lift)
    el = (28 - spread, 67 + dy)
    left = A.bent(0, (25, 57 + dy), (24, 60 + dy), el, wl, hand=MH.MEGA_L, fore_layer='front')
    right = A.bent(1, (71, 57 + dy), (72, 60 + dy), (96 - el[0], el[1]), (96 - wl[0], wl[1]),
                   hand=MH.MEGA_R, fore_layer='front')
    return [left, right]


def charge_figs():
    out = []
    for body, sh, lift, t in ((0, 0, 0, 0.0), (-1, -1, 1, 0.35), (-1, -2, 1, 0.6), (0, -1, 0, 0.3)):
        spikes = PZ.lerp_spikes(PZ.SP_IDLE, PZ.SP_PERK, t) if t <= 1 else PZ.SP_PERK
        out.append(F.Fig(arms=mega_arms(dy=sh, spread=2), body=(0, body), head=(0, 0),
                         face=(G.face(G.BR_ANGRY, G.EY_ANGRY, M_AAH), G.X0, G.Y0), spikes=spikes))
    return out


def fire_figs():
    blast = G.with_jaw(G.face(G.BR_ANGRY, G.EY_SQUEEZE), G.YELL_ROWS)
    open_ = G.with_jaw(G.face(G.BR_ANGRY, G.EY_WIDE), G.YELL_ROWS)
    return [
        F.Fig(arms=mega_arms(dy=1, spread=2), body=(0, 1), head=(0, 2), face=(blast, G.X0, G.Y0),
              spikes=PZ.SP_ROAR),
        F.Fig(arms=mega_arms(dy=-1, spread=4, lift=-1), body=(0, -1), head=(0, 0), face=(open_, G.X0, G.Y0),
              spikes=PZ.SP_BRISTLE),
        F.Fig(arms=mega_arms(spread=3), head=(0, 1), face=(open_, G.X0, G.Y0),
              spikes=PZ.lerp_spikes(PZ.SP_BRISTLE, PZ.SP_ROAR, 0.5)),
    ]


class Charge:
    NAME = 'matt_trueshot_charge'

    @staticmethod
    def figs():
        return charge_figs()


class Fire:
    NAME = 'matt_trueshot_fire'

    @staticmethod
    def figs():
        return fire_figs()
