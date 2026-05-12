from enum import Enum

TRACK_SIZE = 32


class PadType(Enum):
    NORMAL       = "normal"
    THRUSTER     = "thruster"      # propels cube 1 pad forward (global direction)
    BLOCKER      = "blocker"       # pushes cube 1 pad backward (global direction)
    SPATIAL_RIFT = "spatial_rift"  # randomises stack order at this pad


# Pad 0 = finish line; normal cubes start at pad 1.
PAD_TYPES: dict[int, PadType] = {
    3:  PadType.THRUSTER,
    6:  PadType.SPATIAL_RIFT,
    10: PadType.BLOCKER,
    11: PadType.THRUSTER,
    16: PadType.THRUSTER,
    20: PadType.SPATIAL_RIFT,
    23: PadType.THRUSTER,
    28: PadType.BLOCKER,
}


def get_pad_type(pad: int) -> PadType:
    return PAD_TYPES.get(pad % TRACK_SIZE, PadType.NORMAL)
