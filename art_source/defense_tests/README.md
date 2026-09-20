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

Those modes are `super_uppercut`, `gamepad_mash`, `knockback`, `knockback_computah`,
`knockback_boss` and `mash_tiers_live`. Everything else is happy either way, `kill_shove` and the
juggle modes included: they're about what the finisher does, not the mash, so they switch the gate off.

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

Eric's pacing rework (`Scripts/EricPacing.gd`) switches his whole fight on `EricPacing.version`: V2
ships, and V1 is the fight as it was. The modes written against the old fight are pinned to V1
(`ERIC_V1_MODES` at the top of the script) whatever ships: `stagger`, `stagger_chain`, `stagger_win`,
`stagger_lose`, `knockback`, `kill_shove`, `auto_finisher`, `auto_kill`, `tells`, `grab_parry`,
`grab_block`, `parry_projectiles`, `block_eric`, `behind`, `dash_through`, `super_uppercut`,
`gamepad_mash`, `prompt_overlap`, and also `baseline`, `guard_break`, `guard_break_grab` and
`dodge_bosses`, which drive his real attacks through to V1's Downed. The rework's own modes are under
[Eric's reworked fight](#erics-reworked-fight-ericpacing-v2).

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
| `parry_streak` | | streaks count, pay `PlayerFeel`'s hype by tier (15 / 20 / 25 under Eric's `feel_v2`, 25 / 30 / 35 today), climb through the popups and the badge, sound identical every time, end on a hit or a guard break, lapse on their own, and lengthen the stagger window by 0.2 per tier over 2, capped at 0.4 |
| `parry_projectiles` | | **(Eric)** parrying his real projectiles on their way in, including a standing player parrying the sword as it dives into its landing spot: it is flung back, takes 1 off him, dazes him, and never plants, so there is no ring |
| `grab_parry` | | **(Eric)** his grab can only be answered with a parry: a held guard is still grabbed |
| `stagger` | | **(Eric)** the parry stagger, reached by parrying his sword toss: the reflect's damage, what the window opens, the hit cap, where he picks himself up |
| `stagger_chain` | | **(Eric)** his chain carries on after a parry stagger, whose length is `parry_stagger_time` plus the throw's own `reflect_stagger_bonus`: the uppercut ends the window, the window closes, and he is attacking again. Which attack that is comes from his own shuffle, since `end_recovery()` starts a fresh chain |
| `stagger_win` | | **(Eric)** the fight won during a parry stagger |
| `stagger_lose` | | **(Eric)** the fight lost during a parry stagger |
| `tells` | | **(Eric)** the red tell over his head during the wind-up of a parryable attack: his sword toss and his bear hug show one, his spin and his slam do not |

### Dodging

| mode | arguments | what it asserts |
| --- | --- | --- |
| `dodge_ring` | | a perfect dodge off a dash-through attack during dash immunity |
| `dodge_near` | | a perfect dodge off an attack that reaches the spot the dash started from, through the dodge ghost |
| `dodge_bosses` | | the dodge ghost's near-miss reporting across the roster's attacks |
| `dodge_rollout` | `fight=greyson\|carter` | dashing out of the way of a real attack in a real fight. Only these two fights have a readable approach for the bot; the greyson case still watches for the rockets boss 2 no longer has and needs repointing at Computah's pounce, so it is expected to fail |
| `dash_recovery` | | today's dash, with Eric's `feel_v2` switched back off: the lockout after a dash, no move, punch or dash, the guard may still go up, a parry cancels it, a plain block does not |
| `dash_spam` | | today's dash, `feel_v2` off: mashing dash covers less ground than walking |

#### feel_v2's dash

The reworked dash is behind the player's `feel_v2` flag, which only Eric's fight turns on (from
`BossOneScript`), so every mode above that loads Eric runs it. These modes pin it down; the old and new
numbers sit side by side in `PlayerDefense`.

| mode | arguments | what it asserts |
| --- | --- | --- |
| `dash_v2` | | all 8 directions dash the same 250 px, nothing held still dashes in place, a diagonal whose second arrow lands after the dash key in the same frame still counts; diagonals into every corner stop flush and walk back out, and along every rope they slide inside it; 4 afterimages copying his frame, tinted cool, evenly along the path, behind him and over the mat, one dust puff at his feet, the whoosh; they fade and free themselves, and 50 dashes leak no nodes; a hit-stop and a finisher's freeze hold them; every lock (the parry-only lock, a grab, talking, a finisher, a guard break) stops the dash with its effects and sound; every `dash_through` attack is still dodged |
| `dash_recovery_v2` | | the new timeline: 3 frames dashing, 5 standing still, then walking; a punch the first frame after; the guard inside it; a parry ends the landing and the cooldown; a plain block doesn't; mashed dashes 26 frames apart with nothing spent or flashed between; the finisher and a grab clear it |
| `dash_spam_v2` | | 6 s of mashing, and of a deliberate dash every 0.6 s, today against v2: dash rate, presses taken, how long dash immunity is up and how far it goes. v2 mashes at today's rate, never takes a press during a dash, is never immune for longer than today, and nothing keeps immunity up 35% of the time |
| `dash_legacy` | `fight=greyson\|mason` | a fight without `feel_v2`: today's dash frame for frame (250 px in 8 directions, 23 or 24 frames still, mashed 26 or 27 apart, the direction read on the press), with no afterimages, dust or whoosh |
| `dash_layers` | `fight=eric\|greyson\|mason\|josh\|carter\|liam\|jordan` | forces `feel_v2` on and checks every afterimage and puff on every frame as drawn: just before MainPlayer, behind him in the y-sorted fights and over the floor layers at y 101, over the mat in Eric's, and drawn where it belongs. `carter` here is the real Carter fight, not the old Carter & Josh scene |

#### feel_v2's punch

The same flag gives the punch a longer reach and its effects: `PlayerScript.PUNCH_HITBOXES_V2` beside
today's `PUNCH_HITBOXES` (each v2 box contains today's and reaches 6 px further), fitted as every swing
starts, and `PunchFx`'s swoosh, star and whoosh. The swoosh's full-extension frame is the v2 box drawn
out, so the art and the numbers change together (`art_source/punch_fx/`).

| mode | arguments | what it asserts |
| --- | --- | --- |
| `punch_reach` | `fight=eric` | against the real Eric, held down so his hurtbox is live: even the first punch gets the v2 box, though `feel_v2` comes on after the player is ready; in all 4 facings a plain hit and a hit 3 px past today's reach land and a whiff doesn't; the swoosh plays launch, full extension, afterimage on his own position and facing row, one whoosh a swing; a landed punch's star sits inside both the reach and his hurtbox and holds its first frame through the hit-stop; the charged third punch's star is gold; a grab mid-swing leaves nothing; `feel_v2` off gives today's box on the very next swing with nothing drawn or played; the swoosh sheet's full-extension frame spans exactly each v2 box's far edge and width and no frame leaves it; PunchFx has no SceneTree timers or tweens; and nothing of the punch is on screen when a charged punch's finisher freezes the fight |
| `punch_reach` | `fight=mason\|jordan\|...` | a fight without `feel_v2`: today's box exactly in all 4 facings, and PunchFx never draws or plays |
| `punch_contact` | | `feel_v2` lands a punch as the arm reaches full extension, today's once the boss's hurtbox reports it: f+16 against f+24 from the press; one resolve a swing either way, nothing waits on a report under `feel_v2`, the beat window opens and closes on `PlayerFeel`'s numbers (0.04 + 0.25 s against 0.05 + 0.35 s), and a `feel_v2` whiff ends the combo as its swing ends |

### Hype and the finisher

| mode | arguments | what it asserts |
| --- | --- | --- |
| `hype` | | what each action pays (`PlayerFeel`'s gains, by the player's `feel_v2`), what a hit and a guard break cost, and the full meter |
| `hype_inert` | | a fight with nothing to spend hype on hides the meter and pays nothing |
| `super_uppercut` | real time | the supercharged finisher: damage, the hype spend, a whiff and a fizzle keeping the hype, and the kill paths. On today's mash (Q and W): it turns off the `feel_v2` Eric's fight turns on |
| `gamepad_mash` | real time | today's mash, with Eric's `feel_v2` turned off (`verify_controls`' `eric_mash` covers his own keys): A and B fill the meter in the same presses and the same wall-clock time as Q and W, the alternation rule still refuses a repeat, the device follows the pad although the finisher swallows the presses, and the prompt swaps to pad keys only once the finisher has ended |
| `prompt_overlap` | | the hype meter gets out of the finisher prompt's way and comes back |
| `knockback` | real time | **(Eric)** the uppercut shoves him: distance per tier, always away from the player, never out of his bounds, and the longer pause before his next attack |
| `knockback_computah` | real time | a boss anchored to his own cycle rocks back on his sprite instead, and boss 2's near-death clamp clips the uppercut without spending the hype |
| `knockback_boss` | real time, `fight=mason\|jordan\|liam` | the same for the rest of the roster |
| `kill_shove` | `fight=eric`, `tier=normal\|super` | a killing uppercut does not shove: the boss dies where he was hit, one outro, his defeat plays |
| `auto_finisher` | `tier=normal\|super` | a fight handing the player the finisher (`begin_auto`): the entry guards, the daze, no prompt and no presses counted, the held beat, the same damage and hype spend as a mashed one, the knockback, the supercharged sound, and the input lock afterwards |
| `auto_kill` | | a handed-out finisher that kills: no shove, one outro, and nothing can be handed out after the fight is over |

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
| `smoke` | `fight=eric\|greyson\|carter\|mason\|jordan\|liam`, and for Eric `ver=1\|2` | 45 s of a fight with the player standing still: every attack that lands is tagged, one half-heart per damaging hit, a second of i-frames after each, and nothing blocked, parried or dodged without input; for Eric, every bear hug that finished inside the window squeezed three times, a hold still on at the cut-off not counting. Eric runs the pacing that ships unless `ver=` picks one |
| `approach` | `fight=<as above>`, and for Eric `ver=1\|2` | how long each attack is in the air before it lands, against `parry_window`. Anything whose flight is not clearly longer than the window can be parried by pressing the moment it appears, which is not a read; the mode fails and names them. `WINDUP_READS` holds the ones that radiate from the boss and so have no flight to give: they are judged on the wind-up before the hitbox exists, which only has to outlast the window itself |
| `clone_cadence` | | Carter's clone barrage against the parry window, modelled rather than run: pressing as a light comes up is too early, pressing on the dash parries, a bitten clone is only blocked, and a press at a feint costs the next clone unless `rearm_parry()` gives it back |

### Eric's reworked fight (EricPacing V2)

These load V2 whatever ships, and hold his Break gauge still wherever it isn't what is under test.

| mode | arguments | what it asserts |
| --- | --- | --- |
| `v2_cadence` | | **(Eric)** EricPacing's V2 numbers are the pacing plan's section 1; 56 health; 3 attacks a chain and 4 from 40% down; each attack's tell, at full health and enraged, leads by its own time and at or over its floor (slam 0.36, whirlwind 0.40, hug 0.45, sword toss 0.40) in the right colour; and whole chains timed: the gaps between attacks, the Winded window, open to punches and never dazed, and the rest after it |
| `delayed_slam` | | **(Eric)** over 16 slam attacks on a fixed seed: the fight's first slam attack never holds, no attack holds more than one slam, each hold is 0.20 or 0.35 s on frame 6, about 40% of the slams that can hold do, and every slam's standard red tell leads its waves by 0.36 s, held or not |
| `whirl_lunges` | | **(Eric)** the whirlwind's catalog entry; its yellow wind-up standing still, its lunges' count, length, speed and aim, its re-aims in place and its dizzy stop open to punches, at full health and enraged; then against the player's real dash, one dash from a standing start clears each lunge, straight, level and diagonal; and both lunges of one whirlwind, each dashed 3 or 8 frames ahead on straight, level and six diagonal paths, are cleared with the dashes at least `DashImmunity`'s 0.6 s apart, because a re-aim holds until the next lunge can't reach the player sooner than that (and a re-aim after a lunge that met them can run long) |
| `hug_mixup` | | **(Eric)** 14 hugs: the fight's first is red, never three of one colour in a row, both colours come up, each shows its own tell on the same charge, the yellow ring igniting once and then looping; red grabs through a held guard and a dash, a parry staggers it, and stepping out of its line whiffs it into the 0.7 s stumble; yellow lands for 1 through a guard and a parry, holds no one and always ends in the stumble, and a dash goes through it |
| `break_gauge` | | **(Eric)** what fills the Break gauge and what drains it, only for his own attacks; it holds 100, stops at 0 and never decays; its gauge on the top rope at (768, 93) (the placeholder's bar at (770, 96)), its fill in whole texels, pulsing from 80% with its hot fill in step and nothing brightening it on top; the Break empties it under the shatter and BREAK!; it takes nothing until 3 s after he gets up, or after the finisher that followed if that ends later; V1 has no gauge |
| `break_entry` | | **(Eric)** a Break from inside every attack, his windows and the gap between attacks stops it cleanly (hazards freed, sprite and animation speed restored, nothing left hitting); the Break frame; with the final art, his Broken sheet and his sword knocked into the mat on his first frame, at the Break spot in the world and behind him; no stars while he reels, then stars riding his head frame by frame; his open hurtbox and the snap-in beside him, on the side away from the sword and drawn in front of him; 3.0 s Broken (2.6 enraged), then he gets up on one knee, calls his sword from the mat into his hand and starts his next chain `recovery_rest` after the catch; a handed-out uppercut juggles him, and he crashes, gets up for his sword and attacks again the juggle's recovery after the crash; the opener starting the finisher, a fizzle leaving him Broken; the parried sword's +35 breaking him instead of its uppercut; and what can't break him |
| `mash_tiers` | | **(Eric)** the tiered mash, modelled on `FinisherTierMeter` with the finisher's own numbers at 60 fps: a press every 8, 6 and 5 frames reaches tiers 1, 2 and 3 and every 9, 7 and 6 doesn't; each pass and fail keeps 1.3 press intervals clear of its bar's window; the lowest steady rates are about 7.0, 9.4 and 10.9 a second; stopping after a bar keeps it, no press at all fizzles when bar 1's window runs out, and full hype banks bar 1 before the first press |
| `mash_tiers_live` | real time | **(Eric)** the same mash on real keys with the press gate on: the arrows every 5 frames bank all three bars without moving the player or raising their guard, and a key still held afterwards doesn't walk them off; one key over and over is one press; the bumpers every 6 frames bank two; Mason's fight still mashes punch and dodge |
| `juggle` | | **(Eric)** tier 3 through to his crash: three uppercuts 0.55 s apart dealing 8, 6 and 8 of 56, him in the air from the first to the last, peaks of 166, 210 and 309 px before they're fitted to his headroom, the player landing before he does, his recovery once as he crashes, then up for his sword |
| `juggle_kill` | `tier=1\|2\|3` | **(Eric)** the uppercut numbered `tier` kills him: none follows, one outro, no shove, and he finishes his fall and crash before lying there beaten |
| `juggle_super` | | **(Eric)** a full hype meter: bar 1 banked before the first press, tier 2 at bar 2's rate, the last uppercut 0.10 more (8 and 11), the hype spent once |
| `reflect_auto_v2` | | **(Eric)** his parried sword flung back into him: from an empty gauge, a tier-1 juggle with no prompt (his sword's 1 and the uppercut's 8), the gauge at 50, and him up for the sword the uppercut knocked away; from 50, a Break and no juggle |
| `pace_bot` | `tier=skilled\|average` | **(Eric)** a tuning aid, not a gate, and not in the default run: a bot plays V2 to the end, answering each attack as its tell says, punishing his windows and cashing Breaks in (skilled: 95% of reads, full combos, tier 3; average: 65%, two-punch combos, tier 1), and logs the fight's length, Breaks a chain, the tiers reached, where the damage came from and the hits it took. The player can't die |
| `y_sort_eric` | | his fight y-sorts like the other six: he sorts at his feet and draws where he always did, a player in front draws over him and one behind under him, the waves, ring, dust and the flying sword's shadow lie on the floor layer under both, the swords sort at their ground points, and a tell draws over the ropes |
| `pause_basic` | | **(pause screen)** every fight carries one and a live fight can open it; Escape stops the fight dead - 40 paused frames move nothing, a held direction, the boss, both healths, stamina, the fight's own clock, a running Timer's time left and the music's playback position all included - and Escape again brings it all back where it was, at `time_scale` 1, with the clock running again and the music picking up rather than restarting; and the window losing focus opens it on its own, while getting focus back does not resume |
| `pause_hitstop` | | **(pause screen)** a hit-stop is the one kind of timer that would run through a pause: paused inside one, `time_scale` stays at 0.05, 60 paused frames take nothing off the stop's time left, and it runs out normally after the resume |
| `pause_freeze` | | **(pause screen)** the finisher's `FightFreeze` keeps the player's branch running under a disabled scene; pausing has to reach that branch too: 40 paused frames don't move a player who was walking under the freeze, the freeze survives the resume, and it still unfreezes |
| `pause_mash` | real time | **(pause screen)** paused mid-mash, six presses over 24 paused frames don't move the meter, the phase and the alternation latch are kept, and the mash still finishes the uppercut afterwards |
| `pause_barrage` | | **(Carter)** paused inside the Raging Demon's rush: the barrage's own clone clock and clone index stop, no clone moves over 40 paused frames, and it carries on from there |
| `pause_dialogue` | real time | **(Eric)** pre-fight banter is deliberately pausable; the same line is still up after the resume and the balloon's real-clock input lock was re-armed, so the resuming press can't advance it |
| `pause_no_leak` | real time | **(pause screen)** opening and closing never reach the fight: a keyboard round trip throws no punch, raises no guard, sends no block press and no dash; on a pad Start opens it, A on RESUME closes it and neither that accept nor four more A presses inside the resume grace punch, B closes it and neither that cancel nor four more B presses dash; and a guard held across the pause is still up on the other side |
| `pause_blocked` | | **(pause screen)** `fight_over`, the `leaving` flag and a `FightOutro` under the root each block it and Escape does nothing; `MainScene.tscn` carries the layer but is inert there |
| `pause_restart` | | **(pause screen)** RESTART FIGHT from a frozen, zoomed fight in a hit-stop: the confirm row comes up with BACK holding focus, the fight reloads unpaused at `time_scale` 1 with the canvas transform back to identity and both healths full, and the next finisher can still freeze the fight - the proof that `FightFreeze.frozen`, which is static, did not leak |
| `pause_quit` | | **(pause screen)** QUIT TO MAIN MENU confirmed with accept held down and mashed through the scene change: the fight quits unpaused at normal speed, nothing on the main menu has focus while it fades in so none of those presses starts a new game, and once it is up NEW GAME takes focus and a press does |
| `vs_card` | real time, `fight=` | **(VS card)** the card between a fight's pre-fight lines and the fight: it plays once per entry and runs its full length, the player is still held and the fight's post-dialogue timer is still stopped under it, the pause screen is refused while it is up, the same fight entered from the boss select with no line read still plays it, a punch press skips it to the flash without that press or the mash after it punching or dashing, the next press after the grace does punch, and Escape skips it rather than pausing. `fight=` is a key of `VsCardArtLayout.CARDS`: eric, greyson, mason, josh, carter, liam, jordan |
| `entrance` | real time | **(Eric)** his boss entrance: the ring opens on his planted sword, both fighters walk in, the gates slam, and nothing in the fight runs under any of it; a press during it never punches or dashes; his lines call `pull_sword()` and `point_at_player()` as beats; the player has their own state machine back before the VS card takes the hold; a tapped Escape pauses it and a held one skips it, leaving the ring set and the lines started; paused mid-pull his frames stop with the fight, and paused mid-line the fight still starts; and a second entry in the same run does not play it again |

## Notes for whoever runs this next

- **The pause screen's timing rules.** `SceneTree.paused` is what a pause is, so anything in fight
  code that must stop with the fight has to be pausable: Timer nodes, `_physics_process`
  accumulators and node-bound tweens are, and `get_tree().create_timer(t)` is not until its second
  argument (`process_always`) is passed as false. `Engine.time_scale` is never used to pause.
- **The resume grace is 0.15 *real* seconds**, so the modes that have to see it running or run out
  (`pause_no_leak`, `pause_mash`, `pause_dialogue`, `vs_card`) run with `--max-fps 60`; under
  `--fixed-fps` a frame costs no real time and the grace would still be open at the end of the mode.
- **Eric's fight opens on a boss entrance** (`EricIntro`), which holds the player, walks both
  fighters in and only then starts his lines - so his `dialogue_ended` no longer fires seconds after
  the scene loads. `load_fight()` and `load_quiet()` cut it the way a held `ui_cancel` does before
  they end the dialogue; only `entrance` lets it play.
- **The VS card plays on every fight entry**, between the pre-fight lines and the fight, and holds
  the player until it is done. `load_fight()` skips it the way a player does and then waits its own
  0.15 real second input grace out, so every other mode starts on a fight that is already running
  and reads every press it makes. Only `vs_card` lets it play.
- **One case per process where a fight ends.** `status_end`, `locked_end` and `kill_shove` take a
  `tier=` argument rather than looping, because `FightOutro` outlives the fight scene and a second
  fight in the same process meets the first one's leftovers.
- **The parry window is game time.** A parry's freeze slows the game clock, so waiting a number of
  *frames* after a press no longer clears the window. `past_window()` waits for the window itself;
  use it rather than a frame count when a test wants a plain block.
- **Eric gets parked** in the modes that only exercise the player's own rules (`park_eric()`), so his
  fight can change without those modes changing with it. The modes marked **(Eric)** deliberately do
  not park him. Parking also holds his Break gauge (V2), so a run of parries can't break him mid-test.
- **Eric's V2 attacks start in the idle step** (`attack_v2()`), as his rest timer starts them in the
  game: a state entered during a physics step counts one of its wind-up's frames in the same step.
- **A temporary driver node** named `ScratchEricDriver` in his fight scene is freed on load, so a
  debugging aid left in the scene cannot steer these runs.
- **`clone_cadence` mirrors Carter.** Its `CLONE_SHOW`, `CLONE_DASH`, `CLONE_GAP` and
  `CLONE_LIGHT_OUT` are copies of `CarterStateMachine`'s `clone_show`, `clone_dash` and `clone_gap`
  and of `CarterArtLayout.CLONE_LIGHT_OUT`, **and must be changed in the same pass as those**. The
  mode reads the real values off his fight when it is in the build and fails if the copies have
  drifted, so a model of a tighter barrage than he ships cannot hide a problem; the copies are only
  what it falls back to in a build without him.
- **Adding a fight:** append it to `SCENES` at the top and give it a spot in `SMOKE_SPOTS`; `smoke`
  and `blocks` then work on it. New attack ids need their block cost in `BLOCK_COSTS` or their id in
  `UNBLOCKABLE`, or `blocks` will report them as unexpected.
