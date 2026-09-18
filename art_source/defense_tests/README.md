# Defence test suite

Headless checks on the player's defence and everything built on it: stamina, the guard, the parry
and its window, the guard break, the perfect dodge, the dash recovery, crowd hype, the uppercut
finisher's knockback, the status effects and the parry-only lock.

Everything lives in `verify_defense.gd`. It runs one mode per process, prints a `P PASS` or `P FAIL`
line per check, ends with `RESULT mode=<name> fails=<n>` and exits with that failure count.

Presses are real `InputEventKey` events and hits go through `player.receive_hit()`, so what is under
test is the same path the game uses, not a shortcut around it.

## Running it

One mode:

```sh
Godot.exe --headless --fixed-fps 60 --path . \
  --script res://art_source/defense_tests/verify_defense.gd -- mode=parry_rules
```

`--fixed-fps 60` makes game time deterministic. Three modes mash the finisher's prompt, which gates
presses on an interval in *real* seconds, so they need real time instead:

```sh
Godot.exe --headless --max-fps 60 --path . \
  --script res://art_source/defense_tests/verify_defense.gd -- mode=super_uppercut
```

Those modes are `super_uppercut`, `knockback`, `knockback_computah`, `knockback_boss` and
`kill_shove`. Everything else is happy either way.

All of them, with a summary line each:

```sh
GODOT=/path/to/Godot.exe bash art_source/defense_tests/run_defense_tests.sh
```

or a subset:

```sh
GODOT=/path/to/Godot.exe bash art_source/defense_tests/run_defense_tests.sh parry_rules parry_streak status
```

The script writes each run's full output to `art_source/defense_tests/out/<mode>.log` and prints one
line per mode. `out/` is disposable.

## Modes

A mode marked **(Eric)** drives Eric's real attacks, so it asserts things about his fight as well as
the player's rules; if his fight changes, these are the ones to reconcile.

### Stamina and the guard

| mode | arguments | what it asserts |
| --- | --- | --- |
| `stamina` | | the bar's costs, the refill delay and rate, the pause while the guard is held, a dash refused below its cost |
| `baseline` | | with no guard and no dash, every hit lands exactly as it did before any of this existed: damage, i-frames, cadence |
| `block_eric` | | **(Eric)** which of his attacks the guard absorbs and what each costs |
| `behind` | | **(Eric)** the guard only covers the faced side: a wave from the front is blocked, one from behind hits, a sky attack is blocked from any facing |
| `blocks` | `fight=greyson\|carter\|mason\|jordan\|liam` | 45 s of a fight with the guard held: every attack that lands, what blocking it costs, that nothing unblockable is ever blocked, then the direction rules |
| `grab_block` | | **(Eric)** a held guard does not stop his bear hug |
| `dash_through` | | **(Eric)** attacks tagged `dash_through` pass over a dashing player |

### Guard break

| mode | arguments | what it asserts |
| --- | --- | --- |
| `guard_break` | | the block that empties the bar is still absorbed, then the stun, the state, the refill, and that only blocks break the guard |
| `guard_break_timeout` | | the stun ends on its own after `guard_break_time`, and two hits in the same physics flush punish once |
| `guard_break_grab` | | a grab during the stun |
| `guard_break_lose` | | dying during the stun |

### Parry

| mode | arguments | what it asserts |
| --- | --- | --- |
| `parry_rules` | | a fresh press parries, a press whose window has passed only blocks, mashing never parries, a held guard never parries, and a press past the mash lockout parries again |
| `parry_window` | | sweeps the press-to-hit gap frame by frame and reports which gaps parry, at the old 0.15 s window and at the shipped one; then what that is worth against a clone dash, Josh's card spacing and Eric's sword speed |
| `parry_cue` | | the rim that shows the window: it appears on a credited press, is drawn behind the player, lasts exactly `parry_window`, and never appears for a press that got no credit |
| `parry_freeze` | | the parry's dead stop and its slow-motion tail, a three-parry chain at 0.90 s and 0.62 s cadences, and a parry landing on the frame the fight ends |
| `parry_rearm` | | every press is reported through `block_pressed(credited)`, and `rearm_parry()` excuses exactly one press and never a mash inside the same window |
| `parry_streak` | | streaks count, pay 25 / 30 / 35 hype, climb through the popups and the badge, sound identical every time, end on a hit or a guard break, lapse on their own, and lengthen the stagger window by 0.2 per tier over 2, capped at 0.4 |
| `parry_projectiles` | | **(Eric)** parrying his real projectiles on their way in |
| `grab_parry` | | **(Eric)** his grab can only be answered with a parry: a held guard is still grabbed |
| `stagger` | | **(Eric)** the parry stagger: what it opens, the hit cap, where he picks himself up |
| `stagger_chain` | | **(Eric)** his chain carries on correctly after a parry stagger |
| `stagger_win` | | **(Eric)** the fight won during a parry stagger |
| `stagger_lose` | | **(Eric)** the fight lost during a parry stagger |
| `tells` | | **(Eric)** the red tell over his head during the wind-up of a parryable attack |

### Dodging

| mode | arguments | what it asserts |
| --- | --- | --- |
| `dodge_ring` | | a perfect dodge off a dash-through attack during dash immunity |
| `dodge_near` | | a perfect dodge off an attack that reaches the spot the dash started from, through the dodge ghost |
| `dodge_bosses` | | the dodge ghost's near-miss reporting across the roster's attacks |
| `dodge_rollout` | `fight=greyson\|carter` | dashing out of the way of a real attack in a real fight. Only these two fights have a readable approach for the bot; greyson's rockets home onto the player, so that one is expected to fail |
| `dash_recovery` | | the lockout after a dash: no move, punch or dash, the guard may still go up, a parry cancels it, a plain block does not |
| `dash_spam` | | mashing dash covers less ground than walking |

### Hype and the finisher

| mode | arguments | what it asserts |
| --- | --- | --- |
| `hype` | | what each action pays, what a hit and a guard break cost, and the full meter |
| `hype_inert` | | a fight with nothing to spend hype on hides the meter and pays nothing |
| `super_uppercut` | real time | the supercharged finisher: damage, the hype spend, a whiff and a fizzle keeping the hype, and the kill paths |
| `prompt_overlap` | | the hype meter gets out of the finisher prompt's way and comes back |
| `knockback` | real time | **(Eric)** the uppercut shoves him: distance per tier, always away from the player, never out of his bounds, and the longer pause before his next attack |
| `knockback_computah` | real time | a boss anchored to his own cycle rocks back on his sprite instead, and his phase floor and morph still work |
| `knockback_boss` | real time, `fight=mason\|jordan\|liam\|greyson_mech` | the same for the rest of the roster |
| `kill_shove` | real time, `fight=eric\|greyson_mech`, `tier=normal\|super` | a killing uppercut does not shove: the boss dies where he was hit, one outro, his defeat plays |

### Status effects and the lock

| mode | arguments | what it asserts |
| --- | --- | --- |
| `status` | | both effects apply and expire, a refresh resets rather than stacks, inverted movement inverts movement and nothing else, the drain empties the bar and can break a held guard, and a finisher clears them |
| `status_end` | `tier=death\|fight_over` | they come off when the player dies and when the fight ends, and nothing new sticks afterwards |
| `status_dialogue` | | the HUD row hides behind a dialogue balloon like the hype meter, and tidies up correctly if an effect expires while hidden |
| `locked` | | the parry-only lock: no movement, dash or punch, the guard and its parry untouched, the facing and the warp, and every way in and out of it |
| `locked_end` | `tier=death\|fight_over` | the lock releases on death and at fight end |

### Whole fights

| mode | arguments | what it asserts |
| --- | --- | --- |
| `smoke` | `fight=eric\|greyson\|carter\|mason\|jordan\|liam` | 45 s of a fight with the player standing still: every attack that lands is tagged, one half-heart per damaging hit, a second of i-frames after each, and nothing blocked, parried or dodged without input |
| `approach` | `fight=<as above>` | how long each attack is in the air before it lands, against `parry_window`. Anything whose flight is not clearly longer than the window can be parried by pressing the moment it appears, which is not a read; the mode fails and names them |

## Notes for whoever runs this next

- **One case per process where a fight ends.** `status_end`, `locked_end` and `kill_shove` take a
  `tier=` argument rather than looping, because `FightOutro` outlives the fight scene and a second
  fight in the same process meets the first one's leftovers.
- **The parry window is game time.** A parry's freeze slows the game clock, so waiting a number of
  *frames* after a press no longer clears the window. `past_window()` waits for the window itself;
  use it rather than a frame count when a test wants a plain block.
- **Eric gets parked** in the modes that only exercise the player's own rules (`park_eric()`), so his
  fight can change without those modes changing with it. The modes marked **(Eric)** deliberately do
  not park him.
- **A temporary driver node** named `ScratchEricDriver` in his fight scene is freed on load, so a
  debugging aid left in the scene cannot steer these runs.
- **Adding a fight:** append it to `SCENES` at the top and give it a spot in `SMOKE_SPOTS`; `smoke`
  and `blocks` then work on it. New attack ids need their block cost in `BLOCK_COSTS` or their id in
  `UNBLOCKABLE`, or `blocks` will report them as unexpected.
