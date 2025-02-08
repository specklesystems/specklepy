from specklepy.objects.geometry import Line, Point
from specklepy.objects.models.units import Units

p_1 = Point(x=0, y=0, z=0, units=Units.m)
p_2 = Point(x=3, y=0, z=0, units=Units.m)

line = Line(start=p_1, end=p_2, units=Units.m)
line.length = line.calculate_length()
print(line.length)
