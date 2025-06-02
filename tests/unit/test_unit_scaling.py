import pytest

from specklepy.objects.models.units import Units, get_scale_factor


@pytest.mark.parametrize(
    "fromUnits, toUnits, inValue, expectedOutValue",
    [
        # To self
        (Units.km, Units.km, 1.5, 1.5),
        (Units.km, Units.km, 0, 0),
        (Units.m, Units.m, 1.5, 1.5),
        (Units.m, Units.m, 0, 0),
        (Units.cm, Units.cm, 1.5, 1.5),
        (Units.cm, Units.cm, 0, 0),
        (Units.mm, Units.mm, 1.5, 1.5),
        (Units.mm, Units.mm, 0, 0),
        (Units.miles, Units.miles, 1.5, 1.5),
        (Units.miles, Units.miles, 0, 0),
        (Units.yards, Units.yards, 1.5, 1.5),
        (Units.yards, Units.yards, 0, 0),
        (Units.feet, Units.feet, 1.5, 1.5),
        (Units.feet, Units.feet, 0, 0),
        # To Meters
        (Units.km, Units.m, 987654.321, 987654321),
        (Units.m, Units.m, 987654.321, 987654.321),
        (Units.mm, Units.m, 98765432.1, 98765.4321),
        (Units.cm, Units.m, 9876543.21, 98765.4321),
        # To negative meters
        (Units.km, Units.m, -987654.321, -987654321),
        (Units.m, Units.m, -987654.321, -987654.321),
        (Units.mm, Units.m, -98765432.1, -98765.4321),
        (Units.cm, Units.m, -9876543.21, -98765.4321),
        (Units.m, Units.km, 987654.321, 987.654321),
        (Units.m, Units.cm, 987654.321, 98765432.1),
        (Units.m, Units.mm, 987654.321, 987654321),
        # Imperial
        (Units.miles, Units.m, 123.45, 198673.517),
        (Units.miles, Units.inches, 123.45, 7821792),
        (Units.yards, Units.m, 123.45, 112.88268),
        (Units.yards, Units.inches, 123.45, 4444.2),
        (Units.feet, Units.m, 123.45, 37.62756),
        (Units.feet, Units.inches, 123.45, 1481.4),
        (Units.inches, Units.m, 123.45, 3.13563),
    ],
)
def test_get_scale_factor_between_units(
    fromUnits: Units, toUnits: Units, inValue: float, expectedOutValue: float
):
    Tolerance = 1e-10
    actual = inValue * get_scale_factor(fromUnits, toUnits)
    assert actual - expectedOutValue < Tolerance
