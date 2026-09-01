"""Add a 'Ride' action map to the project-wide input asset.

Deterministic GUIDs so re-running never churns the file. The existing Player and
UI maps are left untouched; only a Ride map is added or replaced.
"""
import hashlib
import json
import uuid

ASSET = "Assets/Default/InputSystem_Actions.inputactions"
KB = ";Keyboard&Mouse"
PAD = ";Gamepad"


def uid(*parts):
    h = hashlib.md5(("dirttrail.input|" + "|".join(parts)).encode()).hexdigest()
    return str(uuid.UUID(h))


def action(name, kind, control, initial=False):
    return {
        "name": name, "type": kind, "id": uid("action", name),
        "expectedControlType": control, "processors": "", "interactions": "",
        "initialStateCheck": initial,
    }


def binding(action_name, path, groups, tag="", composite=False, part=False, name=""):
    return {
        "name": name, "id": uid("bind", action_name, path, tag),
        "path": path, "interactions": "", "processors": "", "groups": groups,
        "action": action_name, "isComposite": composite, "isPartOfComposite": part,
    }


def simple(action_name, paths):
    return [binding(action_name, p, KB if p.startswith("<Keyboard>") else PAD) for p in paths]


def axis1d(action_name, negatives, positives):
    """1D axis composite: negative keys give -1, positive keys give +1."""
    out = [binding(action_name, "1DAxis", "", tag="composite", composite=True, name="Keys")]
    for p in negatives:
        out.append(binding(action_name, p, KB, tag="neg", part=True, name="negative"))
    for p in positives:
        out.append(binding(action_name, p, KB, tag="pos", part=True, name="positive"))
    return out


def build_map():
    actions = [
        # Value/Axis, not Button: a held key has to be *polled*, and polling a
        # Button action for "is it down right now" is unreliable. Reading an
        # axis value is not, and it gives analogue triggers real travel.
        action("Throttle", "Value", "Axis", initial=True),
        action("Brake", "Value", "Axis", initial=True),
        # Positive leans the nose down (frontflip), negative lifts it (backflip).
        action("Lean", "Value", "Axis", initial=True),
        action("Nitro", "Button", "Button"),
        action("Pause", "Button", "Button"),
        action("Retry", "Button", "Button"),
    ]

    bindings = []
    bindings += simple("Throttle", ["<Keyboard>/w", "<Keyboard>/upArrow",
                                    "<Gamepad>/rightTrigger", "<Gamepad>/buttonSouth"])
    bindings += simple("Brake", ["<Keyboard>/s", "<Keyboard>/downArrow",
                                 "<Gamepad>/leftTrigger", "<Gamepad>/buttonEast"])
    bindings += axis1d("Lean", ["<Keyboard>/a", "<Keyboard>/leftArrow"],
                       ["<Keyboard>/d", "<Keyboard>/rightArrow"])
    bindings.append(binding("Lean", "<Gamepad>/leftStick/x", PAD, tag="stick"))
    bindings += simple("Nitro", ["<Keyboard>/leftShift", "<Keyboard>/space",
                                 "<Gamepad>/buttonWest"])
    bindings += simple("Pause", ["<Keyboard>/escape", "<Gamepad>/start"])
    bindings += simple("Retry", ["<Keyboard>/r", "<Gamepad>/buttonNorth"])

    return {"name": "Ride", "id": uid("map", "Ride"), "actions": actions,
            "bindings": bindings}


def main():
    with open(ASSET, encoding="utf-8") as fh:
        data = json.load(fh)
    data["maps"] = [m for m in data["maps"] if m["name"] != "Ride"]
    data["maps"].insert(0, build_map())
    with open(ASSET, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=4)
        fh.write("\n")
    print("Ride map: %d actions, %d bindings" %
          (len(data["maps"][0]["actions"]), len(data["maps"][0]["bindings"])))


if __name__ == "__main__":
    main()
