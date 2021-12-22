from warnings import warn
from specklepy.logging.exceptions import SpeckleException, SpeckleWarning

UNITS = ["mm", "cm", "m", "in", "ft", "yd", "mi"]

UNITS_STRINGS = {
    "mm": ["mm", "mil", "millimeters", "millimetres"],
    "cm": ["cm", "centimetre", "centimeter", "centimetres", "centimeters"],
    "m": ["m", "meter", "meters", "metre", "metres"],
    "km": ["km", "kilometer", "kilometre", "kilometers", "kilometres"],
    "in": ["in", "inch", "inches"],
    "ft": ["ft", "foot", "feet"],
    "yd": ["yd", "yard", "yards"],
    "mi": ["mi", "mile", "miles"],
    "none": ["none", "null"],
}

UNITS_ENCODINGS = {
    "none": 0,
    "mm": 1,
    "cm": 2,
    "m": 3,
    "km": 4,
    "in": 5,
    "ft": 6,
    "yd": 7,
    "mi": 8,
}


def get_units_from_string(unit: str):
    if not isinstance(unit, str):
        warn(
            f"Invalid units: expected type str but received {type(unit)} ({unit}). Skipping - no units will be set.",
            SpeckleWarning,
        )
        return
    unit = str.lower(unit)
    for name, alternates in UNITS_STRINGS.items():
        if unit in alternates:
            return name

    raise SpeckleException(
        message=f"Could not understand what unit {unit} is referring to. Please enter a valid unit (eg {UNITS})."
    )


def get_units_from_encoding(unit: int):
    for name, encoding in UNITS_ENCODINGS.items():
        if unit == encoding:
            return name

    raise SpeckleException(
        message=f"Could not understand what unit {unit} is referring to. Please enter a valid unit encoding (eg {UNITS_ENCODINGS})."
    )


def get_encoding_from_units(unit: str):
    try:
        return UNITS_ENCODINGS[unit]
    except KeyError:
        raise SpeckleException(
            message=f"No encoding exists for unit {unit}. Please enter a valid unit to encode (eg {UNITS_ENCODINGS})."
        )
