"""Shared bits of the final-beam approval rig. READS the live repo's art, WRITES only under APPROVAL."""
import os
import numpy as np
from PIL import Image

REPO = "C:/Users/theyi/OneDrive/Documents/new-game-project"
APPROVAL = "C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/god_final_beam/approval"
WORK = "C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/god_final_beam/work"


def out_path(*parts):
    p = os.path.realpath(os.path.join(APPROVAL, *parts))
    root = os.path.realpath(APPROVAL)
    if not p.startswith(root):
        raise RuntimeError("refusing to write outside the approval folder: " + p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def save_png(img, *parts):
    p = out_path(*parts)
    img.save(p)
    return p


def repo_img(rel):
    return Image.open(os.path.join(REPO, rel)).convert("RGBA")


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# Burak's own seven colours, measured off player_4dir_sheet.png (no keyline: black is hair and shoes only).
BURAK = {
    '#': hexc("000000"),   # hair, shoes
    's': hexc("d79864"),   # skin
    'd': hexc("ac714f"),   # skin shadow
    'b': hexc("2464bd"),   # shorts / gloves
    'n': hexc("162fbb"),   # shorts / gloves shadow
    'l': hexc("3883c9"),   # shorts light
    'r': hexc("ac3232"),   # headband
}


def grid_to_img(rows, pal=BURAK, w=None, h=None):
    h = h or len(rows)
    w = w or max(len(r) for r in rows)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                px[x, y] = pal[ch]
            elif ch not in ". ":
                raise ValueError("bad char %r at %d,%d" % (ch, x, y))
    return im


def strip(frames):
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.alpha_composite(f, (i * w, 0))
    return s


def zoomed(img, s, bg=(26, 20, 38, 255)):
    b = Image.new("RGBA", img.size, bg)
    b.alpha_composite(img)
    return b.resize((img.width * s, img.height * s), Image.NEAREST)


# ---------------------------------------------------------------------------------------------------------------
# A tiny canvas that draws like Godot does: world px -> screen px through a Camera2D (zoom, focus), at a render
# scale (0.5 = the 960x540 window the project's captures use). Sprites are sampled nearest, rotated/scaled as quads.
class Canvas:
    def __init__(self, w=960, h=540, render_scale=0.5):
        self.w, self.h = w, h
        self.rs = render_scale
        self.buf = np.zeros((h, w, 3), np.float32)

    def set_camera(self, zoom, focus):
        self.zoom = zoom
        self.focus = np.array(focus, np.float32)

    def world_to_screen(self, p):
        p = np.array(p, np.float32)
        return (p - self.focus) * self.zoom * self.rs + np.array([self.w / 2, self.h / 2], np.float32)

    def fill(self, rgb):
        self.buf[:] = np.array(rgb[:3], np.float32) / 255.0

    def screen_image(self, img, scale_px, mode="normal", alpha=1.0):
        """Screen-space sprite (CanvasLayer), top-left at 0,0, scale_px screen px a texel at 1920x1080."""
        self._draw(img, np.array([[scale_px * self.rs, 0], [0, scale_px * self.rs]]), np.zeros(2), mode, alpha)

    def sprite(self, img, pivot_texel, world_pos, texel_px=3.0, rot=0.0, mode="normal", alpha=1.0, flip_h=False,
               sx=1.0, sy=1.0, tint=None):
        """World sprite: texel `pivot_texel` (a point in texel coords, e.g. (16,16) = centre of a 32 cell) lands on
        `world_pos`; texel_px world px a texel; rot radians (positive = clockwise on screen, Godot's)."""
        k = texel_px * self.zoom * self.rs
        c, s_ = np.cos(rot), np.sin(rot)
        R = np.array([[c, -s_], [s_, c]], np.float32)
        A = R @ np.array([[k * sx * (-1 if flip_h else 1), 0], [0, k * sy]], np.float32)
        origin = self.world_to_screen(world_pos)
        # screen = A @ (uv - pivot) + origin  ->  screen = A @ uv + (origin - A @ pivot)
        off = origin - A @ np.array(pivot_texel, np.float32)
        self._draw(img, A, off, mode, alpha, tint)

    def _draw(self, img, A, off, mode, alpha, tint=None):
        src = np.asarray(img.convert("RGBA"), np.float32) / 255.0
        h, w = src.shape[:2]
        corners = np.array([[0, 0], [w, 0], [0, h], [w, h]], np.float32)
        sc = corners @ A.T + off
        x0 = max(int(np.floor(sc[:, 0].min())), 0)
        x1 = min(int(np.ceil(sc[:, 0].max())), self.w)
        y0 = max(int(np.floor(sc[:, 1].min())), 0)
        y1 = min(int(np.ceil(sc[:, 1].max())), self.h)
        if x1 <= x0 or y1 <= y0:
            return
        Ai = np.linalg.inv(A)
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        px = np.stack([xs + 0.5 - off[0], ys + 0.5 - off[1]], -1)
        uv = px @ Ai.T
        u = np.floor(uv[..., 0]).astype(np.int32)
        v = np.floor(uv[..., 1]).astype(np.int32)
        ok = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        uu = np.clip(u, 0, w - 1)
        vv = np.clip(v, 0, h - 1)
        col = src[vv, uu]
        a = col[..., 3] * ok * alpha
        rgb = col[..., :3]
        if tint is not None:
            rgb = rgb * np.array(tint[:3], np.float32)
        region = self.buf[y0:y1, x0:x1]
        if mode == "add":
            region += rgb * a[..., None]
        else:
            region[:] = region * (1 - a[..., None]) + rgb * a[..., None]
        np.clip(region, 0, 1, out=region)

    def rect_screen(self, x, y, w, h, rgb, alpha=1.0, mode="normal"):
        x0, y0, x1, y1 = max(int(x), 0), max(int(y), 0), min(int(x + w), self.w), min(int(y + h), self.h)
        if x1 <= x0 or y1 <= y0:
            return
        c = np.array(rgb[:3], np.float32) / 255.0
        r = self.buf[y0:y1, x0:x1]
        if mode == "add":
            r += c * alpha
        else:
            r[:] = r * (1 - alpha) + c * alpha
        np.clip(r, 0, 1, out=r)

    def flash(self, rgb, alpha):
        c = np.array(rgb[:3], np.float32) / 255.0
        self.buf[:] = self.buf * (1 - alpha) + c * alpha

    def image(self):
        return Image.fromarray((np.clip(self.buf, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
