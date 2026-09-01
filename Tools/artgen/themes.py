"""Per-level colour themes.

Every level reuses the same generators; only the palette and a couple of shape
switches change. That keeps three levels looking like three places in one game
rather than three games.
"""
from palette import mix

# --- Ridge Run: late afternoon desert, warm dirt, flat-topped buttes ---------
RIDGE = {
    "key": "Ridge",
    "crust":   (231, 205, 162),
    "band1":   (209, 166, 112),
    "band2":   (160, 100, 60),
    "band3":   (131, 76, 47),
    "fill":    (123, 71, 44),
    "stone":   (188, 132, 80),
    "scrub":   (108, 119, 76),
    "scrub2":  (70, 80, 50),
    "sky":     [(127, 152, 165), (183, 178, 168), (231, 189, 141), (238, 214, 178)],
    "far":     (140, 145, 158),
    "mid":     (168, 126, 92),
    "near":    (116, 70, 45),
    "silhouette": "mesa",
    "clear":   (0.498, 0.596, 0.647),
}

# --- Gravel Pit: overcast quarry, cold grey rock, cut benches ----------------
GRAVEL = {
    "key": "Gravel",
    "crust":   (196, 198, 196),
    "band1":   (160, 164, 166),
    "band2":   (118, 124, 129),
    "band3":   (92, 98, 104),
    "fill":    (86, 92, 98),
    "stone":   (140, 146, 150),
    "scrub":   (96, 106, 88),
    "scrub2":  (66, 74, 60),
    "sky":     [(150, 158, 166), (176, 181, 186), (198, 200, 200), (208, 208, 205)],
    "far":     (150, 156, 163),
    "mid":     (120, 127, 134),
    "near":    (82, 88, 94),
    "silhouette": "quarry",
    "clear":   (0.588, 0.620, 0.651),
}

# --- Dust Devil: dusk on the open flats, red rock under a burning sky --------
DUST = {
    "key": "Dust",
    "crust":   (232, 178, 128),
    "band1":   (206, 134, 84),
    "band2":   (166, 84, 54),
    "band3":   (126, 56, 44),
    "fill":    (118, 52, 42),
    "stone":   (196, 122, 78),
    "scrub":   (104, 88, 64),
    "scrub2":  (68, 56, 44),
    "sky":     [(66, 56, 92), (132, 78, 96), (206, 112, 78), (240, 168, 98)],
    "far":     (110, 82, 104),
    "mid":     (150, 84, 74),
    "near":    (96, 48, 44),
    "silhouette": "dune",
    "clear":   (0.259, 0.220, 0.361),
}

ALL = {"Ridge": RIDGE, "Gravel": GRAVEL, "Dust": DUST}


def sky_stops(theme):
    """Four-stop vertical gradient, top to horizon."""
    a, b, c, d = theme["sky"]
    return [(0.00, a), (0.34, mix(a, b, 0.8)), (0.55, b),
            (0.72, mix(b, c, 0.7)), (0.85, c), (1.00, d)]
