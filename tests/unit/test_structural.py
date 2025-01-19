import pytest
from specklepy.objects.geometry import Line, Mesh, Point, Vector
from specklepy.objects.structural.analysis import Model
from specklepy.objects.structural.geometry import (
    Element1D,
    Element2D,
    ElementType1D,
    ElementType2D,
    Node,
    Restraint,
)
from specklepy.objects.structural.loading import LoadGravity
from specklepy.objects.structural.materials import StructuralMaterial
from specklepy.objects.structural.properties import (
    MemberType,
    Property1D,
    Property2D,
    SectionProfile,
    ShapeType,
)


@pytest.fixture()
def point():
    return Point(x=1, y=10, z=0)


@pytest.fixture()
def vector():
    return Vector(x=0, y=0, z=-1)


@pytest.fixture()
def line(point, interval):
    return Line(
        start=point,
        end=point,
        domain=interval,
        # These attributes are not handled in C#
        # bbox=None,
        # length=None
    )


@pytest.fixture()
def mesh(box):
    return Mesh(
        vertices=[2, 1, 2, 4, 77.3, 5, 33, 4, 2],
        faces=[1, 2, 3, 4, 5, 6, 7],
        colors=[111, 222, 333, 444, 555, 666, 777],
        bbox=box,
        area=233,
        volume=232.2,
    )


@pytest.fixture()
def restraint():
    return Restraint(code="FFFFFF")


@pytest.fixture()
def node(restraint, point):
    return Node(basePoint=point, restraint=restraint, name="node1")


@pytest.fixture()
def material():
    return StructuralMaterial(name="TestMaterial")


@pytest.fixture()
def memberType():
    return MemberType(0)


@pytest.fixture()
def shapeType():
    return ShapeType(8)


@pytest.fixture()
def sectionProfile(shapeType):
    return SectionProfile(name="Test", shapeType=shapeType)


@pytest.fixture()
def property1D(memberType, sectionProfile, material):
    return Property1D(
        Material=material,
        SectionProfile=sectionProfile,
        memberType=memberType,
    )


@pytest.fixture()
def elementType1D():
    return ElementType1D(0)


@pytest.fixture()
def element1D(line, restraint, elementType1D, property1D):
    return Element1D(
        baseLine=line,
        end1Releases=restraint,
        end2Releases=restraint,
        type=elementType1D,
        property=property1D,
    )


@pytest.fixture()
def property2D(material):
    return Property2D(Material=material)


@pytest.fixture()
def elementType2D():
    return ElementType2D(0)


@pytest.fixture()
def element2D(point, elementType2D):
    return Element2D(
        topology=[point],
        type=elementType2D,
    )


@pytest.fixture()
def loadGravity(element1D, element2D, vector):
    return LoadGravity(elements=[element1D, element2D], gravityFactors=vector)


@pytest.fixture()
def model(loadGravity, element1D, element2D, material, property1D, property2D):
    return Model(
        loads=[loadGravity],
        elements=[element1D, element2D],
        materials=[material],
        properties=[property1D, property2D],
    )
