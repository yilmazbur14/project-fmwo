"""Per-boss card data. One row per fight; the card generator reads nothing else.

fight    the number shown top-left (playable order - Eric first, because the
         BURAK row in Scripts/GameProgress.gd has no scene and Burak is the
         player, and Matt has no design yet)
rank     the rank WINNING promotes the player to, straight out of GameProgress.gd
epithet  canon - all eight approved by the user 2026-09-20
ramp     5-step dark->light ramp for the boss's half of the band
accent   the two hairline rules along the diagonal split
mark     (emblem, colour, alpha) for the ghosted watermark behind the bust
name     lines for the baked name plate; two lines at 55 for the pair bosses,
         because GREYSON & COMPUTAH is 989px on one line at 99 and would run
         clean across both busts
"""

BOSSES = [
    dict(key="eric", name=["ERIC"], name_size=99, epithet="THE WHITE KNIGHT",
         fight=1, rank="@regular", portrait="Eric/portrait.png",
         ramp=["#525A74", "#7A86A0", "#A3B1C2", "#CDD7E2", "#EAF0F6"],
         accent=("#C48A2C", "#F2C457"), mark=("cross", "#B0242A", 52)),

    dict(key="greyson", name=["GREYSON", "& COMPUTAH"], name_size=55,
         epithet="THE LIFTER AND THE MACHINE",
         fight=2, rank="@active", portrait="Greyson/portrait.png",
         ramp=["#2A1936", "#43265A", "#63407F", "#8C64A8", "#C08CEE"],
         accent=("#2A7A3C", "#6ABE30"), mark=("dumbbell", "#6ABE30", 56)),

    dict(key="mason", name=["MASON"], name_size=99, epithet="THE SHITPOSTER",
         fight=3, rank="@trusted", portrait="Mason/mason.png",
         ramp=["#3A2408", "#6B4410", "#9E6A1C", "#D19A2E", "#F5C84E"],
         accent=("#AC3232", "#D95763"), mark=("star", "#FFFFFF", 44)),

    dict(key="josh", name=["JOSH"], name_size=99, epithet="THE CARD SHARK",
         fight=4, rank="@vip", portrait="Josh/josh_redesign.png",
         ramp=["#10182E", "#1C2A4E", "#2E4478", "#4766A8", "#7091D4"],
         accent=("#C48A2C", "#F2C457"), mark=("spade", "#9FBCEC", 46)),

    dict(key="danny", name=["DANNY"], name_size=99, epithet="THE SLEEPING GIANT",
         fight=5, rank="@helper", portrait="Danny/portrait.png",
         ramp=["#2E0F14", "#521A20", "#7E2A2E", "#AC3F3F", "#D9716A"],
         accent=("#C48A2C", "#F2C457"), mark=("moon", "#CBDBFC", 46)),

    dict(key="carter", name=["CARTER"], name_size=99, epithet="THE DEMON",
         fight=6, rank="@moderator", portrait="Carter/carter_akuma_pose.png",
         ramp=["#140A1C", "#2A1030", "#4A1A46", "#78265E", "#B03A70"],
         accent=("#8A1F38", "#E2402F"), mark=("demon", "#E2402F", 52)),

    dict(key="liam", name=["LIAM", "& BIXBY"], name_size=55,
         epithet="THE THRONE AND THE BEAST",
         fight=7, rank="@admin", portrait="Liam/portrait.png",
         ramp=["#161016", "#2E1A1C", "#54291F", "#8A4A24", "#C87038"],
         accent=("#9A8F80", "#EDE4D6"), mark=("crown", "#F2C457", 50)),

    dict(key="jordan", name=["JORDAN"], name_size=99, epithet="THE ADMIN",
         fight=8, rank="", portrait="Jordan/portrait.png",
         ramp=["#12142A", "#1E2248", "#2E3680", "#5B6EE1", "#93A4F7"],
         accent=("#5FCDE4", "#CBDBFC"), mark=("shield", "#FFFFFF", 44)),

    # --- bar-only rows -------------------------------------------------------
    # These two never get a VS card of their own: Computah shares Greyson's card
    # and Bixby is a mid-fight identity swap on Liam's. They exist here so the
    # HUD can key a fill ramp, an accent and an emblem off the same roster.
    dict(key="computah", name=["COMPUTAH"], name_size=55, epithet="", fight=2,
         rank="", portrait="Computah/computah.png", bar_only=True,
         ramp=["#0E2036", "#14406E", "#2A6FB0", "#59B8F2", "#A6DFFF"],
         accent=("#1F9A38", "#4FE066"), mark=("bolt", "#4FE066", 56)),

    dict(key="bixby", name=["BIXBY"], name_size=55, epithet="", fight=7,
         rank="", portrait="Bixby/bixby.png", bar_only=True,
         ramp=["#1A0A0C", "#3E1214", "#71201E", "#B03A24", "#E8622E"],
         accent=("#AC3232", "#F58A38"), mark=("flame", "#F58A38", 52)),
]


def card_roster():
    """Bosses that get a VS card - everything except the bar-only rows."""
    return [b for b in BOSSES if not b.get("bar_only")]


# Burak's half never changes between cards.
BURAK_RAMP = ["#15131F", "#222034", "#2E2C4A", "#3F3F74", "#3A5BA8"]
BURAK_STRIPE = "#3A5BA8"


def by_key(k):
    for b in BOSSES:
        if b["key"] == k:
            return b
    raise KeyError(k)
