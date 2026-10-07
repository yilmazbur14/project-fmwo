// A figure eaten away texel by texel from the top down as `progress` runs 0 to 1 (Disintegrate.gd), each texel going
// hot pink just before it goes. The order is noise on whole texels of the sheet, so at 3x it goes a pixel block at a
// time, mixed with the height down the frame for the sweep. `progress` comes from a node-bound tween, never TIME, so
// a pause holds it.
shader_type canvas_item;

uniform float progress : hint_range(0.0, 1.0) = 0.0;
// The frame's top and bottom in the sheet's UV, for a sheet of more than one row.
uniform vec2 frame_v = vec2(0.0, 1.0);
// How much of the order is the sweep down the frame rather than the noise.
uniform float sweep = 0.6;
uniform float edge = 0.1;
uniform vec4 edge_color : source_color = vec4(1.0, 0.24, 0.71, 1.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec4 color = texture(TEXTURE, UV) * COLOR;
	vec2 texel = floor(UV / TEXTURE_PIXEL_SIZE);
	float down = clamp((UV.y - frame_v.x) / max(frame_v.y - frame_v.x, 0.0001), 0.0, 1.0);
	float order = mix(hash(texel), down, sweep);
	// At 0 every texel is there, and at 1 the last has gone, its pink edge with it.
	float gone = progress * (1.0 + edge) - edge;
	if (order < gone) {
		color.a = 0.0;
	} else if (order < gone + edge) {
		color.rgb = edge_color.rgb;
	}
	COLOR = color;
}
