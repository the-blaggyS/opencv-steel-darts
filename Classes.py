import math

import numpy as np


class Game:
    def __init__(self):
        self.start_score = 301
        self.players = []
        self.current_player = 0

    def next_player(self):
        self.current_player += 1
        self.current_player %= len(self.players)

    def get_current_player(self):
        return self.players[self.current_player]


class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.darts = 0

    def set_name(self, name):
        self.name = name


class GUIDef:
    def __init__(self):
        self.e1 = []
        self.e2 = []
        self.dart1entry = []
        self.dart2entry = []
        self.dart3entry = []
        self.final_entry = []


class DartDef:
    def __init__(self):
        self.base = -1
        self.multiplier = -1
        self.magnitude = -1
        self.angle = -1
        self.corners = -1


class Ellipse:
    def __init__(self, a, b, x, y, angle):
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        self.angle = angle


class Line:
    def __init__(self, rho, theta):
        self.rho = rho
        self.theta = theta
        self.a = np.cos(self.theta)
        self.b = np.sin(self.theta)
        self.x0 = self.a * rho
        self.y0 = self.b * rho
        self.x1 = int(self.x0 + 2000 * (-self.b))
        self.y1 = int(self.y0 + 2000 * self.a)
        self.x2 = int(self.x0 - 2000 * (-self.b))
        self.y2 = int(self.y0 - 2000 * self.a)
        self.p1 = (self.x1, self.y1)
        self.p2 = (self.x2, self.y2)


class CalibrationData:
    def __init__(self):
        # for perspective transform
        self.top = []
        self.bottom = []
        self.left = []
        self.right = []
        self.points = []
        # radii of the rings, there are 6 in total
        self.ring_radius = [14, 32, 194, 214, 320, 340]
        self.center_dartboard = (400, 400)
        self.sector_angle = 2 * math.pi / 20
        self.dst_points = []
        self.transformation_matrix = [[]]
