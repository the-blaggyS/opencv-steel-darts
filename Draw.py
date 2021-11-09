import math

import cv2

from Classes import CalibrationData


def draw_board(image, calibration_data=CalibrationData()):
    for ring_radius in calibration_data.ring_radius:
        cv2.circle(image, (400, 400), ring_radius, (255, 255, 255), 1)
    for sector in range(20):
        cv2.line(image, (400, 400),
                 (int(400 + calibration_data.ring_radius[5] * math.cos((sector + 0.5) * calibration_data.sector_angle)),
                  int(400 + calibration_data.ring_radius[5] * math.sin((sector + 0.5) * calibration_data.sector_angle))),
                 (255, 255, 255), 1)
    return image


def draw_line(image, line):
    cv2.line(image, (line.x1, line.y1), (line.x2, line.y2), (0, 0, 255), 2)
