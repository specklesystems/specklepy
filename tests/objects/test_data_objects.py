import pytest

from specklepy.core.api.operations import deserialize, serialize
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.objects.data_objects import BlenderObject, DataObject, QgisObject
from specklepy.objects.interfaces import (
    IBlenderObject,
    IDataObject,
    IGisObject,
    IHasUnits,
)
from specklepy.objects.models.units import Units


def test_data_object_creation():
    display_value = [Base()]
    data_obj = DataObject(
        name="Test Data Object",
        properties={"key1": "value1", "key2": 2},
        displayValue=display_value,
    )

    assert data_obj.name == "Test Data Object"
    assert data_obj.properties == {"key1": "value1", "key2": 2}
    assert data_obj.displayValue == display_value
    assert data_obj.speckle_type == "Objects.Data.DataObject"


def test_inheritance_relationships():
    data_obj = DataObject(
        name="Test Data Object",
        properties={"key": "value"},
        displayValue=[Base()],
    )
    assert isinstance(data_obj, DataObject)
    assert isinstance(data_obj, Base)
    assert isinstance(data_obj, IDataObject)

    qgis_obj = QgisObject(
        name="Test QGIS Object",
        properties={"key": "value"},
        displayValue=[Base()],
        type="Feature",
        units=Units.m,
    )
    assert isinstance(qgis_obj, QgisObject)
    assert isinstance(qgis_obj, DataObject)
    assert isinstance(qgis_obj, Base)
    assert isinstance(qgis_obj, IDataObject)
    assert isinstance(qgis_obj, IGisObject)
    assert isinstance(qgis_obj, IHasUnits)

    blender_obj = BlenderObject(
        name="Test Blender Object",
        properties={"key": "value"},
        displayValue=[Base()],
        type="Mesh",
        units=Units.m,
    )
    assert isinstance(blender_obj, BlenderObject)
    assert isinstance(blender_obj, DataObject)
    assert isinstance(blender_obj, Base)
    assert isinstance(blender_obj, IDataObject)
    assert isinstance(blender_obj, IBlenderObject)
    assert isinstance(blender_obj, IHasUnits)


def test_data_object_invalid_types():
    data_obj = DataObject(
        name="Test Object",
        properties={"key": "value"},
        displayValue=[Base()],
    )

    class ComplexObject:
        def __str__(self):
            raise ValueError("Can't convert to string")

    complex_obj = ComplexObject()

    with pytest.raises((ValueError, SpeckleException)):
        data_obj.name = complex_obj  # should be string

    with pytest.raises(SpeckleException):
        data_obj.properties = [1, 2, 3]  # should be dict, not list

    with pytest.raises(SpeckleException):
        data_obj.displayValue = {"key": "value"}  # should be list, not dict


def test_data_object_serialization():
    display_value = [Base()]
    data_obj = DataObject(
        name="Test Data Object",
        properties={"key1": "value1", "key2": 2},
        displayValue=display_value,
    )

    serialized = serialize(data_obj)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, DataObject)
    assert deserialized.name == data_obj.name
    assert deserialized.properties == data_obj.properties
    assert len(deserialized.displayValue) == len(data_obj.displayValue)
    assert deserialized.speckle_type == data_obj.speckle_type


def test_qgis_object_creation():
    display_value = [Base()]
    qgis_obj = QgisObject(
        name="Test QGIS Object",
        properties={"key1": "value1"},
        displayValue=display_value,
        type="Feature",
        units=Units.m,
    )

    assert qgis_obj.name == "Test QGIS Object"
    assert qgis_obj.properties == {"key1": "value1"}
    assert qgis_obj.displayValue == display_value
    assert qgis_obj.type == "Feature"
    assert qgis_obj.units == Units.m.value
    assert "Objects.Data.QgisObject" in qgis_obj.speckle_type


def test_qgis_object_serialization():
    display_value = [Base()]
    qgis_obj = QgisObject(
        name="Test QGIS Object",
        properties={"key1": "value1"},
        displayValue=display_value,
        type="Feature",
        units=Units.m,
    )

    serialized = serialize(qgis_obj)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, QgisObject)
    assert deserialized.name == qgis_obj.name
    assert deserialized.properties == qgis_obj.properties
    assert len(deserialized.displayValue) == len(qgis_obj.displayValue)
    assert deserialized.type == qgis_obj.type
    assert deserialized.units == qgis_obj.units
    assert "Objects.Data.QgisObject" in deserialized.speckle_type


def test_blender_object_creation():
    display_value = [Base()]
    blender_obj = BlenderObject(
        name="Test Blender Object",
        properties={"key1": "value1"},
        displayValue=display_value,
        type="Mesh",
        units=Units.m,
    )

    assert blender_obj.name == "Test Blender Object"
    assert blender_obj.properties == {"key1": "value1"}
    assert blender_obj.displayValue == display_value
    assert blender_obj.type == "Mesh"
    assert blender_obj.units == Units.m.value
    assert "Objects.Data.BlenderObject" in blender_obj.speckle_type


def test_blender_object_invalid_types():
    blender_obj = BlenderObject(
        name="Test Object",
        properties={"key": "value"},
        displayValue=[Base()],
        type="Mesh",
        units=Units.m,
    )

    class ComplexObject:
        def __str__(self):
            raise ValueError("Can't convert to string")

    complex_obj = ComplexObject()

    with pytest.raises((ValueError, SpeckleException)):
        blender_obj.type = complex_obj  # should be string


def test_blender_object_serialization():
    display_value = [Base()]
    blender_obj = BlenderObject(
        name="Test Blender Object",
        properties={"key1": "value1"},
        displayValue=display_value,
        type="Mesh",
        units=Units.m,
    )

    serialized = serialize(blender_obj)
    deserialized = deserialize(serialized)

    assert isinstance(deserialized, BlenderObject)
    assert deserialized.name == blender_obj.name
    assert deserialized.properties == blender_obj.properties
    assert len(deserialized.displayValue) == len(blender_obj.displayValue)
    assert deserialized.type == blender_obj.type
    assert deserialized.units == blender_obj.units
    assert "Objects.Data.BlenderObject" in deserialized.speckle_type


def test_data_object_property_modification():
    data_obj = DataObject(
        name="Original Name",
        properties={"original": "value"},
        displayValue=[Base()],
    )

    data_obj.name = "Updated Name"
    data_obj.properties = {"updated": "property"}
    new_display_value = [Base(), Base()]
    data_obj.displayValue = new_display_value

    assert data_obj.name == "Updated Name"
    assert data_obj.properties == {"updated": "property"}
    assert data_obj.displayValue == new_display_value


def test_qgis_object_property_modification():
    """Test modification of QgisObject properties after creation."""
    qgis_obj = QgisObject(
        name="Original Name",
        properties={"original": "value"},
        displayValue=[Base()],
        type="OriginalType",
        units=Units.m,
    )

    qgis_obj.type = "UpdatedType"

    assert qgis_obj.type == "UpdatedType"


def test_blender_object_property_modification():
    blender_obj = BlenderObject(
        name="Original Name",
        properties={"original": "value"},
        displayValue=[Base()],
        type="OriginalType",
        units=Units.m,
    )

    blender_obj.type = "UpdatedType"

    assert blender_obj.type == "UpdatedType"
