"""Dirt Trail palette. Warm desert earth, one cool accent for depth, ink outlines.

Deliberately narrow: 4 earth ramps, 1 vegetation ramp, 1 signal orange, 1 cool
atmospheric blue. Everything in the game is mixed from these.
"""

INK        = (34, 24, 20)          # every outline in the game
INK_SOFT   = (58, 42, 34)

# earth ramp (light -> dark)
SAND_50    = (243, 228, 199)
SAND_100   = (231, 205, 162)
CLAY_200   = (209, 166, 112)
CLAY_300   = (188, 132, 80)
CLAY_400   = (160, 100, 60)
RUST_500   = (131, 76, 47)
EARTH_600  = (98, 58, 39)
BARK_700   = (68, 43, 31)
BARK_800   = (46, 31, 24)

# vegetation
SAGE_300   = (150, 158, 112)
SAGE_500   = (108, 119, 76)
SAGE_700   = (70, 80, 50)

# atmosphere / distance
HAZE_100   = (226, 197, 165)
DUSK_300   = (162, 152, 152)
DUSK_500   = (118, 112, 119)
SKY_HIGH   = (127, 152, 165)
SKY_MID    = (183, 178, 168)
SKY_LOW    = (231, 189, 141)

# signal
ORANGE     = (216, 94, 38)
ORANGE_HI  = (240, 148, 62)
CREAM      = (247, 240, 224)
STEEL      = (124, 130, 136)
STEEL_HI   = (176, 182, 188)
CHROME     = (198, 202, 206)
RUBBER     = (44, 41, 40)
RUBBER_HI  = (72, 68, 66)

# bike liveries
LIVERY = {
    "scout": {          # Bike A - orange/cream, scrappy, well-used
        "primary":   ORANGE,
        "primary_d": (168, 66, 24),
        "accent":    CREAM,
        "plate":     (238, 226, 200),
        "seat":      (52, 44, 42),
        "jersey":    ORANGE,
        "jersey_d":  (168, 66, 24),
        "pants":     (56, 52, 54),
        "helmet":    CREAM,
        "helmet_d":  (206, 194, 170),
    },
    "mule": {           # Bike B - sage/steel, heavier, older
        "primary":   SAGE_500,
        "primary_d": SAGE_700,
        "accent":    (206, 196, 168),
        "plate":     (216, 206, 178),
        "seat":      (46, 42, 40),
        "jersey":    (206, 196, 168),
        "jersey_d":  (160, 152, 128),
        "pants":     (62, 60, 52),
        "helmet":    SAGE_500,
        "helmet_d":  SAGE_700,
    },
}


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(c, t):
    """t<0 toward ink, t>0 toward sand."""
    return mix(c, INK if t < 0 else SAND_50, abs(t))
