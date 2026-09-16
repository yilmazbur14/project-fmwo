extends Node

# Autoload singleton. Set by a boss just before it transitions to the
# shared VictoryScene.tscn, so that scene knows which fight comes next.
# Empty string means "no next boss configured yet" - the Victory screen
# falls back to returning to the Main Menu.
var next_boss_scene: String = ""
