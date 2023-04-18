#Preview: https://speckle.xyz/streams/d2e38baf76/commits/505b8630c6?c=%5B0.0581,-0.28286,0.32333,0.23898,0.12909,-0.03397,0,1%5D

from typing import List, Tuple
from svg.path import parse_path
import sys, math, requests, json
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.server import ServerTransport
from specklepy.objects import Base
from specklepy.objects.geometry import Point, Line, Arc, Circle, Ellipse, SpiralType, Spiral, Polycurve, Polyline, Mesh, Vector, Plane, Interval


def flatten(nested_list):
    flattened_list = []
    for sublist in nested_list:
        flattened_list.extend(sublist)
    return flattened_list


def send_to_speckle(host, stream_id, objects, msg=None):
    account = get_default_account()
    client = SpeckleClient(host=host)
    client.authenticate_with_account(account)
    transport = ServerTransport(client=client, stream_id=stream_id)
    class SpeckleExport(Base):
        objects = None
    obj = SpeckleExport(objects=objects)
    hash = operations.send(base=obj, transports=[transport])
    commit_id = client.commit.create(stream_id = stream_id, object_id = hash, message = msg)
    print(f"Export ID: {commit_id}")


objList = []

#Vector - start, note: cannot be visualised
vectorObj = Vector.from_coords(1, 0, 0)
#Vector - end

#Point - start
pointObj = Point(x=50, y=190, z=13, units="mm")
objList.append(pointObj)
#Point - end

#Line - start
lineObj = Line(start=Point(x=75, y=30, z=13), end=Point(x=25, y=30, z=13), units="mm")
objList.append(lineObj)
#Line - end

#Arc - start
arcPlane = Plane(origin = Point.from_coords(200, 30, 13), normal = Vector.from_coords(0, 0, 1), xdir = Vector.from_coords(1, 0, 0), ydir = Vector.from_coords(0, 1, 0), units="mm")
arcInterval = Interval(start=0, end=1, totalChildrenCount=1)
arcObj = Arc(startPoint=Point(x=0, y=20, z=13), midPoint=Point(x=500, y=0, z=13), endPoint=Point(x=1000, y=20, z=13), plane=arcPlane, radius=20, interval=arcInterval, units="mm")
objList.append(arcObj)
#Arc - end

#Circle - start
circlePlane = Plane(origin = Point(x=350, y=35, z=13, units="mm"), normal = Vector(x=0, y=0, z=1), xdir = Vector(x=1, y=0, z=0), ydir = Vector(x=0, y=1, z=0), units="mm")
circleObj = Circle(radius=20.0, plane=circlePlane, units="mm")
objList.append(circleObj)
#Circle - end

#Ellipse - start
# ellipsePlane = Plane(origin = Point(x=1, y=0, z=13, units="mm"), normal = Vector(x=0, y=1, z=0), xdir = Vector(x=1, y=0, z=0), ydir = Vector(x=0, y=1, z=0), units="mm")
# ellipseObj = Ellipse(firstRadius=40.0, secondRadius=20.0, plane=ellipsePlane, units="mm")
# objList.append(ellipseObj)
#Ellipse - end

#Spiral - start
# spiralPlane = Plane(origin = Point(x=1, y=0, z=13, units="mm"), normal = Vector(x=0, y=1, z=0), xdir = Vector(x=1, y=0, z=0), ydir = Vector(x=0, y=1, z=0), units="mm")
# p1 = Point(x=50, y=190, z=13, units="mm")
# p2 = Point(x=0, y=280, z=13, units="mm")
# spiralObj = Spiral(startPoint=p1, endPoint=p2, plane=spiralPlane, turns=4, pitchAxis=Vector(x=0, y=1, z=0), spiralType=SpiralType.BiquadraticParabola)
# objList.append(spiralObj)
#Spiral - end

#Polycurve - start
p = 340
xp = 185
p1 = Point(x=50+p, y=0+xp, z=13, units="mm")
p2 = Point(x=0+p, y=0+xp, z=13, units="mm")
arcPlane = Plane(origin = Point.from_coords(0+p, 0+xp, 13), normal = Vector.from_coords(1, 0, 0), xdir = Vector.from_coords(0, 1, 0), ydir = Vector.from_coords(0, 1, 0), units="mm")
arcInterval = Interval(start=0, end=1, totalChildrenCount=1)
arcObj = Arc(startPoint=p1, midPoint=Point(x=250+p, y=40+xp, z=13), endPoint=p2, plane=arcPlane, radius=20, interval=arcInterval, units="mm")
segmentObjs = [p1, arcObj, p2]
polycurveObj = Polycurve(segments=segmentObjs)
objList.append(polycurveObj)
#Polycurve - end

#Polyline - start
coordZ = 13
polylineObj = Polyline.from_points([Point(x=175, y=175, z=coordZ, units="mm"), Point(x=225, y=175, z=coordZ, units="mm"), Point(x=225, y=200, z=coordZ, units="mm"), Point(x=175, y=200, z=coordZ, units="mm"), Point(x=175, y=175, z=coordZ, units="mm")])
objList.append(polylineObj)
#Polyline - end

#Mesh - start, note: cuboid
height = 100
bottomVertices = [0, 0, 0, 100, 0, 0, 100, 100, 0, 0, 100, 0, 0, 0, 0] #automatic close
topVertices = [v + height if i % 3 == 2 else v for i, v in enumerate(bottomVertices)]
allVertices = bottomVertices + topVertices

bottom_faces = []
i = 0
for x in range(len(bottomVertices)-1):
    if x % 3 == 2:
        bottom_faces.append(i)
        i += 1
p = bottom_faces.insert(0, len(bottom_faces))

top_faces = []
for index, i in enumerate(bottom_faces[1:]):
    if index == 0:
        top_faces.append(bottom_faces[0])
    top_faces.append(bottom_faces[0]+1 + bottom_faces[i+1])

tempList = []
faces = []

for i in range(len(bottom_faces)-1):
    between1 = bottom_faces[i+1]+1
    list1 = [4, bottom_faces[i+1], between1]
    mXtop_faces = top_faces[-1:][0]
    between2 = top_faces[i+1]+1
    if between2 > mXtop_faces:
        between2 = top_faces[1]
    list2 = [between2, top_faces[i+1]]
    tempList = list1 + list2
    faces.append(tempList)

allFaces = bottom_faces + top_faces + flatten(faces)

meshObj = Mesh(
    vertices=allVertices,
    faces=allFaces,
    units="mm"
)
#Mesh - end


#Text - start
class Text:
    def __init__(self, text: str = None, font_family: str = None, bounding_box: bool = None, xyz: Tuple[float, float, float] = None, rotation: float = None, scale: float = None):
        self.text = text
        self.font_family = font_family
        self.bounding_box = bounding_box
        self.originX, self.originY, self.originZ = xyz or (0, 0, 0)
        self.x, self.y, self.z = xyz or (0, 0, 0)
        self.rotation = rotation
        self.scale_factor = scale or 1.0
        self.character_offset = 250 * self.scale_factor
        self.spacie = 200 * self.scale_factor
        self.path_list = self.load_path()
        

    def load_path(self) -> List[str]:
        url = f"https://raw.githubusercontent.com/3BMLabs/building.py/main/library/text/json/Arial.json"
        response = requests.get(url)
        glyph_data = response.json()
        return [
            glyph_data[letter]["glyph-path"]
            for letter in self.text if letter in glyph_data
        ]


    def write(self) -> List[List[Polyline]]:
        word_list = []
        for letter_path in self.path_list:
            path = parse_path(letter_path)
            output_list = []
            points = []
            allPoints = []

            for segment in path:
                segment_type = segment.__class__.__name__
                if segment_type == 'Move':
                    if len(points) > 0:
                        points = []
                        allPoints.append("M")
                    subpath_started = True
                elif subpath_started:
                    if segment_type == 'Line':
                        points.extend([(segment.start.real*self.scale_factor, segment.start.imag*self.scale_factor), (segment.end.real, segment.end.imag*self.scale_factor)])
                        allPoints.extend([(segment.start.real*self.scale_factor, segment.start.imag*self.scale_factor), (segment.end.real*self.scale_factor, segment.end.imag*self.scale_factor)])
                    elif segment_type == 'CubicBezier':
                        points.extend(segment.sample(10))
                        allPoints.extend(segment.sample(10))
                    elif segment_type == 'QuadraticBezier':
                        for i in range(11):
                            t = i / 10.0
                            point = segment.point(t)
                            points.append((point.real*self.scale_factor, point.imag*self.scale_factor))
                            allPoints.append((point.real*self.scale_factor, point.imag*self.scale_factor))
                    elif segment_type == 'Arc':
                        points.extend(segment.sample(10))
                        allPoints.extend(segment.sample(10))
            if points:
                output_list.append(self.convert_points_to_polyline(allPoints))
                if self.bounding_box == True and self.bounding_box != None:
                    output_list.append(self.calculate_bounding_box(allPoints)[0])
                width = self.calculate_bounding_box(allPoints)[1]

                self.x += width + self.character_offset
            word_list.append(output_list)
        return word_list


    def calculate_bounding_box(self, points):
        points = [elem for elem in points if elem != 'M']
        x_values = [point[0] for point in points]
        y_values = [point[1] for point in points]

        min_x = min(x_values)
        max_x = max(x_values)
        min_y = min(y_values)
        max_y = max(y_values)

        ltX = self.x
        ltY = self.y + max_y - min_y

        lbX = self.x
        lbY = self.y + min_y - min_y

        rtX = self.x + max_x - min_x
        rtY = self.y + max_y - min_y

        rbX = self.x + max_x - min_x
        rbY = self.y + min_y - min_y
        
        left_top = Point.from_coords(ltX, ltY, self.z)
        left_bottom = Point.from_coords(lbX, lbY, self.z)
        right_top = Point.from_coords(rtX, rtY, self.z)
        right_bottom = Point.from_coords(rbX, rbY, self.z)

        bounding_box_polyline = self.rotate_polyline([left_top, right_top, right_bottom, left_bottom, left_top])

        char_width = rtX - ltX
        char_height = ltY - lbY
        return bounding_box_polyline, char_width, char_height


    def convert_points_to_polyline(self, points: list[tuple[float, float]]) -> Polyline:
        if self.rotation == None:
            self.rotation = 0

        output_list = []
        sub_lists = [[]]

        tempPoints = [elem for elem in points if elem != 'M']
        x_values = [point[0] for point in tempPoints]
        y_values = [point[1] for point in tempPoints]

        xmin = min(x_values)
        ymin = min(y_values)

        for item in points:

            if item == 'M':
                sub_lists.append([])
            else:
                x = item[0] + self.x - xmin
                y = item[1] + self.y - ymin
                z = self.z
                eput = x, y, z
                sub_lists[-1].append(eput)

        output_list = []

        for element in sub_lists:
            tmp = []
            for point in element:
                x = point[0]
                y = point[1]
                z = self.z
                tmp.append(Point.from_coords(x,y,z))
            output_list.append(tmp)

        polyline_list = []
        for pts in output_list:
            polyline_list.append(self.rotate_polyline(pts))
        return polyline_list


    def rotate_polyline(self, polylinePoints):
        translated_points = [(coord.x - self.originX, coord.y - self.originY) for coord in polylinePoints]

        radians = math.radians(self.rotation)
        cos = math.cos(radians)
        sin = math.sin(radians)
        rotated_points = [
            (
                (x - self.originX) * cos - (y - self.originY) * sin + self.originZ,
                (x - self.originX) * sin + (y - self.originY) * cos + self.originZ
            ) for x, y in translated_points
        ]

        pts_list = []
        for x, y in rotated_points:
            pts_list.append(Point(x=x,y=y,z=self.z, units="mm"))

        return Polyline.from_points(pts_list)


#Platform - start
def Platform(height, xyz, btmShape=None, text=None, txyz=None):
    x, y, z = xyz
    
    if btmShape == "btmShape":
        btmShape = [20+x,0+y,0+z,80+x,0+y,0+z,100+x,20+y,0+z,100+x,80+y,0+z,80+x,100+y,0+z,20+x,100+y,0+z,0+x,80+y,0+z,0+x,20+y,0+z,20+x,0+y,0+z]
    elif btmShape == "OveralShape":
        btmShape = [-50,-50,0, 600, -50, 0, 600, 300, 0, -50, 300, 0, -50, -50, 0]
    elif btmShape == "Example0":
        btmShape = [0+x,0+y,0+z, 0+x,35+y,0+z, 35+x,35+y,0+z, 35+x,0+y,0+z, 0+x,0+y,0+z]
    elif btmShape == "Example1":
        btmShape = [0+x,0+y,0+z, 50+x,0+y,0+z, 50+x,5+y,0+z, 27+x,5+y,0+z, 27+x,35+y,0+z, 50+x,35+y,0+z, 50+x,40+y,0+z, 0+x,40+y,0+z, 0+x,35+y,0+z, 23+x,35+y,0+z, 23+x,5+y,0+z, 0+x,5+y,0+z, 0+x,0+y,0+z]

    if text != None and txyz != None:
        tx, ty, tz = txyz
        t = Text(text=text, font_family="arial", bounding_box=False, xyz=[-tx, -ty, 15], rotation=0, scale=0.007).write()

    topVertices = [v + height if i % 3 == 2 else v for i, v in enumerate(btmShape)]
    allVertices = btmShape + topVertices

    bottom_faces = []
    i = 0
    for x in range(len(btmShape)-1):
        if x % 3 == 2:
            bottom_faces.append(i)
            i += 1
    p = bottom_faces.insert(0, len(bottom_faces))

    top_faces = []
    for index, i in enumerate(bottom_faces[1:]):
        if index == 0:
            top_faces.append(bottom_faces[0])
        top_faces.append(bottom_faces[0]+1 + bottom_faces[i+1])

    tempList = []
    side_faces = []

    for i in range(len(bottom_faces)-1):
        between1 = bottom_faces[i+1]+1
        list1 = [4, bottom_faces[i+1], between1]

        mXtop_faces = top_faces[-1:][0]
        between2 = top_faces[i+1]+1
        if between2 > mXtop_faces:
            between2 = top_faces[1]
        list2 = [between2, top_faces[i+1]]

        tempList = list1 + list2
        side_faces.append(tempList)

    allFaces = bottom_faces + top_faces + flatten(side_faces)

    meshPlatform = Mesh(
        vertices=allVertices,
        faces=allFaces,
        units="mm"
    )
    if text != None:
        return meshPlatform, t
    else:
        return meshPlatform


MeshExample0 = Platform(5, [481,160,13], btmShape="Example0")
objList.append(MeshExample0)

MeshExample1 = Platform(5, [475,10,13], btmShape="Example1")
objList.append(MeshExample1)

MeshBase0 = Platform(10, [0,0,0], btmShape="OveralShape")
objList.append(MeshBase0)

MeshBase1 = Platform(2, [0,0,10], btmShape="btmShape", text="LINE", txyz=[0+20,0+50,10])
objList.append(MeshBase1)

MeshBase2 = Platform(2, [150,0,10], btmShape="btmShape", text="ARC", txyz=[150+18,0+50,10])
objList.append(MeshBase2)

MeshBase3 = Platform(2, [150,150,10], btmShape="btmShape", text="POLYLINE", txyz=[150+0,150+50,10])
objList.append(MeshBase3)

MeshBase4 = Platform(2, [0,150,10], btmShape="btmShape", text="POINT", txyz=[0+15,150+50,10])
objList.append(MeshBase4)

MeshBase5 = Platform(2, [300,0,10], btmShape="btmShape", text="CIRCLE", txyz=[300+10,0+50,10])
objList.append(MeshBase5)

MeshBase6 = Platform(2, [300,150,10], btmShape="btmShape", text="POLYCURVE", txyz=[290,150+50,10])
objList.append(MeshBase6)

MeshBase7 = Platform(2, [450,0,10], btmShape="btmShape", text="MESH2", txyz=[450+10,0+50,10])
objList.append(MeshBase7)

MeshBase8 = Platform(2, [450,150,10], btmShape="btmShape", text="MESH1", txyz=[450+10,150+50,10])
objList.append(MeshBase8)
#Platform - end


send_to_speckle(host="https://speckle.xyz", stream_id="d2e38baf76", objects=objList, msg="Objects")
