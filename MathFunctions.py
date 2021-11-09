import math


# distance point to line
def dist(x1, y1, x2, y2, x3, y3):  # x3,y3 is the point
    px = x2 - x1
    py = y2 - y1

    something = px * px + py * py

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

    dist = math.sqrt(dx * dx + dy * dy)

    return dist


def intersect_line_circle(center, radius, p1, p2):
    baX = p2[0] - p1[0]
    baY = p2[1] - p1[1]
    caX = center[0] - p1[0]
    caY = center[1] - p1[1]

    a = baX * baX + baY * baY
    bBy2 = baX * caX + baY * caY
    c = caX * caX + caY * caY - radius * radius

    pBy2 = bBy2 / a
    q = c / a

    disc = pBy2 * pBy2 - q
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
