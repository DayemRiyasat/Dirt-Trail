"""Four backdrop layers per theme. All 1920x1080 and seamless on X.

The sky is a pure vertical gradient in every theme - anything with horizontal
structure shows the tile boundary once it has to repeat across a kilometre of
track. Depth in the other three comes from value and saturation, not blur.

Silhouette style is what makes the three levels read as three places: buttes for
the desert, cut benches for the quarry, smooth dunes for the flats.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import themes as TH
from draw import Canvas
from palette import INK, mix, shade
from unityasset import write_sprite_meta, folder_meta

ROOT = "Assets/Sprites/Parallax"
W, H = 1920, 1080


def wave(x, harmonics, w=W):
    """Seamless: every harmonic completes a whole number of cycles across w."""
    t = x / w * math.tau
    return sum(a * math.sin(t * k + p) for k, a, p in harmonics)


def _save(c, out, theme, name):
    path = "%s/%s_%s.png" % (out, theme["key"], name)
    c.save(path)
    write_sprite_meta(path, (W, H), ppu=40, pivot=(0.5, 0.5), wrap=1)
    return path


def gen_sky(theme, out):
    stops = TH.sky_stops(theme)
    c = Canvas(W, H, ss=1, bg=(*stops[0][1], 255))
    for y in range(H):
        t = y / (H - 1)
        for i in range(len(stops) - 1):
            a, b = stops[i], stops[i + 1]
            if a[0] <= t <= b[0]:
                k = (t - a[0]) / (b[0] - a[0])
                c.d.line([(0, y), (W, y)], fill=(*mix(a[1], b[1], k), 255))
                break
    return _save(c, out, theme, "Sky")


def gen_range_far(theme, out):
    c = Canvas(W, H, ss=2)
    base = 712
    col = theme["far"]
    style = theme["silhouette"]

    if style == "dune":
        peaks = [(2, 26, 0.4), (3, 18, 2.1), (7, 9, 4.0)]
    else:
        peaks = [(2, 46, 0.4), (3, 30, 2.1), (5, 21, 4.0), (11, 9, 1.2), (19, 5, 3.3)]

    ridge = [(x, base - 70 - wave(x, peaks)) for x in range(0, W + 1, 6)]
    c.poly(ridge + [(W, H), (0, H)], col)
    spur = [(x, base - 26 - wave(x, [(3, 26, 1.4), (7, 14, 0.2), (13, 6, 2.6)]))
            for x in range(0, W + 1, 6)]
    c.poly(spur + [(W, H), (0, H)], shade(col, -0.1))
    c.grain(6, seed=11)
    return _save(c, out, theme, "Range_Far")


# ------------------------------------------------------------- mid layer ----
def _mesas(c, body, base):
    """Flat-topped buttes: the shape that says desert."""
    mesas = [(140, 300, 236, 0.0), (420, 168, 150, 0.34), (700, 372, 300, 0.0),
             (1180, 214, 186, 0.0), (1420, 430, 262, 0.22), (1810, 190, 168, 0.0)]
    for cx, w, h, notch in mesas:
        top = base - h
        xl, xr = cx - w / 2.0, cx + w / 2.0
        cap = []
        for k in range(17):
            t = k / 16.0
            y = top + math.sin(t * 9.0) * 3.5
            if notch and t > 1.0 - notch:
                y = top + h * 0.13 + math.sin(t * 9.0) * 2.5
            cap.append((xl + w * t, y))
        poly = cap + [(xr + w * 0.13, base), (xl - w * 0.10, base)]
        for xo in (-W, 0, W):
            c.shape([(cx + xo - w * 0.72, base), (cx + xo - w * 0.5, base - h * 0.26),
                     (cx + xo + w * 0.54, base - h * 0.2), (cx + xo + w * 0.78, base)],
                    shade(body, -0.14), 3.0)
            c.shape([(p[0] + xo, p[1]) for p in poly], body, 3.0)
            sx = cx + w * 0.16
            face = [p for p in cap if p[0] >= sx]
            if face:
                c.poly([(p[0] + xo, p[1]) for p in face] +
                       [(xr + xo + w * 0.13, base), (sx + xo, base)], shade(body, -0.16))
            for i in range(4):
                y = top + h * (0.30 + i * 0.16)
                inset = w * (0.04 + i * 0.025)
                c.line([(xl + xo + inset, y), (xr + xo - inset, y + 2)],
                       shade(body, -0.22 if i % 2 else 0.12), 4.0)
            c.line([(p[0] + xo, p[1]) for p in cap], INK, 3.0)


def _quarry(c, body, base):
    """Cut benches: stepped terraces with a haul road scar across them."""
    walls = [(180, 420, 250), (700, 330, 190), (1120, 460, 300), (1640, 380, 215)]
    for cx, w, h in walls:
        xl, xr = cx - w / 2.0, cx + w / 2.0
        steps = 4
        for xo in (-W, 0, W):
            # Cut back from one side only, the way a quarry is actually worked:
            # symmetrical terraces read as a ziggurat, not a rock face.
            for s in range(steps):
                t = s / float(steps)
                y = base - h * (1.0 - t)
                left = xl + xo + w * 0.05 * s
                right = xr + xo - w * (0.04 + t * 0.52)
                tone = shade(body, 0.10 - s * 0.09)
                c.shape([(left, y), (right, y), (right, base), (left, base)], tone, 3.0)
                c.line([(left, y), (right, y)], shade(body, 0.26), 4.0)
            c.line([(xl + xo, base), (xr + xo, base)], INK, 3.0)


def _dunes(c, body, base):
    """Smooth rolling sand, nothing to catch the eye."""
    for i, (amp, freq, drop, tone) in enumerate((
            (52, [(2, 40, 0.6), (5, 18, 2.0)], 0, 0.10),
            (34, [(3, 26, 1.7), (7, 12, 0.4)], 40, -0.04),
            (22, [(4, 18, 3.1), (9, 8, 1.4)], 78, -0.16))):
        crest = [(x, base - amp - drop * -1 - wave(x, freq)) for x in range(0, W + 1, 6)]
        crest = [(x, y + drop) for x, y in crest]
        c.poly(crest + [(W, H), (0, H)], shade(body, tone))
        c.line(crest, shade(body, tone + 0.14), 3.0)


def gen_mesa_mid(theme, out):
    c = Canvas(W, H, ss=2)
    base = 828
    body = theme["mid"]
    style = theme["silhouette"]

    if style == "quarry":
        _quarry(c, body, base)
    elif style == "dune":
        _dunes(c, body, base)
    else:
        _mesas(c, body, base)

    plane = [(x, base + wave(x, [(4, 5, 0.7), (9, 3, 2.2)])) for x in range(0, W + 1, 8)]
    c.poly(plane + [(W, H), (0, H)], shade(body, -0.05))
    c.line(plane, INK, 3.4)
    c.grain(7, seed=13)
    c.speckle(300, shade(body, -0.2), (1.5, 4), box=(0, base - 20, W, H), seed=15, alpha=45)
    return _save(c, out, theme, "Mesa_Mid")


def gen_ridge_near(theme, out):
    c = Canvas(W, H, ss=2)
    rnd = random.Random(555 + len(theme["key"]))
    base = 930
    body = theme["near"]
    style = theme["silhouette"]

    harmonics = ([(2, 30, 1.9), (5, 16, 0.3), (9, 7, 2.7)] if style == "dune"
                 else [(2, 44, 1.9), (5, 26, 0.3), (9, 13, 2.7), (17, 6, 1.1)])
    crest = [(x, base - 96 - wave(x, harmonics)) for x in range(0, W + 1, 5)]
    c.poly(crest + [(W, H), (0, H)], body)
    c.line(crest, INK, 4.2)
    for i in range(1, len(crest)):
        if crest[i][1] < crest[i - 1][1]:
            c.line([crest[i - 1], crest[i]], shade(body, 0.26), 3.0)

    # what stands on the crest is the third thing that tells the levels apart
    count = {"mesa": 26, "quarry": 18, "dune": 10}[style]
    for _ in range(count):
        x = rnd.uniform(0, W)
        y = base - 96 - wave(x, harmonics)
        roll = rnd.random()
        for xo in (-W, 0, W):
            if style == "quarry":
                # spoil heaps and the odd bit of plant
                w = rnd.uniform(24, 60)
                h = rnd.uniform(14, 34)
                c.shape([(x + xo - w, y + 3), (x + xo - w * 0.4, y - h),
                         (x + xo + w * 0.3, y - h * 0.8), (x + xo + w, y + 3)],
                        shade(body, 0.12), 3.0)
            elif style == "dune":
                if roll < 0.5:
                    continue                      # the flats really are empty
                r = rnd.uniform(10, 22)
                c.shape([(x + xo - r, y + 3), (x + xo - r * 0.5, y - r * 0.6),
                         (x + xo + r * 0.6, y - r * 0.45), (x + xo + r, y + 3)],
                        shade(theme["scrub2"], 0.05), 3.0)
            elif roll < 0.22:
                h = rnd.uniform(46, 88)           # saguaro
                c.stroke([(x + xo, y + 4), (x + xo, y - h)], theme["scrub2"], 13, 3.0)
                if rnd.random() > 0.35:
                    c.stroke([(x + xo, y - h * 0.55), (x + xo + 22, y - h * 0.55),
                              (x + xo + 22, y - h * 0.82)], theme["scrub2"], 10, 3.0)
            else:
                r = rnd.uniform(12, 30)
                c.shape([(x + xo - r, y + 3), (x + xo - r * 0.6, y - r * 0.75),
                         (x + xo, y - r * 0.95), (x + xo + r * 0.7, y - r * 0.6),
                         (x + xo + r, y + 3)], theme["scrub2"], 3.0)

    c.grain(8, seed=17)
    c.speckle(260, shade(body, -0.25), (1.5, 4.5), box=(0, base - 120, W, H),
              seed=19, alpha=50)
    return _save(c, out, theme, "Ridge_Near")


def gen_scrub_fore(theme, out):
    """Menu-only foreground band. Almost pure silhouette."""
    c = Canvas(W, H, ss=2)
    rnd = random.Random(909)
    base = 1042
    body = shade(theme["near"], -0.3)

    harmonics = [(3, 14, 0.9), (7, 8, 2.4), (15, 4, 1.7)]
    lip = [(x, base - 18 - wave(x, harmonics)) for x in range(0, W + 1, 5)]
    c.poly(lip + [(W, H), (0, H)], body)

    for _ in range(30):
        x = rnd.uniform(0, W)
        y = base - 18 - wave(x, harmonics)
        r = rnd.uniform(16, 46)
        for xo in (-W, 0, W):
            if rnd.random() < 0.3:
                c.poly([(x + xo - r, y + 8), (x + xo - r * 0.7, y - r * 0.5),
                        (x + xo - r * 0.1, y - r * 0.72), (x + xo + r * 0.6, y - r * 0.45),
                        (x + xo + r, y + 8)], body)
            else:
                n = rnd.randint(5, 9)
                for k in range(n):
                    a = -90 + (k - n / 2) * rnd.uniform(9, 17)
                    ln = r * rnd.uniform(0.8, 1.5)
                    c.line([(x + xo, y + 6),
                            (x + xo + math.cos(math.radians(a)) * ln,
                             y + math.sin(math.radians(a)) * ln)], body, 5.0)
    c.grain(6, seed=23)
    return _save(c, out, theme, "Scrub_Fore")


def main():
    os.makedirs(ROOT, exist_ok=True)
    folder_meta(ROOT)
    for key, theme in TH.ALL.items():
        out = "%s/%s" % (ROOT, key)
        os.makedirs(out, exist_ok=True)
        folder_meta(out)
        for fn in (gen_sky, gen_range_far, gen_mesa_mid, gen_ridge_near, gen_scrub_fore):
            print("  ", fn(theme, out))


if __name__ == "__main__":
    main()
