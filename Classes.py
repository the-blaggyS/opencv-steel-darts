import math
import uuid

import numpy as np


class Game:
    def __init__(self, game_mode, players):
        self.id = uuid.uuid4()
        self.game_mode = game_mode
        self.players = players
        self.current_player = 0
        self.is_running = True

        for player in self.players:
            player.score = self.game_mode.get_start_score()

    def next_player(self):
        self.current_player += 1
        self.current_player %= len(self.players)

    def get_current_player(self):
        return self.players[self.current_player]

    def is_finished(self):
        if not self.is_running:
            return True
        else:
            return self.game_mode.is_game_finished(self.players)


class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.is_in = False
        self.turns = []

    def set_name(self, name):
        self.name = name

    def num_darts(self):
        num = 0
        for turn in self.turns:
            num += len(turn)
        return num


class GUIDef:
    def __init__(self):
        self.e1 = []
        self.e2 = []
        self.dart1entry = []
        self.dart2entry = []
        self.dart3entry = []
        self.final_entry = []


class Dart:
    def __init__(self, base, multiplier, magnitude, angle):
        self.base = base
        self.multiplier = multiplier
        self.magnitude = magnitude
        self.angle = angle
        self.corners = []
        self.location = (-1, -1)
        self.correctly_detected = True


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
        self.points = [(200, 150), (600, 450), (600, 150), (200, 450)]
        self.offsets = [[0, 0], [0, 0], [0, 0], [0, 0]]
        self.ring_radius = [14, 32, 194, 214, 320, 340]
        self.center_dartboard = (400, 400)
        self.sector_angle = 2 * math.pi / 20
        self.dst_points = [12, 2, 17, 7]
        self.transformation_matrix = [[]]
