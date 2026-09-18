# Playtest #1

**Date:** 2026-09-17
**Build:** branch `mason-boss-and-art-pass`, at Josh's fight and the seven-boss ladder
**Played:** Eric, Greyson & Computah, Mason, Josh

---

## Notes, as written

### Eric
- Whirlwind should not be parriable
- The sword toss should be parriable and if successful should fling the sword back at Eric, dazing him and having him take a small amount of damage
- parry window feels too tight and theres no indication im parrying. need to let player know they are parrying

aside from the playtest, when a parry is successful there should be some kind of game slow down or freeze, make it very rewarding for the parry and the noise should be something more instant and rewarding sounding. take some notes from street fighter 3rd strikes parry noise and slow down. For reference, look at evo moment 37 where the ken parries all hits of the chun li super. its super satisfying to hear and watch

### Greyson
- Add 3rd attack where Computah chases after player, if the player is caught by computah, the player is brought to Greyson where he delivers a 5 hit combo to the users face alternating fists very fast and impactfully. If computah does not catch up to the player in time, his battery will die and he will fall to the ground in place and the user can punch computah. I want computah and Greyson to have two different health bars but they are still one boss. The twist here is if you kill computah first, Greyson becomes a strong second phase of the boss and if you call Greyson, computah becomes a strong second phase of the boss. your goal as the player is to try and hurt them equally. this will require a major redesign and a trashing of the mech suit Greyson has. lets start with a draft of each of their visual polished versions and go from there

### Mason
- Poop bomb comes out too slow and too few of them we want the player to have to know where the line of poop starts as most of the arena will be covered in these poop bombs, the strategy like i said is to know where it begins so you can run to that spot.
- Calling in carter attack comes out too slow, too few amount of times, and the target where the attack is (so the impact size of it as well) needs to be larger
- the chicken nugget meteor storm attack needs more nuggets being thrown out, more nugget bombs covering the screen at once

### Josh
- Remove the shades entirely
- its not obvious what hes holding are trading cards
- hair on the top of his head needs to be showing more
- Dialogue portrait needs to be changed (still the carter and josh combination)
- Card domino attack needs tweaking. All 3 cards should be put down like they are going to drop in front of the player but only 1 at a time does so the player has to escape to the next zone where the card is not going to fall.
- joshs card bombs that he throws are too infrequent, too small of an explosion zone, and are sometimes not even close to the player, it should loosely follow the position of the player just a little bit

---

## Status

### Eric

| # | Note | Status | What was done |
|---|---|---|---|
| 1 | Whirlwind should not be parryable | In progress | Parry-stagger and the red tell come off the whirlwind. It stays blockable and dash-throughable. |
| 2 | Sword toss parryable, reflects back, dazes, small damage | In progress | The toss gains the red tell; a parry reverses the sword into him, dazes him and chips his health. Routed into his existing punish window so the finisher and outro keep working. |
| 3 | Parry window too tight, no indication you're parrying | In progress | Window widened from 0.15 s, measured against Eric's toss, Josh's cards and Carter's clones. A visible cue now marks the parry window itself, so a miss shows whether you were early or late. |

### Parry feel (global, raised alongside the playtest)

| # | Note | Status | What was done |
|---|---|---|---|
| 4 | Slow-down or freeze on a successful parry | In progress | A hard freeze on contact, then a short slow-motion tail before normal speed resumes, layered over the existing flash, popup, streak and hype. Supersedes the earlier "no slow-mo" decision. Being tested against a chain of parries so Josh's three cards and Carter's five clones don't become a slideshow. |
| 5 | Sound should be instant and rewarding, 3rd Strike / Evo 37 | In progress | New primary parry sound: zero attack (first sample is the peak), everything in the first 60 ms, pitched an octave above the existing tinks so the family stacks. First attempt was judged not crisp enough and is being rebuilt as a closer imitation — a broadband click in front of an inharmonic metallic clink, rather than a struck tonal cluster. |

### Greyson & Computah

| # | Note | Status | What was done |
|---|---|---|---|
| 6 | Chase attack, catch into a five-hit combo, battery death into a punish window, two health bars, mutual phase-swap twist, mech thrown out | Design pass | Fight plan written (`scratchpad/greyson_computah_plan.md`). Visual redesigns of both characters being drafted first, per the note. Key decisions: the cycle alternates which body's punish window it offers, so even damage is the default and imbalance is self-inflicted; the healthier body visibly overcharges once the gap grows, warning you while it's still fixable; and a body can't be killed while the other is above 75%, so triggering the bad version of the twist takes a full cycle of warning. |

### Mason

| # | Note | Status | What was done |
|---|---|---|---|
| 7 | Poop line too slow and too sparse; the start of the line must be readable | In progress | Density and speed pushed until most of the arena is covered, plus an explicit telegraph at the line's origin. Being measured for reachability: from the far corner, can the player actually get to the start in time? |
| 8 | Carter call-in too slow, too few, needs a bigger target and impact | In progress | Faster, more frequent, bigger marker — with the hit area kept exactly matched to the marker. |
| 9 | Nugget storm needs more nuggets on screen at once | In progress | Count and overlap raised, keeping every third nugget targeted at the player and checking there's always somewhere to stand. |

### Josh

| # | Note | Status | What was done |
|---|---|---|---|
| 10 | Remove the shades entirely | In progress | Gone from his face and the brim. Gives his eyes back as an expression channel, which also helps the likeness. |
| 11 | Not obvious he's holding trading cards | In progress | Cards sized up with clear edges, light faces and visible pips, so you can count them at 3x. |
| 12 | More hair showing on top of his head | In progress | Hair mass shows under the fedora's brim rather than the hat eating the whole crown. |
| 13 | Dialogue portrait still the Carter-and-Josh combination | In progress | New portrait of Josh alone, matching the current design. |
| 14 | Domino attack: all three cards threaten, one drops at a time | In progress | All three queue visibly at low intensity; the committing card gets a distinctly stronger throbbing tell for its full warning. Corrects an earlier over-fix that hid the waiting cards entirely. |
| 15 | Card bombs too infrequent, blast too small, not near the player | In progress | Tighter spacing, bigger blast with the art scaled to match, and drop points biased toward the player without homing — you can always walk out of the pattern. |

---

## Carried forward

- Josh's likeness was fixed earlier the same day after a related note ("you cant really tell its josh"): long hair swept back, a full goatee, a fuller face and heavier brows.
- Matt has no design of any kind and shows as a deliberate placeholder on the menu tower and victory ladder.
- The menu tower's tier-10 pennant is legible but tighter than the single digits below it; fixing it properly means a wider flag for the top tier only.
