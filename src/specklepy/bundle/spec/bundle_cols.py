# GENERATED FROM spec/bundle-spec.sql — DO NOT EDIT.
# Run `npm run generate` (or node codegen/generate-all.mjs) to refresh.
"""Column index of every produced table's parquet field, in spec order (matches
the bundle_schemas.BY_TABLE descriptor order 1:1). One class per table; use these
instead of hard-coded ordinals so a spec column insertion shifts writers
automatically and a rename/removal fails their imports.
"""

class CAMERA_VIEWS:
    """Column indices of the camera_views table (spec order)."""

    VIEW = 0
    NAME = 1
    IS_DEFAULT = 2
    ORD = 3
    POS_X = 4
    POS_Y = 5
    POS_Z = 6
    FORWARD_X = 7
    FORWARD_Y = 8
    FORWARD_Z = 9
    UP_X = 10
    UP_Y = 11
    UP_Z = 12
    TARGET_X = 13
    TARGET_Y = 14
    TARGET_Z = 15
    UNITS = 16
    IS_ORTHO = 17
    FOV = 18
    LENS_MM = 19
    ORTHO_HEIGHT = 20
    ASPECT = 21
    NEAR = 22
    FAR = 23
    COLUMN_COUNT = 24


class EAV:
    """Column indices of the eav table (spec order)."""

    OBJECT_INDEX = 0
    PATH_INDEX = 1
    VALUE_STRING = 2
    VALUE_DOUBLE = 3
    VALUE_BOOLEAN = 4
    UNIT = 5
    INTERNAL_DEFINITION_NAME = 6
    COLUMN_COUNT = 7


class GEOMETRIES:
    """Column indices of the geometries table (spec order)."""

    GEOMETRY_INDEX = 0
    CONTENT = 1
    ID = 2
    TYPE = 3
    COLUMN_COUNT = 4


class MODEL:
    """Column indices of the model table (spec order)."""

    PATH = 0
    VALUE_STRING = 1
    VALUE_DOUBLE = 2
    VALUE_BOOLEAN = 3
    UNIT = 4
    COLUMN_COUNT = 5


class NODES:
    """Column indices of the nodes table (spec order)."""

    ID = 0
    KIND = 1
    NAME = 2
    DEF_REF = 3
    TRANSFORM = 4
    UNITS = 5
    SUBTYPE = 6
    ARGB = 7
    OPACITY = 8
    METALNESS = 9
    ROUGHNESS = 10
    EMISSIVE = 11
    IOR = 12
    ELEVATION = 13
    GH_TOPOLOGY = 14
    COLUMN_COUNT = 15


class OBJECT_TYPE:
    """Column indices of the object_type table (spec order)."""

    OBJECT_INDEX = 0
    TYPE_INDEX = 1
    COLUMN_COUNT = 2


class OBJECTS:
    """Column indices of the objects table (spec order)."""

    OBJECT_INDEX = 0
    APPLICATION_ID = 1
    COLUMN_COUNT = 2


class PATHS:
    """Column indices of the paths table (spec order)."""

    PATH_INDEX = 0
    PATH = 1
    COLUMN_COUNT = 2


class PROPERTY_SET_DEFINITIONS:
    """Column indices of the property_set_definitions table (spec order)."""

    SET_NAME = 0
    SET_KEY = 1
    SET_DESCRIPTION = 2
    FIELD_NAME = 3
    FIELD_BUCKET_ID = 4
    DATA_TYPE = 5
    DEFAULT_STRING = 6
    DEFAULT_DOUBLE = 7
    DEFAULT_BOOLEAN = 8
    UNIT = 9
    DESCRIPTION = 10
    APPLIES_TO = 11
    COLUMN_COUNT = 12


class RELATIONS:
    """Column indices of the relations table (spec order)."""

    REL = 0
    SRC = 1
    DST = 2
    ORD = 3
    COLUMN_COUNT = 4


class SCENE_VIEWS:
    """Column indices of the scene_views table (spec order)."""

    VIEW = 0
    NAME = 1
    IS_DEFAULT = 2
    ORD = 3
    SOURCE = 4
    REF = 5
    COLUMN_COUNT = 6


class STRUCTURAL_RESULTS:
    """Column indices of the structural_results table (spec order)."""

    OBJECT_INDEX = 0
    ELEMENT_NAME = 1
    LOCATION = 2
    RESULT_TYPE = 3
    LOAD_CASE = 4
    COMPONENT = 5
    POSITION_LABEL = 6
    STATION = 7
    STEP = 8
    VALUE = 9
    VALUE_TEXT = 10
    COLUMN_COUNT = 11


class TYPE_EAV:
    """Column indices of the type_eav table (spec order)."""

    TYPE_INDEX = 0
    PATH_INDEX = 1
    VALUE_STRING = 2
    VALUE_DOUBLE = 3
    VALUE_BOOLEAN = 4
    UNIT = 5
    INTERNAL_DEFINITION_NAME = 6
    COLUMN_COUNT = 7


class TYPES:
    """Column indices of the types table (spec order)."""

    TYPE_INDEX = 0
    TYPE_KEY = 1
    COLUMN_COUNT = 2
