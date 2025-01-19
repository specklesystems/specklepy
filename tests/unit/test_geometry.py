# pylint: disable=redefined-outer-name
import json

import pytest
from specklepy.api import operations
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.objects_v2.encoding import CurveArray, ObjectArray
from specklepy.objects_v2.geometry import (
    Arc,
    Box,
    Brep,
    BrepEdge,
    BrepFace,
    BrepLoop,
    BrepLoopType,
    BrepTrim,
    BrepTrimType,
    Circle,
    Curve,
    Ellipse,
    Interval,
    Line,
    Mesh,
    Plane,
    Point,
    Polycurve,
    Polyline,
    Surface,
    Vector,
)
from specklepy.objects_v2.units import Units
from specklepy.transports.memory import MemoryTransport


@pytest.fixture()
def interval():
    return Interval(start=0, end=5)


@pytest.fixture()
def point():
    return Point(x=1, y=10, z=0)


@pytest.fixture()
def vector():
    return Vector(x=1, y=32, z=10)


@pytest.fixture()
def plane(point, vector):
    return Plane(origin=point, normal=vector, xdir=vector, ydir=vector, units="m")


@pytest.fixture()
def box(plane, interval):
    return Box(
        basePlane=plane,
        ySize=interval,
        zSize=interval,
        xSize=interval,
        area=20.4,
        volume=44.2,
    )


@pytest.fixture()
def line(point, interval):
    return Line(
        start=point,
        end=point,
        domain=interval,
        units="none",
        # These attributes are not handled in C#
        # bbox=None,
        # length=None
    )


@pytest.fixture()
def arc(plane, interval, point):
    return Arc(
        radius=2.3,
        startAngle=22.1,
        endAngle=44.5,
        angleRadians=33,
        plane=plane,
        domain=interval,
        units="m",
        startPoint=point,
        midPoint=point,
        endPoint=point,
        # These attributes are not handled in C#
        # bbox=None,
        # area=None,
        # length=None,
    )


@pytest.fixture()
def circle(plane, interval):
    return Circle(
        radius=22,
        plane=plane,
        domain=interval,
        units="m",
        # These attributes are not handled in C#
        # bbox=None,
        # area=None,
        # length=None,
    )


@pytest.fixture()
def ellipse(plane, interval):
    return Ellipse(
        firstRadius=34,
        secondRadius=22,
        plane=plane,
        domain=interval,
        units="m",
        # These attributes are not handled in C#
        # trimDomain=None,
        # bbox=None,
        # area=None,
        # length=None,
    )


@pytest.fixture()
def polyline(interval):
    return Polyline(
        value=[22, 44, 54.3, 99, 232, 21],
        closed=True,
        domain=interval,
        units="m",
        # These attributes are not handled in C#
        # bbox=None,
        # area=None,
        # length=None,
    )


@pytest.fixture()
def curve(interval):
    return Curve(
        degree=90,
        periodic=True,
        rational=False,
        closed=True,
        domain=interval,
        points=[23, 21, 44, 43, 56, 76, 1, 3, 2],
        weights=[23, 11, 23],
        knots=[22, 45, 76, 11],
        units="m",
        # These attributes are not handled in C#
        # displayValue=None,
        # bbox=None,
        # area=None,
        # length=None,
    )


@pytest.fixture()
def polycurve(interval, curve, polyline):
    return Polycurve(
        segments=[curve, polyline],
        domain=interval,
        closed=True,
        units="m",
        # These attributes are not handled in C#
        # bbox=None,
        # area=None,
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
def surface(interval):
    return Surface(
        degreeU=33,
        degreeV=44,
        rational=True,
        pointData=[1, 2.2, 3, 4, 5, 6, 7, 8, 9],
        countU=3,
        countV=4,
        closedU=True,
        closedV=False,
        domainU=interval,
        domainV=interval,
        knotsU=[1.1, 2.2, 3.3, 4.4],
        knotsV=[9, 8, 7, 6, 5, 4.4],
        units="m",
        # These attributes are not handled in C#
        # bbox=None,
        # area=None,
    )


@pytest.fixture()
def brep_face():
    return BrepFace(
        SurfaceIndex=3,
        LoopIndices=[1, 2, 3, 4],
        OuterLoopIndex=2,
        OrientationReversed=False,
    )


@pytest.fixture()
def brep_edge(interval):
    return BrepEdge(
        Curve3dIndex=2,
        TrimIndices=[4, 5, 6, 7],
        StartIndex=2,
        EndIndex=6,
        ProxyCurveIsReversed=True,
        Domain=interval,
    )


@pytest.fixture()
def brep_loop():
    return BrepLoop(FaceIndex=5, TrimIndices=[3, 4, 5], Type=BrepLoopType.Unknown)


@pytest.fixture()
def brep_trim():
    return BrepTrim(
        EdgeIndex=3,
        StartIndex=4,
        EndIndex=6,
        FaceIndex=1,
        LoopIndex=4,
        CurveIndex=7,
        IsoStatus=6,
        TrimType=BrepTrimType.Mated,
        IsReversed=False,
        # These attributes are not handled in C#
        # Domain=None,
    )


@pytest.fixture
def brep(
    mesh,
    box,
    surface,
    curve,
    polyline,
    circle,
    point,
    brep_edge,
    brep_loop,
    brep_trim,
    brep_face,
):
    return Brep(
        provenance="pytest",
        bbox=box,
        area=32,
        volume=54,
        displayValue=mesh,
        Surfaces=[surface, surface, surface],
        Curve3D=[curve, polyline],
        Curve2D=[circle],
        Vertices=[point, point, point, point],
        Edges=[brep_edge],
        Loops=[brep_loop, brep_loop],
        Trims=[brep_trim],
        Faces=[brep_face, brep_face],
        IsClosed=False,
        Orientation=3,
    )


@pytest.fixture
def geometry_objects_dict(
    point,
    vector,
    plane,
    line,
    arc,
    circle,
    ellipse,
    polyline,
    curve,
    polycurve,
    surface,
    brep_trim,
):
    return {
        "point": point,
        "vector": vector,
        "plane": plane,
        "line": line,
        "arc": arc,
        "circle": circle,
        "ellipse": ellipse,
        "polyline": polyline,
        "curve": curve,
        "polycurve": polycurve,
        "surface": surface,
        "brep_trim": brep_trim,
    }


@pytest.mark.parametrize(
    "object_name",
    [
        "point",
        "vector",
        "plane",
        "line",
        "arc",
        "circle",
        "ellipse",
        "polyline",
        "curve",
        "polycurve",
        "surface",
        "brep_trim",
    ],
)
def test_to_and_from_list(object_name: str, geometry_objects_dict):
    obj = geometry_objects_dict[object_name]
    assert hasattr(obj, "to_list")
    assert hasattr(obj, "from_list")

    chunks = obj.to_list()
    assert isinstance(chunks, list)

    object_class = obj.__class__
    decoded_object: Base = object_class.from_list(chunks)
    assert decoded_object.get_id() == obj.get_id()


def test_brep_surfaces_value_serialization(surface):
    brep = Brep()
    assert brep.Surfaces is None
    assert brep.SurfacesValue is None
    brep.Surfaces = [surface, surface]
    assert brep.SurfacesValue == ObjectArray.from_objects([surface, surface]).data

    brep.SurfacesValue = ObjectArray.from_objects([surface]).data
    assert len(brep.Surfaces) == 1
    assert brep.Surfaces[0].get_id() == surface.get_id()


def test_brep_curve2d_values_serialization(curve, polyline, circle):
    brep = Brep()
    assert brep.Curve2D is None
    assert brep.Curve2DValues is None
    brep.Curve2D = [curve, polyline]
    assert brep.Curve2DValues == CurveArray.from_curves([curve, polyline]).data

    brep.Curve2DValues = CurveArray.from_curves([circle]).data
    assert len(brep.Curve2D) == 1
    assert brep.Curve2D[0].get_id() == circle.get_id()


def test_brep_curve3d_values_serialization(curve, polyline, circle):
    brep = Brep()
    assert brep.Curve3D is None
    assert brep.Curve3DValues is None
    brep.Curve3D = [curve, polyline]
    assert brep.Curve3DValues == CurveArray.from_curves([curve, polyline]).data

    brep.Curve3DValues = CurveArray.from_curves([circle]).data
    assert len(brep.Curve3D) == 1
    assert brep.Curve3D[0].get_id() == circle.get_id()


def test_brep_vertices_values_serialization():
    brep = Brep()
    brep.VerticesValue = [1, 1, 1, 1, 2, 2, 2, 3, 3, 3]
    assert brep.Vertices[0].get_id() == Point(x=1, y=1, z=1, units=Units.mm).get_id()
    assert brep.Vertices[1].get_id() == Point(x=2, y=2, z=2, units=Units.mm).get_id()
    assert brep.Vertices[2].get_id() == Point(x=3, y=3, z=3, units=Units.mm).get_id()


def test_trims_value_serialization():
    brep = Brep()
    brep.TrimsValue = [
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        0,
        1,
        0,
        0,
        0,
        0,
        1,
        2,
        1,
        1,
    ]

    assert (
        brep.Trims[0].get_id()
        == BrepTrim(
            EdgeIndex=0,
            StartIndex=0,
            EndIndex=0,
            FaceIndex=0,
            LoopIndex=0,
            CurveIndex=0,
            IsoStatus=1,
            TrimType=BrepTrimType.Boundary,
            IsReversed=False,
        ).get_id()
    )

    assert (
        brep.Trims[1].get_id()
        == BrepTrim(
            EdgeIndex=1,
            StartIndex=0,
            EndIndex=0,
            FaceIndex=0,
            LoopIndex=0,
            CurveIndex=1,
            IsoStatus=2,
            TrimType=BrepTrimType.Boundary,
            IsReversed=True,
        ).get_id()
    )


def test_loops_value_serialization():
    brep = Brep()
    brep.LoopsValue = [6, 0, 1, 0, 1, 2, 3]

    assert brep == brep.Loops[0]._Brep  # pylint: disable=protected-access
    assert (
        brep.Loops[0].get_id()
        == BrepLoop(
            FaceIndex=0, Type=BrepLoopType(1), TrimIndices=[0, 1, 2, 3]
        ).get_id()
    )


def test_edges_value_serialization():
    brep = Brep()
    brep.EdgesValue = [8, 0, 0, 1, 0, -8.13345756858629, 8.13345756858629, 1, 3]

    assert brep == brep.Edges[0]._Brep  # pylint: disable=protected-access
    assert (
        brep.Edges[0].get_id()
        == BrepEdge(
            Curve3dIndex=0,
            StartIndex=0,
            EndIndex=1,
            ProxyCurveIsReversed=False,
            Domain=Interval(start=-8.13345756858629, end=8.13345756858629),
            TrimIndices=[1, 3],
        ).get_id()
    )


def test_faces_value_serialization():
    brep = Brep()
    brep.FacesValue = [4, 0, 0, 1, 0]

    assert brep == brep.Faces[0]._Brep  # pylint: disable=protected-access
    assert (
        brep.Faces[0].get_id()
        == BrepFace(
            SurfaceIndex=0, OuterLoopIndex=0, OrientationReversed=True, LoopIndices=[0]
        ).get_id()
    )


def test_serialized_brep_attributes(brep: Brep):
    transport = MemoryTransport()
    serialized = operations.serialize(brep, [transport])
    serialized_dict = json.loads(serialized)

    removed_keys = [
        "Surfaces",
        "Curve3D",
        "Curve2D",
        "Vertices",
        "Trims",
        "Loops",
        "Edges",
        "Faces",
    ]

    for k in removed_keys:
        assert k not in serialized_dict


def test_mesh_create():
    vertices = [2, 1, 2, 4, 77.3, 5, 33, 4, 2]
    faces = [1, 2, 3, 4, 5, 6, 7]
    mesh = Mesh.create(vertices, faces)

    with pytest.raises(SpeckleException):
        bad_mesh = Mesh.create(vertices=7, faces=faces)  # noqa: F841

    assert mesh.vertices == vertices
    assert mesh.textureCoordinates == []
