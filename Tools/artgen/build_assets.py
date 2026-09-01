"""ScriptableObject assets: bikes, pickups, UI skin, FX kit, terrain profile.

Tuning lives here, not scattered through the scripts. The two bikes are
deliberately opposed: the Scout rotates faster than it grips, the Mule the
other way round.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unityasset import guid_for, folder_meta
from unityscene import index_scripts, script_guid, sprite_ref, asset_ref, col, num

RES = "Assets/Resources"
FONT_GUID = "8f586378b4e144a9851e7b34d9b748ee"      # LiberationSans SDF

HEADER = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {guid}, type: 3}}
  m_Name: {name}
  m_EditorClassIdentifier:
"""

META = """fileFormatVersion: 2
guid: {guid}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 11400000
  userData:
  assetBundleName:
  assetBundleVariant:
"""


def write_asset(path, script, name, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = HEADER.format(guid=script_guid(script), name=name)
    body += "".join("  %s\n" % line for line in fields.strip("\n").split("\n"))
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(body)
    with open(path + ".meta", "w", newline="\n", encoding="utf-8") as fh:
        fh.write(META.format(guid=guid_for(path)))
    return path


BIKE_ART = "Assets/Sprites/Bike"


def bike(key, name, blurb, tune, dust, stats):
    fields = [
        "displayName: " + name,
        "blurb: " + blurb,
        "body: " + sprite_ref("%s/Body_%s.png" % (BIKE_ART, key)),
        "rider: " + sprite_ref("%s/Rider_%s.png" % (BIKE_ART, key)),
        "wheelFront: " + sprite_ref("%s/Wheel_Front_%s.png" % (BIKE_ART, key)),
        "wheelRear: " + sprite_ref("%s/Wheel_Rear_%s.png" % (BIKE_ART, key)),
        "dust: " + col(*dust),
    ]
    fields += ["%s: %s" % (k, num(v)) for k, v in tune]
    fields += ["statSpeed: %s" % num(stats[0]),
               "statGrip: %s" % num(stats[1]),
               "statAir: %s" % num(stats[2])]
    return write_asset("%s/Bikes/%s.asset" % (RES, key), "BikeConfig", name,
                       "\n".join(fields))


def build_bikes():
    scout = bike(
        "Scout", "SCOUT", "Light. Flicks fast, lands nervous.",
        # gravityScale 1.6 is the number the whole track is built around: it
        # gives the big jumps roughly two seconds of hang, which is one flip
        # with time to set up the landing.
        [("mass", 2.7), ("gravityScale", 1.6),
         ("enginePower", 50), ("maxSpeed", 22), ("brakeForce", 30),
         ("groundTorque", 9), ("airTorque", 22),
         ("groundAngularDamping", 5), ("airAngularDamping", 0.15),
         ("spinCeiling", 320), ("settleHeight", 7), ("landingSpinDamp", 4),
         ("groundAlign", 22), ("landingAssist", 5),
         ("suspensionTravel", 0.16),
         ("nitroMultiplier", 1.7), ("nitroDuration", 3.2)],
        dust=(0.82, 0.66, 0.44, 1), stats=(0.72, 0.45, 0.92))

    mule = bike(
        "Mule", "MULE", "Heavy, older, honest. Sticks where you put it.",
        [("mass", 3.6), ("gravityScale", 1.5),
         ("enginePower", 64), ("maxSpeed", 20), ("brakeForce", 38),
         ("groundTorque", 10), ("airTorque", 17),
         ("groundAngularDamping", 6), ("airAngularDamping", 0.22),
         ("spinCeiling", 260), ("settleHeight", 8), ("landingSpinDamp", 4.5),
         ("groundAlign", 28), ("landingAssist", 8),
         ("suspensionTravel", 0.2),
         ("nitroMultiplier", 1.55), ("nitroDuration", 4.2)],
        dust=(0.7, 0.58, 0.42, 1), stats=(0.58, 0.8, 0.6))

    roster = write_asset(RES + "/BikeRoster.asset", "BikeRoster", "BikeRoster",
                         "bikes:\n- " + asset_ref(scout) + "\n- " + asset_ref(mule))
    return [scout, mule, roster]


def build_pickups():
    nitro = write_asset(
        RES + "/Pickups/Nitro.asset", "PickupConfig", "Nitro", "\n".join([
            "kind: 0",
            "icon: " + sprite_ref("Assets/Sprites/Props/Pickup_Nitro.png"),
            "tint: " + col(0.85, 0.37, 0.15, 1),
            "duration: 0",          # banked as a charge, not a timer
            "bonus: 75",
        ]))
    air = write_asset(
        RES + "/Pickups/AirControl.asset", "PickupConfig", "AirControl", "\n".join([
            "kind: 1",
            "icon: " + sprite_ref("Assets/Sprites/Props/Pickup_Air.png"),
            "tint: " + col(0.42, 0.47, 0.3, 1),
            "duration: 8",
            "bonus: 50",
        ]))
    return [nitro, air]


def build_ui_skin():
    return [write_asset(RES + "/UISkin.asset", "UISkin", "UISkin", "\n".join([
        "plateDark: " + sprite_ref("Assets/Sprites/UI/Plate_Dark.png"),
        "plateSand: " + sprite_ref("Assets/Sprites/UI/Plate_Sand.png"),
        "plateRust: " + sprite_ref("Assets/Sprites/UI/Plate_Rust.png"),
        "stripe: " + sprite_ref("Assets/Sprites/UI/Stripe.png"),
        "chevron: " + sprite_ref("Assets/Sprites/UI/Chevron.png"),
        "font: {fileID: 11400000, guid: %s, type: 2}" % FONT_GUID,
    ]))]


def build_shout_kit():
    """Groups the generated burst sprites by the moment they belong to."""
    import glob
    groups = {
        "flip": ["BRAAAP", "WHIP", "SENDIT", "YEEHAW"],
        "bigFlip": ["BRAAAAAP", "GETSOME", "BOOM"],
        "air": ["WHOOOSH", "WHEEE", "FLOATY"],
        "perfect": ["STUCKIT", "NAILEDIT", "SMOOTH"],
        "wipeout": ["KRUNCH", "OOF", "SMACK", "YARDSALE"],
        "nitro": ["FWOOSH"],
        "airPickup": ["ZIP"],
    }
    lines = []
    for field, names in groups.items():
        lines.append(field + ":")
        for n in names:
            lines.append("- " + sprite_ref("Assets/Sprites/Shouts/%s.png" % n))
    return [write_asset(RES + "/ShoutKit.asset", "ShoutKit", "ShoutKit",
                        "\n".join(lines))]


def build_fx_kit():
    return [write_asset(RES + "/FxKit.asset", "FxKit", "FxKit", "\n".join([
        "dust: " + sprite_ref("Assets/Sprites/FX/Dust_Puff.png"),
        "clod: " + sprite_ref("Assets/Sprites/FX/Dirt_Clod.png"),
        "spark: " + sprite_ref("Assets/Sprites/FX/Spark_Streak.png"),
        "shadow: " + sprite_ref("Assets/Sprites/FX/Ground_Shadow.png"),
    ]))]


SPRITE_SHAPE_SCRIPT_GUID = "af7181f404f1447c0a7a17b3070b952b"   # SpriteShape asset type


def build_sprite_shape_profiles():
    """One profile per theme: an edge sprite for every angle, one corner reused."""
    import themes as TH
    made = []
    for key in TH.ALL:
        folder = "Assets/Sprites/Terrain/%s" % key
        edge = sprite_ref("%s/%s Edge.png" % (folder, key))
        corner = sprite_ref("%s/%s Corner.png" % (folder, key))
        fill_guid = guid_for("%s/%s Fill.png" % (folder, key))

        body = HEADER.format(guid=SPRITE_SHAPE_SCRIPT_GUID,
                             name="%s Sprite Shape Profile" % key)
        body += "  m_Angles:\n"
        body += "  - m_Start: -180\n    m_End: 180\n    m_Order: 0\n    m_Sprites:\n"
        body += "    - " + edge + "\n"
        body += "  m_FillTexture: {fileID: 2800000, guid: %s, type: 3}\n" % fill_guid
        body += "  m_CornerSprites:\n"
        for i in range(8):
            body += "  - m_CornerType: %d\n    m_Sprites:\n    - %s\n" % (i, corner)
        body += "  m_FillOffset: 0\n  m_UseSpriteBorders: 1\n"

        path = "%s/%s Sprite Shape Profile.asset" % (folder, key)
        with open(path, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(body)
        with open(path + ".meta", "w", newline="\n", encoding="utf-8") as fh:
            fh.write(META.format(guid=guid_for(path)))
        made.append(path)
    return made


def build_tracks():
    """A TrackConfig per level, plus the roster the menus read."""
    import track_profile as TP
    made, refs = [], []
    for key in TP.ORDER:
        t = TP.TRACKS[key]
        path = write_asset("%s/Tracks/%s.asset" % (RES, key), "TrackConfig", t.name,
                           "\n".join([
                               "key: " + t.key,
                               "displayName: " + t.name,
                               "blurb: " + t.blurb,
                               "sceneName: " + t.key,
                               "length: " + num(t.finish_x),
                               "jumps: %d" % len(t.lips),
                               "tint: " + col(0.85, 0.37, 0.15, 1),
                           ]))
        made.append(path)
        refs.append(asset_ref(path))
    made.append(write_asset(RES + "/TrackRoster.asset", "TrackRoster", "TrackRoster",
                            "tracks:\n" + "\n".join("- " + r for r in refs)))
    return made


def main():
    index_scripts()
    os.makedirs(RES, exist_ok=True)
    for d in (RES, RES + "/Bikes", RES + "/Pickups", RES + "/Tracks"):
        os.makedirs(d, exist_ok=True)
        folder_meta(d)

    made = (build_bikes() + build_pickups() + build_ui_skin() + build_fx_kit()
            + build_shout_kit()
            + build_sprite_shape_profiles() + build_tracks())
    for p in made:
        print("  ", p)


if __name__ == "__main__":
    main()
