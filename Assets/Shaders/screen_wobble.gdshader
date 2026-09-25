// Matt's Deafening Yell, once the mash has failed (ScreenWobble.gd): the arena and the booms swim in two
// crossed sine waves while the whole view sways round `pivot`, so an arrow's direction is hard to read;
// the input still takes the true one. Worked in base px - SCREEN_UV times the base size, never
// SCREEN_PIXEL_SIZE - so the bend is the same at any window size, and in blocks of the 3x art's texels,
// so every block shows one whole source pixel. What the sway turns in from beyond the view's edge is the
// edge colour, and the view darkens toward its corners. The phases come from a pausable node, never TIME,
// so a pause or a hit-stop holds it.
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, filter_nearest, repeat_disable;
uniform vec2 base_size = vec2(1920.0, 1080.0);
uniform float amount = 0.0;
uniform float amplitude_px = 12.0;
uniform float cross = 0.5;
uniform float wavelength_px = 260.0;
uniform float phase = 0.0;
// Radians, at full amount; the node scales it.
uniform float sway = 0.0;
uniform vec2 pivot = vec2(960.0, 540.0);
uniform float zoom = 1.0;
uniform float snap_px = 3.0;
uniform float vignette = 0.0;
uniform vec4 edge_color : source_color = vec4(0.106, 0.086, 0.220, 1.0);

void fragment() {
	vec2 p = (floor(SCREEN_UV * base_size / snap_px) + 0.5) * snap_px;
	float s = sin(-sway);
	float c = cos(-sway);
	vec2 q = pivot + mat2(vec2(c, s), vec2(-s, c)) * (p - pivot) / zoom;
	float a = amplitude_px * amount;
	q += vec2(a * sin(q.y / wavelength_px * TAU + phase),
			a * cross * sin(q.x / (wavelength_px * 1.6) * TAU - phase * 0.7));
	vec4 seen = texture(screen_texture, q / base_size);
	bool outside = q.x < 0.0 || q.y < 0.0 || q.x >= base_size.x || q.y >= base_size.y;
	vec3 colour = outside ? edge_color.rgb : seen.rgb;
	vec2 n = (p - base_size * 0.5) / (base_size * 0.5);
	float dark = vignette * amount * smoothstep(0.6, 1.45, length(n));
	COLOR = vec4(mix(colour, edge_color.rgb, dark), 1.0);
}
