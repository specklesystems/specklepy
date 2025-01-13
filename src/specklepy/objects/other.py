from specklepy.objects.base import Base
from specklepy.objects.models.units import get_scale_factor_from_string


class Transform(Base, speckle_type="Objects.Other.Transform"):
    """
    generic transform class with a column-based 4x4 transform matrix
    graphics based apps typically use column-based matrices, where the last column defines translation.
    modelling apps may use row-based matrices, where the last row defines translation. transpose if so.
    """

    def __init__(self, matrix=None, units=None):
        super().__init__()
        self.matrix = matrix or [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]
        self.units = units

    def convert_to_units(self, new_units):
        """Converts this transform to different units"""
        if not new_units or not self.units:
            return self.to_array()

        scale_factor = get_scale_factor_from_string(self.units, new_units)

        return [
            self.matrix[0],   # M11
            self.matrix[1],   # M12
            self.matrix[2],   # M13
            self.matrix[3] * scale_factor,  # M14 (translation)
            self.matrix[4],   # M21
            self.matrix[5],   # M22
            self.matrix[6],   # M23
            self.matrix[7] * scale_factor,  # M24 (translation)
            self.matrix[8],   # M31
            self.matrix[9],   # M32
            self.matrix[10],  # M33
            self.matrix[11] * scale_factor,  # M34 (translation)
            self.matrix[12],  # M41
            self.matrix[13],  # M42
            self.matrix[14],  # M43
            self.matrix[15],  # M44
        ]

    @staticmethod
    def create_matrix(values):
        """Creates a matrix from an array of values"""
        if len(values) != 16:
            raise ValueError("Matrix requires exactly 16 values")
        return [float(v) for v in values]

    def to_array(self):
        """Returns the transform matrix as an array"""
        return self.matrix.copy()
