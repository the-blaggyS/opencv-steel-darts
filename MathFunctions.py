import math
import numpy as np


# distance point to line
def dist(x1, y1, x2, y2, x3, y3):  # x3,y3 is the point
    px = x2 - x1
    py = y2 - y1

    something = px**2 + py**2

    u = ((x3 - x1) * px + (y3 - y1) * py) / float(something)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    # Note: If the actual distance does not matter,
    # if you only want to compare what this function
    # returns to other results of this function, you
    # can just return the squared distance instead
    # (i.e. remove the sqrt) to gain a little performance

    distance = math.sqrt(dx**2 + dy**2)

    return distance


# closest point on line to point
def closest_point(x1, y1, x2, y2, x3, y3):  # x3,y3 is the point

    line1 = np.array((x1, y1))
    line2 = np.array((x2, y2))
    point = np.array((x3, y3))

    n = line2 - line1
    v = point - line1

    z = line1 + n * (np.dot(v, n) / np.dot(n, n))

    return z


def intersect_line_circle(center, radius, p1, p2):
    baX = p2[0] - p1[0]
    baY = p2[1] - p1[1]
    caX = center[0] - p1[0]
    caY = center[1] - p1[1]

    a = baX**2 + baY**2
    bBy2 = baX * caX + baY * caY
    c = caX**2 + caY**2 - radius**2

    pBy2 = bBy2 / a
    q = c / a

    disc = pBy2**2 - q
    if disc < 0:
        return False, None, False, None

    tmp_sqrt = math.sqrt(disc)
    ab_scaling_factor1 = -pBy2 + tmp_sqrt
    ab_scaling_factor2 = -pBy2 - tmp_sqrt

    pint1 = p1[0] - baX * ab_scaling_factor1, p1[1] - baY * ab_scaling_factor1
    if disc == 0:
        return True, pint1, False, None

    pint2 = p1[0] - baX * ab_scaling_factor2, p1[1] - baY * ab_scaling_factor2
    return True, pint1, True, pint2
