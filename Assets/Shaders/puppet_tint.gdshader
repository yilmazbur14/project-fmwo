// The placeholder recolour on a boss Jordan has raised as a marionette (JordanPuppet), until that boss's red-and-black
// twin sheets are approved and in (JordanPuppetLayout): each texel's luminance mapped onto a black, deep red, red and bone
// ramp, and anything darker than `keyline` kept black, so every keyline stays one. Modulate still applies on top, so a
// hit flash still flashes.
// His defeat dissolves the puppet on this material rather than Disintegrate's, which would put the boss's own palette
// back for the length of the dissolve: `progress` 0 to 1 is disintegrate.gdshader's texel-by-texel sweep, and at 0 it
// does nothing. No TIME: everything that moves it is a node-bound tween, so a pause holds it.
shader_type canvas_item;

uniform vec4 deep : source_color = vec4(0.353, 0.055, 0.078, 1.0);
uniform vec4 red : source_color = vec4(0.702, 0.125, 0.165, 1.0);
uniform vec4 bone : source_color = vec4(0.910, 0.847, 0.784, 1.0);
uniform float keyline = 0.1;
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform vec2 frame_v = vec2(0.0, 1.0);
uniform float sweep = 0.6;
uniform float edge = 0.1;
uniform vec4 edge_color : source_color = vec4(1.0, 0.24, 0.71, 1.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

vec3 ramp(float lum) {
	if (lum <= keyline) {
		return vec3(0.0);
	}
	float t = (lum - keyline) / max(1.0 - keyline, 0.0001);
	if (t < 0.33) {
		return mix(vec3(0.0), deep.rgb, t / 0.33);
	}
	if (t < 0.7) {
		return mix(deep.rgb, red.rgb, (t - 0.33) / 0.37);
	}
	return mix(red.rgb, bone.rgb, (t - 0.7) / 0.3);
}

void fragment() {
	vec4 source = texture(TEXTURE, UV);
	float lum = dot(source.rgb, vec3(0.299, 0.587, 0.114));
	vec4 color = vec4(ramp(lum), source.a) * COLOR;
	vec2 texel = floor(UV / TEXTURE_PIXEL_SIZE);
	float down = clamp((UV.y - frame_v.x) / max(frame_v.y - frame_v.x, 0.0001), 0.0, 1.0);
	float order = mix(hash(texel), down, sweep);
	float gone = progress * (1.0 + edge) - edge;
	if (order < gone) {
		color.a = 0.0;
	} else if (order < gone + edge) {
		color.rgb = edge_color.rgb;
	}
	COLOR = color;
}
