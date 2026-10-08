# Enter the Discord: All Game Text

Compiled 2026-10-07. Every piece of text a player can see, 490 entries in play order, with 90 flags marked for a look.

- Lines are copied exactly as the game has them, typos included.
- **Speaker:** line = dialogue. "TEXT" = words the game writes on screen. *Italics* after a dash = when it shows.
- "Drawn in art" = words inside an image: changing one means redrawing that file.
- Indented **Flag** / **Check** / **Note** lines are things to look at. A summary of all flags is at the end.
- Progress saving is still being built, so the CONTINUE text may still change.

Tell me which lines to change (quote the old line and give the new one) and I'll make the edits in the game.

## Main menu, boss select, pause, controls and volume, the HUD and the generic popups

### Main menu (the screen the game boots into)

- Drawn in art: "ENTER THE ... DISCORD (the logo: a speech bubble 'ENTER THE' + '...', then a big 'DISCORD' whose O is a Discord-style avatar with a red '1' notification badge)" (file: main\_menu\_title.png)
- Drawn in art: "INVITE (a padlocked invite card at the top of the boss tower); the tower's tiers carry numbered banners 1-9" (file: main\_menu\_bg.png)
- "CONTINUE" — *button above NEW GAME, only when the save has a run to pick up (progress saving - being added on 2026-10-07 while this list was compiled, so check it again once it lands)*
- "VS %s" — *small caption under CONTINUE: where the run resumes, e.g. 'VS CARTER' (the ladder name, so 'VS BURAK' for Captain Burak)*
- "VS GREYSON" — *caption when the save is at Greyson's half of Fight 6*
- "VS LIAM" — *caption when the save is at Liam's half of Fight 7*
- "THE FINALE" — *caption when the save is in Jordan's room*
- "VS GOD JORDAN" — *caption when the save is at the god fight*
- "NEW GAME" — *button*
- "START OVER? / YOUR PROGRESS WILL BE LOST." — *question box (two lines) when NEW GAME is pressed over a saved run*
- "BACK" — *question box button*
- "START OVER" — *question box button*
- "CONTROLS" — *button - opens the Controls screen*
- "VOLUME" — *label over the volume slider*

### Boss select (playtest panel under the volume slider)

- "BOSS SELECT (PLAYTEST)" — *panel title*
- "INVINCIBLE" — *tick box: player takes no damage*
- "1  BURAK / 2  MASON / 3  JOSH / 4  ERIC / 5  DANNY / 6  COMPUTAH / 7  LIAM & BIXBY / 8  CARTER / 9  MATT / 10  JORDAN" — *one button per fight, '\<number\>  \<name\>' (two spaces); names from Scripts/GameProgress.gd:15-24*
- "    GREYSON" — *extra row under 6, starts at Greyson's takeover (leading spaces are an indent)*
- "    LIAM" — *extra row under 7, starts at Liam's takeover*
- "    FINALE" — *extra row under 10, starts at Jordan's KO (his finale)*
- "    GOD" — *extra row under 10, the god fight*
- "    ENDING" — *extra row under 10, the champion ending + credits*
- "%s hasn't been built yet" — *hover tooltip on a greyed-out row; %s is a file path*
    - **Note: never shown in the game.** Every row is built today, so this tooltip never shows (and it would show a raw file path).

### Pause menu (Esc / Start in any fight)

- Drawn in art: "PAUSED  +  '@newcomer idle in \#arena-1' (small grey subtitle under it)" (file: pause\_title\_3x.png) — *the pause screen's title is this image*
    - **Flag: drawn into art, can't follow the game.** The subtitle always says \#arena-1, whichever fight you pause in (the Defeat screen's text uses the real number).
- "PAUSED" — *text title, only used if the art above is switched off*
- "RESUME" — *row*
- "RESTART FIGHT" — *row*
- "CONTROLS" — *row - opens the Controls screen over the fight*
- "VOLUME" — *label over the volume slider*
- "QUIT TO MAIN MENU" — *row*
- "RESUME" — *footer hint, followed by the pause key (ESC) or the Start glyph*
- "BACK" — *footer hint, followed by ESC or the B glyph*
- "START THIS FIGHT AGAIN?" — *confirm box after RESTART FIGHT*
- "LEAVE THE FIGHT AND GO BACK TO THE MAIN MENU?" — *confirm box after QUIT TO MAIN MENU*
- "BACK" — *confirm box button*
- "CONFIRM" — *confirm box button*

### Controls screen (rebinding; from the main menu or the pause menu)

- Drawn in art: "ARENA \#1 (banner over the locker-room door in the background)" (file: controls\_bg.png)
- "CONTROLS" — *screen title*
- "ACTION" — *table header*
- "KEYBOARD" — *table header*
- "GAMEPAD" — *table header*
- "MOVE UP" — *table row name*
- "MOVE DOWN" — *table row name*
- "MOVE LEFT" — *table row name*
- "MOVE RIGHT" — *table row name*
- "ATTACK" — *table row name*
- "DASH" — *table row name*
- "PARRY" — *table row name*
- "LEFT STICK / D-PAD" — *gamepad cell of the four MOVE rows (not rebindable)*
- "PRESS A KEY" — *a keyboard cell while it waits for a key*
- "PRESS A BUTTON" — *a gamepad cell while it waits for a button*
- "ENTER: CHANGE    ESC: BACK    (ESC CAN'T BE BOUND)" — *hint line, keyboard*
- "A: CHANGE    B: BACK" — *hint line, gamepad*
- "ESC: CANCEL" — *hint line while listening, keyboard*
- "B: CANCEL" — *hint line while listening, gamepad*
- "SAME BUTTON: KEEP IT    ESC: CANCEL" — *hint line while listening on a gamepad cell*
- "CONTROLS RESET TO DEFAULTS" — *notice after RESET TO DEFAULTS*
- "STICKS AND THE D-PAD CAN'T BE BOUND" — *notice when a stick or d-pad is pressed on a gamepad cell*
- "%s WAS ON %s, WHICH IS NOW UNBOUND" — *notice when a new binding steals a key: '\<KEY\> WAS ON \<ACTION\>, ...'*
- "RESET TO DEFAULTS" — *button*
- "BACK" — *button*
- "A / B / X / Y / BACK / GUIDE / START / L3 / R3 / LB / RB / D-PAD UP / D-PAD DOWN / D-PAD LEFT / D-PAD RIGHT / LT / RT" — *gamepad button names, written where no glyph art is drawn*
- "ESC" — *the Escape key's name; other keys use the system's name in capitals (Q, W, SHIFT, LEFT, RIGHT ...)*
- "—" — *an unbound cell*
- "BTN %d" — *an unknown pad button's name*
    - **Note: never shown in the game.** Fallback only.
- "AXIS %d" — *an unknown pad axis's name*
    - **Note: never shown in the game.** Fallback only.
- "LEFT STICK" — *what 'move' is called on a gamepad (fills {{move\_name}} and the kegs hint)*
- "ARROWS" — *what 'move' is called on the default keyboard keys*
- Drawn in art: "Q, W, SHIFT and the four arrow keys (key caps)" (file: key\_q.png) — *also key\_w.png, key\_shift.png, key\_arrows.png - the training-room cards*
- Drawn in art: "A, B, X, Y, LB, RB, LT, RT, START, d-pad and stick (button glyphs)" (file: pad\_buttons\_3x.png) — *the gamepad glyph sheets in Assets/UI/Pad/*

### Dialogue box

- "Speaker names as written in the dialogue files: Burak, Captain Burak, Danny, Mason, Josh, Eric, Computah, Greyson, Liam, Bixby, Carter, Matt, Jordan, Aiden, ???" — *shown in the name tab over each line*

### Hold-to-skip hint (every boss entrance, cut-in, takeover, the finale and the champion ending)

- "Hold ESC: skip" — *keyboard*
- "Hold B: skip" — *gamepad*

### VS card pieces shared by every fight

- Drawn in art: "VS" (file: vs.png)
- Drawn in art: "FIGHT 01 ... FIGHT 10" (file: fight\_01.png) — *one plate per number, fight\_01.png to fight\_10.png*
- "VS" — *text VS, only if the art is switched off*
- "FIGHT %02d" — *text 'FIGHT 01', only if a plate is missing*
- "WIN %s" — *text 'WIN @rank', only if a plate is missing*
- "CHALLENGER" — *name for a fight with no card entry*
    - **Note: never shown in the game.** Every fight has a card entry today.

### HUD words

- Drawn in art: "HYPE (label on the player's hype meter, bottom right)" (file: hype\_label\_3x.png)
- "HYPE" — *text version of HYPE, only if the art is off*
- "%d HIT" — *over the player's head after a landed punch: '1 HIT'*
- "%d HITS" — *'2 HITS' ...*
- "%d POW!" — *the third, charged punch: '3 POW!'*
- Drawn in art: "x2, x3 ... (flame badge with the parry-streak count)" (file: streak\_badge\_3x.png) — *digits from streak\_digits\_3x.png*
- "PARRY x%d" — *text streak counter, only if the badge art is off*
- Drawn in art: "BREAK! (when a boss's Break gauge fills)" (file: break\_text\_3x.png)
- "BREAK!" — *text BREAK!, only if the art is off (same in CarterArtLayout.gd:816)*
- Drawn in art: "Boss name plates on the health bar: BURAK, MASON, JOSH, ERIC, DANNY, COMPUTAH, GREYSON, LIAM & BIXBY, LIAM, CARTER, MATT, JORDAN" (file: boss\_plate\_name\_burak\_3x.png) — *one file per boss, boss\_plate\_name\_\<boss\>\_3x.png; the text fallbacks are the names in Scripts/GameProgress.gd:15-24 (plus GreysonScript.gd:42, LiamScript.gd:34)*

### Generic popups over the player

- Drawn in art: "PARRY!" (file: popup\_parry\_3x.png) — *a parry (text fallback DefenseHypeArtLayout.gd:541)*
- Drawn in art: "PARRY x2" (file: popup\_parry\_x2\_3x.png) — *second parry in a row (fallback :546)*
- Drawn in art: "PARRY x3+" (file: popup\_parry\_x3\_3x.png) — *third or more in a row (fallback :547)*
- Drawn in art: "PERFECT!" (file: popup\_perfect\_3x.png) — *a perfect dodge (dash through an attack) (fallback :542)*
- Drawn in art: "HYPE!" (file: popup\_hype\_3x.png) — *the hype meter fills (fallback :544)*
- Drawn in art: "GUARD BREAK!" (file: popup\_guard\_break\_3x.png) — *(fallback :543)*
    - **Note: never shown in the game.** Blocking is switched off (PlayerDefense.BLOCKING\_ENABLED = false), so the guard can't break and this never shows.
- "TIRED!" — *written word: a dash or parry refused for lack of stamina*
- "STUCK!" — *written word: Danny's worms root you (Fight 5 only)*
- "HELD!" — *written word: Danny's belly bump parried (Fight 5 only)*
- "DRAINED!" — *written word: a stamina-drain status*
    - **Note: never shown in the game.** No attack applies a status effect today (nothing calls apply\_status).
- "REVERSED!" — *written word: an inverted-controls status*
    - **Note: never shown in the game.** No attack applies a status effect today.

### The finisher (dazed boss) and other mash prompts

- Drawn in art: "MASH!" (file: qte\_mash\_text\_3x.png) — *under the mash meter (text fallback FinisherArtLayout.gd:260)*
- Drawn in art: "FULL!" (file: qte\_full\_text\_3x.png) — *the meter is full (fallback :261)*
- Drawn in art: "1!  /  2!!  /  3!!!" (file: qte\_tier\_1\_3x.png) — *a bar banked on the three-bar mash (qte\_tier\_1/2/3\_3x.png; fallback FinisherArtLayout.gd:354)*
- Drawn in art: "MAX. UPPERCUT!" (file: knight\_breaker\_3x.png) — *all three bars banked; renamed from KNIGHT BREAKER! on 2026-10-07, the file keeps the old name (fallback FinisherArtLayout.gd:372)*
- "RESIST!" — *written mash word for Matt's Deafening Yell (Fight 9)*
- "ESCAPE!" — *written mash word for being held; only Computah's mine trap and catch use it - flagged under Fight 6*
- "CHARGE!" — *written mash word*
    - **Note: never shown in the game.** Nothing asks for CHARGE! today.

## The intro cutscene (NEW GAME)

### The street

- "ESC: skip" — *corner hint, keyboard (also Scenes/Core/IntroCutsceneScene.tscn:164)*
- "B: skip" — *corner hint, gamepad*
- Drawn in art: "\#GENERAL STORE, 'afk' (graffiti on the shutter), CLOSED, NOODLES (neon, flickers), KEEP OUT, LAUNDRY, PAWN SHOP, BRB, LOST, LIVE, SALE, MEMBERS WANTED / ARENA \#1 (poster), CHAT CAFE, CLOSED" (file: street\_buildings.png) — *shop signs and posters along the street (the NOODLES flicker is sign\_flicker.png)*
- *(Burak walks in, gloomy.)*
- **Burak:** (Another server ghosted me... nobody wants a newcomer.) — *a thought, in brackets*
- *(He stops at the poster wall; close-up of the poster.)*
- Drawn in art: "@everyone / MEMBERS WANTED / TRYOUTS AT / ARENA \#1 / Earn your invite / \#tryouts (on every tear-off tab)" (file: poster\_closeup.png)
- **Burak:** (Members wanted? Tryouts at the arena...)
- **Burak:** ("Earn your invite." Huh.)
- **Burak:** (...Alright. I'm in.)

### Danny at the sign-up desk (the screen after the street)

- Drawn in art: "ARENA \#1 (two banners)" (file: DannyIntro\_pixel.png)
- **Danny:** Sup. I'm Danny. Here to join fart male white orgy? — *the first thing anyone says to Burak; then the training room loads*

## Fight 1: Captain Burak (win: @member)

### Pre-fight

- **Captain Burak:** Ahoy, newcomer! Welcome aboard the server.
- **Burak:** ...who are you supposed to be?
- **Captain Burak:** Captain Burak. Best-dressed member this server's ever seen.
- **Burak:** Captain? It's a Discord server.
- **Captain Burak:** And every server needs a captain. Want your @member rank? Get past me first.
    - **Check: mentions the ladder, probably still fits.** Names the @member rank - still right: Fight 1 pays @member.
- *(He fires a warning shot.)*
- **Captain Burak:** Hah! Relax, kiddo. I'll go easy on ya.

### VS card

- Drawn in art: "FIGHT 01" (file: fight\_01.png)
- Drawn in art: "BURAK" (file: name\_burak.png) — *name plate*
- Drawn in art: "THE CAPTAIN" (file: epithet\_burak.png) — *epithet under the band*
- Drawn in art: "WIN @member" (file: win\_member.png) — *what the win pays*

### Health bar

- Drawn in art: "BURAK" (file: boss\_plate\_name\_burak\_3x.png) — *the bar's name plate (the VS card and plate say BURAK, his lines say Captain Burak)*

### Mid-fight hints (each once per fight, across the top of the screen)

- "TAP %s AS THE SHOT HITS TO PARRY!" — *his first flintlock shot; %s = the parry key (SHIFT / LB)*
- "PUNCH THE BARRELS BEFORE HE'S LOADED!" — *his first keg volley lands*
- "DASH (%s) BETWEEN BARRELS!" — *a keg volley in his later phase; %s = the dash key (W / B)*
- "YOU CAN'T OUTRUN HIM! DASH (%s) THROUGH THE SWING OR TAP %s TO PARRY" — *his cutlass wind-up; first %s = dash key, second = parry key*
    - **Flag: typo or punctuation.** No closing '!' - every other hint in the game ends with one.

### Laugh cut-in

- *(He bursts out laughing.)*
- **Captain Burak:** ...pfffft.... hahahahaha! I've never seen someone get hit by all 5 barrels! Hahahahaha! Danny did you see that? — *Danny heckles from ringside*
    - **Check: mentions the ladder, probably still fits.** Mentions Danny (met in the training room, fought in Fight 5) - still fits.
    - **Flag: typo or punctuation.** 'Danny did you see that?' has no comma after Danny.
- **Danny:** .... — *his ears are ringing*
- **Captain Burak:** Let's get back to it! C'mon kiddo! Think!

### End of fight

- **Captain Burak:** Ow! Okay, okay... you've earned your stripes, kiddo. — *you won*
- **Captain Burak:** Welcome aboard, @member. Don't let it go to your head. That's my job. — *you won*
    - **Check: mentions the ladder, probably still fits.** Names @member - still right for Fight 1.
- **Captain Burak:** Hah! Down with the ship, eh? — *you lost*
- **Captain Burak:** The barrels were RIGHT THERE, kiddo. Think! — *you lost*

### Result screens for this rung

- "@newcomer ranked up to @member!" — *Victory screen message; the rank is RANKS\[0\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-1." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 2: Mason (win: @regular)

### Pre-fight

- **Mason:** hey! whats the big idea?
- **Danny:** sorry pal, it was the only way to get you to fight, ill give you some onion rings too if you beat this guy up — *Danny, from ringside*
    - **Check: mentions the ladder, probably still fits.** Danny bribes Mason from ringside - fits (Danny is fought later, in Fight 5).
- **Mason:** challenge accepted

### VS card

- Drawn in art: "FIGHT 02" (file: fight\_02.png)
- Drawn in art: "MASON" (file: name\_mason.png) — *name plate*
- Drawn in art: "THE SHITPOSTER" (file: epithet\_mason.png) — *epithet under the band*
- Drawn in art: "WIN @regular" (file: win\_regular.png) — *what the win pays*

### Health bar

- Drawn in art: "MASON" (file: boss\_plate\_name\_mason\_3x.png)

### Mid-fight words

- "FEINT!" — *beside him when you bite his hesitation pitch (written)*
- Drawn in art: "HOME RUN!" (file: home\_run.png) — *when you parry a pitch back into his head; text fallback Scripts/MasonArtLayout.gd:126*

### End of fight

- **Mason:** Okay, okay, you win. Just don't touch my fries. — *you won*
- **Mason:** Told you. Really bad time to show up. — *you lost*
    - **Flag: doesn't match the game now.** 'Told you' calls back to something he doesn't say any more - his pre-fight lines never warn that it's a bad time.
- **Mason:** Now if you'll excuse me, my food's getting cold. — *you lost*

### Result screens for this rung

- "@newcomer ranked up to @regular!" — *Victory screen message; the rank is RANKS\[1\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-2." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 3: Josh (win: @active)

### Pre-fight

- **Josh:** Newcomer, huh. Everybody gets dealt a hand.
- **Josh:** Not everybody knows what they're holding.
- **Josh:** Pick a card. Any card.
- **Josh:** ...Wrong one. They're all mine anyway.

### VS card

- Drawn in art: "FIGHT 03" (file: fight\_03.png)
- Drawn in art: "JOSH" (file: name\_josh.png) — *name plate*
- Drawn in art: "THE CARD SHARK" (file: epithet\_josh.png) — *epithet under the band*
- Drawn in art: "WIN @active" (file: win\_active.png) — *what the win pays*

### Health bar

- Drawn in art: "JOSH" (file: boss\_plate\_name\_josh\_3x.png)

### Mid-fight words

- "FEINT!" — *when you parry a fake clone in his Portal Monte (written)*

### End of fight

- **Josh:** You counted them. Nobody counts them. — *you won*
- **Josh:** Keep the deck, kid. Don't let it go to your head. — *you won*
    - **Flag: doesn't match the game now.** 'Don't let it go to your head' is also Captain Burak's line two fights earlier.
- **Josh:** House rules. The house shuffles. — *you lost*
- **Josh:** Come back when you can tell a bomb from a bluff. — *you lost*
    - **Flag: doesn't match the game now.** Josh has no bombs any more (his card-bomb art was removed in the rebuild; the fight is the Portal Monte, Wild Cards and the card hands) - 'a bomb from a bluff' may not fit.

### Result screens for this rung

- "@newcomer ranked up to @active!" — *Victory screen message; the rank is RANKS\[2\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-3." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 4: Eric (win: @veteran)

### Pre-fight

- **Eric:** Not another step filthy conservative.... Did you really think we'd allow filth like you into our beautiful, liberal server? NO. Not while I still breathe the same air as my left-winged brothers and sisters. Your wretched bloodline will die with you today. Good luck!
    - **Flag: typo or punctuation.** 'Not another step filthy conservative....' - no comma after 'step', and four dots.
- *(He pulls his sword and points it at you.)*
- **Eric:** I won't let scum like you into our utopia.

### VS card

- Drawn in art: "FIGHT 04" (file: fight\_04.png)
- Drawn in art: "ERIC" (file: name\_eric.png) — *name plate*
- Drawn in art: "THE WHITE KNIGHT" (file: epithet\_eric.png) — *epithet under the band*
- Drawn in art: "WIN @veteran" (file: win\_veteran.png) — *what the win pays*

### Health bar

- Drawn in art: "ERIC" (file: boss\_plate\_name\_eric\_3x.png)

### Mid-fight words

- "(none of his own - only the generic popups, BREAK!, MASH! and MAX. UPPERCUT!)"

### End of fight

- **Eric:** No... the White Knight, felled by a filthy conservative? — *you won*
- **Eric:** This isn't over. The mods will hear about this! — *you won*
    - **Check: mentions the ladder, probably still fits.** 'The mods' - the @moderator rung is Carter's (Fight 8); fits as a threat.
- **Eric:** Ha! The server stays pure for another day. — *you lost*
- **Eric:** Log off, and don't come back. — *you lost*

### Result screens for this rung

- "@newcomer ranked up to @veteran!" — *Victory screen message; the rank is RANKS\[3\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-4." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 5: Danny (win: @trusted)

### Pre-fight

- **Danny:** ...oh. it's you.
- **Burak:** Danny? The training room guy?
    - **Check: mentions the ladder, probably still fits.** Refers back to the training room - fits.
- **Danny:** helper rank. i guard \#helper. which means i have to fight you. ugh.
    - **Flag: no longer fits the new order.** Danny's rung now pays @trusted. @helper is what beating Liam & Bixby (Fight 7) gives.
- **Danny:** hold on. gotta get serious for this.
- *(He evolves into his sumo form.)*
- **Danny:** ...okay. i'm awake. let's make this quick, i've got a raid at nine.

### VS card

- Drawn in art: "FIGHT 05" (file: fight\_05.png)
- Drawn in art: "DANNY" (file: name\_danny.png) — *name plate*
- Drawn in art: "THE SLEEPING GIANT" (file: epithet\_danny.png) — *epithet under the band*
- Drawn in art: "WIN @trusted" (file: win\_trusted.png) — *what the win pays*

### Health bar

- Drawn in art: "DANNY" (file: boss\_plate\_name\_danny\_3x.png)

### Mid-fight hints and words (each hint once per fight)

- "DODGE HIS HOPS - GET CLEAR OF THE WORMS!" — *first hop of his butt-slam string*
- "THE BIG ONE! TAP %s AS HE LANDS!" — *the last, big slam; %s = parry key*
- "STUCK! TAP %s AS HE HITS TO PARRY!" — *his headbutt while you're stuck in a puddle; %s = parry key*
- "HOLD YOUR GROUND! TAP %s AS HE HITS!" — *his belly bump; %s = parry key*
- "HE'S HEALING! HIT HIM FAST!" — *he lies down to sleep and heal*
- "+%d" — *the health he heals, popping over him while he sleeps: '+1'*
- Drawn in art: "Z z z (sleep letters over him)" (file: danny\_sleep\_z.png) — *while he sleeps*
- "STUCK!" — *popup when his worms root you*
- "HELD!" — *popup when you parry his belly bump*

### The sumo (at 0 HP he blocks the gate) - Dialogue/DannyBossSumo.dialogue

- **Danny:** nah. you're not leaving. sumo. loser gets thrown out.
- "SUMO!" — *called out as the sumo starts (written, in MASH! gold)*
- "PUSH!" — *under the tug-of-war meter (written)*

### End of fight

- **Danny:** ...ow. okay. \#helper's yours. — *you pushed him out of the ring*
    - **Flag: no longer fits the new order.** He now hands over @trusted, not \#helper.
- **Danny:** wake me up when it's raid time. — *you won*
- **Danny:** out of the ring, dum dum. that's sumo. — *you lost*
    - **Flag: doesn't match the game now.** This also plays if you lose BEFORE the sumo (the file says 'in the fight or the sumo'), where 'out of the ring ... that's sumo' doesn't fit.
- **Danny:** ...five more minutes. — *you lost*

### Result screens for this rung

- "@newcomer ranked up to @trusted!" — *Victory screen message; the rank is RANKS\[4\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-5." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 6: Computah, Then Greyson (win: @vip)

### Pre-fight

- **Greyson:** go get him buddy
    - **Check: mentions the ladder, probably still fits.** Greyson is Fight 6's second half - fits.
- *(Nothing happens - three seconds of an empty ring.)*
- **Greyson:** oh right my bad
- **Greyson:** computah, kill this gay freaking bald idiot
- *(His battery charges up.)*

### VS card

- Drawn in art: "FIGHT 06" (file: fight\_06.png)
- Drawn in art: "COMPUTAH" (file: name\_computah.png) — *name plate*
- Drawn in art: "THE MACHINE" (file: epithet\_computah.png) — *epithet under the band*
- Drawn in art: "WIN @vip" (file: win\_vip.png) — *what the win pays*

### Health bar

- Drawn in art: "COMPUTAH" (file: boss\_plate\_name\_computah\_3x.png)

### Mid-fight words (Computah)

- "(none live - his rotation is only the cannon beam today)"
- "OVERLOAD" — *over his bar during his Overload*
    - **Note: never shown in the game.** The Overload is out of his rotation (since 2026-09-24).
- "ESCAPE!" — *mash word in his mine trap and catch*
    - **Note: never shown in the game.** The mine field and the catch are out of his rotation.

### If you lose to Computah

- **Computah:** Target neutralised. Bzzzt. Shall I remove another heart, sir?
- **Greyson:** HAHAHA! Look at his face, Computah!

### ComputahOutro player\_won - never plays

- **Computah:** Bzzzt... critical failure... Mister Greyson, I have been... outplayed.
    - **Note: never shown in the game.** Beating Computah always starts Greyson's takeover, so his 'you won' lines never play.
- **Greyson:** Get UP, Computah! I skipped the gym for this!
    - **Note: never shown in the game.** As above.

### Greyson's takeover

- **Greyson:** COMPUTAH NOOO — *shouted, no talk blips; written exactly as the user wrote it*
- *(Greyson storms the ring.)*
- **Greyson:** That was my gym partner. I hit my first 225 on bench with this little guy. That was a long time ago. Now you've really messed up.
- *(He takes Computah's cannon arm.)*
- **Greyson:** What Computah didn't know was that this cannon is fueled by the crowd's energy... but I know how to get them going.
- *(The crowd roars.)*
- **Greyson:** Pal, you won't like what comes next.
- *(The health bar swaps to his.)*
- Drawn in art: "GREYSON" (file: boss\_plate\_name\_greyson\_3x.png) — *his bar's name plate*

### Mid-fight words (Greyson)

- "(none of his own - his crowd-hype meter has no words; the final brawl uses MASH!)"

### End of fight

- **Greyson:** No... my cannon... my GAINS... — *you won*
- **Greyson:** Fine. You win, pal. Computah would've been proud. Probably. — *you won*
- **Greyson:** Told you, pal. Nobody out-hypes me. — *you lost (on hearts or to the spirit bomb)*
- **Greyson:** Computah, buddy... we did it. — *you lost*

### Result screens for this rung

- "@newcomer ranked up to @vip!" — *Victory screen message; the rank is RANKS\[5\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-6." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 7: Liam & Bixby, Then Liam (win: @helper)

### Entrance and pre-fight

- **Liam:** Well, well! Welcome to my arena, newcomer.
- **Liam:** Nobody gets this far by accident. Congratulations, truly.
    - **Check: mentions the ladder, probably still fits.** 'Nobody gets this far' - still fits at Fight 7 of 10.
- **Liam:** Shame it ends here. Bixby will make quick work of you.
- *(They step down; Liam slaps Bixby.)*
- Drawn in art: "SMACK!" (file: liam\_slap\_keys.png) — *drawn into the slap frame*
- **Liam:** Ha! Don't worry, he LOVES it!
- **Liam:** Come on boy, get 'em!
- *(Another slap; Bixby growls.)*
- **Bixby:** Grrrrrrr...
- **Liam:** That's my good boy! One more for luck!
- *(A third slap; Bixby swallows Liam.)*
- Drawn in art: "!!  ...  CHOMP!  ...  ?  GULP!" (file: bixby\_swallow\_keys.png) — *drawn into the swallow frames*
- **Bixby:** \*GULP\*
- *(Bixby transforms into the beast.)*

### VS card

- Drawn in art: "FIGHT 07" (file: fight\_07.png)
- Drawn in art: "LIAM & BIXBY" (file: name\_liam.png) — *name plate*
- Drawn in art: "THE THRONE AND THE BEAST" (file: epithet\_liam.png) — *epithet under the band*
- Drawn in art: "WIN @helper" (file: win\_helper.png) — *what the win pays*

### Health bar

- Drawn in art: "LIAM / & BIXBY (two lines)" (file: boss\_plate\_name\_liam\_pair\_3x.png) — *Bixby's half of the fight*

### Mid-fight words (Bixby)

- "(none of his own)"

### If you lose to Bixby

- **Liam:** Good boy... GOOD boy! Now can you spit me out? — *Liam, from inside Bixby*
- **Liam:** ...Bixby? Buddy?

### LiamOutro player\_won - never plays

- **Liam:** \*cough\* \*hack\*... Bixby, buddy... we talked about this.
    - **Note: never shown in the game.** Beating Bixby always starts Liam's takeover.
- **Liam:** Fine. You win, newcomer. Jordan's waiting for you.
    - **Note: never shown in the game.** Never plays (see above).
    - **Flag: no longer fits the new order.** 'Jordan's waiting for you' - Carter and Matt still come before Jordan.

### Liam's takeover

- *(Liam gets up.)*
- **Liam:** \*cough\* \*hack\*... Ugh. Thanks for getting me out of there, newcomer. I owe you one.
- **Liam:** But don't get too excited. Bixby's my student... and the only element he ever mastered was fire.
    - **Check: mentions the ladder, probably still fits.** Bixby - fits.
- **Liam:** Me? I've mastered all four. Water. Earth. Fire. Air.
- **Liam:** This fight just got a whole lot harder. — *the user's own line*
- *(Anime laugh.)*
- **Liam:** Nyahahahaha! — *no talk blips - the laugh is the voice*
- *(He pulls his staff out of his mouth.)*
- **Liam:** Kept it somewhere safe.
- **Burak:** ew.
- *(An earth pillar rises and carries him up.)*
- Drawn in art: "LIAM" (file: boss\_plate\_name\_liam\_a\_3x.png) — *his own bar's name plate*

### Mid-fight words (Liam)

- "(none of his own)"

### End of fight

- **Liam:** \*cough\*... okay. Okay! Maybe I should've stuck to fire too. — *you won*
- **Liam:** Fine. You win, newcomer. Jordan's waiting for you. — *you won*
    - **Flag: no longer fits the new order.** 'Jordan's waiting for you' - next is Carter (Fight 8), then Matt, then Jordan.
- **Liam:** Four elements, newcomer. FOUR. — *you lost (to either half after the hand-over)*
- **Liam:** Nyahahaha! — *you lost; no talk blips*
    - **Flag: typo or punctuation.** 'Nyahahaha!' here vs 'Nyahahahaha!' in his takeover - maybe meant to match.

### Result screens for this rung

- "@newcomer ranked up to @helper!" — *Victory screen message; the rank is RANKS\[6\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-7." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 8: Carter (win: @moderator)

### Pre-fight

- **Carter:** ...
- **Carter:** You got past Josh. Fine.
    - **Flag: no longer fits the new order.** Josh is Fight 3 now; the fight right before Carter is Liam & Bixby.
- **Carter:** I only have one move.
    - **Flag: doesn't match the game now.** He has three attacks now (Raging Demon, Beam Rush, Messatsu, chained since 2026-10-05).
- **Carter:** You won't see it twice.
    - **Flag: doesn't match the game now.** Same: more than one move now.

### VS card

- Drawn in art: "FIGHT 08" (file: fight\_08.png)
- Drawn in art: "CARTER" (file: name\_carter.png) — *name plate*
- Drawn in art: "THE DEMON" (file: epithet\_carter.png) — *epithet under the band*
- Drawn in art: "WIN @moderator" (file: win\_moderator.png) — *what the win pays*

### Health bar

- Drawn in art: "CARTER" (file: boss\_plate\_name\_carter\_3x.png)

### Mid-fight words

- "FEINT!" — *when you parry a yellow fake clone (written)*
- Drawn in art: "天 (kanji 'heaven', Akuma's mark)" (file: demon\_finish.png) — *on the back of his gi in his sprites and on the Raging Demon's finishing emblem*

### End of fight

- **Carter:** Hm. — *you won*
- **Carter:** You're awake now. Good. — *you won*
- **Carter:** That was the move. — *you lost*
    - **Flag: doesn't match the game now.** 'The move' - he has three now.

### Result screens for this rung

- "@newcomer ranked up to @moderator!" — *Victory screen message; the rank is RANKS\[7\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-8." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 9: Matt (win: @admin)

### Pre-fight

- **Matt:** Are you enjoying your time so far?
- **Burak:** No the challenge has been brutal and everyone's so weird
    - **Flag: typo or punctuation.** No comma after 'No', no full stop (may be deliberate voice).
- **Matt:** Haha... you're right... but you'll get used to it!
- **Matt:** Well anyways, I'm Matt, calm cool and collected, you ever play RuneScape? I love RuneScape!
    - **Flag: typo or punctuation.** 'calm cool and collected' - no commas.
- **Burak:** Once or twice, it was terrible, just some boomers rotting their brain
- **Matt:** Hehe.... ya... it's not for everyone.. but hey! At least we can all agree RuneScape's the top MMO of all time... right pal?
    - **Flag: typo or punctuation.** 'not for everyone..' - two dots.
- **Burak:** Absolutely not. Hahaha what are you even talking about?
- **Matt:** You don't think it's in the top 5?
- **Burak:** That's not what you said, you said top 1...
- **Matt:** Buddy, I said top 5, you're starting to get me a little angry
    - **Flag: typo or punctuation.** No full stop at the end.
- **Danny:** Matt I think you said top 1... — *from ringside*
    - **Check: mentions the ladder, probably still fits.** Danny heckles - already beaten (Fight 5), fits.
- **Matt:** NO I DID NOT. — *shouted - the ring shakes*
- *(He composes himself.)*
- **Matt:** Sorry about that haha, I don't think that's what I said friend ahaha....
- **Liam:** Pfft Matt I have it on video you said top 1 ahahaha — *from ringside*
    - **Check: mentions the ladder, probably still fits.** Liam heckles - already beaten (Fight 7), fits.
- **Matt:** ENOUGH. SICK OF YOU GUYS DISRESPECTING ME AH I NEED MY HONG STRESS TOY — *shouted - the ring shakes*
- *(He pulls out his Hong stress toy and screams at it; a pause.)*
- **Burak:** Hehe hehe hehe.... top 1 by the way
- *(He roars.)*

### VS card

- Drawn in art: "FIGHT 09" (file: fight\_09.png)
- Drawn in art: "MATT" (file: name\_matt.png) — *name plate*
- Drawn in art: "THE WALL OF SOUND" (file: epithet\_matt.png) — *epithet under the band*
- Drawn in art: "WIN @admin" (file: win\_admin.png) — *what the win pays*

### Health bar

- Drawn in art: "MATT" (file: boss\_plate\_name\_matt\_3x.png)

### Mid-fight hints and words

- "PRESS THE ARROW BEFORE IT LANDS!" — *under you during his first Glass Row; arrows (art, no words) ride each sonic boom*
- "RESIST!" — *mash word through his Deafening Yell, phase two (set in Scripts/States/Matt/MattGlassRow.gd:180)*
- "DASH THROUGH THE GOLD!" — *under you at his first Boomburst (Echo Roars)*
- "PSYCH!" — *beside him when you press on a silent roar's X*

### End of fight

- **Matt:** \*wheeze\* ...okay. Okay. You got me, pal. — *you won*
- **Matt:** ...top 5 though. — *you won*
- **Matt:** Haha! Sorry buddy, I get a little loud sometimes. — *you lost*
- **Matt:** Top 1. Obviously. — *you lost*

### Result screens for this rung

- "@newcomer ranked up to @admin!" — *Victory screen message; the rank is RANKS\[8\] in Scripts/GameProgress.gd:29; button NEXT BOSS*
- "@newcomer was knocked out and kicked from \#arena-9." — *Defeat screen message after losing here; buttons RETRY and RETURN TO MAIN MENU*

## Fight 10: Jordan (kaiju phase)  (win: the invite, no rank)

### Pre-fight

- **Jordan:** So you're the newcomer everyone keeps pinging me about.
- **Jordan:** I run this server. Let's see how you handle my collection.

### VS card

- Drawn in art: "FIGHT 10" (file: fight\_10.png)
- Drawn in art: "JORDAN" (file: name\_jordan.png) — *name plate*
- Drawn in art: "THE ADMIN" (file: epithet\_jordan.png) — *epithet under the band*
- Drawn in art: "(no WIN plate)" (file: VsCardArtLayout.gd:208) — *the last fight hands over the invite, not a rank*

### Health bar

- Drawn in art: "JORDAN" (file: boss\_plate\_name\_jordan\_3x.png) — *also the god fight's bar*

### Mid-fight words

- "(none of his own)"

### End of fight

- "(winning plays his finale - section 4 - instead of lines and the Victory screen)"
- **Jordan:** Should've read the server rules. — *you lost (placeholder lines per the file)*
- **Jordan:** Come back when you've got more than a starter role. — *you lost*
    - **Flag: no longer fits the new order.** By Fight 10 the player is @admin, not on a starter role.

### Result screens for this rung

- "@newcomer received an invite!" — *the Victory message for the last rung*
    - **Note: never shown in the game.** Fight 10 never reaches the Victory screen: the win goes to the finale, the god fight and the champion ending.
- "MAIN MENU" — *Victory button text after the last fight*
    - **Note: never shown in the game.** As above.
- "@newcomer was knocked out and kicked from \#arena-10." — *Defeat after losing to kaiju Jordan or to god Jordan (both count as Fight 10)*
- Drawn in art: "THE ADMIN (Jordan's epithet) vs. the @admin rank" (file: epithet\_jordan.png)
    - **Flag: no longer fits the new order.** Beating Matt makes the player @admin right before Jordan's card calls Jordan THE ADMIN.

## Jordan's finale: the walk-out, the room, the reveal

### The walk-out (in the arena)

- *(Jordan gets up and storms off through the top gate; the crowd boos.)*
- **Jordan:** No you cheated, don't cheat, don't cheat, no don't cheat. I won't allow cheaters in this server — *typed as he walks*
    - **Flag: typo or punctuation.** No full stop at the end.
- *(He's gone; you follow him out.)*

### His room

- Drawn in art: "COLLECT (funko poster), JOIN (Discord poster), 0990 (arcade high score)" (file: room\_props.png) — *posters on his walls*
- "ENTER" — *the key shown in the talk prompt (on a gamepad, the A glyph instead)*
- "TALK" — *the talk prompt over Jordan: '\[ENTER\] TALK'*
- **Burak:** what the hell dude? I won, game over, now let me into the server
    - **Flag: typo or punctuation.** Lower-case start, no end punctuation (maybe voice).
- *(No answer. The other bosses walk in.)*
- **Liam:** Hey bud... I think he has you muted...
- **Burak:** Uhhh ok, I have an idea
- *(Burak puts on a moustache and taps Jordan's shoulder.)*
- **Aiden:** Hey Jordan! My name's Aiden! I love funkos, I love Nintendo and I definitely don't cheat! Can I be let into the server? — *the name tab says Aiden (it's Burak in a moustache)*
- **Jordan:** Hey! What's going on Aiden? Weird, you look exactly like a guy named Burak I saw...
- **Jordan:** Anyways! Yes dude, you sound like a cool dude! Of course you can! Here let me just send you the server invite...
- *(The moustache falls off.)*
- **Jordan:** Hey wait a second... You're Burak! That damn cheating hockey puck! You...You tricked me....
- *(The room trembles.)*
- **Liam:** Hey buddy why don't we just calm down...
- *(Jordan disintegrates Liam.)*
- **Jordan:** What an idiot. He was trying to trick me too. But I'm done playing your games.
- **Jordan:** What you don't understand is... This is my world, my server, the others don't even exist if I don't want them to. — *from 'This is my world' on, the text shakes*
- *(He disintegrates the rest.)*
- **Jordan:** The only person in this server.... is just me. — *the whole line shakes*
- *(The room comes apart; he ascends as a demon god.)*
- **Jordan:** Welcome to my world, Burak. — *with his demon portrait; then the god fight starts*

## The god fight (Puppet Master) and the final beam

### Combination attacks, in rotation order

- "FOLLOW MATT'S ARROWS TO GREYSON!" — *attack 1, Greyson + Matt's dark maze*
    - **Check: mentions the ladder, probably still fits.** Names Matt and Greyson - fits.
- "PRESS (%s) TOWARD THE GLOWING KEG, THEN PUNCH IT!" — *attack 2, Captain Burak + Danny's kegs; %s = the move name, so it reads 'PRESS (ARROWS) TOWARD...' on the default keys, 'PRESS (LEFT STICK) ...' on a pad*
- "(no hint)" — *attack 3, Josh + Eric's portals*
- "KEEP RUNNING AROUND THE CIRCLE, AHEAD OF THE BEAMS!" — *attack 4, Carter + Mason's circle*

### Attack 5, the Elemental Wheel (Liam + Bixby)

- "GET INTO THE GAP IN THE FIRE!" — *the wheel lands on FIRE*
- "STAND, DASH THE WAVE, THEN PARRY THE BITE!" — *WATER*
- "DASH THROUGH EACH RING!" — *EARTH*
- "WALK AGAINST THE WIND, THEN PARRY BOTH BITES!" — *AIR*
- "TWO ELEMENTS AT ONCE!" — *the third spin lands on two elements at once*
- "DASH THROUGH THE WAVE, THEN PARRY THE JAWS!" — *the AIR + WATER double, the first time it comes*
- Drawn in art: "(element icons over Liam's head - pictures, no letters)" (file: element\_icons.png) — *a '+' (Scripts/JordanElementWheel.gd:389) sits between the two icons of a double; placeholder letters W / E / F / A (Scripts/JordanWheelLayout.gd:161) only if the icon art is switched off*

### The final beam (at 0 HP: five-bar mash)

- Drawn in art: "MASH!" (file: qte\_mash\_text\_3x.png) — *under the mash keys until the first bar*
- Drawn in art: "SHIN  /  KU  /  HA  /  DO  /  KEN!!!!" (file: final\_beam\_shout\_words.png) — *one word per bar banked; KEN!!!! fires the beam*
- Drawn in art: "KEN..." (file: final\_beam\_shout\_words.png) — *the mash ran out: the beam fizzles, he laughs and revives, and the fight goes on*
- "SHIN... KU... HA... DO..." — *text version, only if the shout art is missing; note the art drops the '...' after each syllable*
- "KEN!!!!" — *text version of the release word*
- "KEN..." — *text version of the fail word*

## The champion ending and the credits

### The announcer (unseen; the crowd's roar drowns the name)

- **???:** And announcing your new discord champion of this server.... — *speaker name from :235; can't be skipped or advanced*
    - **Flag: typo or punctuation.** Lower-case 'discord' (it's 'Discord' everywhere else); four dots.

### The credits roll

- "ENTER THE DISCORD" — *title, alone on screen first*
- "A GAME BY"
- "Burak Yilmaz"
- "DIRECTED BY" — *each role is followed by 'Burak Yilmaz'*
- "GAME DESIGN" — *each role is followed by 'Burak Yilmaz'*
- "STORY & DIALOGUE" — *each role is followed by 'Burak Yilmaz'*
- "BOSS DESIGN" — *each role is followed by 'Burak Yilmaz'*
- "CHARACTER DESIGN" — *each role is followed by 'Burak Yilmaz'*
- "ART DIRECTION" — *each role is followed by 'Burak Yilmaz'*
- "PIXEL ART & ANIMATION" — *each role is followed by 'Burak Yilmaz'*
- "PROGRAMMING" — *each role is followed by 'Burak Yilmaz'*
- "COMBAT DESIGN" — *each role is followed by 'Burak Yilmaz'*
- "ARENA DESIGN" — *each role is followed by 'Burak Yilmaz'*
- "CUTSCENES" — *each role is followed by 'Burak Yilmaz'*
- "USER INTERFACE" — *each role is followed by 'Burak Yilmaz'*
- "SOUND DESIGN" — *each role is followed by 'Burak Yilmaz'*
- "CHARACTER VOICES" — *each role is followed by 'Burak Yilmaz'*
- "ORIGINAL MUSIC" — *each role is followed by 'Burak Yilmaz'*
- "PRODUCER" — *each role is followed by 'Burak Yilmaz'*
- "EXECUTIVE PRODUCER" — *each role is followed by 'Burak Yilmaz'*
- "CHIEF HYPE OFFICER" — *each role is followed by 'Burak Yilmaz'*
- "THE SERVER" — *section title*
- "the challengers, in ladder order" — *small line under it*
    - **Check: mentions the ladder, probably still fits.** The cast list below is in the new ladder order - fits.
- "CAPTAIN BURAK / MASON / JOSH / ERIC / DANNY / COMPUTAH / GREYSON / LIAM & BIXBY / CARTER / MATT / JORDAN" — *the cast, one name per line*
- "and introducing" — *small line*
- "THE NEWCOMER"
- "MUSIC" — *section title, only if a song below shows*
- ""Universal Collapse"  /  DM DOKURO" — *shows only if the ending's local MP3 is present and played (it's local-only, not committed)*
- ""Neo Tokyo"" — *the god fight's song*
    - **Note: never shown in the game.** Its artist is blank, so this credit never shows. Two more local tracks (Carter's and Mason's themes, :444-445) have no title or artist and never show either.
- "BUILT WITH" — *section title*
- "Godot Engine"
- "Dialogue Manager by Nathan Hoad"
- "SPECIAL THANKS" — *section title*
- "The real server, for being good sports"
- "Discord is a trademark of Discord Inc." — *small print*
- "This is a fan-made game. It is not affiliated with, endorsed by or sponsored by Discord Inc." — *small print*
- "© 2026 Burak Yilmaz" — *small print*
- "THANK YOU FOR PLAYING" — *last card, over the champion still (Assets/UI/Screens/credits\_champion.png, which has no words of its own)*

## The Defeat and Victory screens, RETRY, TO BE CONTINUED, and anything else

### Defeat screen

- "Defeat!" — *big title*
- "SYSTEM" — *the 'author' of the chat message*
- "Today at %d:%02d %s" — *the message's timestamp, the real time: 'Today at 9:41 PM'*
- "Today at 11:59 PM" — *placeholder in the scene, replaced by the real time*
- "@newcomer was knocked out and kicked from \#arena-%d." — *the message; %d = the fight's number (god Jordan counts as 10)*
- "@newcomer was knocked out and kicked from \#arena-1." — *placeholder in the scene, replaced at once*
- "RETRY" — *button, only when the lost fight can be retried*
- "RETURN TO MAIN MENU" — *button*
- Drawn in art: "ARENA (banner, left) and \# ARENA-1 (banner, right); crowd signs GG EZ and L" (file: defeat\_bg.png)
    - **Flag: drawn into art, can't follow the game.** The banner always says ARENA-1, whichever fight you lost.

### Victory screen (shared parts; each rung's message is in its fight)

- "Victory!" — *big title*
- "SYSTEM" — *the 'author' of the chat message*
- "Today at %d:%02d %s" — *the timestamp, the real time*
- "@newcomer ranked up to %s!" — *the message; %s = the rank (see each fight)*
- "@member / @regular / @active / @veteran / @trusted / @vip / @helper / @moderator / @admin / (invite)" — *the ranks, by rung 1-10*
- "@newcomer won the fight!" — *message for a fight outside the ladder*
    - **Note: never shown in the game.** Only the out-of-ladder scenes (section 8) would show it.
- "NEXT BOSS" — *button (also Scenes/Core/VictoryScene.tscn:169)*
- "@newcomer ranked up to @member!" — *placeholder message in the scene, replaced at once*
- Drawn in art: "ARENA (banner) and \# ARENA-1 (banner); a scrolling ticker 'GG  @NEWCOMER  W  LETS GO  +1' along the ring" (file: victory\_bg.png)
    - **Flag: drawn into art, can't follow the game.** The banner always says ARENA-1, whichever fight you won.

### TO BE CONTINUED card

- "TO BE CONTINUED" — *white on black; the three dots appear one at a time (Scenes/Core/ToBeContinuedScene.tscn:37 holds 'TO BE CONTINUED...')*
    - **Note: never shown in the game.** Nothing reaches it today: the finale goes on to the god fight and the god fight to the champion ending. It is only the fallback if either is switched off.

### Window title and build name

- "Project FMWO" — *the game window's title bar*
    - **Flag: doesn't match the game now.** The logo and credits call the game ENTER THE DISCORD.
- "Project FMWO  /  Project FMWO playtest build" — *the Windows .exe's product name and description (file properties)*
    - **Flag: doesn't match the game now.** Same as above.

### Arena art seen in every fight

- Drawn in art: "GG, @, W and a heart on the crowd's signs" (file: crowd\_v3.png)
- Drawn in art: "\# (the crest in the middle of the mat)" (file: arena\_mat.png)

## The training room, and the old scenes that are not in the main game

### Training room - the control cards

- "Classic arrow key movement" — *move card on the default arrow keys (also ControlsSceneScript.gd:5)*
- "Movement" — *move card when the move keys are rebound*
- "Left stick or D-pad" — *move card on a gamepad*
- "Attack" — *card*
- "Dash" — *card*
- "Parry" — *card*

### Danny's tutorial

- **Danny:** I'm mid-raid, so I'm saying this ONCE. {{move\_name}} to move, {{punch\_name}} punches, {{dodge\_name}} dashes. Land three punches and the third one really hurts. — *e.g. 'ARROWS to move, Q punches, W dashes.'*
- **Danny:** TAP {{block\_name}} the instant a hit lands and you PARRY it. There's no blocking on this server, so holding it down just gets you smacked. A parry that lands costs nothing, staggers some attacks, and then you get to hit them back. Miss one and it costs you stamina, so don't just spam it.
- **Danny:** That stamina bar under your hearts pays for dashing and for missed parries, and it only refills slowly. A dash takes a third of it and leaves you stuck for a moment after, unless you parry out of it. Run it dry and you can't do either.
- **Danny:** Boss goes all dizzy? Follow the prompt to finish him: mash {{mash\_left\_name}} and {{mash\_right\_name}}. — *e.g. 'mash LEFT and RIGHT'*
- **Danny:** Need out mid-fight? {{pause\_name}} pauses it, and from there you can resume, start the fight over, change these controls or run home to the menu. That's everything, dum dum. — *e.g. 'ESC pauses it'*
- **Danny:** Now go warm up on that sparring bot: punch it, combo it, finish it. Then WALK INTO THE POST beside it and it starts swinging back - red over its head means TAP {{block\_name}} to parry, yellow means {{dodge\_name}} straight through it. Those two reads are the whole game. You CAN'T lose in here. Done? Hit I'm ready, or walk out the Arena \#1 door. Don't cry to me when the Captain flattens you.
    - **Check: mentions the ladder, probably still fits.** 'the Arena \#1 door' and 'the Captain' - Captain Burak is still Fight 1, fits.

### Training room - the rest

- "I'm ready!" — *button, unlocked after Danny's lines (a gamepad shows the Y glyph on it)*
- "GOING IN..." — *while you stand in the Arena \#1 doorway*
- Drawn in art: "ARENA \#1 (banner over the door)" (file: controls\_bg.png)
- Drawn in art: "BAG / SPAR (the post's lamp, one lit)" (file: training\_dummy\_switch\_3x.png)
- "SPAR MODE: OFF" — *sign on the post, sparring off*
- "SPAR MODE: ON" — *sign on the post, sparring on*
- "WALK INTO ME" — *second line of the post's sign*

### Training room - callouts (small text after each thing you do)

- "it's staggered - punch it" — *after a parry*
- "that cost stamina" — *after a block*
    - **Note: never shown in the game.** Blocking is switched off, so nothing is ever blocked.
- "too slow - press parry as it lands" — *after you're hit*
- "too early" — *a parry press too soon after a missed one, while sparring*
- "wait it out" — *after a guard break*
    - **Note: never shown in the game.** The guard can't break with blocking off.
- "the dash went straight through it" — *after a perfect dodge*
- "SPARRING - parry the red, dash the yellow" — *walking into the post turns sparring on*
- "BAG - it just stands there now" — *walking into it again turns it off*

### Training room - Danny's one-off barks (each the first time only)

- "There you go. Three of those and the third one HURTS." — *first landed punch*
- "It's gone dizzy! MASH the two on the prompt, dum dum!" — *first time the dummy goes dizzy*
- "THAT'S a parry. It's wide open. Hit it." — *first parry*
- "Dashed clean through it. Do that to the yellow ones." — *first perfect dodge*
- "Bar's empty, guard's gone. Stop blocking and MOVE." — *first guard break*
    - **Note: never shown in the game.** The guard can't break with blocking off.
    - **Flag: doesn't match the game now.** Says 'Stop blocking' - Danny's tutorial says there's no blocking on this server.
- "Bored? Walk into that post and it'll hit BACK. Red you parry, yellow you dash through." — *after 6 punches if you never tried sparring*

### NOT IN THE MAIN GAME - Carter & Josh two-on-one (old fight)

- **Josh:** Alright Carter, this one's got fresh legs. Let's give him the full show.
    - **Note: never shown in the game.** Old fight, not reachable.
- **Carter:** Just don't run into me like Tulsa again.
    - **Note: never shown in the game.** Old fight, not reachable.
- **Josh:** That was ONE time. Ready?
    - **Note: never shown in the game.** Old fight, not reachable.
- **Carter:** Born ready. Let's dance.
    - **Note: never shown in the game.** Old fight, not reachable.
- **Carter:** You ran into me. Like Tulsa. AGAIN. — *you won*
    - **Note: never shown in the game.** Old fight.
- **Josh:** Okay... that's two times. — *you won*
    - **Note: never shown in the game.** Old fight.
- **Josh:** Now THAT'S the full show! — *you lost*
    - **Note: never shown in the game.** Old fight.
- **Carter:** Good match, kid. Come back with fresher legs. — *you lost*
    - **Note: never shown in the game.** Old fight.
- "CARTER & JOSH" — *its health-bar name*
    - **Note: never shown in the game.** Old fight.

### NOT IN THE MAIN GAME - Dialogue/dialogue.dialogue (Dialogue Manager's example file, never loaded)

- **Eric:** Hi there! My name's Eric. I'm the first guy you'll have to fight in order to get into our friendly little discord. But don't think of them as fights. These are more like getting to know each other little fun sessions!
    - **Note: never shown in the game.** Never loaded.
    - **Flag: no longer fits the new order.** 'the first guy you'll have to fight' - Eric is Fight 4 now.
- **Nathan:** \[\[Hi\|Hello\|Howdy\]\], this is some dialogue. — *a random pick of Hi / Hello / Howdy*
    - **Note: never shown in the game.** Never loaded.
- **Nathan:** Here are some choices.
    - **Note: never shown in the game.** Never loaded.
- "First one  /  Second one  /  Start again  /  End the conversation" — *choices*
    - **Note: never shown in the game.** Never loaded.
- **Nathan:** You picked the first one. — *after 'First one'*
    - **Note: never shown in the game.** Never loaded.
- **Nathan:** You picked the second one. — *after 'Second one'*
    - **Note: never shown in the game.** Never loaded.
- **Nathan:** For more information see the online documentation.
    - **Note: never shown in the game.** Never loaded.

### NOT IN THE MAIN GAME - old scenes and editor placeholders

- "ENTER THE DISCORD" — *old main menu (the game boots into Scenes/Core/MainMenuScene.tscn)*
    - **Note: never shown in the game.** Old menu scene.
- "START GAME" — *old main menu button*
    - **Note: never shown in the game.** Old menu scene.
- "SETTINGS" — *old main menu button*
    - **Note: never shown in the game.** Old menu scene.
- "(Danny's 'Sup. I'm Danny...' line again)" — *an old copy of Scenes/Core/IntroScene.tscn with the same script*
    - **Note: never shown in the game.** Old duplicate scene.
- "Character" — *dialogue box placeholder, replaced before it shows*
- "Dialogue..." — *dialogue box placeholder, replaced before it shows*
- "Response example" — *choice button placeholder*
    - **Note: never shown in the game.** No live dialogue has choices.
- Drawn in art: "GREYSON / & COMPUTAH, & COMPUTAH, GREYSON (alt), BIXBY, & BIXBY" (file: boss\_plate\_name\_greyson\_pair\_3x.png) — *spare health-bar plates (greyson\_pair, greyson\_a, greyson\_b, bixby, liam\_b) no fight uses*
    - **Note: never shown in the game.** No fight asks for these plates.

## Flags at a glance

90 flags in all. The ones to act on first are the order and story mismatches; the never-shown lines are listed so you can cut them or leave them.

| Kind | Count |
| --- | --- |
| No longer fits the new order | 8 |
| Doesn't match the game now | 10 |
| Typo or punctuation | 11 |
| Drawn into art, can't follow the game | 3 |
| Never shown in the game | 44 |
| Mentions the ladder, probably still fits | 14 |

### No longer fits the new order

- Danny: "helper rank. i guard \#helper. which means i have to fight you. ugh." — Danny's rung now pays @trusted. @helper is what beating Liam & Bixby (Fight 7) gives. *(Fights)*
- Danny: "...ow. okay. \#helper's yours." — He now hands over @trusted, not \#helper. *(Fights)*
- Liam: "Fine. You win, newcomer. Jordan's waiting for you." — 'Jordan's waiting for you' - Carter and Matt still come before Jordan. *(Fights)*
- Liam: "Fine. You win, newcomer. Jordan's waiting for you." — 'Jordan's waiting for you' - next is Carter (Fight 8), then Matt, then Jordan. *(Fights)*
- Carter: "You got past Josh. Fine." — Josh is Fight 3 now; the fight right before Carter is Liam & Bixby. *(Fights)*
- Jordan: "Come back when you've got more than a starter role." — By Fight 10 the player is @admin, not on a starter role. *(Fights)*
- "THE ADMIN (Jordan's epithet) vs. the @admin rank" — Beating Matt makes the player @admin right before Jordan's card calls Jordan THE ADMIN. *(Fights)*
- Eric: "Hi there! My name's Eric. I'm the first guy you'll have to fight in order to get into our friendly little discord. But don't think of them a" — 'the first guy you'll have to fight' - Eric is Fight 4 now. *(Training/old)*

### Doesn't match the game now

- Mason: "Told you. Really bad time to show up." — 'Told you' calls back to something he doesn't say any more - his pre-fight lines never warn that it's a bad time. *(Fights)*
- Josh: "Keep the deck, kid. Don't let it go to your head." — 'Don't let it go to your head' is also Captain Burak's line two fights earlier. *(Fights)*
- Josh: "Come back when you can tell a bomb from a bluff." — Josh has no bombs any more (his card-bomb art was removed in the rebuild; the fight is the Portal Monte, Wild Cards and the card hands) - 'a bomb from a bluff' may not fit. *(Fights)*
- Danny: "out of the ring, dum dum. that's sumo." — This also plays if you lose BEFORE the sumo (the file says 'in the fight or the sumo'), where 'out of the ring ... that's sumo' doesn't fit. *(Fights)*
- Carter: "I only have one move." — He has three attacks now (Raging Demon, Beam Rush, Messatsu, chained since 2026-10-05). *(Fights)*
- Carter: "You won't see it twice." — Same: more than one move now. *(Fights)*
- Carter: "That was the move." — 'The move' - he has three now. *(Fights)*
- "Project FMWO" — The logo and credits call the game ENTER THE DISCORD. *(Screens)*
- "Project FMWO  /  Project FMWO playtest build" — Same as above. *(Screens)*
- "Bar's empty, guard's gone. Stop blocking and MOVE." — Says 'Stop blocking' - Danny's tutorial says there's no blocking on this server. *(Training/old)*

### Typo or punctuation

- "YOU CAN'T OUTRUN HIM! DASH (%s) THROUGH THE SWING OR TAP %s TO PARRY" — No closing '!' - every other hint in the game ends with one. *(Fights)*
- Captain Burak: "...pfffft.... hahahahaha! I've never seen someone get hit by all 5 barrels! Hahahahaha! Danny did you see that?" — 'Danny did you see that?' has no comma after Danny. *(Fights)*
- Eric: "Not another step filthy conservative.... Did you really think we'd allow filth like you into our beautiful, liberal server? NO. Not while I " — 'Not another step filthy conservative....' - no comma after 'step', and four dots. *(Fights)*
- Liam: "Nyahahaha!" — 'Nyahahaha!' here vs 'Nyahahahaha!' in his takeover - maybe meant to match. *(Fights)*
- Burak: "No the challenge has been brutal and everyone's so weird" — No comma after 'No', no full stop (may be deliberate voice). *(Fights)*
- Matt: "Well anyways, I'm Matt, calm cool and collected, you ever play RuneScape? I love RuneScape!" — 'calm cool and collected' - no commas. *(Fights)*
- Matt: "Hehe.... ya... it's not for everyone.. but hey! At least we can all agree RuneScape's the top MMO of all time... right pal?" — 'not for everyone..' - two dots. *(Fights)*
- Matt: "Buddy, I said top 5, you're starting to get me a little angry" — No full stop at the end. *(Fights)*
- Jordan: "No you cheated, don't cheat, don't cheat, no don't cheat. I won't allow cheaters in this server" — No full stop at the end. *(Finale)*
- Burak: "what the hell dude? I won, game over, now let me into the server" — Lower-case start, no end punctuation (maybe voice). *(Finale)*
- ???: "And announcing your new discord champion of this server...." — Lower-case 'discord' (it's 'Discord' everywhere else); four dots. *(Ending)*

### Drawn into art, can't follow the game

- "PAUSED  +  '@newcomer idle in \#arena-1' (small grey subtitle under it)" — The subtitle always says \#arena-1, whichever fight you pause in (the Defeat screen's text uses the real number). *(Menus)*
- "ARENA (banner, left) and \# ARENA-1 (banner, right); crowd signs GG EZ and L" — The banner always says ARENA-1, whichever fight you lost. *(Screens)*
- "ARENA (banner) and \# ARENA-1 (banner); a scrolling ticker 'GG  @NEWCOMER  W  LETS GO  +1' along the ring" — The banner always says ARENA-1, whichever fight you won. *(Screens)*

