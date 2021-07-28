from specklepy.logging.exceptions import SpeckleException

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


def get_units_from_string(unit: str):
    unit = str.lower(unit)
    for name, alternates in UNITS_STRINGS.items():
        if unit in alternates:
            return name

    raise SpeckleException(
        message=f"Could not understand what unit {unit} is referring to. Please enter a valid unit (eg {UNITS})."
    )
