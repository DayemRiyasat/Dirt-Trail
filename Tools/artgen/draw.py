"""Thin vector-ish drawing layer over PIL with consistent ink outlines.

Everything is drawn at `ss` supersampling and downsampled once, which is what
gives the whole game a single consistent edge quality.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageChops

from palette import INK, rgba


class Canvas:
    def __init__(self, w, h, ss=4, bg=(0, 0, 0, 0)):
        self.w, self.h, self.ss = w, h, ss
        self.img = Image.new("RGBA", (w * ss, h * ss), bg)
        self.d = ImageDraw.Draw(self.img)

    # ---- coordinate helpers -------------------------------------------------
    def _p(self, pts):
        s = self.ss
        return [(x * s, y * s) for (x, y) in pts]

    def _w(self, width):
        return max(1, int(round(width * self.ss)))

    # ---- primitives ---------------------------------------------------------
    def line(self, pts, color, width, cap_round=True):
        s = self._p(pts)
        self.d.line(s, fill=rgba(color), width=self._w(width), joint="curve")
        if cap_round and width > 1.5:
            r = width * 0.5
            for p in (pts[0], pts[-1]):
                self.disc(p, r, color)

    def disc(self, c, r, color):
        x, y = c
        s = self.ss
        self.d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=rgba(color))

    def ring(self, c, r, color, width):
        x, y = c
        s = self.ss
        self.d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s],
                       outline=rgba(color), width=self._w(width))

    def poly(self, pts, color, outline=None, ow=0):
        self.d.polygon(self._p(pts), fill=rgba(color) if color else None,
                       outline=rgba(outline) if outline else None,
                       width=self._w(ow) if ow else 1)

    def rect(self, box, color, radius=0, outline=None, ow=0):
        x0, y0, x1, y1 = box
        s = self.ss
        b = [x0 * s, y0 * s, x1 * s, y1 * s]
        if radius:
            self.d.rounded_rectangle(b, radius=radius * s, fill=rgba(color) if color else None,
                                     outline=rgba(outline) if outline else None,
                                     width=self._w(ow) if ow else 1)
        else:
            self.d.rectangle(b, fill=rgba(color) if color else None,
                             outline=rgba(outline) if outline else None,
                             width=self._w(ow) if ow else 1)

    def arc(self, c, r, a0, a1, color, width):
        x, y = c
        s = self.ss
        self.d.arc([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s],
                   a0, a1, fill=rgba(color), width=self._w(width))

    # ---- outlined strokes ---------------------------------------------------
    def stroke(self, pts, color, width, ow=3.0, ink=INK):
        """A tube with a consistent ink outline."""
        self.line(pts, ink, width + ow * 2)
        self.line(pts, color, width)

    def shape(self, pts, color, ow=3.0, ink=INK):
        """Filled polygon with a consistent ink outline drawn inside-out."""
        self.poly(pts, ink)
        self.line(list(pts) + [pts[0]], ink, ow * 2)
        self.poly(pts, color)
        self.line(list(pts) + [pts[0]], ink, ow)

    def outlined_disc(self, c, r, color, ow=3.0, ink=INK):
        self.disc(c, r + ow * 0.5, ink)
        self.disc(c, r - ow * 0.5, color)

    # ---- texture ------------------------------------------------------------
    def grain(self, amount=10, seed=1, scale=1):
        rnd = random.Random(seed)
        w, h = self.img.size
        nw, nh = max(1, w // (4 * scale)), max(1, h // (4 * scale))
        noise = Image.new("L", (nw, nh))
        noise.putdata([rnd.randint(0, 255) for _ in range(nw * nh)])
        noise = noise.resize((w, h), Image.BILINEAR)
        arr = Image.merge("RGB", (noise, noise, noise)).point(lambda v: 128 + (v - 128) * amount // 100)
        base = self.img.convert("RGB")
        blended = ImageChops.overlay(base, arr)
        self.img = Image.merge("RGBA", (*blended.split(), self.img.split()[3]))
        self.d = ImageDraw.Draw(self.img)

    def speckle(self, n, color, r_range=(1, 3), box=None, seed=2, alpha=90):
        rnd = random.Random(seed)
        x0, y0, x1, y1 = box or (0, 0, self.w, self.h)
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        s = self.ss
        for _ in range(n):
            x = rnd.uniform(x0, x1)
            y = rnd.uniform(y0, y1)
            r = rnd.uniform(*r_range)
            ld.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s],
                       fill=(color[0], color[1], color[2], alpha))
        self.img = Image.alpha_composite(self.img, layer)
        self.d = ImageDraw.Draw(self.img)

    def mask_to_alpha(self):
        """Keep only pixels where something was drawn (used for texture passes)."""
        return self.img.split()[3]

    # ---- output -------------------------------------------------------------
    def finish(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)

    def save(self, path):
        out = self.finish()
        out.save(path)
        return out.size


def jitter_path(pts, amp=1.5, seed=0, subdiv=3):
    """Break the machine-perfection of a polyline: subdivide then wobble."""
    rnd = random.Random(seed)
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for k in range(subdiv):
            t = k / subdiv
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            if 0 < i or k > 0:
                x += rnd.uniform(-amp, amp)
                y += rnd.uniform(-amp, amp)
            out.append((x, y))
    out.append(pts[-1])
    return out


def bezier(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def rot(p, c, deg):
    a = math.radians(deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a),
            c[1] + dx * math.sin(a) + dy * math.cos(a))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def offset(p, dx, dy):
    return (p[0] + dx, p[1] + dy)
