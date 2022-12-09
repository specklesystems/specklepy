from enum import Enum
from typing import Union

from specklepy.logging.exceptions import SpeckleException, SpeckleInvalidUnitException

__all__ = [
    "Units",
    "get_encoding_from_units",
    "get_units_from_encoding",
    "get_units_from_string",
]


class Units(Enum):
    mm = "mm"
    cm = "cm"
    m = "m"
    km = "km"
    inches = "in"
    feet = "ft"
    yards = "yd"
    miles = "mi"
    none = "none"


UNITS_STRINGS = {
    Units.mm: ["mm", "mil", "millimeters", "millimetres"],
    Units.cm: ["cm", "centimetre", "centimeter", "centimetres", "centimeters"],
    Units.m: ["m", "meter", "meters", "metre", "metres"],
    Units.km: ["km", "kilometer", "kilometre", "kilometers", "kilometres"],
    Units.inches: ["in", "inch", "inches"],
    Units.feet: ["ft", "foot", "feet"],
    Units.yards: ["yd", "yard", "yards"],
    Units.miles: ["mi", "mile", "miles"],
    Units.none: ["none", "null"],
}

UNITS_ENCODINGS = {
    Units.none: 0,
    None: 0,
    Units.mm: 1,
    Units.cm: 2,
    Units.m: 3,
    Units.km: 4,
    Units.inches: 5,
    Units.feet: 6,
    Units.yards: 7,
    Units.miles: 8,
}


def get_units_from_string(unit: str) -> Units:
    if not isinstance(unit, str):
        raise SpeckleInvalidUnitException(unit)
    unit = str.lower(unit)
    for name, alternates in UNITS_STRINGS.items():
        if unit in alternates:
            return name
    raise SpeckleInvalidUnitException(unit)


def get_units_from_encoding(unit: int):
    for name, encoding in UNITS_ENCODINGS.items():
        if unit == encoding:
            return name

    raise SpeckleException(
        message=(
            f"Could not understand what unit {unit} is referring to."
            f"Please enter a valid unit encoding (eg {UNITS_ENCODINGS})."
        )
    )


def get_encoding_from_units(unit: Union[Units, None]):
    try:
        return UNITS_ENCODINGS[unit]
    except KeyError as e:
        raise SpeckleException(
            message=(
                f"No encoding exists for unit {unit}."
                f"Please enter a valid unit to encode (eg {UNITS_ENCODINGS})."
            )
        ) from e
