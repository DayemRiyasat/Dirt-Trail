"""Terrain art: the Sprite Shape edge sprite and its fill, one set per theme.

The edge sprite carries every bit of surface interest - crust, strata, stones,
scrub - because it sits right under the rider and never repeats visibly. The
fill is almost flat: it covers enormous areas and any pattern in it reads as a
grid of seams.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import themes as TH
from draw import Canvas
from palette import INK, BARK_800, shade
from unityasset import write_sprite_meta, folder_meta

ROOT = "Assets/Sprites/Terrain"
EW, EH = 1024, 200
SURFACE = 78.0


def ridge(x, w=EW):
    """Seamless surface wobble: only integer harmonics of the tile width."""
    t = x / w * math.tau
    return (math.sin(t * 3) * 5.0 + math.sin(t * 7 + 1.1) * 2.6 +
            math.sin(t * 13 + 2.3) * 1.4 + math.sin(t * 23 + 0.4) * 0.7)


def gen_edge(theme, out):
    c = Canvas(EW, EH, ss=2)
    rnd = random.Random(4242 + len(theme["key"]))
    top = [(x, SURFACE + ridge(x)) for x in range(0, EW + 1, 4)]

    c.poly(top + [(EW, EH), (0, EH)], theme["band1"])
    for col, depth in ((theme["band1"], 16), (theme["band2"], 46),
                       (theme["band3"], 92), (shade(theme["band3"], -0.12), 150)):
        band = ([(x, SURFACE + ridge(x) + depth) for x in range(0, EW + 1, 4)] +
                [(EW, EH), (0, EH)])
        c.poly(band, col)

    c.poly(top + [(x, SURFACE + ridge(x) + 9) for x in range(EW, -1, -4)], theme["crust"])

    for depth, wob, wid in ((58, 3, 2.4), (96, 5, 3.2), (150, 4, 2.0)):
        pts = [(x, SURFACE + ridge(x) * 0.4 + depth + math.sin(x / 90.0 * math.tau) * wob)
               for x in range(0, EW + 1, 8)]
        c.line(pts, shade(theme["band3"], -0.28), wid)

    for _ in range(20):                                   # embedded stones
        x = rnd.uniform(0, EW)
        y = rnd.uniform(SURFACE + 26, EH - 16)
        r = rnd.uniform(3.5, 8)
        col = shade(theme["stone"], rnd.uniform(-0.12, 0.14))
        facets = [(math.cos(a) * r * rnd.uniform(0.7, 1.2),
                   math.sin(a) * r * rnd.uniform(0.7, 1.2))
                  for a in [k * math.tau / 6 for k in range(6)]]
        for xo in (x - EW, x, x + EW):
            c.shape([(xo + fx, y + fy) for fx, fy in facets], col, 1.5)

    c.line(top, INK, 5.0)

    for _ in range(9):                                    # berm lumps
        x = rnd.uniform(0, EW)
        w = rnd.uniform(30, 90)
        h = rnd.uniform(5, 15)
        lump = [(x - w, SURFACE + ridge(x - w) + 4)]
        for k in range(1, 13):
            t = k / 12.0
            px = x - w + 2 * w * t
            lump.append((px, SURFACE + ridge(px) - math.sin(t * math.pi) * h))
        lump.append((x + w, SURFACE + ridge(x + w) + 4))
        for xo in (-EW, 0, EW):
            c.shape([(p[0] + xo, p[1]) for p in lump], theme["band1"], 2.4)

    for _ in range(7):                                    # loose rock on top
        x = rnd.uniform(0, EW)
        base = SURFACE + ridge(x)
        r = rnd.uniform(4, 10)
        col = shade(theme["stone"], rnd.uniform(-0.05, 0.22))
        for xo in (-EW, 0, EW):
            c.shape([(x + xo - r, base + 2), (x + xo - r * 0.6, base - r * 0.8),
                     (x + xo + r * 0.3, base - r), (x + xo + r, base + 1)], col, 2.2)

    # The quarry is bare rock; the other two grow something on the crust.
    tufts = 4 if theme["silhouette"] == "quarry" else 14
    for _ in range(tufts):
        x = rnd.uniform(0, EW)
        base = SURFACE + ridge(x) + 1
        n = rnd.randint(3, 6)
        col = theme["scrub"] if rnd.random() > 0.4 else theme["scrub2"]
        for xo in (-EW, 0, EW):
            for k in range(n):
                a = -90 + (k - n / 2) * rnd.uniform(11, 22)
                ln = rnd.uniform(9, 20)
                c.line([(x + xo, base),
                        (x + xo + math.cos(math.radians(a)) * ln,
                         base + math.sin(math.radians(a)) * ln)], col, 2.6)

    c.grain(12, seed=9)
    c.speckle(420, BARK_800, (1, 3), box=(0, SURFACE + 6, EW, EH), seed=21, alpha=34)
    c.speckle(220, theme["crust"], (1, 2.6), box=(0, SURFACE + 4, EW, EH * 0.6),
              seed=22, alpha=38)

    path = "%s/%s Edge.png" % (out, theme["key"])
    c.save(path)
    write_sprite_meta(path, (EW, EH), ppu=100, pivot=(0.5, 0.5), wrap=1)
    return path


def gen_fill(theme, out):
    """Deliberately almost flat: all the interest lives in the edge sprite."""
    S = 256
    c = Canvas(S, S, ss=1, bg=(*theme["fill"], 255))
    c.grain(5, seed=31)
    c.speckle(260, BARK_800, (0.7, 1.4), seed=33, alpha=12)

    path = "%s/%s Fill.png" % (out, theme["key"])
    c.save(path)
    write_sprite_meta(path, (S, S), ppu=100, pivot=(0.5, 0.5), wrap=1)
    return path


def gen_corner(theme, out):
    c = Canvas(64, 64, ss=2, bg=(*theme["band1"], 255))
    c.grain(14, seed=5)
    path = "%s/%s Corner.png" % (out, theme["key"])
    c.save(path)
    write_sprite_meta(path, (64, 64), ppu=100, pivot=(0.5, 0.5), wrap=1)
    return path


def main():
    os.makedirs(ROOT, exist_ok=True)
    folder_meta(ROOT)
    for key, theme in TH.ALL.items():
        out = "%s/%s" % (ROOT, key)
        os.makedirs(out, exist_ok=True)
        folder_meta(out)
        for p in (gen_edge(theme, out), gen_fill(theme, out), gen_corner(theme, out)):
            print("  ", p)


if __name__ == "__main__":
    main()
