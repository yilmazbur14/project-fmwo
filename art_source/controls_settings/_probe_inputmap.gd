extends SceneTree


func _initialize() -> void:
	_go.call_deferred()


func _go() -> void:
	await process_frame
	for action in ["move_up", "punch", "dodge", "block", "ui_accept", "ui_cancel", "ui_up", "ui_select"]:
		var bits := PackedStringArray()
		for event in InputMap.action_get_events(action):
			if event is InputEventKey:
				bits.append("key:%d/%d" % [event.keycode, event.physical_keycode])
			elif event is InputEventJoypadButton:
				bits.append("btn:%d" % event.button_index)
			elif event is InputEventJoypadMotion:
				bits.append("axis:%d@%.1f" % [event.axis, event.axis_value])
		print("ACTION %s [%s]" % [action, ", ".join(bits)])
	var s := root.get_node("InputSettings")
	print("device=%d move=%s punch=%s dodge=%s block=%s" % [s.device, s.move_name, s.punch_name, s.dodge_name, s.block_name])
	print("labels punch key=%s pad=%s frame=%d" % [s.key_label_for(&"punch"), s.pad_label_for(&"punch"), s.pad_frame_for(&"punch")])
	print("cfg exists=%s" % FileAccess.file_exists(s.SAVE_PATH))
	print(FileAccess.get_file_as_string(s.SAVE_PATH))
	quit()
