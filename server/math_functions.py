from typing import Optional

import math
import numpy as np

from server.classes import Circle, Line, Point


# distance point to line
def dist(line: Line, point: Point) -> float:
    px = line.p2.x - line.p1.x
    py = line.p2.y - line.p1.y

    squared_dist = px**2 + py**2

    u = ((point.x - line.p1.x) * px + (point.y - line.p1.y) * py) / float(squared_dist)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = line.p1.x + u * px
    y = line.p1.y + u * py

    dx = x - point.x
    dy = y - point.y

    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance

    distance = math.sqrt(dx**2 + dy**2)
    return distance


# closest point on line to point
def closest_point(line: Line, point: Point) -> Point:

    n = line.p2 - line.p1
    v = point - line.p1

    z = line.p1 + n * (np.dot(v, n) / np.dot(n, n))

    return z


def intersect_line_circle(circle: Circle, line: Line) -> (bool, Optional[Point], bool, Optional[Point]):
    baX = line.p2.x - line.p1.x
    baY = line.p2.y - line.p1.y
    caX = circle.x - line.p1.x
    caY = circle.y - line.p1.y

    a = baX**2 + baY**2
    bBy2 = baX * caX + baY * caY
    c = caX**2 + caY**2 - circle.r**2

    pBy2 = bBy2 / a
    q = c / a

    disc = pBy2**2 - q
    if disc < 0:
        return False, None, False, None

    tmp_sqrt = math.sqrt(disc)
    ab_scaling_factor1 = -pBy2 + tmp_sqrt
    ab_scaling_factor2 = -pBy2 - tmp_sqrt

    pint1 = Point(line.p1.x - baX * ab_scaling_factor1, line.p1.y - baY * ab_scaling_factor1)
    if disc == 0:
        return True, pint1, False, None

    pint2 = Point(line.p1.x - baX * ab_scaling_factor2, line.p1.y - baY * ab_scaling_factor2)
    return True, pint1, True, pint2
