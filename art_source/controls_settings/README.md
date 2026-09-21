# Controls test suite

Headless checks on controller support and the rebindable controls: the input map, the
`InputSettings` autoload's bindings and their file, the 8-way stick, which device the prompts follow,
and every screen that shows a control.

Everything lives in `verify_controls.gd`. It runs one mode per process, prints a `P PASS` or `P FAIL`
line per check, ends with `RESULT mode=<name> fails=<n>` and exits with that failure count. An
unknown mode counts as a failure.

Input goes in as real events through `Input.parse_input_event()`, so what is under test is the path
the game uses. Plugging a pad in and out is simulated by emitting `Input.joy_connection_changed`,
which is exactly what the engine does.

**No run changes the real controls.** Every mode points `InputSettings.save_path` at
`user://input_bindings_test.cfg` before anything changes a binding, resets to the defaults and
deletes that file at the end, so the bindings of whoever is playtesting from this checkout are never
read into a result or overwritten. The one write the real file can get is the one booting the game
gives it anyway: a first run, a repair, or moving a version 1 file onto the current version. The
defence suite (`art_source/defense_tests`) does the same with its own scratch file, because its
presses assume the default keys.

## Running it

```sh
Godot.exe --headless --fixed-fps 60 --path . \
  --script res://art_source/controls_settings/verify_controls.gd -- mode=defaults
```

All of them:

```sh
for m in defaults rebind persist move_vector device screens training rebind_screen handoffs pause_input pause_controls; do
  Godot.exe --headless --fixed-fps 60 --path . \
    --script res://art_source/controls_settings/verify_controls.gd -- mode=$m | grep 'FAIL\|RESULT'
done
```

`outro_mash` and `eric_mash` need real time instead, because the finisher's presses and the outro's
input lock are both timed on the wall clock. `outro_mash` ends a fight, so it runs one case per
process:

```sh
for p in a ab deliberate; do
  Godot.exe --headless --max-fps 60 --path . \
    --script res://art_source/controls_settings/verify_controls.gd -- mode=outro_mash press=$p | grep 'FAIL\|RESULT'
done
for d in keyboard pad; do
  Godot.exe --headless --max-fps 60 --path . \
    --script res://art_source/controls_settings/verify_controls.gd -- mode=eric_mash device=$d | grep 'FAIL\|RESULT'
done
```

Today's mash on attack and dash (Q and W, A and B), which a fight opted out of `feel_v2` keeps, is
checked from the defence suite, where the fights are set up, as `gamepad_mash` and `super_uppercut`
(real time, `--max-fps 60`, like its other mash modes), with `feel_v2` turned off for them.

## Modes

| mode | what it asserts |
| --- | --- |
| `defaults` | every action has exactly one key and one pad binding, and they are the defaults (Q/A, W/B, Shift/LB, arrows plus the d-pad and the left stick); `project.godot` and `InputSettings.DEFAULTS` agree; `project.godot` writes no `ui_*` action; every `ui_*` action keeps all of its built-in events and only ever gains pad events; A confirms and B cancels; the feel_v2 mash pair is registered (the arrows, LB and RB), named and drawn, and kept out of the rebindable list and the file |
| `rebind` | rebinding one side leaves the other byte-identical, in the bindings and in the input map; a trigger binds as an axis and blocks when pulled; a conflict unbinds exactly the loser and nothing else; movement's pad side, the d-pad and the sticks can't be bound to anything; every change is on disk at once; reset |
| `persist` | save, clear and load gives back the same bindings and the same input map, trigger and unbind included; a missing file writes the defaults; a truncated file keeps what it can and is rewritten whole; a file that doesn't parse falls back to the defaults and is rewritten; a version it doesn't know falls back wholesale; a version 1 file whose pad was never changed (X, RB, LB) moves onto A, B, LB with its keyboard kept, one whose pad was changed is kept exactly, and a current file holding X, RB and LB is a choice and is kept; a key of 0 or a missing action falls back on its own |
| `move_vector` | all 16 combinations of the arrow keys read byte for byte as the game's old `ui_*` read did; the stick full over in 8 directions; every direction, and the angles between them, starts moving at the same push; half a degree either side of each 22.5° boundary snaps to the nearer direction; a (0.7, 0.7) corner is exactly two arrow keys, so the dash off it is as long; the d-pad; the dead zone |
| `device` | a pad press, a key press, a mouse click and a real stick push each switch the device; key echoes and releases, stick and trigger drift at 0.3 and mouse motion don't; plugging a pad in switches at once, unplugging the last one switches back; `device_changed` fires exactly once per real change |
| `screens` | the Controls screen keeps its hand-drawn keys on the keyboard's defaults and swaps all four cards, and the Move title, the moment a pad is plugged in, unplugged or touched; rebound and unbound keys; the ready button takes focus; all six of Danny's lines on the keyboard, on a pad (buttons drawn inline) and after a rebind, his mash line naming Eric's keys (LEFT and RIGHT, LB and RB), his last line handing the training room over (the dummy, the post, that nothing in there can kill you, and both ways out); a pad line with glyphs in it typing out whole in the real balloon, one spoken letter per character; the intro's skip hint and B skipping it; the main menu's focus chain on a pad (NEW GAME, CONTROLS, VOLUME, the boss select), nothing holding focus until it has faded in so an accept still held from the screen that led here presses nothing, the focus showing only on a pad, A opening the rebind screen; the victory and defeat buttons taking focus only once their screen has faded in, so an A still being mashed as the fight ended presses nothing |
| `training` | the training room the Controls screen becomes once Danny is done: his last line opens it, the player is freed and put on `feel_v2`, the dummy starts as a bag and the room has the `GroundFx` layer the finisher looks for; the card wall fades to 0.15 after a bout of practice and comes back a beat after it stops, and a finisher takes it out at once (its zoom throws the dummy to screen y 127, behind a card) - through both of those the Ready button, which lives in the sibling group nothing fades, holds full drawn alpha; three punches charge the combo and daze the dummy, and because it can be juggled the prompt is the three-bar tiered one on `mash_left`/`mash_right`; an unmashed prompt fizzles and hands the room back. Health driven to 0 every frame is floored at 1 before `PlayerScript`'s death check reads it, so no `FightOutro` is ever started (it would crash: its `PLAYER_PATH` is not a node this scene has) and the room stays the scene. Sparring, the dummy winds up and swings. On a pad the Ready button drops focus and wears the Y glyph (column 3 of the pad sheet) instead, so eight A presses punch the dummy and never launch the fight while Y confirms straight into it; on the keyboard the button takes its focus back and drops the glyph; and the Arena #1 doorway still works as the second way out. Note for whoever extends this mode: unplugging the last pad INSIDE a fight opens the pause screen, and a paused tree survives a scene change, so the room would load with its physics stopped |
| `rebind_screen` | the table; Enter and A open a cell without becoming its binding; a key and a button bind and show at once; B binds on a pad cell (it is dash's default) and can be put back on dash from the pad alone; pressing the button a cell already has keeps it; sticks and the d-pad are refused with a notice, a trigger is taken; Esc cancels a pad cell, Esc or B a key cell, without leaving; a conflict shows the loser unbound and says so, and the notice fades; focus across the table; reset; the hint following the device; B going back when nothing is listening |
| `eric_mash` | real time, `device=keyboard\|pad`: the fight is on `feel_v2`, so the finisher mashes on its own pair, `mash_left` and `mash_right` (the arrows, LB and RB). The prompt shows those keys, lit in turn, and swaps with the device; attack and dash don't fill the meter; real presses of the pair mash it to an uppercut that lands. Through the mash the player never moves, the guard never goes up and no block reaches the defence to credit a parry. After it, with the last key still held, the release latch keeps them from walking or guarding: it ends at once when the key is let go (a fresh LB then guards and counts as a press), or at 1 s with the key still down (the arrow then walks them) |
| `outro_mash` | real time, `press=a\|ab\|deliberate`: A punches Eric dizzy, the finisher's own pair (LB and RB in his fight) mashes the uppercut into the kill, which the mode checks happened, and the outro that follows still shows each of his lines for at least 1.2 s (the requirement, written into the test rather than read from `FightOutro`). With `ab`, B skipping the typing can't happen inside that time, and a line it reveals stays up 1.2 s again. With `deliberate`, a skip pressed early is eaten, on the pad and on the keyboard alike, and a press once the time is up moves on at once |
| `handoffs` | in Eric's fight with its real pre-fight dialogue, on a pad: B skips the typing and A reads the lines through, and none of those presses, the one closing the last line included, punches or dashes; afterwards nothing has focus; in the fight A punches, and B dashes and never pauses, quits or backs out |
| `pause_input` | the `pause` action exists with exactly one key (Escape, as a physical position) and one button (Start); it is not in the rebindable list, `rebind()` refuses it and nothing about it is written to the file; `pause_name` is ESC on a keyboard and the sheet's column-13 Start glyph drawn inline on a pad; in Eric's fight B (which is `ui_cancel` and the dash) never opens it, Start does and closes it again, unplugging the last pad opens it on its own, Escape opens and closes it, and none of that leaves the fight |
| `pause_controls` | the rebind screen hosted inside the pause screen: CONTROLS opens it in embedded mode over a still-paused fight, attack rebinds to Z from inside it with its pad side untouched, its own backdrop is dropped so the paused fight shows through the pause dim behind it, Back returns to the pause rows (not to the main menu) with focus back on the row that opened it and the screen freed, and after the resume Z punches and Q, which it used to be, does not |

## Notes for whoever runs this next

- **Danny's lines are compiled from the `.dialogue` source**, the way the importer compiles them,
  because a headless run doesn't import. If the imported copy is older than the source, `screens`
  logs a note saying so; the open editor reimports it on its next scan, and before every play.
- **The stick is measured by how far it is pushed, then snapped by angle** to the nearest of the 8
  directions, so every direction starts moving at the same push: 52% of a full one
  (`InputSettings.MOVE_THRESHOLD`, 0.4 of the engine's vector after its 0.2 action dead zone). The
  plan's first version thresholded each axis on its own, which left a diagonal push reading as
  centred until 65%. Whether 52% feels right is for the human test; it is the one number to tune.
- **A punch or a dash rebound to a trigger makes the finisher mash slower**: a trigger has to be let
  back out past the action dead zone before it can press again. The player chose it, and the
  rebind screen shows it, but it is worth knowing if a mash complaint comes in.
- **The glyph sheets' columns are ours**, not Godot's `JoyButton` order: `InputSettings.PAD_BUTTON_FRAMES`
  maps one to the other, and anything unrecognised draws as the "?" in column 12. Start is column 13.
  A column added to the sheets means `hframes` in `ControlsArtLayout.FINAL_PAD_GLYPHS` and in
  `FinisherArtLayout.FINAL_PAD_KEYS` (whose lit look is a whole row on, so it moves with it), in the
  same change.
- **Danny's dialogue draws pad buttons inline.** An inline image is one character to a RichTextLabel,
  typed as a space, so the typing and the voice blips carry on over it; `screens` checks that on a
  real line. The face buttons come from the 11 px set at 3x; LB, RB, LT and RT don't read at that
  size, so they come from the 32 px sheet at 1:1 (`ControlsArtLayout.INLINE_FALLBACK_COLUMNS`). The
  stick has no inline cell, so movement stays named.
