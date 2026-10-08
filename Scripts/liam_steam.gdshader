// Liam's steam (LiamSteam): two drifting layers of the steam tile (value noise until it ships), snapped to 3 px blocks,
// `density` thick, a clear bubble round the player, and thinned over anything fire-coloured beneath it so fire glows
// through. Its drift comes in from LiamSteam's own clock, never TIME, so a pause and a freeze hold it.
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, filter_nearest;
uniform sampler2D steam_tile : repeat_enable, filter_nearest;
uniform bool has_tile = false;
// Frames across the tile's sheet: a second frame is the second layer.
uniform float tile_frames = 1.0;
uniform float tile_px = 384.0;
uniform float density = 0.0;
uniform vec2 bubble_centre = vec2(0.0);
uniform float bubble_radius = 150.0;
uniform float feather = 70.0;
uniform float glow_through = 0.85;
// How thick the tile's two layers add up to: their alphas summed times this, capped at 1 (LiamStateMachine's
// steam_layer_gain; 0.65 before the user asked for the end of attack 3 to be very hard to see).
uniform float layer_gain = 1.2;
uniform vec2 drift_a = vec2(0.0);
uniform vec2 drift_b = vec2(0.0);
uniform float block = 3.0;
uniform vec4 steam_colour : source_color = vec4(0.9, 0.93, 0.96, 1.0);

varying vec2 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float cloud(vec2 p) {
	return value_noise(p) * 0.55 + value_noise(p * 2.1 + 17.0) * 0.3 + value_noise(p * 4.3 + 31.0) * 0.15;
}

vec4 tile_layer(vec2 p, float frame) {
	vec2 cell = fract(p);
	return texture(steam_tile, vec2((cell.x + frame) / tile_frames, cell.y));
}

void fragment() {
	vec2 w = floor(world / block) * block;
	float amount;
	vec3 colour = steam_colour.rgb;
	if (has_tile) {
		vec4 a = tile_layer((w + drift_a) / tile_px, 0.0);
		vec4 b = tile_layer((w + drift_b) / (tile_px * 1.37), tile_frames - 1.0);
		amount = clamp((a.a + b.a) * layer_gain, 0.0, 1.0);
		colour = mix(a.rgb, b.rgb, 0.5);
	} else {
		float n = cloud((w + drift_a) / 260.0) * 0.6 + cloud((w + drift_b) / 190.0 + 7.0) * 0.4;
		amount = smoothstep(0.18, 0.62, n);
	}
	float clear = smoothstep(bubble_radius, bubble_radius + feather, distance(w, bubble_centre));
	vec4 below = texture(screen_texture, SCREEN_UV);
	float warm = clamp((below.r - below.b - 0.25) * 3.0, 0.0, 1.0) * smoothstep(0.45, 0.8, max(below.r, below.g));
	COLOR = vec4(colour, density * amount * clear * (1.0 - glow_through * warm));
}
