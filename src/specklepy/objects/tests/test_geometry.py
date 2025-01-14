import unittest
from specklepy.objects.geometry.point import Point
from specklepy.objects.geometry.vector import Vector
from specklepy.objects.geometry.line import Line
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.geometry.arc import Arc
from specklepy.objects.geometry.mesh import Mesh
from specklepy.objects.geometry.polyline import Polyline
from specklepy.objects.models.units import Units
from specklepy.objects.other import Transform
from specklepy.objects.primitive import Interval
from specklepy.core.api.operations import serialize, deserialize


class TestPoint(unittest.TestCase):
    def setUp(self):
        self.p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
        self.p2 = Point(x=4.0, y=6.0, z=8.0, units=Units.m)
        self.p3 = Point(x=1000.0, y=2000.0, z=3000.0, units=Units.mm)

    def test_creation(self):
        self.assertEqual(self.p1.x, 1.0)
        self.assertEqual(self.p1.y, 2.0)
        self.assertEqual(self.p1.z, 3.0)
        self.assertEqual(self.p1.units, Units.m.value)

    def test_distance_to(self):
        distance = self.p1.distance_to(self.p2)
        expected = ((3.0**2 + 4.0**2 + 5.0**2) ** 0.5)
        self.assertAlmostEqual(distance, expected)

        distance = self.p1.distance_to(self.p3)
        self.assertAlmostEqual(distance, 0.0)

    def test_transformation(self):
        transform = Transform(matrix=[
            2.0, 0.0, 0.0, 1.0,
            0.0, 2.0, 0.0, 1.0,
            0.0, 0.0, 2.0, 1.0,
            0.0, 0.0, 0.0, 1.0
        ], units=Units.m)

        success, transformed = self.p1.transform_to(transform)
        self.assertTrue(success)
        self.assertEqual(transformed.x, 3.0)
        self.assertEqual(transformed.y, 5.0)
        self.assertEqual(transformed.z, 7.0)

    def test_serialization(self):
        serialized = serialize(self.p1)
        deserialized = deserialize(serialized)

        self.assertEqual(deserialized.x, self.p1.x)
        self.assertEqual(deserialized.y, self.p1.y)
        self.assertEqual(deserialized.z, self.p1.z)
        self.assertEqual(deserialized.units, self.p1.units)


class TestVector(unittest.TestCase):
    def setUp(self):
        self.v1 = Vector(x=1.0, y=2.0, z=3.0, units=Units.m)
        self.v2 = Vector(x=4.0, y=5.0, z=6.0, units=Units.m)

    def test_creation(self):
        self.assertEqual(self.v1.x, 1.0)
        self.assertEqual(self.v1.y, 2.0)
        self.assertEqual(self.v1.z, 3.0)
        self.assertEqual(self.v1.units, Units.m.value)

    def test_length(self):
        length = self.v1.length
        expected = (1.0**2 + 2.0**2 + 3.0**2) ** 0.5
        self.assertAlmostEqual(length, expected)

    def test_transformation(self):
        transform = Transform(matrix=[
            2.0, 0.0, 0.0, 1.0,
            0.0, 2.0, 0.0, 1.0,
            0.0, 0.0, 2.0, 1.0,
            0.0, 0.0, 0.0, 1.0
        ], units=Units.m)

        success, transformed = self.v1.transform_to(transform)
        self.assertTrue(success)
        self.assertEqual(transformed.x, 2.0)
        self.assertEqual(transformed.y, 4.0)
        self.assertEqual(transformed.z, 6.0)

    def test_serialization(self):
        serialized = serialize(self.v1)
        deserialized = deserialize(serialized)

        self.assertEqual(deserialized.x, self.v1.x)
        self.assertEqual(deserialized.y, self.v1.y)
        self.assertEqual(deserialized.z, self.v1.z)
        self.assertEqual(deserialized.units, self.v1.units)


class TestLine(unittest.TestCase):
    def setUp(self):
        self.p1 = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
        self.p2 = Point(x=3.0, y=4.0, z=0.0, units=Units.m)
        self.line = Line(start=self.p1, end=self.p2, units=Units.m)

    def test_creation(self):
        self.assertEqual(self.line.start.x, 0.0)
        self.assertEqual(self.line.end.x, 3.0)
        self.assertEqual(self.line.units, Units.m.value)

    def test_length(self):
        self.assertEqual(self.line.length, 5.0)

    def test_transformation(self):
        transform = Transform(matrix=[
            2.0, 0.0, 0.0, 1.0,
            0.0, 2.0, 0.0, 1.0,
            0.0, 0.0, 2.0, 1.0,
            0.0, 0.0, 0.0, 1.0
        ], units=Units.m)

        success, transformed = self.line.transform_to(transform)
        self.assertTrue(success)
        self.assertEqual(transformed.start.x, 1.0)
        self.assertEqual(transformed.end.x, 7.0)

    def test_serialization(self):
        serialized = serialize(self.line)
        deserialized = deserialize(serialized)

        self.assertEqual(deserialized.start.x, self.line.start.x)
        self.assertEqual(deserialized.end.x, self.line.end.x)
        self.assertEqual(deserialized.units, self.line.units)


class TestPolyline(unittest.TestCase):
    def setUp(self):
        self.vertices = [0.0, 0.0, 0.0,
                         1.0, 0.0, 0.0,
                         1.0, 1.0, 0.0,
                         0.0, 1.0, 0.0]
        self.polyline = Polyline(
            value=self.vertices,
            closed=True,
            units=Units.m,
            domain=Interval(start=0.0, end=1.0)
        )

    def test_creation(self):
        self.assertEqual(len(self.polyline.value), 12)
        self.assertTrue(self.polyline.closed)
        self.assertEqual(self.polyline.units, Units.m.value)

    def test_length(self):
        expected_length = 4.0
        self.assertAlmostEqual(self.polyline.length, expected_length)

    def test_get_points(self):
        points = self.polyline.get_points()
        self.assertEqual(len(points), 4)
        self.assertEqual(points[0].x, 0.0)
        self.assertEqual(points[1].x, 1.0)

    def test_transformation(self):
        transform = Transform(matrix=[
            2.0, 0.0, 0.0, 1.0,
            0.0, 2.0, 0.0, 1.0,
            0.0, 0.0, 2.0, 1.0,
            0.0, 0.0, 0.0, 1.0
        ], units=Units.m)

        success, transformed = self.polyline.transform_to(transform)
        self.assertTrue(success)
        points = transformed.get_points()
        self.assertEqual(points[0].x, 1.0)
        self.assertEqual(points[1].x, 3.0)

    def test_serialization(self):
        serialized = serialize(self.polyline)
        deserialized = deserialize(serialized)

        self.assertEqual(deserialized.value, self.polyline.value)
        self.assertEqual(deserialized.closed, self.polyline.closed)
        self.assertEqual(deserialized.units, self.polyline.units)


class TestMesh(unittest.TestCase):
    def setUp(self):
        self.vertices = [
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0,
            1.0, 1.0, 0.0,
            0.0, 1.0, 0.0
        ]
        self.faces = [3, 0, 1, 2, 3, 0, 2, 3]
        self.colors = [255, 0, 0, 255] * 4
        self.area = 1.0
        self.volume = 0.0

        self.mesh = Mesh(
            vertices=self.vertices.copy(),
            faces=self.faces.copy(),
            colors=self.colors.copy(),
            units=Units.m,
            area=self.area,
            volume=self.volume
        )

    def test_creation(self):
        self.assertEqual(self.mesh.vertices_count, 4)
        self.assertEqual(self.mesh.faces_count, 2)
        self.assertEqual(self.mesh.units, Units.m.value)
        self.assertEqual(self.mesh.area, self.area)
        self.assertEqual(self.mesh.volume, self.volume)

    def test_get_point(self):
        point = self.mesh.get_point(1)
        self.assertEqual(point.x, 1.0)
        self.assertEqual(point.y, 0.0)
        self.assertEqual(point.z, 0.0)
        self.assertEqual(point.units, Units.m.value)

    def test_get_face_vertices(self):
        face_vertices = self.mesh.get_face_vertices(0)
        self.assertEqual(len(face_vertices), 3)
        self.assertEqual(face_vertices[0].x, 0.0)
        self.assertEqual(face_vertices[1].x, 1.0)
        self.assertEqual(face_vertices[0].units, Units.m.value)

    def test_transformation(self):
        transform = Transform(matrix=[
            2.0, 0.0, 0.0, 1.0,
            0.0, 2.0, 0.0, 1.0,
            0.0, 0.0, 2.0, 1.0,
            0.0, 0.0, 0.0, 1.0
        ], units=Units.m)

        test_mesh = Mesh(
            vertices=self.vertices.copy(),
            faces=self.faces.copy(),
            colors=self.colors.copy(),
            units=Units.m,
            area=1.0,
            volume=0.0
        )

        success, transformed = test_mesh.transform_to(transform)

        self.assertTrue(success)
        point = transformed.get_point(0)
        self.assertEqual(point.x, 1.0)
        self.assertEqual(point.y, 1.0)
        self.assertEqual(transformed.area, test_mesh.area)
        self.assertEqual(transformed.volume, test_mesh.volume)

    def test_is_closed(self):
        self.assertFalse(self.mesh.is_closed())

    def test_serialization(self):
        serialized = serialize(self.mesh)
        deserialized = deserialize(serialized)

        self.assertEqual(deserialized.vertices, self.mesh.vertices)
        self.assertEqual(deserialized.faces, self.mesh.faces)
        self.assertEqual(deserialized.colors, self.mesh.colors)
        self.assertEqual(deserialized.units, self.mesh.units)
        self.assertEqual(deserialized.area, self.mesh.area)
        self.assertEqual(deserialized.volume, self.mesh.volume)


class TestPlane(unittest.TestCase):
    def setUp(self):
        self.origin = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
        self.normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
        self.xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
        self.ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)
        self.plane = Plane(
            origin=self.origin,
            normal=self.normal,
            xdir=self.xdir,
            ydir=self.ydir,
            units=Units.m
        )

    def test_creation(self):
        self.assertEqual(self.plane.origin.x, 0.0)
        self.assertEqual(self.plane.normal.z, 1.0)
        self.assertEqual(self.plane.units, Units.m.value)

    def test_transformation(self):
        transform = Transform(matrix=[
            2.0, 0.0, 0.0, 1.0,
            0.0, 2.0, 0.0, 1.0,
            0.0, 0.0, 2.0, 1.0,
            0.0, 0.0, 0.0, 1.0
        ], units=Units.m)

        success, transformed = self.plane.transform_to(transform)
        self.assertTrue(success)
        self.assertEqual(transformed.origin.x, 1.0)
        self.assertEqual(transformed.xdir.x, 2.0)

    def test_serialization(self):
        serialized = serialize(self.plane)
        deserialized = deserialize(serialized)

        self.assertEqual(deserialized.origin.x, self.plane.origin.x)
        self.assertEqual(deserialized.normal.z, self.plane.normal.z)
        self.assertEqual(deserialized.units, self.plane.units)


class TestArc(unittest.TestCase):
    def setUp(self):
        plane = Plane(
            origin=Point(x=0, y=0, z=0, units="m"),
            normal=Vector(x=0, y=0, z=1, units="m"),
            xdir=Vector(x=1, y=0, z=0, units="m"),
            ydir=Vector(x=0, y=1, z=0, units="m"),
            units="m"
        )

        self.arc = Arc(
            plane=plane,
            startPoint=Point(x=1, y=0, z=0, units="m"),
            midPoint=Point(x=0.7071, y=0.7071, z=0, units="m"),
            endPoint=Point(x=0, y=1, z=0, units="m"),
            units="m"
        )

    def test_basic_properties(self):
        self.assertAlmostEqual(self.arc.radius, 1.0, places=3)
        self.assertEqual(self.arc.units, "m")

    def test_transform(self):
        transform = Transform(matrix=[
            2, 0, 0, 1,
            0, 2, 0, 1,
            0, 0, 2, 1,
            0, 0, 0, 1
        ], units="m")

        success, transformed = self.arc.transform_to(transform)
        self.assertTrue(success)
        self.assertAlmostEqual(transformed.radius, 2.0, places=3)

    def test_serialization(self):

        serialized = serialize(self.arc)
        deserialized = deserialize(serialized)

        self.assertEqual(deserialized.units, self.arc.units)
        self.assertAlmostEqual(deserialized.radius, self.arc.radius, places=3)

        self.assertAlmostEqual(deserialized.startPoint.x,
                               self.arc.startPoint.x, places=3)
        self.assertAlmostEqual(deserialized.startPoint.y,
                               self.arc.startPoint.y, places=3)
        self.assertAlmostEqual(deserialized.startPoint.z,
                               self.arc.startPoint.z, places=3)

        self.assertAlmostEqual(deserialized.midPoint.x,
                               self.arc.midPoint.x, places=3)
        self.assertAlmostEqual(deserialized.midPoint.y,
                               self.arc.midPoint.y, places=3)
        self.assertAlmostEqual(deserialized.midPoint.z,
                               self.arc.midPoint.z, places=3)

        self.assertAlmostEqual(deserialized.endPoint.x,
                               self.arc.endPoint.x, places=3)
        self.assertAlmostEqual(deserialized.endPoint.y,
                               self.arc.endPoint.y, places=3)
        self.assertAlmostEqual(deserialized.endPoint.z,
                               self.arc.endPoint.z, places=3)

        self.assertAlmostEqual(deserialized.plane.origin.x,
                               self.arc.plane.origin.x, places=3)
        self.assertAlmostEqual(deserialized.plane.origin.y,
                               self.arc.plane.origin.y, places=3)
        self.assertAlmostEqual(deserialized.plane.origin.z,
                               self.arc.plane.origin.z, places=3)
