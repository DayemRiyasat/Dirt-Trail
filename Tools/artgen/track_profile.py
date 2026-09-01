"""The three track profiles, plus a ballistic check on every jump.

Each track is a list of named sections of (x, y, smooth) control points, where
smooth 1 rolls and 0 is a hard lip. `verify()` flies each takeoff at a spread of
entry speeds and reports where it comes down, so landing ramps are sized from
numbers rather than guesses.

The three are deliberately opposed:
  Ridge Run   balanced trail, everything in moderation, the one you learn on
  Gravel Pit  tight and technical, short steep faces, low airtime, unforgiving
  Dust Devil  wide open and fast, few features but each one enormous
"""
import math


class TrackProfile:
    def __init__(self, key, name, blurb, theme, sections, lips,
                 start_x=10.0, finish_pad=14.0, deep_y=-320.0, ortho=12.5):
        self.key = key
        self.name = name
        self.blurb = blurb
        self.theme = theme
        self.sections = sections
        self.lips = set(lips)
        self.start_x = start_x
        self.deep_y = deep_y
        self.ortho = ortho
        self.finish_x = self.ridge()[-1][0] - finish_pad
        self._surface = None

    # ---------------------------------------------------------- geometry --
    def ridge(self):
        out = []
        for _name, pts in self.sections:
            out.extend(pts)
        return out

    def section_bounds(self):
        return {name: (pts[0][0], pts[-1][0]) for name, pts in self.sections}

    def tangents(self):
        """Catmull-Rom style handles, scaled by each point's smooth factor."""
        pts = self.ridge()
        out = []
        for i, (x, y, smooth) in enumerate(pts):
            prev = pts[max(0, i - 1)]
            nxt = pts[min(len(pts) - 1, i + 1)]
            tx = (nxt[0] - prev[0]) / 6.0 * smooth
            ty = (nxt[1] - prev[1]) / 6.0 * smooth

            span = min(abs(x - prev[0]), abs(nxt[0] - x)) or abs(nxt[0] - x)
            limit = span * 0.45
            mag = math.hypot(tx, ty)
            if mag > limit and mag > 0.0001:
                tx *= limit / mag
                ty *= limit / mag
            out.append(((-tx, -ty), (tx, ty)))
        return out

    def sample(self, detail=10):
        pts = self.ridge()
        tans = self.tangents()
        poly = []
        for i in range(len(pts) - 1):
            p0 = (pts[i][0], pts[i][1])
            p3 = (pts[i + 1][0], pts[i + 1][1])
            p1 = (p0[0] + tans[i][1][0], p0[1] + tans[i][1][1])
            p2 = (p3[0] + tans[i + 1][0][0], p3[1] + tans[i + 1][0][1])
            steps = detail if i < len(pts) - 2 else detail + 1
            for s in range(steps):
                t = s / float(detail)
                u = 1 - t
                poly.append((
                    u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
                ))
        poly.append((pts[-1][0], pts[-1][1]))
        return poly

    def surface(self):
        if self._surface is None:
            self._surface = self.sample(16)
        return self._surface

    def height_at(self, x):
        """Height of the real bezier surface, so props sit flat on curves."""
        poly = self.surface()
        if x <= poly[0][0]:
            return poly[0][1]
        for i in range(len(poly) - 1):
            x0, y0 = poly[i]
            x1, y1 = poly[i + 1]
            if x0 <= x <= x1:
                t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
                return y0 + (y1 - y0) * t
        return poly[-1][1]

    def slope_at(self, x, d=1.5):
        return math.degrees(math.atan2(self.height_at(x + d) - self.height_at(x - d), 2 * d))

    @staticmethod
    def offset_polyline(poly, distance):
        out = []
        for i, p in enumerate(poly):
            a = poly[max(0, i - 1)]
            b = poly[min(len(poly) - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / length, dx / length
            if ny < 0:
                nx, ny = -nx, -ny
            out.append((p[0] + nx * distance, p[1] + ny * distance))
        return out

    # ------------------------------------------------------------- check --
    def verify(self, gravity_scale=1.6, speeds=(16.0, 19.0, 22.0), collider_offset=0.22):
        g = 9.81 * gravity_scale
        poly = self.offset_polyline(self.sample(14), collider_offset)
        report = []
        for name, pts in self.sections:
            if name not in self.lips:
                continue
            lip = min(pts, key=lambda p: p[2])
            lx, ly, _ = lip
            before = pts[max(0, pts.index(lip) - 1)]
            angle = math.degrees(math.atan2(ly - before[1], lx - before[0]))

            rows = []
            for v in speeds:
                vx = v * math.cos(math.radians(angle))
                vy = v * math.sin(math.radians(angle))
                t, x = 0.0, lx
                while t < 6.0:
                    t += 1 / 120.0
                    x = lx + vx * t
                    y = ly + collider_offset + vy * t - 0.5 * g * t * t
                    if x > lx + 3 and y <= _ground(poly, x):
                        break
                rows.append((v, round(t, 2), round(x - lx, 1)))
            report.append((name, round(angle, 1), rows))
        return report


def _ground(poly, x):
    for i in range(len(poly) - 1):
        if poly[i][0] <= x <= poly[i + 1][0]:
            x0, y0 = poly[i]
            x1, y1 = poly[i + 1]
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return -9999.0


# =============================================================== RIDGE RUN ==
RIDGE_RUN = TrackProfile(
    "RidgeRun", "RIDGE RUN",
    "The one you learn on. A bit of everything, nothing that bites.",
    "Ridge",
    [
        ("DROP IN", [
            (0, 8.0, 0.3), (18, 7.0, 1.0), (36, 1.0, 1.0), (54, -7.0, 1.0),
            (70, -12.0, 0.8),
        ]),
        ("ROLLERS", [
            (82, -8.0, 1.0), (94, -14.5, 1.0), (106, -9.0, 1.0), (118, -16.0, 1.0),
            (130, -10.0, 1.0), (142, -17.5, 1.0),
        ]),
        ("FIRST KICKER", [
            (154, -16.0, 1.0), (166, -9.0, 0.55), (173, -5.6, 0.12),
            (184, -19.0, 0.5), (194, -11.0, 0.35), (212, -19.5, 0.8), (224, -22.0, 1.0),
        ]),
        ("DOUBLE UP", [
            (236, -19.0, 0.8), (247, -15.5, 0.3), (262, -25.0, 0.6), (274, -21.0, 0.8),
            (286, -17.5, 0.3), (296, -24.5, 0.6), (302, -22.0, 0.8),
        ]),
        ("WHOOPS", [
            (312, -25.0, 1.0), (320, -29.5, 1.0), (328, -25.5, 1.0), (336, -30.0, 1.0),
            (344, -26.0, 1.0),
        ]),
        ("THE BOWL", [
            (356, -33.0, 1.0), (368, -38.0, 1.0), (382, -33.0, 0.8), (394, -26.0, 0.45),
            (402, -21.0, 0.1), (418, -39.0, 0.6), (430, -31.0, 0.3), (466, -48.0, 0.9),
            (482, -51.0, 1.0),
        ]),
        ("STAIRCASE", [
            (496, -46.0, 0.7), (506, -41.0, 0.15), (520, -46.0, 0.6), (530, -40.0, 0.7),
            (540, -35.0, 0.15), (554, -40.0, 0.6), (564, -34.0, 0.7), (574, -29.0, 0.15),
            (588, -34.0, 0.6),
        ]),
        ("STEP DOWN", [
            (600, -30.0, 0.5), (610, -29.6, 0.1), (626, -46.0, 0.4), (646, -54.0, 0.9),
            (660, -57.0, 1.0),
        ]),
        ("RHYTHM", [
            (672, -54.0, 0.8), (680, -50.0, 0.15), (694, -60.0, 0.5), (704, -55.0, 0.7),
            (712, -51.5, 0.15), (726, -61.5, 0.5), (736, -56.5, 0.7), (744, -53.0, 0.15),
            (758, -63.0, 0.5), (770, -60.0, 0.9),
        ]),
        ("TABLETOP", [
            (782, -56.0, 0.6), (792, -51.0, 0.12), (806, -50.6, 1.0), (820, -51.0, 1.0),
            (832, -58.0, 0.6), (844, -63.0, 1.0),
        ]),
        ("THE HIP", [
            (856, -60.0, 0.8), (866, -55.0, 0.15), (880, -68.0, 0.5), (892, -63.0, 0.7),
        ]),
        ("THE LONG ONE", [
            (904, -60.0, 0.8), (916, -53.0, 0.5), (924, -47.5, 0.1), (942, -71.0, 0.5),
            (956, -60.0, 0.3), (994, -80.0, 0.9), (1008, -83.0, 1.0),
        ]),
        ("FINISH RUN", [
            (1022, -79.0, 1.0), (1034, -85.0, 1.0), (1046, -81.0, 1.0), (1060, -84.0, 1.0),
        ]),
    ],
    lips=["FIRST KICKER", "DOUBLE UP", "THE BOWL", "STAIRCASE", "STEP DOWN",
          "RHYTHM", "TABLETOP", "THE HIP", "THE LONG ONE"],
)

# ============================================================== GRAVEL PIT ==
# Cut benches in a quarry. Short steep faces, drops instead of jumps, and the
# whole thing pulled in tight - the camera is closer and the ground never lets
# you settle. Rewards braking, which no other track does.
GRAVEL_PIT = TrackProfile(
    "GravelPit", "GRAVEL PIT",
    "Tight, steep and unforgiving. Brakes are not optional here.",
    "Gravel",
    [
        ("PIT ENTRY", [
            (0, 6.0, 0.4), (16, 4.0, 1.0), (30, -3.0, 0.8), (42, -11.0, 0.6),
            (54, -15.0, 0.9),
        ]),
        ("BENCHES", [                      # four cut ledges, each a short drop
            (66, -14.0, 0.5), (74, -13.6, 0.1),
            (84, -22.0, 0.4), (96, -24.0, 0.8),
            (106, -23.0, 0.5), (114, -22.6, 0.1),
            (124, -31.0, 0.4), (136, -33.0, 0.8),
        ]),
        ("CHATTER", [                      # tight low rollers, no air at all
            (146, -32.0, 1.0), (153, -35.5, 1.0), (160, -32.2, 1.0),
            (167, -36.0, 1.0), (174, -32.6, 1.0), (181, -36.5, 1.0),
            (190, -34.0, 1.0),
        ]),
        ("THE SHELF", [                    # flat lip off a high wall
            (202, -31.0, 0.5), (212, -30.6, 0.08),
            (226, -47.0, 0.35), (244, -54.0, 0.85), (256, -56.0, 1.0),
        ]),
        ("THE SPINE", [                    # sharp up, sharp down, sharp up
            (268, -53.0, 0.6), (278, -45.0, 0.18),
            (290, -57.0, 0.45), (300, -52.0, 0.7),
            (310, -44.0, 0.18), (322, -56.0, 0.45), (334, -52.0, 0.8),
        ]),
        ("THE CRUSHER", [                  # deep bowl, steep exit face
            (346, -58.0, 0.9), (358, -66.0, 1.0), (370, -60.0, 0.7),
            (380, -52.0, 0.35), (388, -47.0, 0.1),
            (402, -62.0, 0.5), (412, -55.0, 0.3), (438, -68.0, 0.9), (452, -71.0, 1.0),
        ]),
        ("STEPS UP", [                     # three step-ups, climbing out
            (464, -68.0, 0.7), (472, -63.0, 0.15), (484, -67.0, 0.6),
            (492, -62.0, 0.7), (500, -57.0, 0.15), (512, -61.0, 0.6),
            (520, -56.0, 0.7), (528, -51.0, 0.15), (540, -55.0, 0.6),
        ]),
        ("THE LEDGE", [                    # last drop, biggest of the day
            (552, -52.0, 0.6), (562, -46.0, 0.12),
            (580, -68.0, 0.4), (600, -76.0, 0.85), (614, -79.0, 1.0),
        ]),
        ("PIT EXIT", [
            (628, -77.0, 1.0), (640, -81.0, 1.0), (652, -78.5, 1.0), (666, -81.0, 1.0),
        ]),
    ],
    lips=["BENCHES", "THE SHELF", "THE SPINE", "THE CRUSHER", "STEPS UP", "THE LEDGE"],
    ortho=10.5,
)

# ============================================================== DUST DEVIL ==
# The opposite of the pit. Long fast ground between very few, very large
# features - most of the track is spent building speed for the next one.
DUST_DEVIL = TrackProfile(
    "DustDevil", "DUST DEVIL",
    "Wide open and fast. Three jumps, all of them enormous.",
    "Dust",
    [
        ("LAUNCH", [
            (0, 14.0, 0.3), (24, 12.0, 1.0), (52, 2.0, 1.0), (80, -12.0, 1.0),
            (108, -22.0, 0.9),
        ]),
        ("THE FLATS", [                    # long and fast, barely a bump
            (140, -26.0, 1.0), (176, -24.0, 1.0), (212, -28.0, 1.0),
            (248, -25.5, 1.0), (284, -30.0, 1.0),
        ]),
        ("BIG ONE", [                      # first of the three, already huge
            (312, -28.0, 0.9), (336, -20.0, 0.5), (352, -11.0, 0.08),
            (380, -34.0, 0.6), (398, -24.0, 0.3), (452, -46.0, 0.95), (476, -50.0, 1.0),
        ]),
        ("WASHBOARD", [                    # fast rollers to rebuild speed
            (504, -46.0, 1.0), (520, -52.0, 1.0), (536, -46.5, 1.0),
            (552, -53.0, 1.0), (568, -47.0, 1.0), (584, -54.0, 1.0),
        ]),
        ("MESA GAP", [                     # the biggest gap in the game
            (612, -50.0, 0.9), (640, -40.0, 0.5), (658, -29.0, 0.06),
            (694, -58.0, 0.55), (716, -46.0, 0.28), (786, -74.0, 0.95),
            (812, -79.0, 1.0),
        ]),
        ("LONG DRIFT", [
            (846, -76.0, 1.0), (884, -82.0, 1.0), (922, -77.0, 1.0), (960, -84.0, 1.0),
        ]),
        ("FINALE", [                       # a double, if you carry enough speed
            (992, -80.0, 0.9), (1018, -70.0, 0.5), (1034, -60.0, 0.07),
            (1066, -88.0, 0.55), (1086, -77.0, 0.3), (1146, -102.0, 0.95),
            (1170, -106.0, 1.0),
        ]),
        ("RUN OUT", [
            (1200, -104.0, 1.0), (1226, -110.0, 1.0), (1252, -106.0, 1.0),
            (1280, -109.0, 1.0),
        ]),
    ],
    lips=["BIG ONE", "MESA GAP", "FINALE"],
    ortho=14.5,
)

TRACKS = {t.key: t for t in (RIDGE_RUN, GRAVEL_PIT, DUST_DEVIL)}
ORDER = ["RidgeRun", "GravelPit", "DustDevil"]


if __name__ == "__main__":
    for key in ORDER:
        track = TRACKS[key]
        print("\n=== %s  (%s, %.0f units, ortho %.1f) ===" %
              (track.name, track.theme, track.finish_x, track.ortho))
        print("%-14s %6s   %s" % ("SECTION", "RAMP", "entry speed -> airtime / gap"))
        for name, angle, rows in track.verify():
            flights = "   ".join("%.0f -> %.2fs %.0fu" % (v, t, d) for v, t, d in rows)
            print("%-14s %5.1f    %s" % (name, angle, flights))
