from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from tkinter import Entry
from typing import Any, Dict, List, Optional, Tuple

import math
import numpy as np


@dataclass(init=False)
class Point(np.ndarray):
    x: float
    y: float

    def __new__(cls, x, y):
        obj = np.asarray((x, y)).view(cls)
        return obj

    @property
    def x(self):
        return self[0]

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self):
        return self[1]

    @y.setter
    def y(self, value):
        self[1] = value

    def perp(self) -> Point:
        return Point(-self.y, self.x)

    @classmethod
    def cast(cls, obj) -> Point:
        casted_obj = cls(*obj)
        return casted_obj


@dataclass(init=False)
class IntPoint(Point):
    x: int
    y: int

    def __new__(cls, x, y):
        obj = super().__new__(cls, int(x), int(y))
        return obj


@dataclass
class Dart:
    base: int
    multiplier: int
    magnitude: float
    angle: float
    location: Point = field(init=False)
    correctly_detected: Optional[bool] = field(default=True, init=False)

    def asdict(self) -> Dict[str, Any]:
        return {
            'id': uuid.uuid4(),
            'date': datetime.now(),
            'base': self.base,
            'multiplier': self.multiplier,
            'loc_x': self.location.x,
            'loc_y': self.location.y
        }

    def asjson(self) -> Dict[str, str]:
        return {k: str(v) for k, v in self.asdict().items()}


@dataclass
class Capture:
    darts: List[Dart] = field(default_factory=list)


@dataclass
class Player:
    name: str
    score: int = 0
    is_in: bool = False
    captures: List[Capture] = field(default_factory=list)

    def set_name(self, name):
        self.name = name

    def num_darts(self):
        num = 0
        for capture in self.captures:
            num += len(capture.darts)
        return num


@dataclass(init=False)
class GUIDef:
    e1: Entry
    e2: Entry
    dart1entry: Entry
    dart2entry: Entry
    dart3entry: Entry
    final_entry: Entry


@dataclass(init=False)
class Frame(np.ndarray):
    width: int
    height: int

    def __new__(cls, width, height):
        obj = np.asarray((width, height)).view(cls)
        return obj

    @property
    def width(self):
        return self[0]

    @width.setter
    def width(self, value):
        self[0] = value

    @property
    def height(self):
        return self[1]

    @height.setter
    def height(self, value):
        self[1] = value


@dataclass
class Image(np.ndarray):
    pass


@dataclass(init=False)
class Circle(Point):
    r: float

    def __new__(cls, x, y, r):
        obj = super().__new__(cls, x, y)
        obj.r = r
        return obj


@dataclass(init=False)
class Ellipse(Point):
    a: float
    b: float
    angle: float


@dataclass
class Line:
    # rho: InitVar[float]
    # theta: InitVar[float]
    p1: Point
    p2: Point

    # def __init__(self, rho, theta):
    #     self.rho = rho
    #     self.theta = theta
    #
    # def __post_init__(self, rho, theta):
    #     a = np.cos(theta)
    #     b = np.sin(theta)
    #     p0 = Point(a * rho, b * rho)
    #     x1 = p0.x + 2000 * (-b)
    #     y1 = p0.y + 2000 * a
    #     x2 = p0.x - 2000 * (-b)
    #     y2 = p0.y - 2000 * a
    #     self.p1 = Point(x1, y1)
    #     self.p2 = Point(x2, y2)


@dataclass
class VectorLine:
    support_vector: Point
    directional_vector: Point


@dataclass
class CancellationToken:
    is_cancelled: bool = False

    def cancel(self):
        self.is_cancelled = True


@dataclass
class CalibrationData:
    image_shape: Frame
    center_dartboard: Point
    ring_radii: List[int]
    sector_angle: float
    points: List[Point]
    dst_points: List[int]
    offsets: List[Point]
    transformation_matrix: np.ndarray

    def __init__(self, image_shape: Tuple):
        self.image_shape = Frame(*image_shape[1::-1])
        self.center_dartboard = Point(*np.floor_divide(self.image_shape, 2))
        image_height_ratio = self.image_shape.height / 800
        self.ring_radii = np.multiply([14, 32, 194, 214, 320, 340], image_height_ratio).astype(int)
        self.sector_angle = 2 * math.pi / 20
        self.points = [
            self.center_dartboard + np.divide([min(self.image_shape)] * 2, 4) * np.array([-1, -1]),
            self.center_dartboard + np.divide([min(self.image_shape)] * 2, 4) * np.array([1, 1]),
            self.center_dartboard + np.divide([min(self.image_shape)] * 2, 4) * np.array([1, -1]),
            self.center_dartboard + np.divide([min(self.image_shape)] * 2, 4) * np.array([-1, 1])
        ]
        self.dst_points = [12, 2, 17, 7]
        self.offsets = [Point(0.0, 0.0)] * 4
        self.transformation_matrix = np.empty(shape=())
