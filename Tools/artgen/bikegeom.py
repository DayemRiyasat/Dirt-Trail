"""Single source of truth for bike sprite geometry.

The prefab builder reads these to place wheel/rider transforms, so the art and
the GameObject hierarchy can never drift apart.
"""
PPU = 200.0

BODY_W, BODY_H = 720, 440
REAR_AXLE  = (196.0, 300.0)
FRONT_AXLE = (556.0, 300.0)
GROUND_Y   = 408.0
WHEEL_R    = 108.0
BODY_PIVOT = (376.0, 300.0)          # midpoint between axles

WHEEL_W = WHEEL_H = 232
WHEEL_C = (116.0, 116.0)

RIDER_W, RIDER_H = 400, 480
RIDER_PEG = (206.0, 424.0)           # pivot: the footpeg the rider stands on
BIKE_PEG  = (352.0, 316.0)           # same point in body-canvas coordinates


def px_to_unit(px_pt, pivot_px):
    """Body-canvas pixel -> local Unity units relative to the body pivot."""
    return ((px_pt[0] - pivot_px[0]) / PPU, -(px_pt[1] - pivot_px[1]) / PPU)


def pivot_norm(pivot_px, w, h):
    return (pivot_px[0] / w, 1.0 - pivot_px[1] / h)


REAR_AXLE_LOCAL  = px_to_unit(REAR_AXLE, BODY_PIVOT)
FRONT_AXLE_LOCAL = px_to_unit(FRONT_AXLE, BODY_PIVOT)
PEG_LOCAL        = px_to_unit(BIKE_PEG, BODY_PIVOT)
WHEEL_R_UNITS    = WHEEL_R / PPU
BIKE_HALF_LEN    = (FRONT_AXLE[0] - REAR_AXLE[0]) / 2.0 / PPU
